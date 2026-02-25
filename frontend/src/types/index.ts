export interface Location {
  lat: number;
  lng: number;
  address?: string;
  sector?: string;
  name?: string;
}

export interface SourceReference {
  source_id: string;
  source_type: 'image' | 'audio' | 'text' | 'document' | 'satellite';
  timestamp: string;
  raw_content_ref: string;
  credibility_score: number;
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
  injured_min?: number;
  injured_max?: number;
  confidence: number;
  sources: SourceReference[];
  created_at: string;
  updated_at: string;
  contradictions: string[];
  decay_rate: number;
  status: 'active' | 'responding' | 'contained' | 'resolved';
  assigned_resources: string[];
}

export interface ResourceNode {
  id: string;
  type: 'resource';
  resource_type: string;
  unit_id: string;
  current_location: Location;
  destination?: Location;
  status: 'available' | 'dispatched' | 'on_scene' | 'returning' | 'offline';
  assigned_incident?: string;
  personnel: number;
  capacity_remaining: number;
  eta_minutes?: number;
  updated_at: string;
}

export interface LocationNode {
  id: string;
  type: 'location';
  location: Location;
  location_type: string;
  capacity_total?: number;
  capacity_used?: number;
  status: 'operational' | 'damaged' | 'destroyed' | 'unknown';
  accessibility: 'accessible' | 'partially_blocked' | 'blocked' | 'hazardous' | 'unknown';
  confidence: number;
  updated_at: string;
}

export interface ContradictionAlert {
  id: string;
  entity_id: string;
  entity_type: string;
  entity_name: string;
  claims: Array<{
    source: string;
    source_type?: string;
    claim: string;
    confidence: number;
    timestamp: string;
  }>;
  verdict: 'consistent' | 'contradiction' | 'uncertain' | 'temporal_gap';
  severity: 'low' | 'medium' | 'high';
  temporal_analysis?: string;
  recommended_action: string;
  recommended_action_details: string;
  urgency: 'critical' | 'high' | 'medium' | 'low';
  created_at: string;
  resolved: boolean;
  resolution?: string;
  resolved_by?: string;
  resolved_at?: string;
}

export interface ActionRecommendation {
  id: string;
  action_type: string;
  target_incident_id?: string;
  target_location?: Location;
  target_sector?: string;
  resources_to_allocate: string[];
  rationale: string;
  supporting_factors: string[];
  confidence: number;
  tradeoffs: Array<{
    impact: string;
    affected_incidents: string[];
    affected_confidence?: number;
    worst_case: string;
  }>;
  uncertainty_factors: string[];
  requires_human_approval: boolean;
  decision_deadline: string;
  time_sensitivity: 'critical' | 'high' | 'medium' | 'low';
  status: 'pending' | 'approved' | 'rejected' | 'executed' | 'expired';
  created_at: string;
  decided_at?: string;
  decided_by?: string;
}

export interface GraphEdge {
  id: string;
  source_node_id: string;
  target_node_id: string;
  relationship: string;
  confidence: number;
  metadata: Record<string, unknown>;
}

export interface ResourceAssignment {
  id: string;
  resource_id: string;
  target_incident_id: string;
  rationale: string;
  priority: number;
  estimated_eta_minutes?: number;
  status: 'suggested' | 'approved' | 'rejected' | 'executed';
  created_at: string;
  decided_at?: string;
}

export interface CampRecommendation {
  id: string;
  name: string;
  location: Location;
  camp_type: 'relief_camp' | 'rescue_staging' | 'medical_triage';
  capacity_persons: number;
  rationale: string;
  confidence: number;
  factors: Record<string, string>;
  status: 'suggested' | 'approved' | 'rejected' | 'active';
  created_at: string;
  decided_at?: string;
}

export interface AllocationPlan {
  id: string;
  resource_assignments: ResourceAssignment[];
  camp_recommendations: CampRecommendation[];
  overall_confidence: number;
  key_assumptions: string[];
  created_at: string;
  status: 'draft' | 'active' | 'superseded';
}

export interface VoiceReport {
  id: string;
  transcript: string;
  camp_name?: string;
  caller_location?: string;
  population_count?: number;
  medical_emergencies: Array<Record<string, unknown>>;
  supplies_needed: string[];
  infrastructure_status?: string;
  signals_created: string[];
  created_at: string;
}

export interface SituationGraph {
  incidents: Record<string, IncidentNode>;
  resources: Record<string, ResourceNode>;
  locations: Record<string, LocationNode>;
  edges: Record<string, GraphEdge>;
  contradictions: Record<string, ContradictionAlert>;
  pending_actions: Record<string, ActionRecommendation>;
  allocation_plans: Record<string, AllocationPlan>;
  camp_locations: Record<string, CampRecommendation>;
  voice_reports: Record<string, VoiceReport>;
  scenario_id: string;
  scenario_name: string;
  scenario_start_time: string;
  current_sim_time: string;
  last_updated: string;
}

export interface WSMessage {
  type: string;
  payload: unknown;
  timestamp: string;
}

export interface TimelineEvent {
  id: string;
  type: string;
  timestamp: string;
  data: Record<string, unknown>;
}
