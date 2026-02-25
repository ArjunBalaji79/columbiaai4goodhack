"""
Resource Allocation & Camp Management API routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

router = APIRouter()


def get_coordinator():
    from main import get_coordinator as _get_coordinator
    coord = _get_coordinator()
    if coord is None:
        raise HTTPException(503, "Coordinator not initialized")
    return coord


class AssignResourceRequest(BaseModel):
    resource_id: str
    incident_id: str


# ============== RESOURCE ALLOCATION ==============

@router.get("/resources/allocation")
async def get_allocation_state(coordinator=Depends(get_coordinator)):
    """Get current resource allocation overview."""
    graph = coordinator.graph_manager.graph
    resources = [r.model_dump(mode="json") for r in graph.resources.values()]
    incidents = [i.model_dump(mode="json") for i in graph.incidents.values() if i.status == "active"]
    plans = [p.model_dump(mode="json") for p in graph.allocation_plans.values()]
    camps = [c.model_dump(mode="json") for c in graph.camp_locations.values()]
    return {
        "resources": resources,
        "incidents": incidents,
        "allocation_plans": plans,
        "camps": camps,
        "stats": coordinator.graph_manager.get_stats()
    }


@router.post("/resources/assign")
async def assign_resource(body: AssignResourceRequest, coordinator=Depends(get_coordinator)):
    """Manually assign a resource to an incident."""
    from api.websocket import broadcast

    result = coordinator.graph_manager.assign_resource_manual(body.resource_id, body.incident_id)
    if not result:
        raise HTTPException(404, "Resource or incident not found")

    await broadcast("graph_update", coordinator.graph_manager.graph.model_dump(mode="json"))
    return {"status": "assigned", "resource_id": body.resource_id, "incident_id": body.incident_id}


@router.post("/resources/unassign/{resource_id}")
async def unassign_resource(resource_id: str, coordinator=Depends(get_coordinator)):
    """Unassign a resource from its current assignment."""
    from api.websocket import broadcast

    result = coordinator.graph_manager.unassign_resource(resource_id)
    if not result:
        raise HTTPException(404, "Resource not found")

    await broadcast("graph_update", coordinator.graph_manager.graph.model_dump(mode="json"))
    return {"status": "unassigned", "resource_id": resource_id}


@router.post("/resources/generate-plan")
async def generate_allocation_plan(coordinator=Depends(get_coordinator)):
    """Ask AI to generate an optimized allocation plan."""
    from api.websocket import broadcast

    plan = await coordinator.generate_allocation_plan()
    await broadcast("allocation_update", plan.model_dump(mode="json"))
    return plan.model_dump(mode="json")


@router.post("/resources/plans/{plan_id}/approve")
async def approve_plan(plan_id: str, coordinator=Depends(get_coordinator)):
    """Approve an allocation plan — executes all suggested assignments."""
    from api.websocket import broadcast

    plan = coordinator.graph_manager.graph.allocation_plans.get(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")

    plan.status = "active"
    for assignment in plan.resource_assignments:
        if assignment.status == "suggested":
            coordinator.graph_manager.assign_resource_manual(
                assignment.resource_id, assignment.target_incident_id
            )
            assignment.status = "approved"

    for camp in plan.camp_recommendations:
        if camp.status == "suggested":
            coordinator.graph_manager.add_camp(camp)

    coordinator.graph_manager.graph.last_updated = datetime.utcnow()
    await broadcast("graph_update", coordinator.graph_manager.graph.model_dump(mode="json"))
    return {"status": "approved", "plan_id": plan_id}


# ============== CAMPS ==============

@router.post("/camps/generate")
async def generate_camp_recommendations(coordinator=Depends(get_coordinator)):
    """Ask AI to suggest optimal camp locations."""
    from api.websocket import broadcast

    camps = await coordinator.generate_camp_recommendations()
    for camp in camps:
        await broadcast("camp_recommendation", camp.model_dump(mode="json"))
    return [c.model_dump(mode="json") for c in camps]


@router.get("/camps")
async def get_camps(coordinator=Depends(get_coordinator)):
    """Get all camp recommendations."""
    return [c.model_dump(mode="json") for c in coordinator.graph_manager.graph.camp_locations.values()]


@router.post("/camps/{camp_id}/approve")
async def approve_camp(camp_id: str, coordinator=Depends(get_coordinator)):
    """Approve a camp recommendation."""
    from api.websocket import broadcast

    camp = coordinator.graph_manager.approve_camp(camp_id)
    if not camp:
        raise HTTPException(404, "Camp not found")

    await broadcast("graph_update", coordinator.graph_manager.graph.model_dump(mode="json"))
    return {"status": "approved", "camp_id": camp_id}


@router.post("/camps/{camp_id}/reject")
async def reject_camp(camp_id: str, coordinator=Depends(get_coordinator)):
    """Reject a camp recommendation."""
    from api.websocket import broadcast

    camp = coordinator.graph_manager.reject_camp(camp_id)
    if not camp:
        raise HTTPException(404, "Camp not found")

    await broadcast("graph_update", coordinator.graph_manager.graph.model_dump(mode="json"))
    return {"status": "rejected", "camp_id": camp_id}
