from pydantic import BaseModel, Field
from typing import Literal, Optional, Any
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
    raw_content_ref: str
    credibility_score: float = Field(ge=0.0, le=1.0)


# ============== SITUATION GRAPH NODES ==============

class IncidentNode(BaseModel):
    id: str
    type: Literal["incident"] = "incident"
    incident_type: str
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
    sources: list[SourceReference] = []
    created_at: datetime
    updated_at: datetime

    # Epistemic state
    contradictions: list[str] = []
    decay_rate: float = 0.01

    # Status
    status: Literal["active", "responding", "contained", "resolved"] = "active"
    assigned_resources: list[str] = []


class ResourceNode(BaseModel):
    id: str
    type: Literal["resource"] = "resource"
    resource_type: str
    unit_id: str

    # Position
    current_location: Location
    destination: Optional[Location] = None

    # Status
    status: Literal["available", "dispatched", "on_scene", "returning", "offline"]
    assigned_incident: Optional[str] = None

    # Capacity
    personnel: int = 2
    capacity_remaining: int = 2

    # Timing
    eta_minutes: Optional[int] = None
    updated_at: datetime


class LocationNode(BaseModel):
    id: str
    type: Literal["location"] = "location"
    location: Location
    location_type: str

    # For hospitals
    capacity_total: Optional[int] = None
    capacity_used: Optional[int] = None

    # For infrastructure
    status: Literal["operational", "damaged", "destroyed", "unknown"] = "unknown"
    accessibility: Literal["accessible", "partially_blocked", "blocked", "hazardous", "unknown"] = "unknown"

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

    claims: list[dict]

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
    action_type: str

    # Target
    target_incident_id: Optional[str] = None
    target_location: Optional[Location] = None
    target_sector: Optional[str] = None

    # Resources
    resources_to_allocate: list[str] = []

    # Reasoning
    rationale: str
    supporting_factors: list[str] = []
    confidence: float = Field(ge=0.0, le=1.0)

    # Tradeoffs - KEY DIFFERENTIATOR
    tradeoffs: list[dict] = []

    # Uncertainty
    uncertainty_factors: list[str] = []

    # Human-in-loop
    requires_human_approval: bool = True
    decision_deadline: datetime
    time_sensitivity: Urgency

    # Status
    status: Literal["pending", "approved", "rejected", "executed", "expired"] = "pending"
    created_at: datetime
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None


# ============== RESOURCE ALLOCATION ==============

class ResourceAssignment(BaseModel):
    id: str
    resource_id: str
    target_incident_id: str
    rationale: str
    priority: int = 1
    estimated_eta_minutes: Optional[int] = None
    status: Literal["suggested", "approved", "rejected", "executed"] = "suggested"
    created_at: datetime
    decided_at: Optional[datetime] = None


class CampRecommendation(BaseModel):
    id: str
    name: str
    location: Location
    camp_type: Literal["relief_camp", "rescue_staging", "medical_triage"]
    capacity_persons: int = 100
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    factors: dict = {}
    status: Literal["suggested", "approved", "rejected", "active"] = "suggested"
    created_at: datetime
    decided_at: Optional[datetime] = None


class AllocationPlan(BaseModel):
    id: str
    resource_assignments: list[ResourceAssignment] = []
    camp_recommendations: list[CampRecommendation] = []
    overall_confidence: float = Field(ge=0.0, le=1.0, default=0.7)
    key_assumptions: list[str] = []
    created_at: datetime
    status: Literal["draft", "active", "superseded"] = "draft"


# ============== VOICE DATA ==============

class VoiceReport(BaseModel):
    id: str
    transcript: str
    camp_name: Optional[str] = None
    caller_location: Optional[str] = None
    population_count: Optional[int] = None
    medical_emergencies: list[dict] = []
    supplies_needed: list[str] = []
    infrastructure_status: Optional[str] = None
    signals_created: list[str] = []
    created_at: datetime


# ============== SITUATION GRAPH ==============

class SituationGraph(BaseModel):
    incidents: dict[str, IncidentNode] = {}
    resources: dict[str, ResourceNode] = {}
    locations: dict[str, LocationNode] = {}
    edges: dict[str, GraphEdge] = {}

    # Pending items
    contradictions: dict[str, ContradictionAlert] = {}
    pending_actions: dict[str, ActionRecommendation] = {}

    # Resource allocation
    allocation_plans: dict[str, AllocationPlan] = {}
    camp_locations: dict[str, CampRecommendation] = {}

    # Voice reports
    voice_reports: dict[str, VoiceReport] = {}

    # Metadata
    scenario_id: str = ""
    scenario_name: str = ""
    scenario_start_time: datetime
    current_sim_time: datetime
    last_updated: datetime


# ============== DEBATE ==============

class DebateTurn(BaseModel):
    turn_number: int
    agent_name: str
    role: Literal["defender", "challenger", "rebuttal", "synthesis"]
    argument: str
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime


# ============== API MODELS ==============

class SignalInput(BaseModel):
    signal_type: SourceType
    content: str
    metadata: dict = {}
    timestamp: Optional[datetime] = None


class DashboardState(BaseModel):
    graph: SituationGraph
    stats: dict
    recent_events: list[dict]


class HumanDecision(BaseModel):
    item_type: Literal["contradiction", "action"]
    item_id: str
    decision: str
    override_value: Optional[str] = None
    notes: Optional[str] = None
    decided_by: str = "operator"


# ============== WEBSOCKET MESSAGES ==============

class WSMessageType(str, Enum):
    GRAPH_UPDATE = "graph_update"
    NEW_INCIDENT = "new_incident"
    CONTRADICTION_ALERT = "contradiction_alert"
    ACTION_RECOMMENDATION = "action_recommendation"
    RESOURCE_UPDATE = "resource_update"
    INCIDENT_RESOLVED = "incident_resolved"
    HUMAN_DECISION = "human_decision"
    REQUEST_REFRESH = "request_refresh"
    INITIAL_STATE = "initial_state"
    SIM_STATUS = "sim_status"
    TIMELINE_EVENT = "timeline_event"


class WSMessage(BaseModel):
    type: WSMessageType
    payload: Any
    timestamp: datetime


# ============== SCENARIO ==============

class ScenarioEvent(BaseModel):
    time_offset_seconds: int
    event_type: Literal["signal", "signal_batch", "aftershock", "resource_change", "time_marker"]
    data: dict


class DemoScenario(BaseModel):
    scenario_id: str
    scenario_name: str
    description: str
    city_name: str
    initial_event: dict
    start_time: datetime
    duration_minutes: int
    events: list[ScenarioEvent]
    initial_resources: list[dict] = []
    initial_locations: list[dict] = []
