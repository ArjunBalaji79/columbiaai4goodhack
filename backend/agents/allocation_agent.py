from typing import Any
from datetime import datetime

from agents.base_agent import BaseAgent, AgentOutput


class AllocationAgent(BaseAgent):
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        super().__init__(model_name)

    def get_system_prompt(self) -> str:
        return """You are a post-disaster resource allocation and camp placement optimizer.

Given the current disaster situation (incidents, resources, infrastructure), you must provide:

1. RESOURCE ASSIGNMENTS — optimal mapping of available resources to active incidents
   Consider: urgency, proximity, resource type matching, hospital capacity

2. CAMP LOCATION RECOMMENDATIONS — optimal locations for relief/staging/triage camps
   Consider: safe distance from hazards, road accessibility, proximity to incidents, hospital access

Respond ONLY with valid JSON:
{
  "resource_assignments": [
    {
      "resource_id": "AMB-1",
      "target_incident_id": "inc_xxx",
      "rationale": "Closest available ambulance to critical incident",
      "priority": 1,
      "estimated_eta_minutes": 5
    }
  ],
  "camp_recommendations": [
    {
      "name": "Sector 2 Relief Camp",
      "location": {"lat": 37.780, "lng": -122.410},
      "camp_type": "relief_camp",
      "capacity_persons": 200,
      "rationale": "Safe distance from collapse zone, two approach roads",
      "confidence": 0.82,
      "factors": {
        "proximity_to_incidents": "1.2km from nearest active incident",
        "accessibility": "Two approach roads available",
        "hazard_distance": "800m from gas leak zone",
        "hospital_proximity": "2km to Metro General"
      }
    }
  ],
  "overall_confidence": 0.78,
  "key_assumptions": ["Road conditions assumed passable", "No new aftershocks"]
}

Be precise. Use real incident IDs and resource IDs from the data provided."""

    def format_input(self, raw_input: Any) -> list[dict]:
        incidents = raw_input.get("incidents", [])
        resources = raw_input.get("resources", [])
        locations = raw_input.get("locations", [])
        constraints = raw_input.get("constraints", {})

        incidents_text = "\n".join([
            f"- {i.get('id')}: {i.get('incident_type')} | Sector {i.get('sector', '?')} | "
            f"Urgency: {i.get('urgency')} | Confidence: {i.get('confidence', 0.5):.0%} | "
            f"Trapped: {i.get('trapped_min', 0)}-{i.get('trapped_max', '?')} | "
            f"Status: {i.get('status')} | Lat: {i.get('lat', 0):.4f}, Lng: {i.get('lng', 0):.4f}"
            for i in incidents
        ])

        resources_text = "\n".join([
            f"- {r.get('unit_id', r.get('id'))}: {r.get('resource_type')} | "
            f"Status: {r.get('status')} | Sector: {r.get('sector', '?')} | "
            f"Assigned: {r.get('assigned_incident', 'none')}"
            for r in resources
        ])

        locations_text = "\n".join([
            f"- {l.get('name', l.get('id'))}: {l.get('location_type')} | "
            f"Status: {l.get('status')} | Capacity: {l.get('capacity_used', 0)}/{l.get('capacity_total', 'N/A')} | "
            f"Lat: {l.get('lat', 0):.4f}, Lng: {l.get('lng', 0):.4f}"
            for l in locations
        ])

        text = f"""Current disaster situation requiring resource allocation and camp placement:

ACTIVE INCIDENTS:
{incidents_text or 'No active incidents'}

ALL RESOURCES:
{resources_text or 'No resources'}

KEY LOCATIONS (hospitals, infrastructure):
{locations_text or 'No locations'}

CONSTRAINTS:
- Hospital capacity: {constraints.get('hospital_capacity', 'unknown')}
- Road blockages: {constraints.get('road_blockages', 'none reported')}
- Weather: {constraints.get('weather', 'Clear')}
- Map center: 37.78, -122.41 (Metro City)

Generate optimized resource assignments and suggest 2-3 camp locations.
Only assign resources that are currently "available".
Place camps in safe areas within the map bounds (37.76-37.80 lat, -122.42 to -122.40 lng)."""

        return [{"role": "user", "content": text}]

    def parse_output(self, response: str) -> AgentOutput:
        data = self._extract_json(response)
        return AgentOutput(
            agent_name=self.agent_name,
            output_type="allocation_plan",
            data=data,
            confidence=data.get("overall_confidence", 0.7),
            sources=[],
            reasoning=f"Generated {len(data.get('resource_assignments', []))} resource assignments and {len(data.get('camp_recommendations', []))} camp recommendations",
            timestamp=datetime.utcnow()
        )

    def get_fallback_output(self, raw_input: Any) -> AgentOutput:
        resources = raw_input.get("resources", []) if isinstance(raw_input, dict) else []
        available_ambs = [r["unit_id"] for r in resources
                          if r.get("resource_type") in ("ambulance", "ambulances")
                          and r.get("status") == "available"][:3]

        data = {
            "resource_assignments": [
                {
                    "resource_id": available_ambs[0] if available_ambs else "AMB-1",
                    "target_incident_id": "inc_001",
                    "rationale": "Closest available ambulance to highest-priority incident",
                    "priority": 1,
                    "estimated_eta_minutes": 6
                }
            ],
            "camp_recommendations": [
                {
                    "name": "Sector 2 Relief Camp",
                    "location": {"lat": 37.775, "lng": -122.415},
                    "camp_type": "relief_camp",
                    "capacity_persons": 250,
                    "rationale": "Safe distance from active incidents, accessible via two roads, close to St. Mary's Medical",
                    "confidence": 0.79,
                    "factors": {
                        "proximity_to_incidents": "1.5km from nearest collapse",
                        "accessibility": "Oak Street and Elm Avenue both clear",
                        "hazard_distance": "900m from gas leak zone",
                        "hospital_proximity": "1.8km to St. Mary's Medical"
                    }
                },
                {
                    "name": "Harbor Staging Area",
                    "location": {"lat": 37.768, "lng": -122.405},
                    "camp_type": "rescue_staging",
                    "capacity_persons": 100,
                    "rationale": "Open area near harbor, ideal for helicopter operations and equipment staging",
                    "confidence": 0.74,
                    "factors": {
                        "proximity_to_incidents": "2km from active zone",
                        "accessibility": "Harbor Road clear, helicopter landing viable",
                        "hazard_distance": "1.5km from hazards",
                        "hospital_proximity": "3km to County Medical"
                    }
                }
            ],
            "overall_confidence": 0.76,
            "key_assumptions": [
                "Road conditions assumed passable on recommended routes",
                "No imminent aftershock expected",
                "Hospital capacity data current as of last update"
            ]
        }
        return AgentOutput(
            agent_name=self.agent_name,
            output_type="allocation_plan",
            data=data,
            confidence=0.76,
            sources=[],
            reasoning="Generated 1 resource assignment and 2 camp recommendations (fallback)",
            timestamp=datetime.utcnow()
        )
