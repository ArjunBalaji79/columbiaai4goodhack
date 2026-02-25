import { AlertTriangle, Clock, Satellite, Mic, FileText, Eye, Swords } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ContradictionAlert } from '../../types';
import { ConfidenceBadge } from '../shared/ConfidenceBadge';
import { UrgencyBadge } from '../shared/UrgencyBadge';
import { useSituationGraph } from '../../hooks/useSituationGraph';

interface ContradictionCardProps {
  alert: ContradictionAlert;
}

function getSourceIcon(sourceType?: string) {
  const iconClass = 'w-3.5 h-3.5';
  switch (sourceType) {
    case 'satellite': return <Satellite className={iconClass} />;
    case 'first_responder': return <Mic className={iconClass} />;
    case 'civilian': return <Mic className={iconClass} />;
    case 'social_media': return <FileText className={iconClass} />;
    case 'official_report': return <FileText className={iconClass} />;
    default: return <Eye className={iconClass} />;
  }
}

export function ContradictionCard({ alert }: ContradictionCardProps) {
  const { resolveContradiction } = useSituationGraph();

  return (
    <div className="bg-[#1a1a25] border border-red-500/30 rounded-lg p-4 slide-in flash-alert">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400 pulse-critical" />
          <span className="font-semibold text-red-400 text-sm uppercase tracking-wide">
            CONTRADICTION DETECTED
          </span>
        </div>
        <UrgencyBadge urgency={alert.urgency} animate />
      </div>

      {/* Entity name */}
      <div className="text-white font-semibold text-base mb-3">
        {alert.entity_name}
      </div>

      {/* Conflicting Claims */}
      <div className="space-y-2 mb-3">
        {alert.claims.map((claim, i) => (
          <div key={i} className="bg-[#12121a] rounded-md p-2.5">
            <div className="flex items-center gap-1.5 text-zinc-400 text-xs mb-1.5">
              {getSourceIcon(claim.source_type)}
              <span className="font-mono">{claim.source}</span>
              <span className="ml-auto text-zinc-500">{claim.timestamp}</span>
            </div>
            <div className="text-zinc-200 text-sm leading-relaxed">
              "{claim.claim}"
            </div>
            <div className="mt-1.5">
              <ConfidenceBadge value={claim.confidence} />
            </div>
          </div>
        ))}
      </div>

      {/* Temporal Analysis */}
      {alert.temporal_analysis && (
        <div className="flex items-start gap-2 text-zinc-400 text-xs mb-3 p-2 bg-[#12121a] rounded">
          <Clock className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-amber-400" />
          <span>{alert.temporal_analysis}</span>
        </div>
      )}

      {/* Verdict */}
      <div className="text-xs text-zinc-500 mb-3">
        <span className="text-amber-400 font-medium">Recommended:</span>{' '}
        {alert.recommended_action_details}
      </div>

      {/* Action buttons */}
      <div className="flex gap-2">
        {alert.claims.length >= 2 && (
          <>
            <button
              onClick={() => resolveContradiction(alert.id, 'accept_first')}
              className="flex-1 px-2 py-1.5 bg-zinc-700/50 hover:bg-zinc-700 rounded text-xs text-zinc-300 transition-colors truncate"
              title={`Accept: ${alert.claims[0]?.claim}`}
            >
              Accept #1
            </button>
            <button
              onClick={() => resolveContradiction(alert.id, 'accept_second')}
              className="flex-1 px-2 py-1.5 bg-zinc-700/50 hover:bg-zinc-700 rounded text-xs text-zinc-300 transition-colors truncate"
              title={`Accept: ${alert.claims[1]?.claim}`}
            >
              Accept #2
            </button>
          </>
        )}
        <button
          onClick={() => resolveContradiction(alert.id, 'request_verification')}
          className="flex-1 px-2 py-1.5 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded text-xs font-medium transition-colors"
        >
          Verify
        </button>
      </div>

      {/* Debate Room link */}
      <Link
        to={`/debate/${alert.id}`}
        className="mt-2 flex items-center justify-center gap-1.5 w-full px-2 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 text-amber-400 rounded text-xs font-medium transition-colors"
      >
        <Swords className="w-3 h-3" />
        Watch Agents Debate →
      </Link>
    </div>
  );
}
