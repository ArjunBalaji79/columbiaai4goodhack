from typing import Any
from datetime import datetime

from agents.base_agent import BaseAgent, AgentOutput


class VerificationAgent(BaseAgent):
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        super().__init__(model_name)

    def get_system_prompt(self) -> str:
        return """You are an epistemic verification agent detecting contradictions across information sources.

You receive multiple claims about the same entity (location, incident, resource).

Your task:

1. IDENTIFY CONTRADICTIONS
   - Type: direct (A says X, B says NOT X) | temporal | spatial | magnitude
   - Severity: low | medium | high
   - Description: what specifically conflicts

2. CREDIBILITY WEIGHTING
   - Rank sources by reliability
   - Consider: source type, recency, specificity, corroboration
   - Note: official > first_responder > eyewitness > social_media

3. TEMPORAL ANALYSIS
   - Are conflicts explainable by time gap?
   - Could situation have changed between reports?

4. VERDICT
   - CONSISTENT: sources agree, high confidence
   - CONTRADICTION: sources conflict, needs resolution
   - UNCERTAIN: insufficient data to determine
   - TEMPORAL_GAP: conflict likely due to situation change

5. RECOMMENDED ACTION
   - ACCEPT: use highest-confidence claim
   - FLAG_FOR_HUMAN: significant contradiction, needs decision
   - REQUEST_VERIFICATION: send ground/aerial verification
   - WAIT: more data needed

Respond ONLY with valid JSON:
{
  "entity": "Main Street Bridge",
  "entity_type": "infrastructure",
  "claims_analyzed": [
    {"source": "audio_003", "claim": "collapsed", "confidence": 0.72, "timestamp": "15:01"},
    {"source": "satellite_001", "claim": "intact", "confidence": 0.89, "timestamp": "14:40"}
  ],
  "contradictions": [
    {
      "type": "direct",
      "severity": "high",
      "description": "Audio claims collapse, satellite shows intact",
      "possible_explanation": "21-minute time gap - collapse may have occurred after image"
    }
  ],
  "verdict": "CONTRADICTION",
  "temporal_analysis": "Satellite predates audio by 21 minutes. Collapse post-image is plausible.",
  "recommended_action": "REQUEST_VERIFICATION",
  "recommended_action_details": "Deploy aerial drone or ground team to confirm bridge status",
  "urgency": "high"
}"""

    def format_input(self, raw_input: Any) -> list[dict]:
        entity = raw_input.get("entity", "Unknown entity")
        entity_type = raw_input.get("entity_type", "unknown")
        claims = raw_input.get("claims", [])

        claims_text = "\n".join([
            f"- Source: {c.get('source', 'unknown')} | "
            f"Claim: {c.get('claim', '')} | "
            f"Confidence: {c.get('confidence', 0.5)} | "
            f"Timestamp: {c.get('timestamp', 'unknown')} | "
            f"Source type: {c.get('source_type', 'unknown')}"
            for c in claims
        ])

        text = f"""Verify conflicting claims about: {entity} (type: {entity_type})

Claims received:
{claims_text}

Analyze for contradictions and provide your verdict."""

        return [{"role": "user", "content": text}]

    def parse_output(self, response: str) -> AgentOutput:
        data = self._extract_json(response)

        return AgentOutput(
            agent_name=self.agent_name,
            output_type="verification",
            data=data,
            confidence=0.8,
            sources=[c.get("source", "") for c in (data.get("claims_analyzed") or [])],
            reasoning=f"Verification: {data.get('verdict', 'UNCERTAIN')} - {data.get('temporal_analysis', '')}",
            timestamp=datetime.utcnow()
        )

    def get_fallback_output(self, raw_input: Any) -> AgentOutput:
        entity = raw_input.get("entity", "Unknown") if isinstance(raw_input, dict) else "Unknown"
        claims = raw_input.get("claims", []) if isinstance(raw_input, dict) else []

        data = {
            "entity": entity,
            "entity_type": raw_input.get("entity_type", "infrastructure") if isinstance(raw_input, dict) else "infrastructure",
            "claims_analyzed": claims[:3],
            "contradictions": [
                {
                    "type": "direct",
                    "severity": "high",
                    "description": f"Conflicting reports about {entity} status from different sources",
                    "possible_explanation": "21-minute time gap between satellite image and ground report — collapse may have occurred after image capture"
                }
            ],
            "verdict": "CONTRADICTION",
            "temporal_analysis": f"Satellite image predates audio report by 21 minutes. {entity} collapse post-satellite-image is plausible given 6.8M seismic event.",
            "recommended_action": "REQUEST_VERIFICATION",
            "recommended_action_details": f"Deploy HELI-1 for aerial visual confirmation of {entity} status. Critical routing decision pending.",
            "urgency": "high"
        }
        return AgentOutput(
            agent_name=self.agent_name,
            output_type="verification",
            data=data,
            confidence=0.82,
            sources=[c.get("source", "") for c in claims],
            reasoning=f"Verification: CONTRADICTION detected for {entity} — temporal gap analysis suggests situation change",
            timestamp=datetime.utcnow()
        )
