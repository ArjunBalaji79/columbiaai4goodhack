from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel
from datetime import datetime
import json
import re


class AgentOutput(BaseModel):
    agent_name: str
    output_type: str
    data: dict
    confidence: float
    sources: list[str]
    reasoning: str
    timestamp: datetime


class BaseAgent(ABC):
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        self.agent_name = self.__class__.__name__
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            import google.generativeai as genai
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.get_system_prompt()
            )
        return self._model

    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

    @abstractmethod
    def format_input(self, raw_input: Any) -> list[dict]:
        pass

    @abstractmethod
    def parse_output(self, response: str) -> AgentOutput:
        pass

    async def process(self, raw_input: Any) -> AgentOutput:
        messages = self.format_input(raw_input)
        try:
            import asyncio
            import functools
            import google.generativeai as genai

            model = self._get_model()
            contents = self._convert_messages(messages)

            response = await asyncio.to_thread(
                functools.partial(
                    model.generate_content,
                    contents,
                    generation_config=genai.GenerationConfig(
                        max_output_tokens=4096,
                        temperature=0.7
                    )
                )
            )
            return self.parse_output(response.text)
        except Exception as e:
            print(f"[{self.agent_name}] API error: {e} — using demo fallback")
            return self.get_fallback_output(raw_input)

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        """Convert messages to Gemini content format."""
        contents = []
        for msg in messages:
            role = "user" if msg.get("role") == "user" else "model"
            content = msg.get("content", "")

            if isinstance(content, str):
                contents.append({"role": role, "parts": [content]})
            elif isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            parts.append(part["text"])
                        elif part.get("type") == "image":
                            source = part.get("source", {})
                            parts.append({
                                "inline_data": {
                                    "mime_type": source.get("media_type", "image/jpeg"),
                                    "data": source.get("data", "")
                                }
                            })
                    elif isinstance(part, str):
                        parts.append(part)
                contents.append({"role": role, "parts": parts})
            else:
                contents.append({"role": role, "parts": [str(content)]})

        return contents

    def get_fallback_output(self, raw_input: Any) -> AgentOutput:
        """Override in subclasses to provide realistic demo fallback data."""
        return AgentOutput(
            agent_name=self.agent_name,
            output_type="fallback",
            data={"error": "API unavailable", "demo_mode": True},
            confidence=0.5,
            sources=[],
            reasoning="Demo fallback — check GEMINI_API_KEY in backend/.env",
            timestamp=datetime.utcnow()
        )

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from response text, handling markdown code blocks and minor syntax errors."""
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            candidate = match.group(1).strip()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        start = text.find('{')
        if start != -1:
            depth = 0
            for i, ch in enumerate(text[start:], start):
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        candidate = text[start:i + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            cleaned = re.sub(r',\s*([}\]])', r'\1', candidate)
                            try:
                                return json.loads(cleaned)
                            except json.JSONDecodeError:
                                break

        raise ValueError(f"Could not extract JSON from response: {text[:200]}")
