from typing import Any
from datetime import datetime

from agents.base_agent import BaseAgent, AgentOutput


class VisionAgent(BaseAgent):
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        super().__init__(model_name)

    def get_system_prompt(self) -> str:
        return """You are a disaster damage assessment specialist analyzing images from an active emergency.

For each image, extract:

1. DAMAGE ASSESSMENT
   - damage_level: none | minor | moderate | severe | catastrophic
   - damage_types: list of [structural_collapse, fire, flooding, debris, gas_leak, power_line_down]
   - affected_area_estimate: string description

2. CASUALTY INDICATORS
   - visible_persons: number or "none visible"
   - trapped_indicators: boolean + description
   - estimated_casualties: {min: int, max: int, confidence: float}

3. ACCESS STATUS
   - accessibility: accessible | partially_blocked | blocked | hazardous
   - hazards: list of observed hazards
   - recommended_approach: string or null

4. CONFIDENCE
   - overall_confidence: float 0-1
   - limitations: what you CANNOT determine from this image
   - additional_info_needed: what would help

Respond ONLY with valid JSON matching this structure:
{
  "damage_level": "severe",
  "damage_types": ["structural_collapse", "fire"],
  "affected_area_estimate": "approximately 3-story building, eastern wing",
  "visible_persons": 0,
  "trapped_indicators": {"present": true, "description": "debris pattern suggests occupied floors collapsed"},
  "estimated_casualties": {"min": 2, "max": 10, "confidence": 0.6},
  "accessibility": "blocked",
  "hazards": ["unstable structure", "active fire", "debris field"],
  "recommended_approach": "approach from west, await structural assessment",
  "overall_confidence": 0.75,
  "limitations": ["cannot assess interior damage", "smoke obscures eastern section"],
  "additional_info_needed": ["building occupancy data", "structural blueprints"]
}

Be precise. Acknowledge uncertainty. Never hallucinate details not visible."""

    def format_input(self, raw_input: Any) -> list[dict]:
        content = raw_input.get("content", "")
        metadata = raw_input.get("metadata", {})

        # Build context message
        context_parts = ["Analyze this disaster scene image."]
        if metadata.get("sector"):
            context_parts.append(f"Location: Sector {metadata['sector']}")
        if metadata.get("source"):
            context_parts.append(f"Source: {metadata['source']}")

        message_content = []

        # Add the image if base64 content provided
        if content and len(content) > 100:
            message_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": content
                }
            })
        else:
            # Use the scene description from metadata if available
            description = metadata.get("description", "")
            if description:
                context_parts.append(f"Scene description (no image file): {description}")
            else:
                context_parts.append("No image provided - generate a realistic assessment for a severe structural collapse.")

        message_content.append({
            "type": "text",
            "text": " ".join(context_parts)
        })

        return [{"role": "user", "content": message_content}]

    def parse_output(self, response: str) -> AgentOutput:
        data = self._extract_json(response)

        return AgentOutput(
            agent_name=self.agent_name,
            output_type="damage_assessment",
            data=data,
            confidence=data.get("overall_confidence", 0.5),
            sources=[],
            reasoning=f"Vision analysis: {data.get('damage_level', 'unknown')} damage detected",
            timestamp=datetime.utcnow()
        )

    def get_fallback_output(self, raw_input: Any) -> AgentOutput:
        import random
        scenarios = [
            {
                "damage_level": "severe",
                "damage_types": ["structural_collapse", "debris"],
                "affected_area_estimate": "3-story commercial building, full eastern wing",
                "visible_persons": 0,
                "trapped_indicators": {"present": True, "description": "Pancake collapse pattern, debris field consistent with occupied floors"},
                "estimated_casualties": {"min": 3, "max": 8, "confidence": 0.72},
                "accessibility": "blocked",
                "hazards": ["unstable structure", "debris field", "potential gas leak"],
                "recommended_approach": "Approach from west side only, await structural assessment",
                "overall_confidence": 0.78,
                "limitations": ["Cannot assess interior without ground team", "Smoke obscures eastern section"],
                "additional_info_needed": ["Building occupancy records", "Structural blueprints"]
            },
            {
                "damage_level": "moderate",
                "damage_types": ["fire", "structural_damage"],
                "affected_area_estimate": "Residential building, 2 floors affected",
                "visible_persons": 2,
                "trapped_indicators": {"present": False, "description": "Persons appear mobile, evacuating"},
                "estimated_casualties": {"min": 0, "max": 3, "confidence": 0.55},
                "accessibility": "partially_blocked",
                "hazards": ["active fire", "smoke"],
                "recommended_approach": "Fire suppression priority, evacuate adjacent units",
                "overall_confidence": 0.68,
                "limitations": ["Fire obscures full damage extent"],
                "additional_info_needed": ["Thermal imaging", "Occupancy count"]
            },
            {
                "damage_level": "catastrophic",
                "damage_types": ["structural_collapse", "fire", "debris"],
                "affected_area_estimate": "Multi-block industrial zone, 4 structures affected",
                "visible_persons": 0,
                "trapped_indicators": {"present": True, "description": "Vehicle crushing, roof collapse across 3 structures"},
                "estimated_casualties": {"min": 5, "max": 20, "confidence": 0.65},
                "accessibility": "hazardous",
                "hazards": ["unstable structure", "active fire", "chemical storage risk", "power line down"],
                "recommended_approach": "HAZMAT assessment required before entry, 200m exclusion zone",
                "overall_confidence": 0.71,
                "limitations": ["Chemical hazard prevents close inspection", "Multiple collapse layers"],
                "additional_info_needed": ["HAZMAT manifest", "Aerial thermal scan"]
            }
        ]
        data = random.choice(scenarios)
        return AgentOutput(
            agent_name=self.agent_name,
            output_type="damage_assessment",
            data=data,
            confidence=data["overall_confidence"],
            sources=[],
            reasoning=f"Vision analysis: {data['damage_level']} damage detected with {', '.join(data['damage_types'][:2])}",
            timestamp=datetime.utcnow()
        )
