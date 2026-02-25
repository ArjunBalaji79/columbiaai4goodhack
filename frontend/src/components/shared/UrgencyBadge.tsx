interface UrgencyBadgeProps {
  urgency: 'critical' | 'high' | 'medium' | 'low';
  animate?: boolean;
}

export function UrgencyBadge({ urgency, animate = false }: UrgencyBadgeProps) {
  const styles = {
    critical: 'bg-red-500/20 text-red-400 border border-red-500/30',
    high: 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
    medium: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
    low: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
  };

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium uppercase tracking-wide ${styles[urgency]} ${animate && urgency === 'critical' ? 'pulse-critical' : ''}`}>
      {urgency}
    </span>
  );
}
