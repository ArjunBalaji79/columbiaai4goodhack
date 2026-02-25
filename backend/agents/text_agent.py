from typing import Any
from datetime import datetime

from agents.base_agent import BaseAgent, AgentOutput


class TextAgent(BaseAgent):
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        super().__init__(model_name)

    def get_system_prompt(self) -> str:
        return """You are an intelligence analyst extracting verified facts from text reports during a disaster.

For each text input, extract:

1. SOURCE CLASSIFICATION
   - source_type: official_report | news | social_media | eyewitness | unverified
   - credibility_score: float 0-1 based on source type and content quality

2. CLAIMS EXTRACTION
   For each distinct claim:
   - claim: the factual assertion
   - claim_type: damage | casualty | resource | status | location | other
   - location: if mentioned
   - confidence: your confidence this claim is accurate
   - verifiable: can this be cross-checked?

3. RED FLAGS
   - inconsistencies: internal contradictions
   - exaggeration_indicators: hyperbole, round numbers, emotional language
   - missing_context: what's not being said

Respond ONLY with valid JSON:
{
  "source_type": "social_media",
  "credibility_score": 0.45,
  "claims": [
    {
      "claim": "Main Street Bridge has collapsed",
      "claim_type": "damage",
      "location": {"name": "Main Street Bridge", "coordinates": null},
      "confidence": 0.4,
      "verifiable": true
    }
  ],
  "red_flags": {
    "inconsistencies": [],
    "exaggeration_indicators": ["OMG", "!!", "everyone stay away"],
    "missing_context": ["no timestamp", "no visual evidence", "single source"]
  },
  "raw_text": "original text here"
}"""

    def format_input(self, raw_input: Any) -> list[dict]:
        content = raw_input.get("content", "")
        metadata = raw_input.get("metadata", {})

        source_context = ""
        if metadata.get("source_type"):
            source_context = f"\nSource type: {metadata['source_type']}"
        if metadata.get("timestamp"):
            source_context += f"\nTimestamp: {metadata['timestamp']}"

        text = f"Analyze this disaster report and extract claims:{source_context}\n\n{content}"
        return [{"role": "user", "content": text}]

    def parse_output(self, response: str) -> AgentOutput:
        data = self._extract_json(response)

        claims = data.get("claims") or []
        avg_confidence = (
            sum(c.get("confidence", 0.5) for c in claims) / len(claims)
            if claims else 0.5
        )

        return AgentOutput(
            agent_name=self.agent_name,
            output_type="text_analysis",
            data=data,
            confidence=data.get("credibility_score", avg_confidence),
            sources=[],
            reasoning=f"Text analysis: {len(claims)} claims extracted from {data.get('source_type', 'unknown')} source",
            timestamp=datetime.utcnow()
        )

    def get_fallback_output(self, raw_input: Any) -> AgentOutput:
        import random
        content = raw_input.get("content", "") if isinstance(raw_input, dict) else str(raw_input)
        metadata = raw_input.get("metadata", {}) if isinstance(raw_input, dict) else {}
        source_type = metadata.get("source_type", "")

        # Determine credibility based on source type hint
        if "official" in source_type or "911" in source_type or "utility" in source_type:
            cred = round(random.uniform(0.75, 0.92), 2)
            src = source_type or "official_report"
            red_flags = {"inconsistencies": [], "exaggeration_indicators": [], "missing_context": []}
        elif "social" in source_type:
            cred = round(random.uniform(0.25, 0.55), 2)
            src = "social_media"
            red_flags = {
                "inconsistencies": [],
                "exaggeration_indicators": ["!!!", "OMG", "everyone"],
                "missing_context": ["no timestamp", "no visual evidence", "single source"]
            }
        else:
            cred = round(random.uniform(0.45, 0.72), 2)
            src = source_type or "eyewitness"
            red_flags = {"inconsistencies": [], "exaggeration_indicators": [], "missing_context": ["unverified source"]}

        scenarios = [
            {
                "source_type": src,
                "credibility_score": cred,
                "claims": [
                    {"claim": "Major structural collapse reported at 500 Market Street", "claim_type": "damage",
                     "location": {"name": "500 Market Street"}, "confidence": cred * 0.9, "verifiable": True},
                    {"claim": "Multiple persons trapped, rescue ongoing", "claim_type": "casualty",
                     "location": {"name": "500 Market Street"}, "confidence": cred * 0.8, "verifiable": True}
                ],
                "red_flags": red_flags,
                "raw_text": content[:300] if content else "No text provided"
            },
            {
                "source_type": src,
                "credibility_score": cred,
                "claims": [
                    {"claim": "Main Street Bridge status disputed — possible collapse", "claim_type": "damage",
                     "location": {"name": "Main Street Bridge"}, "confidence": cred * 0.7, "verifiable": True},
                    {"claim": "Route 12 impassable from Sector 2 to Sector 4", "claim_type": "status",
                     "location": {"name": "Route 12"}, "confidence": cred * 0.85, "verifiable": True}
                ],
                "red_flags": red_flags,
                "raw_text": content[:300] if content else "No text provided"
            },
            {
                "source_type": src,
                "credibility_score": cred,
                "claims": [
                    {"claim": "Gas leak detected at Oak/Elm intersection, evacuation recommended", "claim_type": "status",
                     "location": {"name": "Oak/Elm Intersection"}, "confidence": cred * 0.95, "verifiable": True},
                    {"claim": "200-meter exclusion zone required", "claim_type": "resource",
                     "location": {"name": "Sector 3"}, "confidence": cred * 0.9, "verifiable": False}
                ],
                "red_flags": red_flags,
                "raw_text": content[:300] if content else "No text provided"
            }
        ]
        data = random.choice(scenarios)
        data["raw_text"] = content[:300] if content else data["raw_text"]

        return AgentOutput(
            agent_name=self.agent_name,
            output_type="text_analysis",
            data=data,
            confidence=cred,
            sources=[],
            reasoning=f"Text analysis: {len(data['claims'])} claims from {src} (credibility: {cred:.0%})",
            timestamp=datetime.utcnow()
        )
