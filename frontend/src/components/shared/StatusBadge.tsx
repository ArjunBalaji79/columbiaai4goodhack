interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const styles: Record<string, string> = {
    active: 'bg-red-500/20 text-red-400',
    responding: 'bg-blue-500/20 text-blue-400',
    contained: 'bg-amber-500/20 text-amber-400',
    resolved: 'bg-green-500/20 text-green-400',
    available: 'bg-green-500/20 text-green-400',
    dispatched: 'bg-blue-500/20 text-blue-400',
    on_scene: 'bg-purple-500/20 text-purple-400',
    returning: 'bg-amber-500/20 text-amber-400',
    offline: 'bg-zinc-500/20 text-zinc-400',
    operational: 'bg-green-500/20 text-green-400',
    damaged: 'bg-amber-500/20 text-amber-400',
    destroyed: 'bg-red-500/20 text-red-400',
    pending: 'bg-amber-500/20 text-amber-400',
    approved: 'bg-green-500/20 text-green-400',
    rejected: 'bg-red-500/20 text-red-400',
  };

  const style = styles[status] || 'bg-zinc-500/20 text-zinc-400';

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium uppercase ${style}`}>
      {status.replace('_', ' ')}
    </span>
  );
}
