"""
Voice API — ElevenLabs TTS for situation reports + voice transcription ingestion.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from config import get_settings

router = APIRouter()


def get_coordinator():
    from main import get_coordinator as _get_coordinator
    coord = _get_coordinator()
    if coord is None:
        raise HTTPException(503, "Coordinator not initialized")
    return coord


class TranscribeRequest(BaseModel):
    transcript: str
    camp_name: Optional[str] = None
    caller_location: Optional[str] = None


class SynthesizeRequest(BaseModel):
    text: Optional[str] = None


# ============== TTS SITUATION REPORT ==============

@router.get("/voice/report")
async def get_situation_report(coordinator=Depends(get_coordinator)):
    """Generate a spoken situation summary using AI."""
    from api.copilot import _build_situation_summary
    import google.generativeai as genai
    import asyncio
    import functools

    summary = _build_situation_summary(coordinator)

    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction="You are a disaster response briefing officer. Convert the situation data into a clear, spoken briefing of 3-5 sentences. Use natural spoken language, not bullet points. Be concise and prioritize the most critical information."
        )
        response = await asyncio.to_thread(
            functools.partial(
                model.generate_content,
                [{"role": "user", "parts": [f"Generate a spoken situation briefing from this data:\n\n{summary}"]}],
                generation_config=genai.GenerationConfig(max_output_tokens=300, temperature=0.5)
            )
        )
        report_text = response.text
    except Exception as e:
        print(f"[Voice] AI report generation failed: {e}")
        graph = coordinator.graph_manager.graph
        incidents = len(graph.incidents)
        critical = len([i for i in graph.incidents.values() if i.urgency.value == "critical"])
        available = len([r for r in graph.resources.values() if r.status == "available"])
        report_text = (
            f"Situation report: {incidents} incidents tracked, {critical} critical. "
            f"{available} resources available for deployment. "
            f"All teams maintain current assignments pending further updates."
        )

    return {"report_text": report_text}


@router.post("/voice/synthesize")
async def synthesize_speech(body: SynthesizeRequest, coordinator=Depends(get_coordinator)):
    """Convert text to speech using ElevenLabs TTS API."""
    settings = get_settings()

    if not settings.elevenlabs_api_key:
        raise HTTPException(400, "ELEVENLABS_API_KEY not configured")

    # If no text provided, generate situation report
    if not body.text:
        report = await get_situation_report(coordinator)
        text = report["report_text"]
    else:
        text = body.text

    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB",
                headers={
                    "xi-api-key": settings.elevenlabs_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "model_id": "eleven_turbo_v2_5",
                    "voice_settings": {
                        "stability": 0.7,
                        "similarity_boost": 0.8
                    }
                },
                timeout=30.0
            )
            if response.status_code != 200:
                raise HTTPException(502, f"ElevenLabs API error: {response.status_code}")

            return Response(
                content=response.content,
                media_type="audio/mpeg",
                headers={"Content-Disposition": "inline; filename=report.mp3"}
            )
    except httpx.TimeoutException:
        raise HTTPException(504, "ElevenLabs API timeout")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"ElevenLabs error: {str(e)}")


# ============== VOICE TRANSCRIPTION INGESTION ==============

@router.post("/voice/transcribe")
async def ingest_voice_transcript(body: TranscribeRequest, coordinator=Depends(get_coordinator)):
    """Process a voice transcript as a text signal into the situation graph."""
    from api.websocket import broadcast
    from graph.schemas import VoiceReport

    report_id = f"voice_{str(uuid.uuid4())[:8]}"

    # Feed transcript into the text agent as a signal
    result = await coordinator.process_signal("text", body.transcript, {
        "source": f"voice_report_{report_id}",
        "source_type": "field_coordinator",
        "location_name": body.camp_name or body.caller_location or "Field Report",
    })

    # Store voice report
    report = VoiceReport(
        id=report_id,
        transcript=body.transcript,
        camp_name=body.camp_name,
        caller_location=body.caller_location,
        signals_created=[result.get("signal_id", "")],
        created_at=datetime.utcnow()
    )
    coordinator.graph_manager.add_voice_report(report)

    await broadcast("voice_report", report.model_dump(mode="json"))

    return {
        "report_id": report_id,
        "signal_result": result,
        "status": "processed"
    }


@router.get("/voice/reports")
async def get_voice_reports(coordinator=Depends(get_coordinator)):
    """Get all voice reports."""
    return [r.model_dump(mode="json") for r in coordinator.graph_manager.graph.voice_reports.values()]
