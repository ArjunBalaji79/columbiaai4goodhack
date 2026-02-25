# CrisisCore - Project Instructions

## What We're Building

**CrisisCore** is a multimodal, multi-agent disaster response coordination system for the Columbia AI for Good Hackathon.

**One-liner:** Transform chaotic disaster signals (images, audio, text, voice) into prioritized, auditable response decisions with visible uncertainty.

**Key insight:** Most disaster AI hides uncertainty. We surface it. When agents disagree, humans see why.

## Project Structure

```
crisiscore/
├── backend/
│   ├── main.py              # FastAPI entry
│   ├── config.py            # Settings + API keys
│   ├── agents/              # All AI agents (8 total)
│   ├── graph/               # Situation graph
│   ├── orchestrator/        # Coordination logic
│   ├── api/                 # REST + WebSocket + Voice
│   └── demo_data/           # Scenario files
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # ResourcesPage, VoicePage, DebatePage, CopilotPage
│   │   ├── hooks/           # Custom hooks
│   │   └── types/           # TypeScript types
│   └── public/
└── scripts/
```

## Tech Stack

- **Backend:** Python 3.9+, FastAPI, Google Generative AI SDK
- **Frontend:** React 18, TypeScript, Tailwind, Vite
- **Map:** Leaflet + React-Leaflet
- **Flow Viz:** React Flow
- **AI:** Google Gemini 2.0 Flash
- **Voice:** ElevenLabs TTS API + Browser Speech Recognition

## Key Commands

```bash
# Backend
cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm run dev
```

## Code Style

- Python: Type hints everywhere, Pydantic for models
- TypeScript: Strict mode, interfaces over types
- Components: Functional with hooks, no classes
- Naming: `snake_case` Python, `camelCase` TypeScript

## Agent Architecture Pattern

Every agent follows this pattern:
```python
class SomeAgent(BaseAgent):
    def get_system_prompt(self) -> str: ...
    def format_input(self, raw_input) -> list[dict]: ...
    def parse_output(self, response: str) -> AgentOutput: ...
```

## Key Features

1. **Multi-agent contradiction detection** — Cross-modal verification with live debate
2. **Resource allocation** — AI-optimized resource-to-incident assignments with approve/reject
3. **Camp location finder** — AI suggests optimal relief camp placements based on hazards, accessibility, and proximity
4. **Voice command center** — ElevenLabs TTS situation reports + browser voice recording for field reports
5. **Epistemic transparency** — Explicit tradeoffs, confidence scores, uncertainty factors on every decision
