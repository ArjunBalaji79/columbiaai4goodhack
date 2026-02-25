# Frontend Specifications

## Overview

React 18 + TypeScript + Tailwind + Vite dashboard for disaster response coordination.

---

## Design System

### Theme: Mission Control Noir

Dark mode optimized for EOC environments. High contrast, data-dense, minimal decoration.

### Colors

```css
/* frontend/src/index.css */

:root {
  /* Backgrounds */
  --bg-primary: #0a0a0f;
  --bg-secondary: #12121a;
  --bg-elevated: #1a1a25;
  --bg-hover: #22222f;
  
  /* Text */
  --text-primary: #e4e4e7;
  --text-secondary: #a1a1aa;
  --text-muted: #71717a;
  
  /* Status Colors */
  --critical: #ef4444;
  --critical-bg: rgba(239, 68, 68, 0.1);
  --warning: #f59e0b;
  --warning-bg: rgba(245, 158, 11, 0.1);
  --success: #22c55e;
  --success-bg: rgba(34, 197, 94, 0.1);
  --info: #3b82f6;
  --info-bg: rgba(59, 130, 246, 0.1);
  
  /* Confidence indicators */
  --confidence-high: #22c55e;
  --confidence-medium: #f59e0b;
  --confidence-low: #ef4444;
  
  /* Borders */
  --border: #27272a;
  --border-focus: #3b82f6;
}
```

### Typography

```css
/* Monospace for data */
.font-mono {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

/* Sans for UI */
.font-sans {
  font-family: 'Inter', system-ui, sans-serif;
}
```

---

## Component Structure

```
src/
├── components/
│   ├── layout/
│   │   ├── Dashboard.tsx      # Main layout grid
│   │   ├── Header.tsx         # Top bar with status
│   │   └── Panel.tsx          # Reusable panel wrapper
│   │
│   ├── map/
│   │   ├── MapView.tsx        # Leaflet container
│   │   ├── IncidentMarker.tsx # Custom marker for incidents
│   │   ├── ResourceMarker.tsx # Marker for resources
│   │   └── SectorOverlay.tsx  # Sector boundaries
│   │
│   ├── decisions/
│   │   ├── DecisionQueue.tsx  # List of pending decisions
│   │   ├── ActionCard.tsx     # Single action recommendation
│   │   ├── ContradictionCard.tsx # Contradiction alert
│   │   └── TradeoffDisplay.tsx   # Visualize tradeoffs
│   │
│   ├── evidence/
│   │   ├── EvidenceFlow.tsx   # React Flow graph
│   │   ├── SignalNode.tsx     # Node for raw signal
│   │   ├── AgentNode.tsx      # Node for agent processing
│   │   └── OutputNode.tsx     # Node for agent output
│   │
│   ├── resources/
│   │   ├── ResourcePanel.tsx  # Resource overview
│   │   ├── ResourceCard.tsx   # Single resource status
│   │   └── HospitalStatus.tsx # Hospital capacity bars
│   │
│   ├── timeline/
│   │   ├── EventTimeline.tsx  # Recent events list
│   │   └── EventCard.tsx      # Single event
│   │
│   └── shared/
│       ├── ConfidenceBadge.tsx  # Confidence indicator
│       ├── UrgencyBadge.tsx     # Urgency indicator
│       ├── StatusBadge.tsx      # Status indicator
│       └── Countdown.tsx        # Decision deadline timer
│
├── hooks/
│   ├── useWebSocket.ts        # WebSocket connection
│   ├── useSituationGraph.ts   # Graph state management
│   └── useSimulation.ts       # Demo playback control
│
└── types/
    └── index.ts               # All TypeScript types
```

---

## Key Components

### Dashboard.tsx

Main layout grid.

```tsx
// Rough structure
export function Dashboard() {
  const { graph, isConnected } = useSituationGraph();
  
  return (
    <div className="h-screen bg-bg-primary text-text-primary grid grid-cols-12 grid-rows-[auto_1fr_1fr] gap-2 p-2">
      
      {/* Header - full width */}
      <Header 
        className="col-span-12"
        scenarioName={graph.scenario_name}
        simTime={graph.current_sim_time}
        isConnected={isConnected}
      />
      
      {/* Map - left 8 cols, top row */}
      <Panel className="col-span-8 row-span-1">
        <MapView graph={graph} />
      </Panel>
      
      {/* Decision Queue - right 4 cols, top row */}
      <Panel className="col-span-4 row-span-1" title="Decision Queue">
        <DecisionQueue 
          contradictions={graph.contradictions}
          actions={graph.pending_actions}
        />
      </Panel>
      
      {/* Evidence Flow - left 8 cols, bottom row */}
      <Panel className="col-span-8 row-span-1" title="Evidence Flow">
        <EvidenceFlow />
      </Panel>
      
      {/* Resources - right 4 cols, bottom row */}
      <Panel className="col-span-4 row-span-1" title="Resources">
        <ResourcePanel resources={graph.resources} />
      </Panel>
      
    </div>
  );
}
```

### DecisionQueue.tsx

Shows pending contradictions and action recommendations.

```tsx
interface DecisionQueueProps {
  contradictions: Record<string, ContradictionAlert>;
  actions: Record<string, ActionRecommendation>;
}

export function DecisionQueue({ contradictions, actions }: DecisionQueueProps) {
  // Sort by urgency, then by deadline
  const sortedItems = useMemo(() => {
    const all = [
      ...Object.values(contradictions).filter(c => !c.resolved).map(c => ({
        type: 'contradiction' as const,
        item: c,
        urgency: c.urgency,
        deadline: null
      })),
      ...Object.values(actions).filter(a => a.status === 'pending').map(a => ({
        type: 'action' as const,
        item: a,
        urgency: a.time_sensitivity,
        deadline: a.decision_deadline
      }))
    ];
    
    return all.sort((a, b) => {
      const urgencyOrder = { critical: 0, high: 1, medium: 2, low: 3 };
      return urgencyOrder[a.urgency] - urgencyOrder[b.urgency];
    });
  }, [contradictions, actions]);
  
  return (
    <div className="space-y-3 overflow-y-auto">
      {sortedItems.length === 0 ? (
        <div className="text-text-muted text-center py-8">
          No pending decisions
        </div>
      ) : (
        sortedItems.map(({ type, item }) => (
          type === 'contradiction' 
            ? <ContradictionCard key={item.id} alert={item} />
            : <ActionCard key={item.id} action={item} />
        ))
      )}
    </div>
  );
}
```

### ContradictionCard.tsx

Displays cross-modal contradiction with resolution options.

```tsx
interface ContradictionCardProps {
  alert: ContradictionAlert;
}

export function ContradictionCard({ alert }: ContradictionCardProps) {
  const { resolveContradiction } = useSituationGraph();
  
  return (
    <div className="bg-bg-elevated border border-critical/30 rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-critical" />
          <span className="font-medium">CONTRADICTION</span>
        </div>
        <UrgencyBadge urgency={alert.urgency} />
      </div>
      
      {/* Entity */}
      <div className="text-lg font-semibold mb-3">{alert.entity_name}</div>
      
      {/* Conflicting Claims */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        {alert.claims.map((claim, i) => (
          <div key={i} className="bg-bg-secondary p-3 rounded">
            <div className="flex items-center gap-2 text-text-secondary text-sm mb-1">
              {getSourceIcon(claim.source)}
              <span>{claim.source}</span>
            </div>
            <div className="font-medium">{claim.claim}</div>
            <div className="flex items-center gap-2 mt-1">
              <ConfidenceBadge value={claim.confidence} />
              <span className="text-text-muted text-xs">{claim.timestamp}</span>
            </div>
          </div>
        ))}
      </div>
      
      {/* Temporal Analysis */}
      {alert.temporal_analysis && (
        <div className="text-text-secondary text-sm mb-3 p-2 bg-bg-secondary rounded">
          <Clock className="w-4 h-4 inline mr-1" />
          {alert.temporal_analysis}
        </div>
      )}
      
      {/* Actions */}
      <div className="flex gap-2">
        <button 
          onClick={() => resolveContradiction(alert.id, 'accept_first')}
          className="flex-1 px-3 py-2 bg-bg-secondary hover:bg-bg-hover rounded text-sm"
        >
          Accept: {alert.claims[0].claim}
        </button>
        <button 
          onClick={() => resolveContradiction(alert.id, 'accept_second')}
          className="flex-1 px-3 py-2 bg-bg-secondary hover:bg-bg-hover rounded text-sm"
        >
          Accept: {alert.claims[1].claim}
        </button>
        <button 
          onClick={() => resolveContradiction(alert.id, 'request_verification')}
          className="px-3 py-2 bg-info/20 hover:bg-info/30 text-info rounded text-sm"
        >
          Verify
        </button>
      </div>
    </div>
  );
}
```

### ActionCard.tsx

Resource allocation recommendation with tradeoffs.

```tsx
interface ActionCardProps {
  action: ActionRecommendation;
}

export function ActionCard({ action }: ActionCardProps) {
  const { approveAction, rejectAction } = useSituationGraph();
  const [expanded, setExpanded] = useState(false);
  
  return (
    <div className="bg-bg-elevated border border-border rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Truck className="w-5 h-5 text-info" />
          <span className="font-medium uppercase">{action.action_type.replace('_', ' ')}</span>
        </div>
        <div className="flex items-center gap-2">
          <ConfidenceBadge value={action.confidence} />
          <UrgencyBadge urgency={action.time_sensitivity} />
        </div>
      </div>
      
      {/* Target */}
      <div className="mb-3">
        <span className="text-text-secondary">Target: </span>
        <span className="font-semibold">{action.target_sector || action.target_incident_id}</span>
      </div>
      
      {/* Resources */}
      <div className="flex flex-wrap gap-2 mb-3">
        {action.resources_to_allocate.map(r => (
          <span key={r} className="px-2 py-1 bg-bg-secondary rounded text-sm font-mono">
            {r}
          </span>
        ))}
      </div>
      
      {/* Rationale */}
      <div className="text-text-secondary text-sm mb-3">
        {action.rationale}
      </div>
      
      {/* Tradeoffs - THE KEY FEATURE */}
      {action.tradeoffs.length > 0 && (
        <div className="mb-3">
          <button 
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-warning text-sm font-medium"
          >
            <AlertTriangle className="w-4 h-4" />
            {action.tradeoffs.length} Tradeoff{action.tradeoffs.length > 1 ? 's' : ''}
            <ChevronDown className={`w-4 h-4 transition-transform ${expanded ? 'rotate-180' : ''}`} />
          </button>
          
          {expanded && (
            <div className="mt-2 space-y-2">
              {action.tradeoffs.map((t, i) => (
                <div key={i} className="p-2 bg-warning-bg border border-warning/20 rounded text-sm">
                  <div className="font-medium text-warning">{t.impact}</div>
                  <div className="text-text-secondary mt-1">{t.worst_case}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      
      {/* Deadline */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-text-muted text-sm">Decision deadline:</span>
        <Countdown deadline={action.decision_deadline} />
      </div>
      
      {/* Actions */}
      <div className="flex gap-2">
        <button 
          onClick={() => approveAction(action.id)}
          className="flex-1 px-4 py-2 bg-success/20 hover:bg-success/30 text-success font-medium rounded"
        >
          ✓ Approve
        </button>
        <button 
          onClick={() => rejectAction(action.id)}
          className="flex-1 px-4 py-2 bg-critical/20 hover:bg-critical/30 text-critical font-medium rounded"
        >
          ✗ Reject
        </button>
        <button 
          onClick={() => {/* Open details modal */}}
          className="px-4 py-2 bg-bg-secondary hover:bg-bg-hover rounded"
        >
          Details
        </button>
      </div>
    </div>
  );
}
```

### ConfidenceBadge.tsx

Visual confidence indicator.

```tsx
interface ConfidenceBadgeProps {
  value: number; // 0-1
  showLabel?: boolean;
}

export function ConfidenceBadge({ value, showLabel = true }: ConfidenceBadgeProps) {
  const getColor = () => {
    if (value >= 0.7) return 'text-confidence-high bg-confidence-high/10';
    if (value >= 0.4) return 'text-confidence-medium bg-confidence-medium/10';
    return 'text-confidence-low bg-confidence-low/10';
  };
  
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-mono ${getColor()}`}>
      {showLabel && 'Conf: '}{Math.round(value * 100)}%
    </span>
  );
}
```

---

## Hooks

### useWebSocket.ts

```tsx
import { useEffect, useRef, useState, useCallback } from 'react';

interface UseWebSocketOptions {
  url: string;
  onMessage: (message: any) => void;
  reconnectInterval?: number;
}

export function useWebSocket({ url, onMessage, reconnectInterval = 3000 }: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  
  const connect = useCallback(() => {
    const ws = new WebSocket(url);
    
    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected, reconnecting...');
      reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      onMessage(message);
    };
    
    wsRef.current = ws;
  }, [url, onMessage, reconnectInterval]);
  
  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);
  
  const send = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);
  
  return { isConnected, send };
}
```

### useSituationGraph.ts

```tsx
import { create } from 'zustand';
import { SituationGraph, ContradictionAlert, ActionRecommendation } from '../types';

interface SituationGraphState {
  graph: SituationGraph | null;
  isConnected: boolean;
  
  // Actions
  setGraph: (graph: SituationGraph) => void;
  updateGraph: (partial: Partial<SituationGraph>) => void;
  setConnected: (connected: boolean) => void;
  
  // Decision actions (these send to backend)
  resolveContradiction: (id: string, resolution: string) => void;
  approveAction: (id: string) => void;
  rejectAction: (id: string) => void;
}

export const useSituationGraph = create<SituationGraphState>((set, get) => ({
  graph: null,
  isConnected: false,
  
  setGraph: (graph) => set({ graph }),
  
  updateGraph: (partial) => set((state) => ({
    graph: state.graph ? { ...state.graph, ...partial } : null
  })),
  
  setConnected: (connected) => set({ isConnected: connected }),
  
  resolveContradiction: async (id, resolution) => {
    // Send to backend via WebSocket or REST
    // Backend will update graph and broadcast
  },
  
  approveAction: async (id) => {
    // Send approval to backend
  },
  
  rejectAction: async (id) => {
    // Send rejection to backend
  },
}));
```

---

## Map Configuration

```tsx
// frontend/src/components/map/MapView.tsx

import { MapContainer, TileLayer } from 'react-leaflet';

// Dark map tiles
const DARK_TILES = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';

// Metro City center (fictional)
const DEFAULT_CENTER: [number, number] = [37.78, -122.42];
const DEFAULT_ZOOM = 13;

export function MapView({ graph }) {
  return (
    <MapContainer
      center={DEFAULT_CENTER}
      zoom={DEFAULT_ZOOM}
      className="h-full w-full rounded"
      style={{ background: '#0a0a0f' }}
    >
      <TileLayer
        url={DARK_TILES}
        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
      />
      
      {/* Incident markers */}
      {Object.values(graph.incidents).map(incident => (
        <IncidentMarker key={incident.id} incident={incident} />
      ))}
      
      {/* Resource markers */}
      {Object.values(graph.resources).map(resource => (
        <ResourceMarker key={resource.id} resource={resource} />
      ))}
      
      {/* Sector boundaries */}
      <SectorOverlay />
    </MapContainer>
  );
}
```

---

## Package Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-leaflet": "^4.2.1",
    "leaflet": "^1.9.4",
    "reactflow": "^11.10.0",
    "zustand": "^4.4.0",
    "lucide-react": "^0.300.0",
    "date-fns": "^3.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/leaflet": "^1.9.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```
