import { useState } from 'react';
import { Truck, AlertTriangle, ChevronDown, CheckCircle, XCircle } from 'lucide-react';
import { ActionRecommendation } from '../../types';
import { ConfidenceBadge } from '../shared/ConfidenceBadge';
import { UrgencyBadge } from '../shared/UrgencyBadge';
import { Countdown } from '../shared/Countdown';
import { useSituationGraph } from '../../hooks/useSituationGraph';

interface ActionCardProps {
  action: ActionRecommendation;
}

export function ActionCard({ action }: ActionCardProps) {
  const [expanded, setExpanded] = useState(true); // Auto-expand tradeoffs
  const { approveAction, rejectAction } = useSituationGraph();

  if (action.status !== 'pending') {
    return (
      <div className="bg-[#1a1a25] border border-[#27272a] rounded-lg p-3 opacity-60">
        <div className="flex items-center gap-2 text-zinc-400 text-sm">
          {action.status === 'approved' ? (
            <CheckCircle className="w-4 h-4 text-green-400" />
          ) : (
            <XCircle className="w-4 h-4 text-red-400" />
          )}
          <span className="uppercase text-xs font-medium">
            {action.action_type.replace(/_/g, ' ')} — {action.status}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#1a1a25] border border-[#27272a] rounded-lg p-4 slide-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Truck className="w-4 h-4 text-blue-400" />
          <span className="font-semibold text-zinc-100 text-sm uppercase tracking-wide">
            {action.action_type.replace(/_/g, ' ')}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <ConfidenceBadge value={action.confidence} />
          <UrgencyBadge urgency={action.time_sensitivity} animate={action.time_sensitivity === 'critical'} />
        </div>
      </div>

      {/* Target */}
      {(action.target_sector || action.target_incident_id) && (
        <div className="text-sm mb-2">
          <span className="text-zinc-500">Target: </span>
          <span className="text-zinc-200 font-medium">
            {action.target_sector || action.target_incident_id}
          </span>
        </div>
      )}

      {/* Resources */}
      {action.resources_to_allocate.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {action.resources_to_allocate.map(r => (
            <span key={r} className="px-2 py-0.5 bg-blue-500/10 border border-blue-500/20 rounded text-xs font-mono text-blue-300">
              {r}
            </span>
          ))}
        </div>
      )}

      {/* Rationale */}
      <div className="text-zinc-400 text-xs leading-relaxed mb-3">
        {action.rationale}
      </div>

      {/* Tradeoffs - THE KEY FEATURE */}
      {action.tradeoffs.length > 0 && (
        <div className="mb-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1.5 text-amber-400 text-xs font-medium hover:text-amber-300 transition-colors w-full text-left"
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            {action.tradeoffs.length} Tradeoff{action.tradeoffs.length > 1 ? 's' : ''}
            <ChevronDown className={`w-3.5 h-3.5 ml-auto transition-transform ${expanded ? 'rotate-180' : ''}`} />
          </button>

          {expanded && (
            <div className="mt-2 space-y-2">
              {action.tradeoffs.map((t, i) => (
                <div key={i} className="p-2.5 bg-amber-500/5 border border-amber-500/20 rounded text-xs">
                  <div className="font-medium text-amber-400 mb-1">{t.impact}</div>
                  <div className="text-zinc-400">{t.worst_case}</div>
                  {t.affected_confidence !== undefined && (
                    <div className="mt-1 text-zinc-500">
                      Affected incident confidence: {Math.round(t.affected_confidence * 100)}%
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Deadline */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-zinc-500 text-xs">Decision deadline:</span>
        <Countdown deadline={action.decision_deadline} />
      </div>

      {/* Action Buttons - Clean approve/disapprove only */}
      <div className="flex gap-2">
        <button
          onClick={() => approveAction(action.id)}
          className="flex-1 px-4 py-2.5 bg-green-500/20 hover:bg-green-500/30 text-green-400 font-semibold rounded text-sm transition-colors border border-green-500/30"
        >
          ✓ Approve
        </button>
        <button
          onClick={() => rejectAction(action.id)}
          className="flex-1 px-4 py-2.5 bg-red-500/20 hover:bg-red-500/30 text-red-400 font-semibold rounded text-sm transition-colors border border-red-500/30"
        >
          ✗ Reject
        </button>
      </div>
    </div>
  );
}
