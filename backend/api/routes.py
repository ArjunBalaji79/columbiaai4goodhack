"""
REST API routes for CrisisCore backend.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional
import base64

from graph.schemas import (
    SituationGraph,
    SignalInput,
    HumanDecision,
)

router = APIRouter()


def get_coordinator():
    from main import get_coordinator as _get_coordinator
    coord = _get_coordinator()
    if coord is None:
        raise HTTPException(503, "Coordinator not initialized")
    return coord


# ============== HEALTH ==============

@router.get("/health")
async def health():
    return {"status": "ok", "service": "CrisisCore"}


# ============== GRAPH STATE ==============

@router.get("/graph")
async def get_graph(coordinator=Depends(get_coordinator)):
    """Get current situation graph state."""
    return coordinator.graph_manager.graph.model_dump(mode="json")


@router.get("/graph/incidents")
async def get_incidents(coordinator=Depends(get_coordinator)):
    """Get all incidents."""
    return {k: v.model_dump(mode="json") for k, v in coordinator.graph_manager.graph.incidents.items()}


@router.get("/graph/incidents/{incident_id}")
async def get_incident(incident_id: str, coordinator=Depends(get_coordinator)):
    """Get specific incident."""
    if incident_id not in coordinator.graph_manager.graph.incidents:
        raise HTTPException(404, "Incident not found")
    return coordinator.graph_manager.graph.incidents[incident_id].model_dump(mode="json")


@router.get("/graph/resources")
async def get_resources(coordinator=Depends(get_coordinator)):
    """Get all resources."""
    return {k: v.model_dump(mode="json") for k, v in coordinator.graph_manager.graph.resources.items()}


@router.get("/graph/stats")
async def get_stats(coordinator=Depends(get_coordinator)):
    """Get dashboard statistics."""
    return coordinator.graph_manager.get_stats()


# ============== SIGNAL INGESTION ==============

@router.post("/signals/image")
async def ingest_image(
    file: UploadFile = File(...),
    location_lat: Optional[float] = None,
    location_lng: Optional[float] = None,
    sector: Optional[str] = None,
    coordinator=Depends(get_coordinator)
):
    """Ingest an image signal."""
    content = await file.read()
    base64_content = base64.b64encode(content).decode()

    result = await coordinator.process_signal(
        signal_type="image",
        content=base64_content,
        metadata={
            "filename": file.filename,
            "location": {"lat": location_lat, "lng": location_lng} if location_lat else None,
            "sector": sector
        }
    )
    return result


@router.post("/signals/audio")
async def ingest_audio(
    file: UploadFile = File(...),
    transcript: Optional[str] = None,
    coordinator=Depends(get_coordinator)
):
    """Ingest an audio signal."""
    content = await file.read()
    base64_content = base64.b64encode(content).decode()

    result = await coordinator.process_signal(
        signal_type="audio",
        content=base64_content,
        metadata={"filename": file.filename, "transcript": transcript}
    )
    return result


@router.post("/signals/text")
async def ingest_text(
    signal_input: SignalInput,
    coordinator=Depends(get_coordinator)
):
    """Ingest a text signal."""
    result = await coordinator.process_signal(
        signal_type="text",
        content=signal_input.content,
        metadata=signal_input.metadata
    )
    return result


# ============== HUMAN DECISIONS ==============

@router.get("/decisions/pending")
async def get_pending_decisions(coordinator=Depends(get_coordinator)):
    """Get all pending decisions."""
    return {
        "contradictions": [
            c.model_dump(mode="json")
            for c in coordinator.graph_manager.graph.contradictions.values()
            if not c.resolved
        ],
        "actions": [
            a.model_dump(mode="json")
            for a in coordinator.graph_manager.graph.pending_actions.values()
            if a.status == "pending"
        ]
    }


@router.post("/decisions/contradiction/{alert_id}")
async def resolve_contradiction(
    alert_id: str,
    decision: HumanDecision,
    coordinator=Depends(get_coordinator)
):
    """Resolve a contradiction alert."""
    if alert_id not in coordinator.graph_manager.graph.contradictions:
        raise HTTPException(404, "Contradiction not found")

    result = await coordinator.resolve_contradiction(alert_id, decision)
    return result.model_dump(mode="json") if result else {"error": "Failed to resolve"}


@router.post("/decisions/action/{action_id}/approve")
async def approve_action(
    action_id: str,
    coordinator=Depends(get_coordinator)
):
    """Approve a pending action recommendation."""
    if action_id not in coordinator.graph_manager.graph.pending_actions:
        raise HTTPException(404, "Action not found")

    result = await coordinator.approve_action(action_id)
    return result.model_dump(mode="json") if result else {"error": "Failed to approve"}


@router.post("/decisions/action/{action_id}/reject")
async def reject_action(
    action_id: str,
    reason: Optional[str] = None,
    coordinator=Depends(get_coordinator)
):
    """Reject a pending action recommendation."""
    if action_id not in coordinator.graph_manager.graph.pending_actions:
        raise HTTPException(404, "Action not found")

    result = await coordinator.reject_action(action_id, reason)
    return result.model_dump(mode="json") if result else {"error": "Failed to reject"}


# ============== SIMULATION CONTROL ==============

@router.post("/simulation/start")
async def start_simulation(
    scenario_id: str = "earthquake_001",
    speed: float = 1.0,
    coordinator=Depends(get_coordinator)
):
    """Start demo simulation."""
    await coordinator.start_simulation(scenario_id, speed)
    return {"status": "started", "scenario": scenario_id, "speed": speed}


@router.post("/simulation/pause")
async def pause_simulation(coordinator=Depends(get_coordinator)):
    """Pause simulation."""
    await coordinator.pause_simulation()
    return {"status": "paused"}


@router.post("/simulation/resume")
async def resume_simulation(coordinator=Depends(get_coordinator)):
    """Resume simulation."""
    await coordinator.resume_simulation()
    return {"status": "resumed"}


@router.post("/simulation/reset")
async def reset_simulation(coordinator=Depends(get_coordinator)):
    """Reset simulation."""
    await coordinator.reset_simulation()
    return {"status": "reset"}


@router.get("/simulation/status")
async def get_simulation_status(coordinator=Depends(get_coordinator)):
    """Get simulation status."""
    return coordinator.get_simulation_status()


# ============== AUDIT ==============

@router.get("/audit/decision/{decision_id}")
async def get_decision_audit(
    decision_id: str,
    coordinator=Depends(get_coordinator)
):
    """Get full audit trail for a decision."""
    return await coordinator.get_decision_audit(decision_id)


@router.get("/audit/incident/{incident_id}")
async def get_incident_audit(
    incident_id: str,
    coordinator=Depends(get_coordinator)
):
    """Get all data related to an incident."""
    return await coordinator.get_incident_audit(incident_id)


@router.get("/timeline")
async def get_timeline(coordinator=Depends(get_coordinator)):
    """Get recent timeline events."""
    return {"events": coordinator.recent_events[-30:]}


# ============== DEBATE ==============

@router.post("/debate/{alert_id}/start")
async def start_debate(
    alert_id: str,
    coordinator=Depends(get_coordinator)
):
    """Start a live agent debate for a contradiction alert."""
    if alert_id not in coordinator.graph_manager.graph.contradictions:
        raise HTTPException(404, "Contradiction not found")

    turns = await coordinator.start_debate(alert_id)
    return {"status": "complete", "alert_id": alert_id, "turns": turns}
