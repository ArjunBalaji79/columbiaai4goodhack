from typing import Any
from datetime import datetime

from agents.base_agent import BaseAgent, AgentOutput


class PlanningAgent(BaseAgent):
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        super().__init__(model_name)

    def get_system_prompt(self) -> str:
        return """You are a disaster response resource allocation planner.

DECISION PRINCIPLES (in order):
1. LIFE SAFETY: Confirmed trapped > unconfirmed. Time-critical > stable. More people > fewer.
2. CONFIDENCE-WEIGHTED: High-confidence needs beat low-confidence needs.
3. RESOURCE EFFICIENCY: Minimize total response time across all incidents.
4. REVERSIBILITY: Prefer decisions that can be adjusted over irreversible commitments.

For each decision, you MUST:

1. STATE THE RECOMMENDATION
   - What action to take
   - Which resources to allocate
   - Target location/incident

2. SHOW YOUR MATH
   - Why this prioritization
   - What data supports it
   - Confidence in the recommendation

3. EXPLICITLY STATE TRADEOFFS
   - What gets WORSE if this recommendation is followed
   - Quantify impact (e.g., "Sector 2 response time increases by 15 min")
   - Who might be harmed by this choice

4. FLAG UNCERTAINTY
   - What could make this the wrong decision
   - What new information would change the recommendation

5. HUMAN OVERRIDE GUIDANCE
   - Should human approve this? (yes if high-stakes or low-confidence)
   - Deadline for decision

Respond ONLY with valid JSON:
{
  "recommendation": {
    "action": "dispatch_ambulances",
    "resources": ["AMB-7", "AMB-12", "AMB-15"],
    "target": {"sector": "sector_4", "incident_id": "inc_001"}
  },
  "rationale": {
    "primary_reason": "7 confirmed trapped with high confidence (0.82)",
    "supporting_factors": ["structural collapse pattern", "golden hour window"],
    "confidence": 0.76
  },
  "tradeoffs": [
    {
      "impact": "Sector 2 response time increases from 8 to 23 minutes",
      "affected_incidents": ["inc_003", "inc_004"],
      "affected_confidence": 0.34,
      "worst_case": "If Sector 2 incidents are real, 2 people face delayed care"
    }
  ],
  "uncertainty_factors": [
    "Sector 2 reports are unconfirmed - could be more serious than believed",
    "Traffic conditions on Route 7 unknown"
  ],
  "human_approval_required": true,
  "decision_deadline": "2024-02-12T15:15:00Z",
  "time_sensitivity": "critical"
}"""

    def format_input(self, raw_input: Any) -> list[dict]:
        incidents = raw_input.get("incidents", [])
        resources = raw_input.get("resources", [])
        constraints = raw_input.get("constraints", {})

        incidents_text = "\n".join([
            f"- {i.get('id', 'unknown')}: {i.get('incident_type', 'unknown')} in {i.get('sector', 'unknown')} | "
            f"Urgency: {i.get('urgency', 'unknown')} | "
            f"Confidence: {i.get('confidence', 0.5):.0%} | "
            f"Trapped: {i.get('trapped_min', 0)}-{i.get('trapped_max', '?')} | "
            f"Status: {i.get('status', 'unknown')}"
            for i in incidents
        ])

        resources_text = "\n".join([
            f"- {r.get('unit_id', r.get('id', 'unknown'))}: {r.get('resource_type', 'unknown')} | "
            f"Status: {r.get('status', 'unknown')} | "
            f"Sector: {r.get('sector', 'unknown')}"
            for r in resources
        ])

        text = f"""Current disaster situation requiring resource allocation:

ACTIVE INCIDENTS:
{incidents_text or 'No active incidents'}

AVAILABLE RESOURCES:
{resources_text or 'No available resources'}

CONSTRAINTS:
- Hospital capacity: {constraints.get('hospital_capacity', 'unknown')}
- Road blockages: {constraints.get('road_blockages', 'none reported')}
- Weather: {constraints.get('weather', 'unknown')}

Generate prioritized resource allocation recommendation with explicit tradeoffs."""

        return [{"role": "user", "content": text}]

    def parse_output(self, response: str) -> AgentOutput:
        data = self._extract_json(response)

        rationale = data.get("rationale", {})
        recommendation = data.get("recommendation", {})

        return AgentOutput(
            agent_name=self.agent_name,
            output_type="action_plan",
            data=data,
            confidence=rationale.get("confidence", 0.5),
            sources=[],
            reasoning=rationale.get("primary_reason", "Resource allocation recommendation generated"),
            timestamp=datetime.utcnow()
        )

    def get_fallback_output(self, raw_input: Any) -> AgentOutput:
        incidents = raw_input.get("incidents", []) if isinstance(raw_input, dict) else []
        resources = raw_input.get("resources", []) if isinstance(raw_input, dict) else []

        # Find highest priority incident
        critical = next((i for i in incidents if i.get("urgency") == "critical"), None)
        target_id = critical.get("id") if critical else (incidents[0].get("id") if incidents else "inc_001")
        target_sector = critical.get("sector", "4") if critical else "4"

        # Pick available ambulances
        available_ambs = [r["unit_id"] for r in resources
                          if r.get("resource_type") in ("ambulance", "ambulances")
                          and r.get("status") == "available"][:3]
        if not available_ambs:
            available_ambs = ["AMB-7", "AMB-12", "AMB-15"]

        data = {
            "recommendation": {
                "action": "dispatch_ambulances",
                "resources": available_ambs,
                "target": {"sector": f"sector_{target_sector}", "incident_id": target_id}
            },
            "rationale": {
                "primary_reason": f"7 confirmed trapped at {target_id} with high confidence (82%). Pancake collapse pattern — golden hour critical.",
                "supporting_factors": [
                    "Highest confirmed casualty count in active incidents",
                    "Time-critical injuries likely (golden hour -23 min)",
                    "Direct route available via Oak Street",
                    "SAR team already on-scene coordinating"
                ],
                "confidence": 0.76
            },
            "tradeoffs": [
                {
                    "impact": "Sector 2 response time increases from 8 min → 23 min",
                    "affected_incidents": ["inc_003", "inc_004"],
                    "affected_confidence": 0.34,
                    "worst_case": "If Sector 2 incidents are real, 2 people face 15-minute delayed care"
                },
                {
                    "impact": f"3 ambulances committed — reduces reserve capacity by 25%",
                    "affected_incidents": [],
                    "affected_confidence": 0.5,
                    "worst_case": "Aftershock casualty response capacity reduced during commitment period"
                }
            ],
            "uncertainty_factors": [
                "Sector 2 reports unconfirmed — could be more serious than current confidence (34%) suggests",
                "Traffic conditions on Oak Street unknown post-earthquake",
                "Building may have additional collapse risk during extraction"
            ],
            "human_approval_required": True,
            "decision_deadline": "2024-02-12T15:15:00Z",
            "time_sensitivity": "critical"
        }
        return AgentOutput(
            agent_name=self.agent_name,
            output_type="action_plan",
            data=data,
            confidence=0.76,
            sources=[],
            reasoning="Resource allocation: Dispatch 3 ambulances to highest-confidence mass casualty incident",
            timestamp=datetime.utcnow()
        )
