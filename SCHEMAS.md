# Data Schemas

All Pydantic models for CrisisCore.

---

## Core Types

```python
# backend/graph/schemas.py

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime
from enum import Enum

# ============== ENUMS ==============

class DamageLevel(str, Enum):
    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CATASTROPHIC = "catastrophic"

class Urgency(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class SourceType(str, Enum):
    IMAGE = "image"
    AUDIO = "audio"
    TEXT = "text"
    DOCUMENT = "document"
    SATELLITE = "satellite"

class Verdict(str, Enum):
    CONSISTENT = "consistent"
    CONTRADICTION = "contradiction"
    UNCERTAIN = "uncertain"
    TEMPORAL_GAP = "temporal_gap"

class ActionType(str, Enum):
    ACCEPT = "accept"
    FLAG_FOR_HUMAN = "flag_for_human"
    REQUEST_VERIFICATION = "request_verification"
    WAIT = "wait"

# ============== LOCATION ==============

class Location(BaseModel):
    lat: float
    lng: float
    address: Optional[str] = None
    sector: Optional[str] = None
    name: Optional[str] = None

# ============== SOURCE REFERENCE ==============

class SourceReference(BaseModel):
    source_id: str
    source_type: SourceType
    timestamp: datetime
    raw_content_ref: str  # File path or text hash
    credibility_score: float = Field(ge=0.0, le=1.0)

# ============== SITUATION GRAPH NODES ==============

class IncidentNode(BaseModel):
    id: str
    type: Literal["incident"] = "incident"
    incident_type: str  # structural_collapse, fire, flood, etc.
    location: Location
    damage_level: DamageLevel
    urgency: Urgency
    
    # Casualty estimates
    trapped_min: Optional[int] = None
    trapped_max: Optional[int] = None
    injured_min: Optional[int] = None
    injured_max: Optional[int] = None
    
    # Metadata
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[SourceReference]
    created_at: datetime
    updated_at: datetime
    
    # Epistemic state
    contradictions: list[str] = []  # IDs of contradicting sources
    decay_rate: float = 0.01  # Confidence decay per minute
    
    # Status
    status: Literal["active", "responding", "contained", "resolved"] = "active"
    assigned_resources: list[str] = []

class ResourceNode(BaseModel):
    id: str
    type: Literal["resource"] = "resource"
    resource_type: str  # ambulance, fire_truck, helicopter, search_team
    unit_id: str  # AMB-7, HELI-2, etc.
    
    # Position
    current_location: Location
    destination: Optional[Location] = None
    
    # Status
    status: Literal["available", "dispatched", "on_scene", "returning", "offline"]
    assigned_incident: Optional[str] = None
    
    # Capacity
    personnel: int
    capacity_remaining: int  # For ambulances: patient slots
    
    # Timing
    eta_minutes: Optional[int] = None
    updated_at: datetime

class LocationNode(BaseModel):
    id: str
    type: Literal["location"] = "location"
    location: Location
    location_type: str  # hospital, shelter, bridge, building
    
    # For hospitals
    capacity_total: Optional[int] = None
    capacity_used: Optional[int] = None
    
    # For infrastructure
    status: Literal["operational", "damaged", "destroyed", "unknown"] = "unknown"
    accessibility: Literal["accessible", "partially_blocked", "blocked", "hazardous"] = "unknown"
    
    # Metadata
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    sources: list[SourceReference] = []
    updated_at: datetime

# ============== EDGES ==============

class GraphEdge(BaseModel):
    id: str
    source_node_id: str
    target_node_id: str
    relationship: Literal[
        "located_at",
        "assigned_to", 
        "blocks_access_to",
        "caused_by",
        "requires_resource",
        "evacuate_to"
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict = {}

# ============== AGENT OUTPUTS ==============

class AgentOutput(BaseModel):
    agent_name: str
    output_type: str
    data: dict
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[str]
    reasoning: str
    timestamp: datetime

class ContradictionAlert(BaseModel):
    id: str
    entity_id: str
    entity_type: str
    entity_name: str
    
    claims: list[dict]  # [{source, claim, confidence, timestamp}]
    
    verdict: Verdict
    severity: Literal["low", "medium", "high"]
    
    temporal_analysis: Optional[str] = None
    recommended_action: ActionType
    recommended_action_details: str
    
    urgency: Urgency
    created_at: datetime
    
    # Resolution
    resolved: bool = False
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None

class ActionRecommendation(BaseModel):
    id: str
    action_type: str  # dispatch_ambulances, evacuate, request_verification
    
    # Target
    target_incident_id: Optional[str] = None
    target_location: Optional[Location] = None
    target_sector: Optional[str] = None
    
    # Resources
    resources_to_allocate: list[str]  # Resource IDs
    
    # Reasoning
    rationale: str
    supporting_factors: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Tradeoffs - THE KEY DIFFERENTIATOR
    tradeoffs: list[dict]  # [{impact, affected_incidents, worst_case}]
    
    # Uncertainty
    uncertainty_factors: list[str]
    
    # Human-in-loop
    requires_human_approval: bool
    decision_deadline: datetime
    time_sensitivity: Urgency
    
    # Status
    status: Literal["pending", "approved", "rejected", "executed", "expired"] = "pending"
    created_at: datetime
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None

# ============== SITUATION GRAPH ==============

class SituationGraph(BaseModel):
    incidents: dict[str, IncidentNode] = {}
    resources: dict[str, ResourceNode] = {}
    locations: dict[str, LocationNode] = {}
    edges: dict[str, GraphEdge] = {}
    
    # Pending items
    contradictions: dict[str, ContradictionAlert] = {}
    pending_actions: dict[str, ActionRecommendation] = {}
    
    # Metadata
    scenario_id: str
    scenario_start_time: datetime
    current_sim_time: datetime
    last_updated: datetime

# ============== API MODELS ==============

class SignalInput(BaseModel):
    signal_type: SourceType
    content: str  # Base64 for images/audio, raw text for text
    metadata: dict = {}
    timestamp: Optional[datetime] = None

class DashboardState(BaseModel):
    graph: SituationGraph
    stats: dict  # {total_incidents, active_incidents, resources_deployed, etc.}
    recent_events: list[dict]  # Last N events for timeline

class HumanDecision(BaseModel):
    item_type: Literal["contradiction", "action"]
    item_id: str
    decision: str  # approve, reject, override
    override_value: Optional[str] = None
    notes: Optional[str] = None
    decided_by: str = "operator"
```

---

## WebSocket Messages

```python
# backend/api/websocket.py messages

class WSMessageType(str, Enum):
    # Server → Client
    GRAPH_UPDATE = "graph_update"
    NEW_INCIDENT = "new_incident"
    CONTRADICTION_ALERT = "contradiction_alert"
    ACTION_RECOMMENDATION = "action_recommendation"
    RESOURCE_UPDATE = "resource_update"
    INCIDENT_RESOLVED = "incident_resolved"
    
    # Client → Server
    HUMAN_DECISION = "human_decision"
    REQUEST_REFRESH = "request_refresh"

class WSMessage(BaseModel):
    type: WSMessageType
    payload: dict
    timestamp: datetime
```

---

## Demo Scenario Schema

```python
# For demo_data/scenario_earthquake.json

class ScenarioEvent(BaseModel):
    time_offset_seconds: int  # Seconds from scenario start
    event_type: Literal[
        "signal",          # New signal arrives
        "signal_batch",    # Multiple signals at once
        "aftershock",      # Situation evolution
        "resource_change", # Resource status change
        "time_marker"      # Demo pacing marker
    ]
    data: dict

class DemoScenario(BaseModel):
    scenario_id: str
    scenario_name: str
    description: str
    
    # Setting
    city_name: str
    initial_event: dict  # {type: earthquake, magnitude: 6.8, etc.}
    
    # Timing
    start_time: datetime
    duration_minutes: int
    
    # Events timeline
    events: list[ScenarioEvent]
    
    # Initial resources
    initial_resources: list[ResourceNode]
    
    # Initial locations (hospitals, etc.)
    initial_locations: list[LocationNode]
```

---

## Frontend Types

```typescript
// frontend/src/types/index.ts

export interface Location {
  lat: number;
  lng: number;
  address?: string;
  sector?: string;
  name?: string;
}

export interface IncidentNode {
  id: string;
  type: 'incident';
  incident_type: string;
  location: Location;
  damage_level: 'none' | 'minor' | 'moderate' | 'severe' | 'catastrophic';
  urgency: 'critical' | 'high' | 'medium' | 'low';
  trapped_min?: number;
  trapped_max?: number;
  confidence: number;
  sources: SourceReference[];
  status: 'active' | 'responding' | 'contained' | 'resolved';
  contradictions: string[];
}

export interface ResourceNode {
  id: string;
  type: 'resource';
  resource_type: string;
  unit_id: string;
  current_location: Location;
  status: 'available' | 'dispatched' | 'on_scene' | 'returning' | 'offline';
  assigned_incident?: string;
  eta_minutes?: number;
}

export interface ContradictionAlert {
  id: string;
  entity_id: string;
  entity_name: string;
  claims: Array<{
    source: string;
    claim: string;
    confidence: number;
    timestamp: string;
  }>;
  verdict: 'consistent' | 'contradiction' | 'uncertain' | 'temporal_gap';
  severity: 'low' | 'medium' | 'high';
  recommended_action: string;
  urgency: 'critical' | 'high' | 'medium' | 'low';
  resolved: boolean;
}

export interface ActionRecommendation {
  id: string;
  action_type: string;
  target_sector?: string;
  resources_to_allocate: string[];
  rationale: string;
  confidence: number;
  tradeoffs: Array<{
    impact: string;
    affected_incidents: string[];
    worst_case: string;
  }>;
  requires_human_approval: boolean;
  decision_deadline: string;
  time_sensitivity: 'critical' | 'high' | 'medium' | 'low';
  status: 'pending' | 'approved' | 'rejected' | 'executed';
}

export interface SituationGraph {
  incidents: Record<string, IncidentNode>;
  resources: Record<string, ResourceNode>;
  locations: Record<string, LocationNode>;
  contradictions: Record<string, ContradictionAlert>;
  pending_actions: Record<string, ActionRecommendation>;
  current_sim_time: string;
}

export interface WSMessage {
  type: string;
  payload: any;
  timestamp: string;
}
```
