# Backend API Specifications

## Overview

FastAPI backend with REST endpoints + WebSocket for real-time updates.

**Base URL:** `http://localhost:8000`  
**WebSocket:** `ws://localhost:8000/ws`

---

## Project Setup

### Directory Structure

```
backend/
├── main.py              # FastAPI app entry
├── config.py            # Settings
├── requirements.txt
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── vision_agent.py
│   ├── audio_agent.py
│   ├── text_agent.py
│   ├── verification_agent.py
│   ├── planning_agent.py
│   └── temporal_agent.py
│
├── graph/
│   ├── __init__.py
│   ├── schemas.py       # Pydantic models (see SCHEMAS.md)
│   └── situation_graph.py
│
├── orchestrator/
│   ├── __init__.py
│   ├── coordinator.py   # Main orchestration
│   ├── deliberation.py  # Agent disagreement handling
│   └── simulation.py    # Demo playback
│
├── api/
│   ├── __init__.py
│   ├── routes.py        # REST endpoints
│   └── websocket.py     # WebSocket handler
│
└── demo_data/
    ├── scenario_earthquake.json
    ├── images/
    ├── audio/
    └── documents/
```

### requirements.txt

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
websockets==12.0
google-generativeai>=0.3.0
pydantic==2.5.0
python-dotenv==1.0.0
aiofiles==23.2.1
```

### config.py

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    gemini_api_key: str
    cors_origins: list[str] = ["http://localhost:5173"]
    simulation_speed: float = 1.0  # 1.0 = real-time, 2.0 = 2x speed
    
    class Config:
        env_file = ".env"

@lru_cache
def get_settings():
    return Settings()
```

---

## Main Application

```python
# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import get_settings
from api.routes import router
from api.websocket import websocket_endpoint
from orchestrator.coordinator import Coordinator

settings = get_settings()

# Global coordinator instance
coordinator: Coordinator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global coordinator
    coordinator = Coordinator()
    await coordinator.initialize()
    yield
    await coordinator.shutdown()

app = FastAPI(
    title="CrisisCore API",
    description="Multimodal disaster response coordination",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.add_api_websocket_route("/ws", websocket_endpoint)

def get_coordinator() -> Coordinator:
    return coordinator
```

---

## REST Endpoints

```python
# backend/api/routes.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional
import base64

from graph.schemas import (
    SituationGraph, 
    SignalInput, 
    HumanDecision,
    ActionRecommendation,
    ContradictionAlert
)
from main import get_coordinator

router = APIRouter()

# ============== GRAPH STATE ==============

@router.get("/graph", response_model=SituationGraph)
async def get_graph(coordinator = Depends(get_coordinator)):
    """Get current situation graph state."""
    return coordinator.graph

@router.get("/graph/incidents")
async def get_incidents(coordinator = Depends(get_coordinator)):
    """Get all incidents."""
    return coordinator.graph.incidents

@router.get("/graph/incidents/{incident_id}")
async def get_incident(incident_id: str, coordinator = Depends(get_coordinator)):
    """Get specific incident."""
    if incident_id not in coordinator.graph.incidents:
        raise HTTPException(404, "Incident not found")
    return coordinator.graph.incidents[incident_id]

@router.get("/graph/resources")
async def get_resources(coordinator = Depends(get_coordinator)):
    """Get all resources."""
    return coordinator.graph.resources

# ============== SIGNAL INGESTION ==============

@router.post("/signals/image")
async def ingest_image(
    file: UploadFile = File(...),
    location_lat: Optional[float] = None,
    location_lng: Optional[float] = None,
    sector: Optional[str] = None,
    coordinator = Depends(get_coordinator)
):
    """Ingest an image signal."""
    content = await file.read()
    base64_content = base64.b64encode(content).decode()
    
    result = await coordinator.process_signal(
        signal_type="image",
        content=base64_content,
        metadata={
            "filename": file.filename,
            "location": {"lat": location_lat, "lng": location_lng} if location_lat else None,
            "sector": sector
        }
    )
    return result

@router.post("/signals/audio")
async def ingest_audio(
    file: UploadFile = File(...),
    transcript: Optional[str] = None,
    coordinator = Depends(get_coordinator)
):
    """Ingest an audio signal."""
    content = await file.read()
    base64_content = base64.b64encode(content).decode()
    
    result = await coordinator.process_signal(
        signal_type="audio",
        content=base64_content,
        metadata={"filename": file.filename, "transcript": transcript}
    )
    return result

@router.post("/signals/text")
async def ingest_text(
    input: SignalInput,
    coordinator = Depends(get_coordinator)
):
    """Ingest a text signal (social media, report, etc.)."""
    result = await coordinator.process_signal(
        signal_type="text",
        content=input.content,
        metadata=input.metadata
    )
    return result

# ============== HUMAN DECISIONS ==============

@router.get("/decisions/pending")
async def get_pending_decisions(coordinator = Depends(get_coordinator)):
    """Get all pending decisions (contradictions + actions)."""
    return {
        "contradictions": [
            c for c in coordinator.graph.contradictions.values() 
            if not c.resolved
        ],
        "actions": [
            a for a in coordinator.graph.pending_actions.values() 
            if a.status == "pending"
        ]
    }

@router.post("/decisions/contradiction/{alert_id}")
async def resolve_contradiction(
    alert_id: str,
    decision: HumanDecision,
    coordinator = Depends(get_coordinator)
):
    """Resolve a contradiction alert."""
    if alert_id not in coordinator.graph.contradictions:
        raise HTTPException(404, "Contradiction not found")
    
    result = await coordinator.resolve_contradiction(alert_id, decision)
    return result

@router.post("/decisions/action/{action_id}/approve")
async def approve_action(
    action_id: str,
    coordinator = Depends(get_coordinator)
):
    """Approve a pending action recommendation."""
    if action_id not in coordinator.graph.pending_actions:
        raise HTTPException(404, "Action not found")
    
    result = await coordinator.approve_action(action_id)
    return result

@router.post("/decisions/action/{action_id}/reject")
async def reject_action(
    action_id: str,
    reason: Optional[str] = None,
    coordinator = Depends(get_coordinator)
):
    """Reject a pending action recommendation."""
    if action_id not in coordinator.graph.pending_actions:
        raise HTTPException(404, "Action not found")
    
    result = await coordinator.reject_action(action_id, reason)
    return result

# ============== SIMULATION CONTROL ==============

@router.post("/simulation/start")
async def start_simulation(
    scenario_id: str = "earthquake_001",
    speed: float = 1.0,
    coordinator = Depends(get_coordinator)
):
    """Start demo simulation."""
    await coordinator.start_simulation(scenario_id, speed)
    return {"status": "started", "scenario": scenario_id, "speed": speed}

@router.post("/simulation/pause")
async def pause_simulation(coordinator = Depends(get_coordinator)):
    """Pause simulation."""
    await coordinator.pause_simulation()
    return {"status": "paused"}

@router.post("/simulation/resume")
async def resume_simulation(coordinator = Depends(get_coordinator)):
    """Resume simulation."""
    await coordinator.resume_simulation()
    return {"status": "resumed"}

@router.post("/simulation/reset")
async def reset_simulation(coordinator = Depends(get_coordinator)):
    """Reset simulation to beginning."""
    await coordinator.reset_simulation()
    return {"status": "reset"}

@router.get("/simulation/status")
async def get_simulation_status(coordinator = Depends(get_coordinator)):
    """Get current simulation status."""
    return coordinator.get_simulation_status()

# ============== AUDIT ==============

@router.get("/audit/decision/{decision_id}")
async def get_decision_audit(
    decision_id: str,
    coordinator = Depends(get_coordinator)
):
    """Get full audit trail for a decision."""
    return await coordinator.get_decision_audit(decision_id)

@router.get("/audit/incident/{incident_id}")
async def get_incident_audit(
    incident_id: str,
    coordinator = Depends(get_coordinator)
):
    """Get all signals and decisions related to an incident."""
    return await coordinator.get_incident_audit(incident_id)
```

---

## WebSocket Handler

```python
# backend/api/websocket.py

from fastapi import WebSocket, WebSocketDisconnect
from typing import Set
import json
from datetime import datetime

# Active connections
connections: Set[WebSocket] = set()

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.add(websocket)
    
    try:
        # Send initial state
        from main import get_coordinator
        coordinator = get_coordinator()
        await websocket.send_json({
            "type": "initial_state",
            "payload": coordinator.graph.model_dump(),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle client messages
            if message["type"] == "human_decision":
                # Process decision
                pass
            elif message["type"] == "request_refresh":
                await websocket.send_json({
                    "type": "graph_update",
                    "payload": coordinator.graph.model_dump(),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        connections.remove(websocket)

async def broadcast(message_type: str, payload: dict):
    """Broadcast message to all connected clients."""
    message = {
        "type": message_type,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    disconnected = set()
    for ws in connections:
        try:
            await ws.send_json(message)
        except:
            disconnected.add(ws)
    
    # Clean up disconnected
    for ws in disconnected:
        connections.discard(ws)

# Message types to broadcast:
# - graph_update: Full graph state
# - new_incident: New incident added
# - incident_update: Incident modified
# - contradiction_alert: New contradiction detected
# - action_recommendation: New action recommended
# - resource_update: Resource status changed
# - decision_made: Human made a decision
```

---

## Coordinator (Orchestration)

```python
# backend/orchestrator/coordinator.py

import google.generativeai as genai
from typing import Optional
import asyncio
from datetime import datetime

from config import get_settings
from graph.schemas import SituationGraph, IncidentNode, ResourceNode
from agents.vision_agent import VisionAgent
from agents.audio_agent import AudioAgent
from agents.text_agent import TextAgent
from agents.verification_agent import VerificationAgent
from agents.planning_agent import PlanningAgent
from agents.temporal_agent import TemporalAgent
from api.websocket import broadcast

class Coordinator:
    def __init__(self):
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        
        # Initialize agents
        self.vision_agent = VisionAgent(self.client)
        self.audio_agent = AudioAgent(self.client)
        self.text_agent = TextAgent(self.client)
        self.verification_agent = VerificationAgent(self.client)
        self.planning_agent = PlanningAgent(self.client)
        self.temporal_agent = TemporalAgent(self.client)
        
        # Initialize empty graph
        self.graph = SituationGraph(
            scenario_id="",
            scenario_start_time=datetime.utcnow(),
            current_sim_time=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        # Simulation state
        self.simulation_running = False
        self.simulation_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Called on startup."""
        pass
    
    async def shutdown(self):
        """Called on shutdown."""
        if self.simulation_task:
            self.simulation_task.cancel()
    
    async def process_signal(self, signal_type: str, content: str, metadata: dict):
        """Route signal to appropriate agent and update graph."""
        
        # Select agent
        if signal_type == "image":
            agent_output = await self.vision_agent.process({
                "content": content,
                "metadata": metadata
            })
        elif signal_type == "audio":
            agent_output = await self.audio_agent.process({
                "content": content,
                "metadata": metadata
            })
        elif signal_type == "text":
            agent_output = await self.text_agent.process({
                "content": content,
                "metadata": metadata
            })
        else:
            raise ValueError(f"Unknown signal type: {signal_type}")
        
        # Update graph based on agent output
        await self._update_graph_from_output(agent_output)
        
        # Check for contradictions
        await self._check_contradictions(agent_output)
        
        # Trigger planning if needed
        await self._maybe_generate_recommendations()
        
        # Broadcast update
        await broadcast("graph_update", self.graph.model_dump())
        
        return agent_output
    
    async def _update_graph_from_output(self, output):
        """Update situation graph based on agent output."""
        # Implementation depends on output type
        pass
    
    async def _check_contradictions(self, new_output):
        """Check if new output contradicts existing data."""
        # Find related entities
        # Call verification agent
        # If contradiction, add to graph.contradictions
        pass
    
    async def _maybe_generate_recommendations(self):
        """Generate action recommendations if needed."""
        # Check if there are unaddressed high-priority incidents
        # Call planning agent
        # Add recommendations to graph.pending_actions
        pass
    
    async def resolve_contradiction(self, alert_id: str, decision):
        """Handle human resolution of contradiction."""
        alert = self.graph.contradictions[alert_id]
        alert.resolved = True
        alert.resolution = decision.decision
        alert.resolved_by = decision.decided_by
        alert.resolved_at = datetime.utcnow()
        
        # Update graph based on resolution
        await broadcast("decision_made", {
            "type": "contradiction",
            "id": alert_id,
            "decision": decision.decision
        })
        
        return alert
    
    async def approve_action(self, action_id: str):
        """Execute approved action."""
        action = self.graph.pending_actions[action_id]
        action.status = "approved"
        action.decided_at = datetime.utcnow()
        
        # Update resources
        for resource_id in action.resources_to_allocate:
            if resource_id in self.graph.resources:
                resource = self.graph.resources[resource_id]
                resource.status = "dispatched"
                resource.assigned_incident = action.target_incident_id
        
        await broadcast("decision_made", {
            "type": "action",
            "id": action_id,
            "decision": "approved"
        })
        
        return action
    
    async def reject_action(self, action_id: str, reason: Optional[str] = None):
        """Reject action recommendation."""
        action = self.graph.pending_actions[action_id]
        action.status = "rejected"
        action.decided_at = datetime.utcnow()
        
        await broadcast("decision_made", {
            "type": "action",
            "id": action_id,
            "decision": "rejected",
            "reason": reason
        })
        
        return action
    
    # ============== SIMULATION ==============
    
    async def start_simulation(self, scenario_id: str, speed: float = 1.0):
        """Start demo simulation."""
        from orchestrator.simulation import run_simulation
        self.simulation_running = True
        self.simulation_task = asyncio.create_task(
            run_simulation(self, scenario_id, speed)
        )
    
    async def pause_simulation(self):
        self.simulation_running = False
    
    async def resume_simulation(self):
        self.simulation_running = True
    
    async def reset_simulation(self):
        self.simulation_running = False
        if self.simulation_task:
            self.simulation_task.cancel()
        # Reset graph to initial state
        self.graph = SituationGraph(
            scenario_id="",
            scenario_start_time=datetime.utcnow(),
            current_sim_time=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        await broadcast("graph_update", self.graph.model_dump())
    
    def get_simulation_status(self):
        return {
            "running": self.simulation_running,
            "scenario_id": self.graph.scenario_id,
            "current_time": self.graph.current_sim_time.isoformat(),
            "elapsed_seconds": (
                self.graph.current_sim_time - self.graph.scenario_start_time
            ).total_seconds()
        }
```

---

## Quick Start

```bash
# 1. Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 4. Run server
uvicorn main:app --reload --port 8000

# 5. Test
curl http://localhost:8000/api/graph
```
