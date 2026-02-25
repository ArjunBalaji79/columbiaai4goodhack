"""
Main orchestrator - coordinates all agents and manages the situation graph.
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional

import google.generativeai as genai

from config import get_settings
from graph.schemas import (
    SituationGraph, IncidentNode, ResourceNode, LocationNode,
    ContradictionAlert, ActionRecommendation,
    DamageLevel, Urgency, ActionType, Verdict,
    Location, SourceReference, SourceType, HumanDecision
)
from graph.situation_graph import SituationGraphManager
from agents.vision_agent import VisionAgent
from agents.audio_agent import AudioAgent
from agents.text_agent import TextAgent
from agents.verification_agent import VerificationAgent
from agents.planning_agent import PlanningAgent
from agents.temporal_agent import TemporalAgent
from agents.debate_agent import DebateAgent
from agents.allocation_agent import AllocationAgent


def _parse_urgency(raw: str) -> Urgency:
    """Extract a valid Urgency enum from a potentially verbose string like 'critical — some explanation'."""
    raw = str(raw).lower()
    for level in ("critical", "high", "medium", "low"):
        if level in raw:
            return Urgency(level)
    return Urgency.HIGH


class Coordinator:
    def __init__(self):
        settings = get_settings()
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)

        # Initialize agents (they use gemini-2.0-flash by default)
        self.vision_agent = VisionAgent()
        self.audio_agent = AudioAgent()
        self.text_agent = TextAgent()
        self.verification_agent = VerificationAgent()
        self.planning_agent = PlanningAgent()
        self.temporal_agent = TemporalAgent()
        self.allocation_agent = AllocationAgent()

        # Graph manager
        self.graph_manager = SituationGraphManager()

        # Signal tracking for contradiction detection
        self.signal_claims: dict[str, list[dict]] = {}  # entity_name -> list of claims
        self.handled_contradictions: set[str] = set()  # entity_names that already have alerts

        # Simulation state
        self.simulation_running = False
        self.simulation_task: Optional[asyncio.Task] = None
        self.simulation_paused = False

        # Recent events for timeline
        self.recent_events: list[dict] = []

        # Planning cooldown — avoid firing the planning agent on every single signal
        self._last_planning_call: Optional[datetime] = None
        self._planning_cooldown_seconds: int = 20

    @property
    def graph(self) -> SituationGraph:
        return self.graph_manager.graph

    async def initialize(self):
        """Called on startup."""
        pass

    async def shutdown(self):
        """Called on shutdown."""
        if self.simulation_task:
            self.simulation_task.cancel()

    async def process_signal(self, signal_type: str, content: str, metadata: dict) -> dict:
        """Route signal to appropriate agent and update graph."""
        from api.websocket import broadcast

        signal_id = str(uuid.uuid4())[:8]

        # Add timeline event
        self._add_event(f"signal_{signal_type}", {
            "signal_id": signal_id,
            "type": signal_type,
            "metadata": metadata
        })

        try:
            # Select agent and process
            if signal_type == "image":
                agent_output = await self.vision_agent.process({
                    "content": content,
                    "metadata": metadata
                })
            elif signal_type == "audio":
                agent_output = await self.audio_agent.process({
                    "content": content,
                    "metadata": metadata
                })
            elif signal_type == "text":
                agent_output = await self.text_agent.process({
                    "content": content,
                    "metadata": metadata
                })
            else:
                raise ValueError(f"Unknown signal type: {signal_type}")

            # Broadcast signal processing result
            await broadcast("signal_processed", {
                "signal_id": signal_id,
                "signal_type": signal_type,
                "agent_name": agent_output.agent_name,
                "output_type": agent_output.output_type,
                "data": agent_output.data,
                "confidence": agent_output.confidence,
                "reasoning": agent_output.reasoning,
                "timestamp": agent_output.timestamp.isoformat(),
                "metadata": metadata
            })

            # Update graph
            incident = await self._update_graph_from_output(
                agent_output, signal_type, signal_id, metadata
            )

            # Check contradictions (skip during simulation — scripted injections handle this)
            if incident and not self.simulation_running:
                await self._check_contradictions(agent_output, incident, signal_id)

            # Maybe generate recommendations
            await self._maybe_generate_recommendations()

            # Broadcast update
            await broadcast("graph_update", self.graph_manager.graph.model_dump(mode="json"))
            await broadcast("timeline_event", {
                "events": self.recent_events[-10:]
            })

            return {
                "signal_id": signal_id,
                "agent": agent_output.agent_name,
                "output_type": agent_output.output_type,
                "confidence": agent_output.confidence,
                "data": agent_output.data
            }

        except Exception as e:
            print(f"Error processing signal: {e}")
            return {"error": str(e), "signal_id": signal_id}

    async def _update_graph_from_output(self, output, signal_type: str, signal_id: str, metadata: dict):
        """Update situation graph based on agent output."""
        data = output.data
        now = datetime.utcnow()

        # Build source reference
        source_ref = SourceReference(
            source_id=signal_id,
            source_type=SourceType(signal_type) if signal_type in ["image", "audio", "text"] else SourceType.TEXT,
            timestamp=now,
            raw_content_ref=signal_id,
            credibility_score=output.confidence
        )

        # Parse location from metadata
        loc_data = metadata.get("location", {}) or {}
        location = Location(
            lat=loc_data.get("lat", 37.78 + (hash(signal_id) % 100) * 0.001),
            lng=loc_data.get("lng", -122.41 + (hash(signal_id[::-1]) % 100) * 0.001),
            sector=metadata.get("sector", "1"),
            name=metadata.get("location_name")
        )

        incident = None

        if signal_type == "image":
            damage_level_str = data.get("damage_level", "moderate")
            try:
                damage_level = DamageLevel(damage_level_str)
            except ValueError:
                damage_level = DamageLevel.MODERATE

            # Map damage level to urgency
            urgency_map = {
                DamageLevel.CATASTROPHIC: Urgency.CRITICAL,
                DamageLevel.SEVERE: Urgency.CRITICAL,
                DamageLevel.MODERATE: Urgency.HIGH,
                DamageLevel.MINOR: Urgency.MEDIUM,
                DamageLevel.NONE: Urgency.LOW
            }
            urgency = urgency_map.get(damage_level, Urgency.MEDIUM)

            casualties = data.get("estimated_casualties") or {}
            incident_id = f"inc_{signal_id}"

            incident = IncidentNode(
                id=incident_id,
                incident_type="structural_collapse" if "structural_collapse" in (data.get("damage_types") or []) else "damage",
                location=location,
                damage_level=damage_level,
                urgency=urgency,
                trapped_min=casualties.get("min"),
                trapped_max=casualties.get("max"),
                confidence=data.get("overall_confidence", 0.5),
                sources=[source_ref],
                created_at=now,
                updated_at=now
            )
            self.graph_manager.add_incident(incident)
            await self._broadcast_incident(incident)

        elif signal_type == "audio":
            urgency_map = {
                "critical": Urgency.CRITICAL,
                "high": Urgency.HIGH,
                "medium": Urgency.MEDIUM,
                "low": Urgency.LOW
            }
            urgency = urgency_map.get(data.get("urgency", "high"), Urgency.HIGH)

            persons = data.get("persons_involved") or {}
            trapped = persons.get("trapped", {}) if isinstance(persons.get("trapped"), dict) else {}
            incident_id = f"inc_{signal_id}"

            incident = IncidentNode(
                id=incident_id,
                incident_type=data.get("incident_type", "emergency"),
                location=location,
                damage_level=DamageLevel.SEVERE if urgency == Urgency.CRITICAL else DamageLevel.MODERATE,
                urgency=urgency,
                trapped_min=trapped.get("min") if isinstance(trapped, dict) else None,
                trapped_max=trapped.get("max") if isinstance(trapped, dict) else None,
                confidence=data.get("overall_confidence", 0.5),
                sources=[source_ref],
                created_at=now,
                updated_at=now
            )
            self.graph_manager.add_incident(incident)
            await self._broadcast_incident(incident)

        elif signal_type == "text":
            # Only accumulate claims for contradiction detection outside of simulation
            if not self.simulation_running:
                claims = data.get("claims") or []
                for claim_data in claims:
                    entity_name = claim_data.get("location", {}).get("name", "") if isinstance(claim_data.get("location"), dict) else ""
                    if entity_name:
                        if entity_name in self.handled_contradictions:
                            continue
                        if entity_name not in self.signal_claims:
                            self.signal_claims[entity_name] = []
                        self.signal_claims[entity_name].append({
                            "source": f"text_{signal_id}",
                            "source_type": data.get("source_type", "unverified"),
                            "claim": claim_data.get("claim", ""),
                            "confidence": claim_data.get("confidence", 0.4),
                            "timestamp": now.strftime("%H:%M")
                        })

        return incident

    async def _check_contradictions(self, new_output, incident: IncidentNode, signal_id: str):
        """Check if new output contradicts existing data."""
        from api.websocket import broadcast

        # Check claims for contradictions (iterate over copy to allow deletion)
        for entity_name, claims in list(self.signal_claims.items()):
            # Skip if entity was already processed/deleted by another process
            if entity_name not in self.signal_claims:
                continue
            # Skip if entity already has a contradiction alert
            if entity_name in self.handled_contradictions:
                continue
            if len(claims) >= 2:
                # Run verification agent
                verification_input = {
                    "entity": entity_name,
                    "entity_type": "infrastructure",
                    "claims": claims
                }

                try:
                    verification_output = await self.verification_agent.process(verification_input)
                    ver_data = verification_output.data

                    if ver_data.get("verdict") in ["CONTRADICTION", "TEMPORAL_GAP"]:
                        alert_id = f"alert_{str(uuid.uuid4())[:8]}"

                        verdict_map = {
                            "CONTRADICTION": Verdict.CONTRADICTION,
                            "TEMPORAL_GAP": Verdict.TEMPORAL_GAP,
                            "CONSISTENT": Verdict.CONSISTENT,
                            "UNCERTAIN": Verdict.UNCERTAIN
                        }
                        action_map = {
                            "REQUEST_VERIFICATION": ActionType.REQUEST_VERIFICATION,
                            "FLAG_FOR_HUMAN": ActionType.FLAG_FOR_HUMAN,
                            "ACCEPT": ActionType.ACCEPT,
                            "WAIT": ActionType.WAIT
                        }

                        alert = ContradictionAlert(
                            id=alert_id,
                            entity_id=entity_name.lower().replace(" ", "_"),
                            entity_type=ver_data.get("entity_type", "infrastructure"),
                            entity_name=entity_name,
                            claims=ver_data.get("claims_analyzed") or claims[:2],
                            verdict=verdict_map.get(ver_data.get("verdict", "UNCERTAIN"), Verdict.UNCERTAIN),
                            severity=(ver_data.get("contradictions") or [{}])[0].get("severity", "high"),
                            temporal_analysis=ver_data.get("temporal_analysis"),
                            recommended_action=action_map.get(
                                ver_data.get("recommended_action", "FLAG_FOR_HUMAN"),
                                ActionType.FLAG_FOR_HUMAN
                            ),
                            recommended_action_details=ver_data.get("recommended_action_details", ""),
                            urgency=_parse_urgency(ver_data.get("urgency", "high")),
                            created_at=datetime.utcnow()
                        )

                        self.graph_manager.add_contradiction(alert)

                        # Broadcast contradiction alert
                        print(f"[CONTRADICTION ALERT] Created alert for entity: {entity_name} (verdict: {ver_data.get('verdict')})")
                        await broadcast("contradiction_alert", alert.model_dump(mode="json"))
                        self._add_event("contradiction_detected", {
                            "alert_id": alert_id,
                            "entity": entity_name,
                            "verdict": ver_data.get("verdict")
                        })

                        # Mark entity as handled and clear claims
                        self.handled_contradictions.add(entity_name)
                        print(f"[CONTRADICTION HANDLED] Added '{entity_name}' to handled set. Total handled: {len(self.handled_contradictions)}")
                        if entity_name in self.signal_claims:
                            del self.signal_claims[entity_name]
                        break

                except Exception as e:
                    import traceback
                    print(f"Error in contradiction check for '{entity_name}': {e}")
                    traceback.print_exc()
                    # Clean up claims on error to prevent repeated processing
                    if entity_name in self.signal_claims:
                        del self.signal_claims[entity_name]

    async def _maybe_generate_recommendations(self):
        """Generate action recommendations if needed."""
        from api.websocket import broadcast

        # Cooldown: don't hammer the planning agent on every signal
        now = datetime.utcnow()
        if self._last_planning_call is not None:
            elapsed = (now - self._last_planning_call).total_seconds()
            if elapsed < self._planning_cooldown_seconds:
                return

        # Check for unaddressed critical incidents with available resources
        critical_incidents = [
            i for i in self.graph_manager.graph.incidents.values()
            if i.urgency in [Urgency.CRITICAL, Urgency.HIGH]
            and i.status == "active"
            and len(i.assigned_resources) == 0
        ]

        if not critical_incidents:
            return

        # Check we don't already have too many pending actions
        pending_count = len([a for a in self.graph_manager.graph.pending_actions.values()
                             if a.status == "pending"])
        if pending_count >= 3:
            return

        available_resources = self.graph_manager.get_available_resources()
        if not available_resources:
            return

        # Build context for planning agent
        all_incidents = [
            {
                "id": i.id,
                "incident_type": i.incident_type,
                "sector": i.location.sector or "unknown",
                "urgency": i.urgency.value,
                "confidence": i.confidence,
                "trapped_min": i.trapped_min,
                "trapped_max": i.trapped_max,
                "status": i.status
            }
            for i in self.graph_manager.graph.incidents.values()
            if i.status == "active"
        ]

        all_resources = [
            {
                "id": r.id,
                "unit_id": r.unit_id,
                "resource_type": r.resource_type,
                "status": r.status,
                "sector": r.current_location.sector or "unknown"
            }
            for r in available_resources[:6]  # Limit for context
        ]

        hospital_capacity = {}
        for loc in self.graph_manager.graph.locations.values():
            if loc.location_type == "hospital" and loc.capacity_total:
                capacity_used = loc.capacity_used or 0
                hospital_capacity[loc.id] = f"{capacity_used}/{loc.capacity_total}"

        try:
            self._last_planning_call = datetime.utcnow()
            planning_output = await self.planning_agent.process({
                "incidents": all_incidents,
                "resources": all_resources,
                "constraints": {
                    "hospital_capacity": hospital_capacity or "not reported",
                    "road_blockages": "Route 12 partially blocked",
                    "weather": "Clear, wind 10km/h NE"
                }
            })

            plan_data = planning_output.data
            recommendation = plan_data.get("recommendation", {})
            rationale = plan_data.get("rationale", {})

            # Find target incident
            target_incident_id = recommendation.get("target", {}).get("incident_id")
            if not target_incident_id and critical_incidents:
                target_incident_id = critical_incidents[0].id

            target_location = None
            if target_incident_id and target_incident_id in self.graph_manager.graph.incidents:
                target_location = self.graph_manager.graph.incidents[target_incident_id].location

            action_id = f"action_{str(uuid.uuid4())[:8]}"
            action = ActionRecommendation(
                id=action_id,
                action_type=recommendation.get("action", "dispatch_resources"),
                target_incident_id=target_incident_id,
                target_location=target_location,
                target_sector=recommendation.get("target", {}).get("sector"),
                resources_to_allocate=recommendation.get("resources") or [r.unit_id for r in available_resources[:3]],
                rationale=rationale.get("primary_reason", planning_output.reasoning),
                supporting_factors=rationale.get("supporting_factors") or [],
                confidence=rationale.get("confidence", planning_output.confidence),
                tradeoffs=plan_data.get("tradeoffs") or [],
                uncertainty_factors=plan_data.get("uncertainty_factors") or [],
                requires_human_approval=plan_data.get("human_approval_required", True),
                decision_deadline=datetime.utcnow() + timedelta(minutes=5),
                time_sensitivity=_parse_urgency(plan_data.get("time_sensitivity", "critical")),
                created_at=datetime.utcnow()
            )

            self.graph_manager.add_action(action)
            await broadcast("action_recommendation", action.model_dump(mode="json"))
            self._add_event("action_recommended", {
                "action_id": action_id,
                "action_type": action.action_type,
                "resources": action.resources_to_allocate
            })

        except Exception as e:
            print(f"Error generating recommendation: {e}")

    async def _broadcast_incident(self, incident: IncidentNode):
        """Broadcast new incident to clients."""
        from api.websocket import broadcast
        await broadcast("new_incident", incident.model_dump(mode="json"))

    async def resolve_contradiction(self, alert_id: str, decision: HumanDecision):
        """Handle human resolution of contradiction."""
        from api.websocket import broadcast

        alert = self.graph_manager.resolve_contradiction(
            alert_id, decision.decision, decision.decided_by
        )
        if not alert:
            return None

        await broadcast("decision_made", {
            "type": "contradiction",
            "id": alert_id,
            "decision": decision.decision
        })
        await broadcast("graph_update", self.graph_manager.graph.model_dump(mode="json"))

        self._add_event("contradiction_resolved", {
            "alert_id": alert_id,
            "resolution": decision.decision
        })

        return alert

    async def approve_action(self, action_id: str, decided_by: str = "operator"):
        """Execute approved action."""
        from api.websocket import broadcast

        action = self.graph_manager.approve_action(action_id, decided_by)
        if not action:
            return None

        await broadcast("decision_made", {
            "type": "action",
            "id": action_id,
            "decision": "approved",
            "resources": action.resources_to_allocate
        })
        await broadcast("graph_update", self.graph_manager.graph.model_dump(mode="json"))

        self._add_event("action_approved", {
            "action_id": action_id,
            "resources": action.resources_to_allocate
        })

        return action

    async def reject_action(self, action_id: str, reason: Optional[str] = None, decided_by: str = "operator"):
        """Reject action recommendation."""
        from api.websocket import broadcast

        action = self.graph_manager.reject_action(action_id, reason, decided_by)
        if not action:
            return None

        await broadcast("decision_made", {
            "type": "action",
            "id": action_id,
            "decision": "rejected",
            "reason": reason
        })
        await broadcast("graph_update", self.graph_manager.graph.model_dump(mode="json"))

        return action

    # ============== SIMULATION ==============

    async def start_simulation(self, scenario_id: str, speed: float = 1.0):
        """Start demo simulation."""
        from orchestrator.simulation import run_simulation

        if self.simulation_task:
            self.simulation_task.cancel()

        self.simulation_running = True
        self.simulation_paused = False
        self.simulation_task = asyncio.create_task(
            run_simulation(self, scenario_id, speed)
        )

    async def pause_simulation(self):
        self.simulation_paused = True
        self.simulation_running = False

    async def resume_simulation(self):
        self.simulation_paused = False
        self.simulation_running = True

    async def reset_simulation(self):
        self.simulation_running = False
        self.simulation_paused = False
        if self.simulation_task:
            self.simulation_task.cancel()
            self.simulation_task = None

        self.signal_claims.clear()
        self.handled_contradictions.clear()
        self.recent_events.clear()
        self.graph_manager.reset()

        from api.websocket import broadcast
        await broadcast("graph_update", self.graph_manager.graph.model_dump(mode="json"))

    def get_simulation_status(self) -> dict:
        return {
            "running": self.simulation_running,
            "paused": self.simulation_paused,
            "scenario_id": self.graph_manager.graph.scenario_id,
            "scenario_name": self.graph_manager.graph.scenario_name,
            "current_time": self.graph_manager.graph.current_sim_time.isoformat(),
            "elapsed_seconds": (
                self.graph_manager.graph.current_sim_time - self.graph_manager.graph.scenario_start_time
            ).total_seconds()
        }

    # ============== DEBATE ==============

    async def start_debate(self, alert_id: str) -> list:
        """Start a live agent debate for a contradiction alert."""
        from api.websocket import broadcast

        alert = self.graph_manager.graph.contradictions.get(alert_id)
        if not alert:
            return []

        debate_agent = DebateAgent()
        self._add_event("debate_started", {"alert_id": alert_id, "entity": alert.entity_name})

        turns = await debate_agent.run_debate(alert, broadcast)
        self._add_event("debate_completed", {"alert_id": alert_id, "turns": len(turns)})
        return [t.model_dump(mode="json") for t in turns]

    async def get_decision_audit(self, decision_id: str) -> dict:
        return self.graph_manager.get_decision_audit(decision_id)

    async def get_incident_audit(self, incident_id: str) -> dict:
        return self.graph_manager.get_incident_audit(incident_id)

    # ============== RESOURCE ALLOCATION ==============

    async def generate_allocation_plan(self):
        """Generate an optimized resource allocation plan using AI."""
        from graph.schemas import AllocationPlan, ResourceAssignment, CampRecommendation

        # Build context from current graph
        all_incidents = [
            {
                "id": i.id, "incident_type": i.incident_type,
                "sector": i.location.sector or "unknown",
                "urgency": i.urgency.value, "confidence": i.confidence,
                "trapped_min": i.trapped_min, "trapped_max": i.trapped_max,
                "status": i.status,
                "lat": i.location.lat, "lng": i.location.lng
            }
            for i in self.graph_manager.graph.incidents.values()
            if i.status == "active"
        ]

        all_resources = [
            {
                "id": r.id, "unit_id": r.unit_id,
                "resource_type": r.resource_type, "status": r.status,
                "sector": r.current_location.sector or "unknown",
                "assigned_incident": r.assigned_incident
            }
            for r in self.graph_manager.graph.resources.values()
        ]

        all_locations = [
            {
                "id": l.id, "name": l.location.name or l.id,
                "location_type": l.location_type, "status": l.status,
                "capacity_total": l.capacity_total, "capacity_used": l.capacity_used,
                "lat": l.location.lat, "lng": l.location.lng
            }
            for l in self.graph_manager.graph.locations.values()
        ]

        output = await self.allocation_agent.process({
            "incidents": all_incidents,
            "resources": all_resources,
            "locations": all_locations,
            "constraints": {
                "hospital_capacity": {l["name"]: f"{l['capacity_used']}/{l['capacity_total']}" for l in all_locations if l["location_type"] == "hospital" and l["capacity_total"]},
                "road_blockages": "Route 12 partially blocked",
                "weather": "Clear"
            }
        })

        plan_data = output.data
        plan_id = f"plan_{str(uuid.uuid4())[:8]}"
        now = datetime.utcnow()

        # Build assignments
        assignments = []
        for a in plan_data.get("resource_assignments", []):
            assignments.append(ResourceAssignment(
                id=f"assign_{str(uuid.uuid4())[:6]}",
                resource_id=a.get("resource_id", ""),
                target_incident_id=a.get("target_incident_id", ""),
                rationale=a.get("rationale", ""),
                priority=a.get("priority", 1),
                estimated_eta_minutes=a.get("estimated_eta_minutes"),
                created_at=now
            ))

        # Build camp recommendations
        camps = []
        for c in plan_data.get("camp_recommendations", []):
            loc = c.get("location", {})
            camps.append(CampRecommendation(
                id=f"camp_{str(uuid.uuid4())[:6]}",
                name=c.get("name", "Camp"),
                location=Location(lat=loc.get("lat", 37.78), lng=loc.get("lng", -122.41)),
                camp_type=c.get("camp_type", "relief_camp"),
                capacity_persons=c.get("capacity_persons", 100),
                rationale=c.get("rationale", ""),
                confidence=c.get("confidence", 0.7),
                factors=c.get("factors", {}),
                created_at=now
            ))

        plan = AllocationPlan(
            id=plan_id,
            resource_assignments=assignments,
            camp_recommendations=camps,
            overall_confidence=plan_data.get("overall_confidence", 0.7),
            key_assumptions=plan_data.get("key_assumptions", []),
            created_at=now
        )

        self.graph_manager.add_allocation_plan(plan)
        self._add_event("allocation_plan_generated", {"plan_id": plan_id})
        return plan

    async def generate_camp_recommendations(self):
        """Generate optimal camp location suggestions using AI."""
        plan = await self.generate_allocation_plan()
        # Extract just the camps from the plan
        for camp in plan.camp_recommendations:
            self.graph_manager.add_camp(camp)
        return plan.camp_recommendations

    def _add_event(self, event_type: str, data: dict):
        event = {
            "id": str(uuid.uuid4())[:8],
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        self.recent_events.append(event)
        # Keep last 50 events
        if len(self.recent_events) > 50:
            self.recent_events = self.recent_events[-50:]
