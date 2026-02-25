import { Panel } from './Panel';
import { MapView } from '../map/MapView';
import { DecisionQueue } from '../decisions/DecisionQueue';
import { EvidenceFlow } from '../evidence/EvidenceFlow';
import { ResourcePanel } from '../resources/ResourcePanel';
import { SignalIntelligence } from '../signals/SignalIntelligence';
import { useSituationGraph } from '../../hooks/useSituationGraph';
import { Activity } from 'lucide-react';

export function Dashboard() {
  const { graph, isConnected } = useSituationGraph();

  const pendingCount = graph
    ? Object.values(graph.contradictions).filter(c => !c.resolved).length +
      Object.values(graph.pending_actions).filter(a => a.status === 'pending').length
    : 0;

  return (
    <div className="h-full flex flex-col bg-[#0a0a0f] text-[#e4e4e7] overflow-hidden">
      {!isConnected && (
        <div className="mx-2 mt-2 px-4 py-2 bg-red-500/10 border border-red-500/30 rounded text-red-400 text-sm flex items-center gap-2">
          <Activity className="w-4 h-4" />
          Connecting to CrisisCore backend... (start with: cd backend && uvicorn main:app --reload --port 8000)
        </div>
      )}

      {/* Main grid */}
      <div className="flex-1 overflow-hidden p-2 grid gap-2" style={{
        gridTemplateColumns: '1fr 1fr 320px',
        gridTemplateRows: '1fr 1fr',
      }}>
        {/* Map - spans 2 rows on left */}
        <Panel
          title="Situation Map"
          className="row-span-2"
          noPadding
          headerRight={
            graph && (
              <div className="flex items-center gap-3 text-xs text-zinc-500">
                <LegendItem color="#ef4444" label="Critical" />
                <LegendItem color="#f97316" label="High" />
                <LegendItem color="#f59e0b" label="Medium" />
                <LegendItem color="#22c55e" label="Resources" />
              </div>
            )
          }
        >
          <MapView graph={graph} />
        </Panel>

        {/* Signal Intelligence - top center */}
        <Panel title="Signal Intelligence — AI Analysis">
          <SignalIntelligence />
        </Panel>

        {/* Decision Queue - top right */}
        <Panel
          title="Decision Queue"
          headerRight={
            pendingCount > 0 ? (
              <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 text-xs font-bold">
                {pendingCount}
              </span>
            ) : null
          }
        >
          <DecisionQueue
            contradictions={graph?.contradictions ?? {}}
            actions={graph?.pending_actions ?? {}}
          />
        </Panel>

        {/* Evidence Flow - bottom center */}
        <Panel title="Evidence Flow" noPadding>
          <EvidenceFlow />
        </Panel>

        {/* Resources - bottom right */}
        <Panel title="Resources & Hospitals">
          <ResourcePanel
            resources={graph?.resources ?? {}}
            locations={graph?.locations ?? {}}
          />
        </Panel>
      </div>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1">
      <div className="w-2 h-2 rounded-full" style={{ background: color }} />
      <span>{label}</span>
    </div>
  );
}
