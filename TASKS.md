# Quick Tasks Reference

Use this for "what should I build next?" decisions.

---

## Priority Order

Build in this order for fastest path to working demo:

### 1. 🔥 Backend Skeleton (2 hours)
```
Create: backend/main.py, config.py, requirements.txt
Goal: Server runs, accepts requests
Test: curl http://localhost:8000/health returns {"status": "ok"}
```

### 2. 🔥 Frontend Skeleton (2 hours)
```
Create: Vite + React + Tailwind setup
Goal: Dashboard layout renders
Test: npm run dev shows dark-themed grid layout
```

### 3. 🔥 Vision Agent (2 hours)
```
Create: backend/agents/base_agent.py, vision_agent.py
Goal: Analyze image, return structured damage assessment
Test: Send base64 image, get JSON response with confidence scores
```

### 4. 🔥 Text Agent (1 hour)
```
Create: backend/agents/text_agent.py
Goal: Extract claims from text with credibility scores
Test: Send social media post, get extracted claims
```

### 5. 🔥 Situation Graph (2 hours)
```
Create: backend/graph/schemas.py, situation_graph.py
Goal: Store incidents, resources, track state
Test: Add incident, query it back, update it
```

### 6. 🔥 WebSocket + Real-time (2 hours)
```
Create: backend/api/websocket.py, frontend hooks
Goal: Frontend receives live updates
Test: Backend broadcasts, frontend displays
```

### 7. 🔥 Map View (2 hours)
```
Create: frontend/components/map/*
Goal: Dark map with incident markers
Test: Incidents from graph appear as markers
```

### 8. 🔥 Verification Agent (2 hours)
```
Create: backend/agents/verification_agent.py
Goal: Detect contradictions between sources
Test: Send conflicting claims, get contradiction alert
```

### 9. 🔥 Contradiction UI (2 hours)
```
Create: frontend/components/decisions/ContradictionCard.tsx
Goal: Display contradiction with resolution buttons
Test: Click resolve, backend updates
```

### 10. 🔥 Planning Agent (2 hours)
```
Create: backend/agents/planning_agent.py
Goal: Generate resource recommendations with tradeoffs
Test: Given incidents + resources, get recommendation
```

### 11. 🔥 Action Card UI (2 hours)
```
Create: frontend/components/decisions/ActionCard.tsx
Goal: Display recommendation with tradeoffs, approve/reject
Test: Approve action, resources update
```

### 12. 🔥 Simulation Engine (2 hours)
```
Create: backend/orchestrator/simulation.py
Goal: Play back scenario timeline
Test: Start simulation, events fire on schedule
```

### 13. 🔥 Demo Data (2 hours)
```
Create: Images, audio, text reports, scenario JSON
Goal: Compelling 3-minute demo content
Test: Full simulation runs smoothly
```

### 14. 🔥 Polish + Record (3 hours)
```
Final: Animations, error handling, demo recording
Goal: Winning demo video
Test: 3-min video ready for submission
```

---

## Quick File Creation Commands

When starting a new file, use these patterns:

### New Agent
```python
# backend/agents/{name}_agent.py
from .base_agent import BaseAgent, AgentOutput

class {Name}Agent(BaseAgent):
    def get_system_prompt(self) -> str:
        return """..."""
    
    def format_input(self, raw_input):
        return [{"role": "user", "content": ...}]
    
    def parse_output(self, response: str) -> AgentOutput:
        # Parse JSON from response
        pass
```

### New React Component
```tsx
// frontend/src/components/{category}/{Name}.tsx
interface {Name}Props {
  // props
}

export function {Name}({ ...props }: {Name}Props) {
  return (
    <div className="...">
      {/* content */}
    </div>
  );
}
```

### New API Endpoint
```python
# In backend/api/routes.py
@router.get("/path")
async def handler(coordinator = Depends(get_coordinator)):
    return {"data": ...}
```

---

## Common Patterns

### Sending to Claude API
```python
response = self.client.messages.create(
    model="claude-opus-4-5-20251101",
    max_tokens=4096,
    system=self.get_system_prompt(),
    messages=[{"role": "user", "content": content}]
)
return response.content[0].text
```

### Sending Image to Claude
```python
messages=[{
    "role": "user",
    "content": [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": base64_string
            }
        },
        {"type": "text", "text": "Analyze this disaster image."}
    ]
}]
```

### WebSocket Broadcast
```python
await broadcast("event_type", {"key": "value"})
```

### Zustand Store Update
```typescript
set((state) => ({
  graph: { ...state.graph, incidents: newIncidents }
}))
```

---

## "I'm Stuck" Checklist

1. **Server won't start?**
   - Check `.env` has `GEMINI_API_KEY`
   - Check `requirements.txt` installed
   - Check port 8000 not in use

2. **Frontend won't connect?**
   - Check CORS origins in `config.py`
   - Check WebSocket URL matches backend

3. **Agent returns garbage?**
   - Print raw response before parsing
   - Check system prompt is clear about JSON format
   - Add "Respond ONLY with valid JSON" to prompt

4. **Map not showing?**
   - Check Leaflet CSS imported
   - Check container has explicit height
   - Check tile URL is correct

5. **Types not matching?**
   - Regenerate from `schemas.py`
   - Check camelCase vs snake_case

---

## Demo Checklist (Last Day)

- [ ] Simulation runs start to finish without errors
- [ ] Contradiction appears and can be resolved
- [ ] Action recommendation shows tradeoffs
- [ ] Approve/reject buttons work
- [ ] Map updates in real-time
- [ ] At least 3 different signal types shown
- [ ] Confidence scores visible
- [ ] Demo video is under 3 minutes
- [ ] Audio is clear
- [ ] README explains the project
