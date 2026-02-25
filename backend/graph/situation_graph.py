"""
SituationGraph manager - handles all in-memory graph state.
"""
from datetime import datetime
from typing import Optional
import uuid

from graph.schemas import (
    SituationGraph, IncidentNode, ResourceNode, LocationNode,
    GraphEdge, ContradictionAlert, ActionRecommendation,
    AllocationPlan, CampRecommendation, ResourceAssignment, VoiceReport,
    DamageLevel, Urgency, Location, SourceReference, SourceType
)


class SituationGraphManager:
    def __init__(self):
        self.graph = SituationGraph(
            scenario_id="",
            scenario_name="",
            scenario_start_time=datetime.utcnow(),
            current_sim_time=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        # Audit trail: list of events
        self.audit_log: list[dict] = []

    def reset(self):
        self.graph = SituationGraph(
            scenario_id="",
            scenario_name="",
            scenario_start_time=datetime.utcnow(),
            current_sim_time=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        self.audit_log = []

    def add_incident(self, incident: IncidentNode) -> IncidentNode:
        self.graph.incidents[incident.id] = incident
        self.graph.last_updated = datetime.utcnow()
        self._log_event("incident_added", {"incident_id": incident.id, "type": incident.incident_type})
        return incident

    def update_incident(self, incident_id: str, updates: dict) -> Optional[IncidentNode]:
        if incident_id not in self.graph.incidents:
            return None
        incident = self.graph.incidents[incident_id]
        for key, value in updates.items():
            if hasattr(incident, key):
                setattr(incident, key, value)
        incident.updated_at = datetime.utcnow()
        self.graph.last_updated = datetime.utcnow()
        self._log_event("incident_updated", {"incident_id": incident_id, "updates": list(updates.keys())})
        return incident

    def add_resource(self, resource: ResourceNode) -> ResourceNode:
        self.graph.resources[resource.id] = resource
        self.graph.last_updated = datetime.utcnow()
        return resource

    def update_resource(self, resource_id: str, updates: dict) -> Optional[ResourceNode]:
        if resource_id not in self.graph.resources:
            return None
        resource = self.graph.resources[resource_id]
        for key, value in updates.items():
            if hasattr(resource, key):
                setattr(resource, key, value)
        resource.updated_at = datetime.utcnow()
        self.graph.last_updated = datetime.utcnow()
        return resource

    def add_location(self, location: LocationNode) -> LocationNode:
        self.graph.locations[location.id] = location
        self.graph.last_updated = datetime.utcnow()
        return location

    def add_contradiction(self, alert: ContradictionAlert) -> ContradictionAlert:
        self.graph.contradictions[alert.id] = alert
        self.graph.last_updated = datetime.utcnow()
        self._log_event("contradiction_added", {
            "alert_id": alert.id,
            "entity": alert.entity_name,
            "verdict": alert.verdict
        })
        return alert

    def resolve_contradiction(self, alert_id: str, resolution: str, resolved_by: str = "operator"):
        if alert_id not in self.graph.contradictions:
            return None
        alert = self.graph.contradictions[alert_id]
        alert.resolved = True
        alert.resolution = resolution
        alert.resolved_by = resolved_by
        alert.resolved_at = datetime.utcnow()
        self.graph.last_updated = datetime.utcnow()
        self._log_event("contradiction_resolved", {
            "alert_id": alert_id,
            "resolution": resolution,
            "resolved_by": resolved_by
        })
        return alert

    def add_action(self, action: ActionRecommendation) -> ActionRecommendation:
        self.graph.pending_actions[action.id] = action
        self.graph.last_updated = datetime.utcnow()
        self._log_event("action_recommended", {
            "action_id": action.id,
            "action_type": action.action_type,
            "resources": action.resources_to_allocate
        })
        return action

    def approve_action(self, action_id: str, decided_by: str = "operator") -> Optional[ActionRecommendation]:
        if action_id not in self.graph.pending_actions:
            return None
        action = self.graph.pending_actions[action_id]
        action.status = "approved"
        action.decided_at = datetime.utcnow()
        action.decided_by = decided_by
        self.graph.last_updated = datetime.utcnow()

        # Update resources
        for resource_id in action.resources_to_allocate:
            if resource_id in self.graph.resources:
                resource = self.graph.resources[resource_id]
                resource.status = "dispatched"
                resource.assigned_incident = action.target_incident_id
                resource.eta_minutes = 8
                resource.updated_at = datetime.utcnow()
                if action.target_location:
                    resource.destination = action.target_location

        # Update incident status
        if action.target_incident_id and action.target_incident_id in self.graph.incidents:
            incident = self.graph.incidents[action.target_incident_id]
            incident.status = "responding"
            incident.assigned_resources.extend(action.resources_to_allocate)
            incident.updated_at = datetime.utcnow()

        self._log_event("action_approved", {
            "action_id": action_id,
            "decided_by": decided_by,
            "resources": action.resources_to_allocate
        })
        return action

    def reject_action(self, action_id: str, reason: Optional[str] = None, decided_by: str = "operator") -> Optional[ActionRecommendation]:
        if action_id not in self.graph.pending_actions:
            return None
        action = self.graph.pending_actions[action_id]
        action.status = "rejected"
        action.decided_at = datetime.utcnow()
        action.decided_by = decided_by
        self.graph.last_updated = datetime.utcnow()
        self._log_event("action_rejected", {
            "action_id": action_id,
            "reason": reason,
            "decided_by": decided_by
        })
        return action

    def add_edge(self, edge: GraphEdge) -> GraphEdge:
        self.graph.edges[edge.id] = edge
        return edge

    def get_incidents_by_urgency(self) -> list[IncidentNode]:
        urgency_order = {Urgency.CRITICAL: 0, Urgency.HIGH: 1, Urgency.MEDIUM: 2, Urgency.LOW: 3}
        return sorted(
            [i for i in self.graph.incidents.values() if i.status == "active"],
            key=lambda x: urgency_order.get(x.urgency, 4)
        )

    def get_available_resources(self, resource_type: Optional[str] = None) -> list[ResourceNode]:
        resources = [r for r in self.graph.resources.values() if r.status == "available"]
        if resource_type:
            resources = [r for r in resources if r.resource_type == resource_type]
        return resources

    def find_related_incidents(self, location: Location, radius_km: float = 1.0) -> list[IncidentNode]:
        """Find incidents near a given location."""
        import math
        result = []
        for incident in self.graph.incidents.values():
            dist = self._haversine(location.lat, location.lng,
                                   incident.location.lat, incident.location.lng)
            if dist <= radius_km:
                result.append(incident)
        return result

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km."""
        import math
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        return 2 * R * math.asin(math.sqrt(a))

    def get_decision_audit(self, decision_id: str) -> dict:
        """Get full audit trail for a decision."""
        events = [e for e in self.audit_log if decision_id in str(e)]
        action = self.graph.pending_actions.get(decision_id)
        contradiction = self.graph.contradictions.get(decision_id)

        return {
            "decision_id": decision_id,
            "action": action.model_dump() if action else None,
            "contradiction": contradiction.model_dump() if contradiction else None,
            "audit_events": events
        }

    def get_incident_audit(self, incident_id: str) -> dict:
        """Get all data related to an incident."""
        incident = self.graph.incidents.get(incident_id)
        if not incident:
            return {"error": "Incident not found"}

        related_actions = [
            a.model_dump() for a in self.graph.pending_actions.values()
            if a.target_incident_id == incident_id
        ]

        return {
            "incident": incident.model_dump(),
            "related_actions": related_actions,
            "audit_events": [e for e in self.audit_log
                             if e.get("data", {}).get("incident_id") == incident_id]
        }

    def _log_event(self, event_type: str, data: dict):
        self.audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": data
        })

    def decay_confidences(self, elapsed_minutes: float):
        """Decay confidence values over time."""
        for incident in self.graph.incidents.values():
            if incident.status == "active":
                decay = incident.decay_rate * elapsed_minutes
                incident.confidence = max(0.1, incident.confidence - decay)
        self.graph.last_updated = datetime.utcnow()

    # ============== ALLOCATION & CAMPS ==============

    def add_allocation_plan(self, plan: AllocationPlan) -> AllocationPlan:
        self.graph.allocation_plans[plan.id] = plan
        self.graph.last_updated = datetime.utcnow()
        self._log_event("allocation_plan_created", {"plan_id": plan.id})
        return plan

    def add_camp(self, camp: CampRecommendation) -> CampRecommendation:
        self.graph.camp_locations[camp.id] = camp
        self.graph.last_updated = datetime.utcnow()
        self._log_event("camp_added", {"camp_id": camp.id, "type": camp.camp_type})
        return camp

    def approve_camp(self, camp_id: str) -> Optional[CampRecommendation]:
        if camp_id not in self.graph.camp_locations:
            return None
        camp = self.graph.camp_locations[camp_id]
        camp.status = "active"
        camp.decided_at = datetime.utcnow()
        self.graph.last_updated = datetime.utcnow()
        self._log_event("camp_approved", {"camp_id": camp_id})
        return camp

    def reject_camp(self, camp_id: str) -> Optional[CampRecommendation]:
        if camp_id not in self.graph.camp_locations:
            return None
        camp = self.graph.camp_locations[camp_id]
        camp.status = "rejected"
        camp.decided_at = datetime.utcnow()
        self.graph.last_updated = datetime.utcnow()
        self._log_event("camp_rejected", {"camp_id": camp_id})
        return camp

    def assign_resource_manual(self, resource_id: str, incident_id: str) -> Optional[ResourceNode]:
        """Manually assign a resource to an incident."""
        resource = self.graph.resources.get(resource_id)
        incident = self.graph.incidents.get(incident_id)
        if not resource or not incident:
            return None
        resource.status = "dispatched"
        resource.assigned_incident = incident_id
        resource.destination = incident.location
        resource.eta_minutes = 8
        resource.updated_at = datetime.utcnow()
        if resource_id not in incident.assigned_resources:
            incident.assigned_resources.append(resource_id)
        incident.updated_at = datetime.utcnow()
        self.graph.last_updated = datetime.utcnow()
        self._log_event("resource_assigned", {"resource_id": resource_id, "incident_id": incident_id})
        return resource

    def unassign_resource(self, resource_id: str) -> Optional[ResourceNode]:
        resource = self.graph.resources.get(resource_id)
        if not resource:
            return None
        old_incident_id = resource.assigned_incident
        resource.status = "available"
        resource.assigned_incident = None
        resource.destination = None
        resource.eta_minutes = None
        resource.updated_at = datetime.utcnow()
        if old_incident_id and old_incident_id in self.graph.incidents:
            incident = self.graph.incidents[old_incident_id]
            if resource_id in incident.assigned_resources:
                incident.assigned_resources.remove(resource_id)
        self.graph.last_updated = datetime.utcnow()
        self._log_event("resource_unassigned", {"resource_id": resource_id})
        return resource

    def add_voice_report(self, report: VoiceReport) -> VoiceReport:
        self.graph.voice_reports[report.id] = report
        self.graph.last_updated = datetime.utcnow()
        self._log_event("voice_report_added", {"report_id": report.id})
        return report

    def get_stats(self) -> dict:
        incidents = self.graph.incidents
        resources = self.graph.resources
        return {
            "total_incidents": len(incidents),
            "active_incidents": len([i for i in incidents.values() if i.status == "active"]),
            "responding_incidents": len([i for i in incidents.values() if i.status == "responding"]),
            "resources_available": len([r for r in resources.values() if r.status == "available"]),
            "resources_deployed": len([r for r in resources.values() if r.status in ["dispatched", "on_scene"]]),
            "pending_contradictions": len([c for c in self.graph.contradictions.values() if not c.resolved]),
            "pending_actions": len([a for a in self.graph.pending_actions.values() if a.status == "pending"]),
            "camps_active": len([c for c in self.graph.camp_locations.values() if c.status == "active"]),
            "camps_suggested": len([c for c in self.graph.camp_locations.values() if c.status == "suggested"]),
        }
