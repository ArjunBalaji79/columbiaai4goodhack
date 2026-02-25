import { Camera, Mic, FileText, Brain } from 'lucide-react';
import { ConfidenceBadge } from '../shared/ConfidenceBadge';
import { UrgencyBadge } from '../shared/UrgencyBadge';
import { useSituationGraph } from '../../hooks/useSituationGraph';

export interface ProcessedSignal {
  signal_id: string;
  signal_type: 'image' | 'audio' | 'text';
  agent_name: string;
  output_type: string;
  data: Record<string, unknown>;
  confidence: number;
  reasoning: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

function SignalIcon({ type }: { type: string }) {
  const cls = 'w-4 h-4';
  if (type === 'image') return <Camera className={`${cls} text-blue-400`} />;
  if (type === 'audio') return <Mic className={`${cls} text-purple-400`} />;
  return <FileText className={`${cls} text-green-400`} />;
}

function getAssetUrl(metadata?: Record<string, unknown>): string | null {
  const assetFile = metadata?.asset_file as string;
  if (!assetFile) return null;
  return `/assets/${assetFile}`;
}

function SignalCard({ signal }: { signal: ProcessedSignal }) {
  const { data, signal_type, agent_name, confidence, metadata } = signal;
  const assetUrl = getAssetUrl(metadata);

  // Color per signal type
  const borderColor = signal_type === 'image' ? 'border-blue-500/30' :
                      signal_type === 'audio' ? 'border-purple-500/30' :
                      'border-green-500/30';
  const headerBg = signal_type === 'image' ? 'bg-blue-500/10' :
                   signal_type === 'audio' ? 'bg-purple-500/10' :
                   'bg-green-500/10';
  const agentColor = signal_type === 'image' ? 'text-blue-400' :
                     signal_type === 'audio' ? 'text-purple-400' :
                     'text-green-400';

  return (
    <div className={`bg-[#1a1a25] border ${borderColor} rounded-lg overflow-hidden mb-3`}>
      {/* Header */}
      <div className={`${headerBg} px-3 py-2 flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <SignalIcon type={signal_type} />
          <span className={`text-xs font-bold uppercase tracking-wider ${agentColor}`}>
            {signal_type} signal
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-zinc-500 text-xs font-mono">{agent_name}</span>
          <ConfidenceBadge value={confidence} />
        </div>
      </div>

      {/* Actual image thumbnail for image signals */}
      {signal_type === 'image' && assetUrl && (
        <div className="relative">
          <img
            src={assetUrl}
            alt="Signal imagery"
            className="w-full h-32 object-cover"
          />
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-[#1a1a25] to-transparent h-8" />
        </div>
      )}

      {/* Audio player for audio signals */}
      {signal_type === 'audio' && assetUrl && (
        <div className="px-3 pt-2">
          <audio controls className="w-full h-8 opacity-80" style={{ filter: 'invert(1) hue-rotate(180deg)' }}>
            <source src={assetUrl} type="audio/mpeg" />
          </audio>
        </div>
      )}

      {/* Content based on signal type */}
      <div className="p-3">
        {signal_type === 'image' && <ImageSignalContent data={data} />}
        {signal_type === 'audio' && <AudioSignalContent data={data} />}
        {signal_type === 'text' && <TextSignalContent data={data} />}
      </div>
    </div>
  );
}

function ImageSignalContent({ data }: { data: Record<string, unknown> }) {
  const damageColors: Record<string, string> = {
    catastrophic: 'text-red-400',
    severe: 'text-orange-400',
    moderate: 'text-amber-400',
    minor: 'text-yellow-400',
    none: 'text-green-400',
  };
  const damageLevel = data.damage_level as string || 'unknown';
  const damageTypes = data.damage_types as string[] || [];
  const casualties = data.estimated_casualties as { min?: number; max?: number } || {};
  const hazards = data.hazards as string[] || [];
  const accessibility = data.accessibility as string || '';

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-zinc-400 text-xs">Damage Level</span>
        <span className={`font-bold text-sm uppercase ${damageColors[damageLevel] || 'text-zinc-300'}`}>
          {damageLevel}
        </span>
      </div>
      {damageTypes.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {damageTypes.map((t: string) => (
            <span key={t} className="text-xs px-2 py-0.5 bg-red-500/10 text-red-300 rounded">
              {t.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      )}
      {(casualties.min !== undefined) && (
        <div className="flex items-center justify-between text-xs">
          <span className="text-zinc-400">Casualties est.</span>
          <span className="text-amber-400 font-mono">{casualties.min}–{casualties.max}</span>
        </div>
      )}
      {hazards.length > 0 && (
        <div className="text-xs text-zinc-500 truncate">
          ⚠ {hazards.slice(0, 2).join(' · ')}
        </div>
      )}
      {accessibility && (
        <div className="flex items-center justify-between text-xs">
          <span className="text-zinc-400">Access</span>
          <span className={accessibility === 'accessible' ? 'text-green-400' : 'text-red-400'}>
            {accessibility.replace(/_/g, ' ')}
          </span>
        </div>
      )}
    </div>
  );
}

function AudioSignalContent({ data }: { data: Record<string, unknown> }) {
  const transcript = data.transcript as string || '';
  const speakerType = data.speaker_type as string || '';
  const emotionalState = data.emotional_state as string || '';
  const urgency = data.urgency as string || '';
  const persons = data.persons_involved as Record<string, unknown> || {};
  const trapped = persons.trapped as Record<string, number> | null;

  return (
    <div className="space-y-2">
      {transcript && (
        <div className="text-zinc-300 text-xs italic bg-[#12121a] p-2 rounded leading-relaxed">
          "{transcript.slice(0, 120)}{transcript.length > 120 ? '...' : ''}"
        </div>
      )}
      <div className="grid grid-cols-2 gap-2">
        {speakerType && (
          <div className="text-xs">
            <span className="text-zinc-500">Speaker</span>
            <div className="text-purple-300 capitalize mt-0.5">{speakerType.replace(/_/g, ' ')}</div>
          </div>
        )}
        {urgency && (
          <div className="text-xs">
            <span className="text-zinc-500">Urgency</span>
            <div className="mt-0.5">
              <UrgencyBadge urgency={urgency as 'critical' | 'high' | 'medium' | 'low'} />
            </div>
          </div>
        )}
      </div>
      {trapped && (
        <div className="text-xs flex items-center justify-between">
          <span className="text-zinc-400">Trapped</span>
          <span className="text-amber-400 font-mono">{trapped.min}–{trapped.max} persons</span>
        </div>
      )}
      {emotionalState && (
        <div className="text-xs text-zinc-500">Emotional state: {emotionalState}</div>
      )}
    </div>
  );
}

function TextSignalContent({ data }: { data: Record<string, unknown> }) {
  const sourceType = data.source_type as string || '';
  const credibilityScore = data.credibility_score as number || 0;
  const claims = data.claims as Array<Record<string, unknown>> || [];
  const redFlags = data.red_flags as Record<string, unknown> || {};
  const exaggeration = redFlags.exaggeration_indicators as string[] || [];
  const rawText = data.raw_text as string || '';

  const sourceColors: Record<string, string> = {
    official_report: 'text-green-400',
    first_responder: 'text-blue-400',
    '911_transcript': 'text-blue-400',
    eyewitness: 'text-amber-400',
    social_media: 'text-red-400',
    unverified: 'text-red-400',
    utility_company: 'text-cyan-400',
  };

  return (
    <div className="space-y-2">
      {rawText && (
        <div className="text-zinc-300 text-xs bg-[#12121a] p-2 rounded leading-relaxed italic">
          "{rawText.slice(0, 100)}{rawText.length > 100 ? '...' : ''}"
        </div>
      )}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-zinc-500">Source</span>
          <div className={`mt-0.5 capitalize ${sourceColors[sourceType] || 'text-zinc-300'}`}>
            {sourceType.replace(/_/g, ' ')}
          </div>
        </div>
        <div>
          <span className="text-zinc-500">Credibility</span>
          <div className="mt-0.5">
            <ConfidenceBadge value={credibilityScore} showLabel={false} />
          </div>
        </div>
      </div>
      {claims.length > 0 && (
        <div className="text-xs">
          <span className="text-zinc-500">{claims.length} claim{claims.length > 1 ? 's' : ''} extracted:</span>
          {claims.slice(0, 2).map((claim, i) => (
            <div key={i} className="mt-1 flex items-start gap-1.5">
              <span className="text-zinc-600 mt-0.5">›</span>
              <span className="text-zinc-300">{(claim.claim as string || '').slice(0, 80)}</span>
            </div>
          ))}
        </div>
      )}
      {exaggeration.length > 0 && (
        <div className="text-xs text-amber-600 flex items-center gap-1">
          <span>⚠ Flags:</span>
          <span>{exaggeration.slice(0, 2).join(', ')}</span>
        </div>
      )}
    </div>
  );
}

export function SignalIntelligence() {
  const { processedSignals } = useSituationGraph();

  if (processedSignals.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-32 text-zinc-600">
        <Brain className="w-8 h-8 mb-2 opacity-50" />
        <span className="text-sm">Awaiting signals...</span>
        <span className="text-xs mt-1 opacity-50">Start simulation to see AI analysis</span>
      </div>
    );
  }

  return (
    <div className="overflow-y-auto h-full pr-1">
      {processedSignals.map((signal) => (
        <SignalCard key={signal.signal_id} signal={signal} />
      ))}
    </div>
  );
}
