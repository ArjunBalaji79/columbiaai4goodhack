import { useState } from 'react';
import { Package, Cpu, MapPin, CheckCircle, XCircle, Loader2, Tent, Truck, AlertTriangle } from 'lucide-react';
import { useSituationGraph } from '../hooks/useSituationGraph';
import { AllocationPlan, CampRecommendation, ResourceNode } from '../types';

const TYPE_COLORS: Record<string, string> = {
  ambulance: 'text-green-400',
  ambulances: 'text-green-400',
  fire_engine: 'text-orange-400',
  fire_truck: 'text-orange-400',
  ladder_truck: 'text-orange-400',
  search_and_rescue: 'text-blue-400',
  helicopter: 'text-purple-400',
};

const STATUS_COLORS: Record<string, string> = {
  available: 'bg-green-500/20 text-green-400 border-green-500/30',
  dispatched: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  on_scene: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  returning: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30',
  offline: 'bg-red-500/20 text-red-400 border-red-500/30',
};

const CAMP_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  relief_camp: { label: 'Relief Camp', color: 'text-green-400' },
  rescue_staging: { label: 'Rescue Staging', color: 'text-blue-400' },
  medical_triage: { label: 'Medical Triage', color: 'text-red-400' },
};

function ResourceTable({ resources }: { resources: ResourceNode[] }) {
  const [filter, setFilter] = useState<string>('all');
  const filtered = filter === 'all' ? resources : resources.filter(r => r.status === filter);

  return (
    <div>
      <div className="flex gap-1 mb-3">
        {['all', 'available', 'dispatched', 'on_scene'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-2 py-1 rounded text-xs transition-colors ${
              filter === f ? 'bg-zinc-600 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800'
            }`}
          >
            {f === 'all' ? 'All' : f.replace('_', ' ')}
          </button>
        ))}
      </div>
      <div className="overflow-auto max-h-[400px]">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-zinc-500 border-b border-[#27272a]">
              <th className="text-left py-2 px-2">Unit</th>
              <th className="text-left py-2 px-2">Type</th>
              <th className="text-left py-2 px-2">Status</th>
              <th className="text-left py-2 px-2">Sector</th>
              <th className="text-left py-2 px-2">Assigned To</th>
              <th className="text-left py-2 px-2">ETA</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(r => (
              <tr key={r.id} className="border-b border-[#27272a]/50 hover:bg-[#22222f]">
                <td className="py-2 px-2 font-mono text-zinc-200">{r.unit_id}</td>
                <td className={`py-2 px-2 ${TYPE_COLORS[r.resource_type] || 'text-zinc-400'}`}>
                  {r.resource_type}
                </td>
                <td className="py-2 px-2">
                  <span className={`px-1.5 py-0.5 rounded text-[10px] border ${STATUS_COLORS[r.status] || ''}`}>
                    {r.status}
                  </span>
                </td>
                <td className="py-2 px-2 text-zinc-400">{r.current_location.sector || '—'}</td>
                <td className="py-2 px-2 text-zinc-400 font-mono">{r.assigned_incident || '—'}</td>
                <td className="py-2 px-2 text-zinc-400">{r.eta_minutes ? `${r.eta_minutes}m` : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="text-center text-zinc-600 py-6 text-xs">No resources match filter</div>
        )}
      </div>
    </div>
  );
}

function PlanCard({ plan, onApprove }: { plan: AllocationPlan; onApprove: () => void }) {
  return (
    <div className="border border-[#27272a] rounded-lg bg-[#1a1a25] p-4 slide-in">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-semibold text-zinc-200">AI Allocation Plan</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <div className="w-12 h-1.5 rounded-full bg-zinc-700 overflow-hidden">
              <div
                className={`h-full rounded-full ${plan.overall_confidence >= 0.7 ? 'bg-green-400' : 'bg-amber-400'}`}
                style={{ width: `${plan.overall_confidence * 100}%` }}
              />
            </div>
            <span className="text-xs text-zinc-400 font-mono">{(plan.overall_confidence * 100).toFixed(0)}%</span>
          </div>
          <span className={`text-[10px] px-1.5 py-0.5 rounded border ${
            plan.status === 'active' ? 'bg-green-500/20 text-green-400 border-green-500/30'
            : 'bg-zinc-700/50 text-zinc-400 border-zinc-600'
          }`}>
            {plan.status}
          </span>
        </div>
      </div>

      {plan.resource_assignments.length > 0 && (
        <div className="mb-3">
          <p className="text-xs text-zinc-500 mb-1.5">Resource Assignments:</p>
          {plan.resource_assignments.map((a, i) => (
            <div key={i} className="flex items-center gap-2 text-xs py-1 border-b border-[#27272a]/50 last:border-0">
              <Truck className="w-3 h-3 text-blue-400 flex-shrink-0" />
              <span className="text-zinc-200 font-mono">{a.resource_id}</span>
              <span className="text-zinc-600">→</span>
              <span className="text-zinc-400 font-mono">{a.target_incident_id}</span>
              <span className="text-zinc-600 flex-1 truncate">— {a.rationale}</span>
            </div>
          ))}
        </div>
      )}

      {plan.key_assumptions.length > 0 && (
        <div className="mb-3">
          <p className="text-xs text-zinc-500 mb-1">Assumptions:</p>
          <div className="flex flex-wrap gap-1">
            {plan.key_assumptions.map((a, i) => (
              <span key={i} className="text-[10px] text-zinc-500 bg-zinc-800 px-1.5 py-0.5 rounded">{a}</span>
            ))}
          </div>
        </div>
      )}

      {plan.status === 'draft' && (
        <button
          onClick={onApprove}
          className="w-full flex items-center justify-center gap-2 py-2 bg-green-500/20 hover:bg-green-500/30 border border-green-500/40 text-green-300 rounded-lg text-xs font-medium transition-colors"
        >
          <CheckCircle className="w-3.5 h-3.5" />
          Approve Plan
        </button>
      )}
    </div>
  );
}

function CampCard({ camp, onApprove, onReject }: {
  camp: CampRecommendation;
  onApprove: () => void;
  onReject: () => void;
}) {
  const typeInfo = CAMP_TYPE_LABELS[camp.camp_type] || { label: camp.camp_type, color: 'text-zinc-400' };

  return (
    <div className="border border-[#27272a] rounded-lg bg-[#1a1a25] p-4 slide-in">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Tent className="w-4 h-4 text-green-400" />
          <span className="text-sm font-semibold text-zinc-200">{camp.name}</span>
        </div>
        <span className={`text-[10px] ${typeInfo.color}`}>{typeInfo.label}</span>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-2 text-xs">
        <div>
          <span className="text-zinc-500">Capacity:</span>
          <span className="text-zinc-300 ml-1">{camp.capacity_persons} persons</span>
        </div>
        <div>
          <span className="text-zinc-500">Confidence:</span>
          <span className="text-zinc-300 ml-1">{(camp.confidence * 100).toFixed(0)}%</span>
        </div>
      </div>

      <p className="text-xs text-zinc-400 mb-2">{camp.rationale}</p>

      {Object.keys(camp.factors).length > 0 && (
        <div className="mb-3 space-y-0.5">
          {Object.entries(camp.factors).map(([key, val]) => (
            <div key={key} className="text-[10px] text-zinc-500">
              <span className="text-zinc-600">{key.replace(/_/g, ' ')}:</span> {val}
            </div>
          ))}
        </div>
      )}

      {camp.status === 'suggested' && (
        <div className="flex gap-2">
          <button
            onClick={onApprove}
            className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-green-500/20 hover:bg-green-500/30 border border-green-500/40 text-green-300 rounded text-xs transition-colors"
          >
            <CheckCircle className="w-3 h-3" /> Approve
          </button>
          <button
            onClick={onReject}
            className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-red-300 rounded text-xs transition-colors"
          >
            <XCircle className="w-3 h-3" /> Reject
          </button>
        </div>
      )}

      {camp.status === 'active' && (
        <div className="text-center text-green-400 text-xs py-1 bg-green-500/10 rounded">Active</div>
      )}
    </div>
  );
}

export function ResourcesPage() {
  const { graph } = useSituationGraph();
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);
  const [isGeneratingCamps, setIsGeneratingCamps] = useState(false);

  const resources = graph ? Object.values(graph.resources) : [];
  const plans = graph ? Object.values(graph.allocation_plans) : [];
  const camps = graph ? Object.values(graph.camp_locations) : [];

  const availableCount = resources.filter(r => r.status === 'available').length;
  const deployedCount = resources.filter(r => r.status === 'dispatched' || r.status === 'on_scene').length;

  async function handleGeneratePlan() {
    setIsGeneratingPlan(true);
    try {
      await fetch('/api/resources/generate-plan', { method: 'POST' });
    } catch (e) {
      console.error('Failed to generate plan:', e);
    } finally {
      setIsGeneratingPlan(false);
    }
  }

  async function handleGenerateCamps() {
    setIsGeneratingCamps(true);
    try {
      await fetch('/api/camps/generate', { method: 'POST' });
    } catch (e) {
      console.error('Failed to generate camps:', e);
    } finally {
      setIsGeneratingCamps(false);
    }
  }

  async function handleApprovePlan(planId: string) {
    try {
      await fetch(`/api/resources/plans/${planId}/approve`, { method: 'POST' });
    } catch (e) {
      console.error('Failed to approve plan:', e);
    }
  }

  async function handleApproveCamp(campId: string) {
    try {
      await fetch(`/api/camps/${campId}/approve`, { method: 'POST' });
    } catch (e) {
      console.error('Failed to approve camp:', e);
    }
  }

  async function handleRejectCamp(campId: string) {
    try {
      await fetch(`/api/camps/${campId}/reject`, { method: 'POST' });
    } catch (e) {
      console.error('Failed to reject camp:', e);
    }
  }

  return (
    <div className="flex flex-col h-full bg-[#0a0a0f] overflow-hidden">
      {/* Sub-header */}
      <div className="border-b border-[#27272a] px-6 py-3 flex items-center justify-between flex-shrink-0 bg-[#0d0d14]">
        <div className="flex items-center gap-3">
          <Package className="w-4 h-4 text-blue-400" />
          <span className="text-zinc-200 text-sm font-semibold">Resource Allocation</span>
          <div className="flex items-center gap-3 text-xs text-zinc-500 ml-2">
            <span className="text-green-400">{availableCount} available</span>
            <span className="text-blue-400">{deployedCount} deployed</span>
            <span>{resources.length} total</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleGeneratePlan}
            disabled={isGeneratingPlan || !graph}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/40 text-blue-300 rounded text-xs font-medium transition-colors disabled:opacity-40"
          >
            {isGeneratingPlan ? <Loader2 className="w-3 h-3 animate-spin" /> : <Cpu className="w-3 h-3" />}
            Generate AI Plan
          </button>
          <button
            onClick={handleGenerateCamps}
            disabled={isGeneratingCamps || !graph}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/20 hover:bg-green-500/30 border border-green-500/40 text-green-300 rounded text-xs font-medium transition-colors disabled:opacity-40"
          >
            {isGeneratingCamps ? <Loader2 className="w-3 h-3 animate-spin" /> : <MapPin className="w-3 h-3" />}
            Suggest Camp Locations
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-hidden grid grid-cols-2 gap-2 p-2">
        {/* Left: Resource Table */}
        <div className="bg-[#12121a] border border-[#27272a] rounded-lg p-4 overflow-auto">
          <h3 className="text-xs text-zinc-500 uppercase tracking-wider mb-3 flex items-center gap-2">
            <Truck className="w-3.5 h-3.5" />
            Resource Inventory
          </h3>
          {resources.length > 0 ? (
            <ResourceTable resources={resources} />
          ) : (
            <div className="flex flex-col items-center justify-center h-48 text-zinc-600 gap-2">
              <AlertTriangle className="w-8 h-8 opacity-30" />
              <p className="text-xs">No resources loaded. Start the simulation first.</p>
            </div>
          )}
        </div>

        {/* Right: AI Plans + Camps */}
        <div className="overflow-auto space-y-2">
          {/* AI Plans */}
          <div className="bg-[#12121a] border border-[#27272a] rounded-lg p-4">
            <h3 className="text-xs text-zinc-500 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Cpu className="w-3.5 h-3.5" />
              AI Allocation Plans
            </h3>
            {plans.length > 0 ? (
              <div className="space-y-3">
                {plans.map(plan => (
                  <PlanCard key={plan.id} plan={plan} onApprove={() => handleApprovePlan(plan.id)} />
                ))}
              </div>
            ) : (
              <div className="text-center text-zinc-600 py-6 text-xs">
                Click "Generate AI Plan" to get optimized resource assignments
              </div>
            )}
          </div>

          {/* Camp Recommendations */}
          <div className="bg-[#12121a] border border-[#27272a] rounded-lg p-4">
            <h3 className="text-xs text-zinc-500 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Tent className="w-3.5 h-3.5" />
              Camp Locations
              {camps.filter(c => c.status === 'active').length > 0 && (
                <span className="px-1.5 py-0.5 rounded-full bg-green-500/20 text-green-400 text-[10px] font-bold">
                  {camps.filter(c => c.status === 'active').length} active
                </span>
              )}
            </h3>
            {camps.length > 0 ? (
              <div className="space-y-3">
                {camps.map(camp => (
                  <CampCard
                    key={camp.id}
                    camp={camp}
                    onApprove={() => handleApproveCamp(camp.id)}
                    onReject={() => handleRejectCamp(camp.id)}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center text-zinc-600 py-6 text-xs">
                Click "Suggest Camp Locations" to get AI-recommended placements
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
