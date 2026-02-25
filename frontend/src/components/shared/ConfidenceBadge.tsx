interface ConfidenceBadgeProps {
  value: number;
  showLabel?: boolean;
  size?: 'sm' | 'md';
}

export function ConfidenceBadge({ value, showLabel = true, size = 'sm' }: ConfidenceBadgeProps) {
  const getColor = () => {
    if (value >= 0.7) return 'text-green-400 bg-green-400/10';
    if (value >= 0.4) return 'text-amber-400 bg-amber-400/10';
    return 'text-red-400 bg-red-400/10';
  };

  const textSize = size === 'sm' ? 'text-xs' : 'text-sm';

  return (
    <span className={`px-2 py-0.5 rounded font-mono ${textSize} ${getColor()}`}>
      {showLabel && 'Conf: '}{Math.round(value * 100)}%
    </span>
  );
}
