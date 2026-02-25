import { useSituationGraph } from '../../hooks/useSituationGraph';
import { format } from 'date-fns';
import { AlertTriangle, Radio, Image, Mic, FileText, Zap, CheckCircle } from 'lucide-react';

function getEventIcon(type: string) {
  const cls = 'w-3.5 h-3.5 flex-shrink-0';
  if (type.includes('contradiction')) return <AlertTriangle className={`${cls} text-red-400`} />;
  if (type.includes('aftershock')) return <Zap className={`${cls} text-amber-400`} />;
  if (type === 'signal_image') return <Image className={`${cls} text-blue-400`} />;
  if (type === 'signal_audio') return <Mic className={`${cls} text-purple-400`} />;
  if (type === 'signal_text') return <FileText className={`${cls} text-zinc-400`} />;
  if (type.includes('approved') || type.includes('resolved')) return <CheckCircle className={`${cls} text-green-400`} />;
  if (type.includes('incident')) return <Radio className={`${cls} text-red-400`} />;
  return <Radio className={`${cls} text-zinc-500`} />;
}

function getEventLabel(event: { type: string; data: Record<string, unknown> }): string {
  const { type, data } = event;
  if (type === 'signal_image') return `Image signal: ${data.metadata ? 'camera feed' : 'uploaded'}`;
  if (type === 'signal_audio') return `Audio signal received`;
  if (type === 'signal_text') return `Text report: ${(data.metadata as Record<string, string>)?.source_type || 'unverified'}`;
  if (type === 'contradiction_detected') return `⚡ Contradiction: ${data.entity as string}`;
  if (type === 'contradiction_resolved') return `✓ Resolved: ${data.resolution as string}`;
  if (type === 'incident_added') return `New incident: ${data.type as string}`;
  if (type === 'action_recommended') return `Recommendation: ${(data.action_type as string)?.replace(/_/g, ' ')}`;
  if (type === 'action_approved') return `✓ Approved: ${data.resources ? `${(data.resources as string[]).length} resources` : ''}`;
  if (type === 'aftershock') return `AFTERSHOCK ${data.magnitude}M`;
  if (type === 'time_marker') return data.label as string || 'Event';
  return type.replace(/_/g, ' ');
}

export function EventTimeline() {
  const { timelineEvents } = useSituationGraph();

  if (timelineEvents.length === 0) {
    return (
      <div className="text-zinc-600 text-xs text-center py-4">
        Awaiting events...
      </div>
    );
  }

  return (
    <div className="overflow-y-auto h-full">
      <div className="space-y-0.5">
        {timelineEvents.slice(0, 30).map((event, idx) => (
          <div
            key={event.id || idx}
            className="flex items-center gap-2 py-1.5 px-2 rounded hover:bg-[#1a1a25] transition-colors group"
          >
            {getEventIcon(event.type)}
            <span className="text-xs text-zinc-300 flex-1 truncate">
              {getEventLabel(event)}
            </span>
            <span className="text-xs text-zinc-600 font-mono flex-shrink-0">
              {event.timestamp
                ? format(new Date(event.timestamp), 'HH:mm:ss')
                : ''}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
