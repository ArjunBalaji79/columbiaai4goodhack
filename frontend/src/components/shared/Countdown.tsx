import { useState, useEffect } from 'react';
import { formatDistanceToNow } from 'date-fns';

interface CountdownProps {
  deadline: string;
}

export function Countdown({ deadline }: CountdownProps) {
  const [timeLeft, setTimeLeft] = useState('');
  const [isExpired, setIsExpired] = useState(false);
  const [isUrgent, setIsUrgent] = useState(false);

  useEffect(() => {
    const update = () => {
      const deadlineDate = new Date(deadline);
      const now = new Date();
      const diffMs = deadlineDate.getTime() - now.getTime();

      if (diffMs <= 0) {
        setTimeLeft('EXPIRED');
        setIsExpired(true);
        return;
      }

      setIsExpired(false);
      setIsUrgent(diffMs < 120000); // 2 minutes

      const diffSec = Math.floor(diffMs / 1000);
      const minutes = Math.floor(diffSec / 60);
      const seconds = diffSec % 60;
      setTimeLeft(`${minutes}:${seconds.toString().padStart(2, '0')}`);
    };

    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [deadline]);

  return (
    <span className={`font-mono text-sm font-medium ${
      isExpired ? 'text-red-400' :
      isUrgent ? 'text-amber-400 pulse-critical' :
      'text-zinc-300'
    }`}>
      {timeLeft}
    </span>
  );
}
