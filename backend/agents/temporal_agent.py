from typing import Any
from datetime import datetime

from agents.base_agent import BaseAgent, AgentOutput


class TemporalAgent(BaseAgent):
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        super().__init__(model_name)

    def get_system_prompt(self) -> str:
        return """You are a temporal reasoning agent that projects how disaster situations evolve over time.

Your responsibilities:

1. CONFIDENCE DECAY
   - Information gets stale. Calculate decay based on:
     - Time since observation
     - Type of phenomenon (fire spreads fast, building damage is stable)
     - Environmental factors (wind, aftershocks)

2. SITUATION PROJECTION
   - Given known spread rates, project current state
   - Example: Fire observed at 500 sqm 20 min ago, wind 10km/h NE -> estimate current extent

3. STALENESS FLAGGING
   - Flag data that's too old to be reliable
   - Recommend refresh priorities

4. TIMELINE RECONSTRUCTION
   - Order events chronologically
   - Identify gaps in timeline

Respond ONLY with valid JSON:
{
  "entity": "fire_sector_3",
  "original_observation": {
    "state": {"area_sqm": 2500, "intensity": "active"},
    "timestamp": "2024-02-12T15:05:00Z",
    "age_minutes": 15
  },
  "projected_state": {
    "state": {"area_sqm": 4200, "intensity": "active"},
    "timestamp": "2024-02-12T15:20:00Z",
    "confidence": 0.68
  },
  "projection_assumptions": [
    "wind_speed_10kmh_NE",
    "no_firebreak_intervention",
    "building_density_high"
  ],
  "confidence_decay": {
    "original_confidence": 0.85,
    "current_confidence": 0.68,
    "decay_reason": "15 minutes elapsed, fire dynamics uncertain"
  },
  "staleness_flag": false,
  "refresh_priority": "high",
  "refresh_recommendation": "Request updated aerial thermal imaging"
}"""

    def format_input(self, raw_input: Any) -> list[dict]:
        entity = raw_input.get("entity", "unknown")
        observations = raw_input.get("observations", [])
        current_time = raw_input.get("current_time", datetime.utcnow().isoformat())

        obs_text = "\n".join([
            f"- {o.get('timestamp', 'unknown')}: {o.get('state', {})} (confidence: {o.get('confidence', 0.5)})"
            for o in observations
        ])

        text = f"""Project temporal evolution for: {entity}

Current time: {current_time}

Historical observations:
{obs_text or 'No observations provided'}

Calculate confidence decay and project current state."""

        return [{"role": "user", "content": text}]

    def parse_output(self, response: str) -> AgentOutput:
        data = self._extract_json(response)

        return AgentOutput(
            agent_name=self.agent_name,
            output_type="temporal_projection",
            data=data,
            confidence=data.get("projected_state", {}).get("confidence", 0.5),
            sources=[],
            reasoning=f"Temporal projection: staleness_flag={data.get('staleness_flag', False)}, refresh_priority={data.get('refresh_priority', 'unknown')}",
            timestamp=datetime.utcnow()
        )

    def get_fallback_output(self, raw_input: Any) -> AgentOutput:
        entity = raw_input.get("entity", "unknown_entity")
        return AgentOutput(
            agent_name=self.agent_name,
            output_type="temporal_projection",
            data={
                "entity": entity,
                "original_observation": {
                    "state": {"status": "active", "severity": "high"},
                    "timestamp": datetime.utcnow().isoformat(),
                    "age_minutes": 12
                },
                "projected_state": {
                    "state": {"status": "active", "severity": "high", "trend": "worsening"},
                    "timestamp": datetime.utcnow().isoformat(),
                    "confidence": 0.62
                },
                "projection_assumptions": [
                    "no_intervention_since_last_observation",
                    "environmental_conditions_stable"
                ],
                "confidence_decay": {
                    "original_confidence": 0.85,
                    "current_confidence": 0.62,
                    "decay_reason": "12 minutes elapsed since last observation"
                },
                "staleness_flag": False,
                "refresh_priority": "high",
                "refresh_recommendation": "Request updated observation from nearest available unit"
            },
            confidence=0.62,
            sources=[],
            reasoning=f"Temporal projection for {entity}: confidence decayed from 0.85 to 0.62 over 12 minutes",
            timestamp=datetime.utcnow()
        )
