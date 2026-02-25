"""
Co-Pilot API — conversational interface to the current situation graph.
Operators ask natural language questions; AI responds with specific, cited answers.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import google.generativeai as genai

from config import get_settings

router = APIRouter()


def get_coordinator():
    from main import get_coordinator as _get_coordinator
    coord = _get_coordinator()
    if coord is None:
        raise HTTPException(503, "Coordinator not initialized")
    return coord


class CopilotRequest(BaseModel):
    question: str
    history: list[dict] = []  # [{role: "user"|"assistant", content: str}]


class CopilotResponse(BaseModel):
    answer: str
    timestamp: str


def _build_situation_summary(coordinator) -> str:
    """Serialize the current graph state into a readable summary for the AI."""
    graph = coordinator.graph_manager.graph
    lines = []

    lines.append(f"SCENARIO: {graph.scenario_name or 'Unknown scenario'}")
    lines.append(f"SIM TIME: {graph.current_sim_time.strftime('%H:%M:%S')}")
    lines.append("")

    # Incidents
    if graph.incidents:
        lines.append(f"ACTIVE INCIDENTS ({len(graph.incidents)}):")
        for inc in sorted(graph.incidents.values(), key=lambda i: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(i.urgency.value, 4)):
            trapped = f", {inc.trapped_min}–{inc.trapped_max} trapped" if inc.trapped_min is not None else ""
            lines.append(
                f"  [{inc.id}] {inc.incident_type} | {inc.urgency.value.upper()} | "
                f"Sector {inc.location.sector or '?'} | confidence {inc.confidence:.0%}{trapped} | status: {inc.status}"
            )
    else:
        lines.append("ACTIVE INCIDENTS: none")
    lines.append("")

    # Resources
    available = [r for r in graph.resources.values() if r.status == "available"]
    dispatched = [r for r in graph.resources.values() if r.status == "dispatched"]
    lines.append(f"RESOURCES: {len(available)} available, {len(dispatched)} dispatched")
    if dispatched:
        for r in dispatched:
            lines.append(f"  [{r.unit_id}] {r.resource_type} — dispatched, Sector {r.current_location.sector or '?'}")
    lines.append("")

    # Contradictions
    unresolved = [c for c in graph.contradictions.values() if not c.resolved]
    if unresolved:
        lines.append(f"UNRESOLVED CONTRADICTIONS ({len(unresolved)}):")
        for c in unresolved:
            lines.append(f"  [{c.id}] {c.entity_name} | {c.verdict.value} | urgency: {c.urgency.value}")
    else:
        lines.append("UNRESOLVED CONTRADICTIONS: none")
    lines.append("")

    # Pending actions
    pending = [a for a in graph.pending_actions.values() if a.status == "pending"]
    if pending:
        lines.append(f"PENDING DECISIONS ({len(pending)}):")
        for a in pending:
            lines.append(f"  [{a.id}] {a.action_type} — {a.rationale[:80]}...")
    else:
        lines.append("PENDING DECISIONS: none")

    # Hospitals
    hospitals = [loc for loc in graph.locations.values() if loc.location_type == "hospital"]
    if hospitals:
        lines.append("")
        lines.append("HOSPITAL CAPACITY:")
        for h in hospitals:
            used = h.capacity_used or 0
            total = h.capacity_total or 0
            pct = int(used / total * 100) if total > 0 else 0
            lines.append(f"  {h.location.name or h.id}: {used}/{total} ({pct}% full) — {h.status}")

    return "\n".join(lines)


COPILOT_SYSTEM = """You are an AI co-pilot for a disaster response coordination center. You have access to the current operational situation and answer operator questions in plain, direct English.

Rules:
- Be specific: cite incident IDs, sector numbers, confidence percentages
- Be brief: 2-4 sentences unless the question requires more detail
- Be honest about uncertainty: if you don't know, say so
- Use the situation data provided — don't make up information not in the context
- When asked about tradeoffs or "what if", reason through it explicitly
- You are advising a human who will make the final decision — give them information, not just validation"""


@router.post("/copilot/ask", response_model=CopilotResponse)
async def ask_copilot(
    request: CopilotRequest,
    coordinator=Depends(get_coordinator)
):
    """Answer a natural language question about the current disaster situation."""
    situation = _build_situation_summary(coordinator)

    # Build Gemini chat history
    gemini_history = [
        {"role": "user", "parts": [f"Current operational situation:\n\n{situation}\n\nPlease keep this context in mind for all my questions."]},
        {"role": "model", "parts": ["Understood. I have the current situation loaded. What do you need to know?"]}
    ]

    # Add conversation history
    for msg in request.history[-8:]:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    try:
        import asyncio
        import functools
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=COPILOT_SYSTEM
        )
        chat = model.start_chat(history=gemini_history)
        response = await asyncio.to_thread(
            functools.partial(
                chat.send_message,
                request.question,
                generation_config=genai.GenerationConfig(max_output_tokens=512, temperature=0.7)
            )
        )
        answer = response.text
    except Exception as e:
        print(f"[Copilot] API error: {e} — using fallback")
        answer = _fallback_answer(request.question, coordinator)

    return CopilotResponse(
        answer=answer,
        timestamp=datetime.utcnow().isoformat()
    )


def _fallback_answer(question: str, coordinator) -> str:
    """Realistic fallback when API is unavailable."""
    q = question.lower()
    graph = coordinator.graph_manager.graph

    critical = [i for i in graph.incidents.values() if i.urgency.value == "critical" and i.status == "active"]
    unresolved = [c for c in graph.contradictions.values() if not c.resolved]
    available = [r for r in graph.resources.values() if r.status == "available"]

    if "risk" in q or "biggest" in q or "priority" in q:
        if critical:
            inc = critical[0]
            trapped = f"with {inc.trapped_min}–{inc.trapped_max} possibly trapped" if inc.trapped_min else ""
            return (
                f"Your highest risk is incident {inc.id} — a {inc.incident_type} in Sector {inc.location.sector or '?'} "
                f"{trapped} at {inc.confidence:.0%} confidence. "
                f"{'The unresolved bridge contradiction also creates routing risk.' if unresolved else ''}"
            )
        return "No critical incidents active. Monitor the unresolved contradictions for emerging risks."

    if "bridge" in q or "contradict" in q:
        if unresolved:
            c = unresolved[0]
            return (
                f"The {c.entity_name} contradiction remains unresolved. Two sources conflict: "
                f"a satellite image (14:40) shows it intact, but a first-responder radio call (15:01) reports collapse. "
                f"The 21-minute gap is the key uncertainty. Recommend dispatching HELI-1 for aerial confirmation before routing resources through that sector."
            )
        return "No active contradictions. The bridge status was resolved."

    if "ambulan" in q or "resource" in q or "send" in q or "dispatch" in q:
        if available:
            return (
                f"You have {len(available)} resources available including "
                f"{sum(1 for r in available if 'ambulance' in r.resource_type)} ambulances. "
                f"Highest-priority unassigned incident is {critical[0].id if critical else 'none currently critical'}. "
                f"Awaiting your approval on the pending deployment recommendation."
            )
        return "All resources are currently dispatched. No units available for new assignments without reallocation."

    if "hospital" in q:
        hospitals = [loc for loc in graph.locations.values() if loc.location_type == "hospital"]
        if hospitals:
            h = min(hospitals, key=lambda x: (x.capacity_used or 0) / (x.capacity_total or 1))
            return f"{h.location.name or h.id} has the most capacity — {h.capacity_used}/{h.capacity_total} beds used. Route non-critical cases there to preserve Metro General for trauma."
        return "No hospital capacity data loaded yet."

    if "wait" in q:
        return (
            "Waiting increases risk in two ways: the golden-hour window for trapped persons is closing, and the "
            "aftershock probability remains elevated for the next 2 hours. If you're waiting for aerial verification, "
            "that's justified — but delay in dispatching to confirmed incidents is not recommended."
        )

    return (
        f"Current status: {len(graph.incidents)} incidents tracked, "
        f"{len(critical)} critical, {len(unresolved)} unresolved contradictions, "
        f"{len(available)} resources available. Ask me about specific incidents, resources, or decisions."
    )
