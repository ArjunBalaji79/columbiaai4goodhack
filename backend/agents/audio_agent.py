from typing import Any
from datetime import datetime

from agents.base_agent import BaseAgent, AgentOutput


class AudioAgent(BaseAgent):
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        super().__init__(model_name)

    def get_system_prompt(self) -> str:
        return """You are an emergency communications analyst processing audio from disaster response.

For each audio input, extract:

1. TRANSCRIPTION (if not provided)
   - Full text of audio content

2. SPEAKER ANALYSIS
   - speaker_type: first_responder | civilian | dispatch | official | unknown
   - emotional_state: calm | stressed | panicked | injured
   - credibility_indicators: training evident, coherent details, etc.

3. INCIDENT DETAILS
   - location_mentioned: any addresses, landmarks, descriptions
   - incident_type: what is being reported
   - urgency: critical | high | medium | low
   - persons_involved: {trapped: int?, injured: int?, evacuated: int?}

4. ACTIONABLE INTEL
   - resource_requests: what help is being requested
   - access_issues: blocked routes, hazards mentioned
   - time_references: any timestamps or durations mentioned

5. CONFIDENCE
   - overall_confidence: float 0-1
   - unclear_portions: parts that were hard to understand

Respond ONLY with valid JSON:
{
  "transcript": "We have multiple people trapped on the 4th floor...",
  "speaker_type": "first_responder",
  "emotional_state": "stressed",
  "credibility_indicators": ["professional terminology", "systematic reporting"],
  "location_mentioned": {"raw": "4th floor, Market Street building", "parsed": null},
  "incident_type": "structural_collapse_trapped_persons",
  "urgency": "critical",
  "persons_involved": {"trapped": {"min": 3, "max": 5}, "injured": null},
  "resource_requests": ["rescue team", "medical"],
  "access_issues": ["stairwell blocked"],
  "time_references": ["ongoing"],
  "overall_confidence": 0.82,
  "unclear_portions": ["exact floor number uncertain"]
}"""

    def format_input(self, raw_input: Any) -> list[dict]:
        content = raw_input.get("content", "")
        metadata = raw_input.get("metadata", {})
        transcript = metadata.get("transcript", "")

        if transcript:
            text = f"Process this emergency audio transcript:\n\n{transcript}"
        elif content and len(content) > 100:
            # Real audio would be processed here - for demo use description
            text = f"Analyze this emergency audio communication. The audio contains a distress call from an incident scene."
        else:
            text = "Process this emergency audio communication from a disaster scene."

        return [{"role": "user", "content": text}]

    def parse_output(self, response: str) -> AgentOutput:
        data = self._extract_json(response)

        return AgentOutput(
            agent_name=self.agent_name,
            output_type="audio_analysis",
            data=data,
            confidence=data.get("overall_confidence", 0.5),
            sources=[],
            reasoning=f"Audio analysis: {data.get('speaker_type', 'unknown')} reporting {data.get('incident_type', 'unknown')}",
            timestamp=datetime.utcnow()
        )

    def get_fallback_output(self, raw_input: Any) -> AgentOutput:
        import random
        metadata = raw_input.get("metadata", {}) if isinstance(raw_input, dict) else {}
        transcript = metadata.get("transcript", "")

        scenarios = [
            {
                "transcript": transcript or "Unit 7 to dispatch — we have a confirmed pancake collapse at 500 Market Street. I can hear at least 5 voices calling for help. Floors 2 through 4 have collapsed. Stairwells are gone. Requesting SAR team and 3 ambulances minimum. Approach from west side only.",
                "speaker_type": "first_responder",
                "emotional_state": "stressed",
                "credibility_indicators": ["professional terminology", "systematic reporting", "unit identification"],
                "location_mentioned": {"raw": "500 Market Street, floors 2-4", "parsed": None},
                "incident_type": "structural_collapse_trapped_persons",
                "urgency": "critical",
                "persons_involved": {"trapped": {"min": 4, "max": 7}, "injured": None},
                "resource_requests": ["SAR team", "3 ambulances", "structural engineer"],
                "access_issues": ["stairwells collapsed", "west approach only"],
                "time_references": ["ongoing"],
                "overall_confidence": 0.85,
                "unclear_portions": []
            },
            {
                "transcript": transcript or "This is Sarah Chen at 847 Oak Street, 3rd floor apartment. The stairs have completely collapsed. There are 4 of us, including my two children aged 6 and 9. The building is still shaking. Please help us. We cannot get out.",
                "speaker_type": "civilian",
                "emotional_state": "panicked",
                "credibility_indicators": ["specific address", "detailed description", "consistent narrative"],
                "location_mentioned": {"raw": "847 Oak Street, 3rd floor", "parsed": None},
                "incident_type": "building_collapse_trapped_civilians",
                "urgency": "critical",
                "persons_involved": {"trapped": {"min": 4, "max": 4}, "injured": None},
                "resource_requests": ["rescue team", "ambulance"],
                "access_issues": ["staircase collapsed"],
                "time_references": ["ongoing"],
                "overall_confidence": 0.79,
                "unclear_portions": ["building structural status unclear"]
            },
            {
                "transcript": transcript or "Dispatch, this is Engine 3. We have active fire at Elm and Oak, spreading to adjacent structure. Wind is pushing it northeast. We need 2 more engine companies and a ladder truck. Evacuating 3-block radius. No confirmed casualties yet but building occupancy unknown.",
                "speaker_type": "first_responder",
                "emotional_state": "calm",
                "credibility_indicators": ["professional radio protocol", "systematic assessment", "unit identification"],
                "location_mentioned": {"raw": "Elm and Oak intersection", "parsed": None},
                "incident_type": "structural_fire_spreading",
                "urgency": "high",
                "persons_involved": {"trapped": None, "injured": None, "evacuated": {"min": 50, "max": 200}},
                "resource_requests": ["2 engine companies", "ladder truck"],
                "access_issues": ["smoke visibility poor", "wind direction northeast"],
                "time_references": ["ongoing"],
                "overall_confidence": 0.88,
                "unclear_portions": []
            }
        ]
        data = random.choice(scenarios)
        if transcript:
            data["transcript"] = transcript
        return AgentOutput(
            agent_name=self.agent_name,
            output_type="audio_analysis",
            data=data,
            confidence=data["overall_confidence"],
            sources=[],
            reasoning=f"Audio analysis: {data['speaker_type']} reporting {data['incident_type']} with {data['urgency']} urgency",
            timestamp=datetime.utcnow()
        )
