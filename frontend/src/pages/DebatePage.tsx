import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Swords, ArrowLeft, Play, CheckCircle, XCircle, Shield, Loader2, AlertTriangle } from 'lucide-react';
import { useSituationGraph } from '../hooks/useSituationGraph';
import { DebateTurn } from '../types/debate';

const ROLE_CONFIG = {
  defender: {
    label: 'Defender',
    color: 'text-blue-400',
    borderColor: 'border-blue-500/40',
    bgColor: 'bg-blue-500/5',
    headerBg: 'bg-blue-500/10',
    align: 'self-start',
    agentIcon: '🔵',
    side: 'left' as const,
  },
  challenger: {
    label: 'Challenger',
    color: 'text-red-400',
    borderColor: 'border-red-500/40',
    bgColor: 'bg-red-500/5',
    headerBg: 'bg-red-500/10',
    align: 'self-end',
    agentIcon: '🔴',
    side: 'right' as const,
  },
  rebuttal: {
    label: 'Rebuttal',
    color: 'text-blue-300',
    borderColor: 'border-blue-400/40',
    bgColor: 'bg-blue-400/5',
    headerBg: 'bg-blue-400/10',
    align: 'self-start',
    agentIcon: '🔵',
    side: 'left' as const,
  },
  synthesis: {
    label: 'Verdict',
    color: 'text-amber-400',
    borderColor: 'border-amber-500/50',
    bgColor: 'bg-amber-500/5',
    headerBg: 'bg-amber-500/10',
    align: 'self-center',
    agentIcon: '⚖️',
    side: 'center' as const,
  },
};

function TurnBubble({ turn, isNew }: { turn: DebateTurn; isNew: boolean }) {
  const cfg = ROLE_CONFIG[turn.role] || ROLE_CONFIG.defender;
  const isCenter = cfg.side === 'center';

  return (
    <div
      className={`w-full flex ${isCenter ? 'justify-center' : cfg.side === 'right' ? 'justify-end' : 'justify-start'} ${isNew ? 'slide-in' : ''}`}
    >
      <div
        className={`max-w-xl border ${cfg.borderColor} ${cfg.bgColor} rounded-xl overflow-hidden ${isCenter ? 'w-full' : 'w-4/5'}`}
      >
        {/* Header */}
        <div className={`${cfg.headerBg} px-4 py-2 flex items-center justify-between`}>
          <div className="flex items-center gap-2">
            <span className="text-base">{cfg.agentIcon}</span>
            <span className={`text-xs font-bold uppercase tracking-wider ${cfg.color}`}>
              {turn.agent_name}
            </span>
            <span className="text-zinc-600 text-xs">·</span>
            <span className="text-zinc-500 text-xs">{cfg.label}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-zinc-600 text-xs font-mono">Turn {turn.turn_number}/4</span>
            <div className="flex items-center gap-1">
              <div
                className="w-12 h-1 rounded-full bg-zinc-700 overflow-hidden"
                title={`Confidence: ${(turn.confidence * 100).toFixed(0)}%`}
              >
                <div
                  className={`h-full rounded-full ${turn.confidence >= 0.7 ? 'bg-green-400' : turn.confidence >= 0.5 ? 'bg-amber-400' : 'bg-red-400'}`}
                  style={{ width: `${turn.confidence * 100}%` }}
                />
              </div>
              <span className="text-zinc-400 text-xs font-mono">{(turn.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>

        {/* Argument */}
        <div className="px-4 py-3">
          <p className={`text-sm leading-relaxed ${turn.role === 'synthesis' ? 'text-amber-100' : 'text-zinc-200'}`}>
            {turn.argument}
          </p>
        </div>
      </div>
    </div>
  );
}

function ClaimBox({ label, source, claim, confidence, color }: {
  label: string; source: string; claim: string; confidence: number; color: string;
}) {
  return (
    <div className={`flex-1 border ${color} rounded-lg p-3 bg-[#1a1a25]`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">{label}</span>
        <span className="text-xs text-zinc-500 font-mono">{(confidence * 100).toFixed(0)}% conf.</span>
      </div>
      <div className="text-xs text-zinc-500 mb-1">{source}</div>
      <div className="text-sm text-zinc-200 italic">"{claim}"</div>
    </div>
  );
}

export function DebatePage() {
  const { alertId } = useParams<{ alertId: string }>();
  const navigate = useNavigate();
  const { graph, debateTurns, clearDebate, resolveContradiction } = useSituationGraph();
  const [isRunning, setIsRunning] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newTurnIdx, setNewTurnIdx] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Determine which alert we're debating
  const allContradictions = graph?.contradictions ?? {};
  const unresolved = Object.values(allContradictions).filter(c => !c.resolved);

  // Use alertId from URL, or fall back to first unresolved
  const effectiveAlertId = alertId && alertId !== 'latest'
    ? alertId
    : unresolved[0]?.id ?? null;

  const alert = effectiveAlertId ? allContradictions[effectiveAlertId] : null;
  const turns = effectiveAlertId ? (debateTurns[effectiveAlertId] ?? []) : [];
  const claims = alert?.claims ?? [];

  // Watch for new turns completing
  useEffect(() => {
    if (turns.length > 0) {
      const lastTurn = turns[turns.length - 1];
      setNewTurnIdx(lastTurn.turn_number);
      if (lastTurn.done || lastTurn.turn_number >= 4) {
        setIsDone(true);
        setIsRunning(false);
      }
    }
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns.length]);

  async function startDebate() {
    if (!effectiveAlertId) return;
    clearDebate(effectiveAlertId);
    setIsRunning(true);
    setIsDone(false);
    setError(null);

    try {
      const res = await fetch(`/api/debate/${effectiveAlertId}/start`, { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      // Turns arrive via WebSocket; the response confirms completion
    } catch (e) {
      setError('Failed to start debate. Check backend connection.');
      setIsRunning(false);
    }
  }

  function handleDecision(decision: string) {
    if (!effectiveAlertId) return;
    resolveContradiction(effectiveAlertId, decision);
    navigate('/');
  }

  // No contradictions in graph yet
  if (!graph) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-zinc-500 gap-3">
        <Swords className="w-12 h-12 opacity-30" />
        <p className="text-sm">Connecting to situation graph…</p>
        <Link to="/" className="text-xs text-zinc-600 hover:text-zinc-400 underline">← Back to Dashboard</Link>
      </div>
    );
  }

  if (!alert && !effectiveAlertId) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-zinc-500 gap-4">
        <AlertTriangle className="w-12 h-12 opacity-30 text-amber-500" />
        <p className="text-sm">No active contradictions to debate.</p>
        <p className="text-xs text-zinc-600">Run the simulation until a contradiction is detected.</p>
        <Link to="/" className="text-xs text-zinc-600 hover:text-zinc-400 flex items-center gap-1">
          <ArrowLeft className="w-3 h-3" /> Back to Dashboard
        </Link>
      </div>
    );
  }

  if (!alert) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-zinc-500 gap-3">
        <p className="text-sm">Contradiction not found.</p>
        <Link to="/debate" className="text-xs text-zinc-600 hover:text-zinc-400 underline">
          View available contradictions
        </Link>
      </div>
    );
  }

  const claimA = claims[0] ?? {};
  const claimB = claims[1] ?? {};

  return (
    <div className="flex flex-col h-full bg-[#0a0a0f] overflow-hidden">
      {/* Sub-header */}
      <div className="border-b border-[#27272a] px-6 py-3 flex items-center justify-between flex-shrink-0 bg-[#0d0d14]">
        <div className="flex items-center gap-3">
          <Link to="/" className="text-zinc-600 hover:text-zinc-400 transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <Swords className="w-4 h-4 text-amber-400" />
          <div>
            <span className="text-zinc-200 text-sm font-semibold">Debate Room</span>
            <span className="text-zinc-500 text-xs ml-2">— {alert.entity_name}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500 bg-red-500/10 border border-red-500/20 px-2 py-0.5 rounded text-red-400">
            {alert.verdict?.toUpperCase() ?? 'CONTRADICTION'}
          </span>
          <span className="text-xs text-zinc-600">Urgency: {alert.urgency}</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-6 py-6 space-y-6">

          {/* Claim comparison */}
          <div className="flex gap-3">
            <ClaimBox
              label="Claim A"
              source={String(claimA.source ?? 'Source A')}
              claim={String(claimA.claim ?? 'No claim text')}
              confidence={Number(claimA.confidence ?? 0.5)}
              color="border-blue-500/30"
            />
            <ClaimBox
              label="Claim B"
              source={String(claimB.source ?? 'Source B')}
              claim={String(claimB.claim ?? 'No claim text')}
              confidence={Number(claimB.confidence ?? 0.5)}
              color="border-red-500/30"
            />
          </div>

          {/* Temporal context */}
          {alert.temporal_analysis && (
            <div className="text-xs text-zinc-500 bg-[#1a1a25] border border-[#27272a] rounded-lg px-4 py-2 flex items-start gap-2">
              <span className="text-amber-500 mt-0.5">⏱</span>
              <span>{alert.temporal_analysis}</span>
            </div>
          )}

          {/* Start button */}
          {turns.length === 0 && !isRunning && (
            <div className="flex flex-col items-center gap-3 py-6">
              <p className="text-zinc-500 text-sm text-center">
                Two AI agents will argue both sides. Watch them reason through the evidence.
              </p>
              <button
                onClick={startDebate}
                className="flex items-center gap-2 px-6 py-3 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 rounded-lg font-medium transition-colors"
              >
                <Play className="w-4 h-4" />
                Start Debate
              </button>
            </div>
          )}

          {/* Running indicator */}
          {isRunning && turns.length < 4 && (
            <div className="flex items-center gap-2 text-zinc-500 text-xs pl-2">
              <Loader2 className="w-3 h-3 animate-spin" />
              <span>Agent processing turn {turns.length + 1} of 4…</span>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded px-3 py-2">
              {error}
            </div>
          )}

          {/* Debate turns */}
          <div className="space-y-4">
            {turns.map((turn) => (
              <TurnBubble
                key={turn.turn_number}
                turn={turn}
                isNew={turn.turn_number === newTurnIdx}
              />
            ))}
          </div>

          {/* Decision buttons — shown after synthesis */}
          {isDone && (
            <div className="border border-[#27272a] rounded-xl bg-[#0d0d14] p-5 flex flex-col items-center gap-4">
              <div className="flex items-center gap-2 text-zinc-300">
                <Shield className="w-4 h-4 text-amber-400" />
                <span className="text-sm font-semibold">Human Decision Required</span>
              </div>
              <p className="text-xs text-zinc-500 text-center">
                You've heard both sides. Make the call.
              </p>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handleDecision('accept_claim_a')}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/40 text-blue-300 rounded-lg text-sm font-medium transition-colors"
                >
                  <CheckCircle className="w-4 h-4" />
                  Accept Claim A
                </button>
                <button
                  onClick={() => handleDecision('accept_claim_b')}
                  className="flex items-center gap-2 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-red-300 rounded-lg text-sm font-medium transition-colors"
                >
                  <CheckCircle className="w-4 h-4" />
                  Accept Claim B
                </button>
                <button
                  onClick={() => handleDecision('verify_required')}
                  className="flex items-center gap-2 px-4 py-2 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 rounded-lg text-sm font-medium transition-colors"
                >
                  <Shield className="w-4 h-4" />
                  Send Aerial Unit
                </button>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Contradiction list sidebar for navigation when no specific alertId */}
      {unresolved.length > 1 && (
        <div className="border-t border-[#27272a] px-6 py-2 flex items-center gap-3 flex-shrink-0">
          <span className="text-zinc-600 text-xs">Other contradictions:</span>
          {unresolved.filter(c => c.id !== effectiveAlertId).map(c => (
            <Link
              key={c.id}
              to={`/debate/${c.id}`}
              className="text-xs text-amber-400 hover:text-amber-300 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded transition-colors"
            >
              {c.entity_name}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
