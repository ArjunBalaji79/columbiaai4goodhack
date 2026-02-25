import { useMemo } from 'react';
import { ContradictionAlert, ActionRecommendation, SituationGraph } from '../../types';
import { ContradictionCard } from './ContradictionCard';
import { ActionCard } from './ActionCard';
import { Inbox } from 'lucide-react';

interface DecisionQueueProps {
  contradictions: SituationGraph['contradictions'];
  actions: SituationGraph['pending_actions'];
}

const URGENCY_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3
};

export function DecisionQueue({ contradictions, actions }: DecisionQueueProps) {
  const sortedItems = useMemo(() => {
    const allItems: Array<{
      type: 'contradiction' | 'action';
      item: ContradictionAlert | ActionRecommendation;
      urgency: string;
    }> = [
      ...Object.values(contradictions)
        .filter(c => !c.resolved)
        .map(c => ({ type: 'contradiction' as const, item: c, urgency: c.urgency })),
      ...Object.values(actions)
        .filter(a => a.status === 'pending')
        .map(a => ({ type: 'action' as const, item: a, urgency: a.time_sensitivity })),
    ];

    return allItems.sort((a, b) =>
      (URGENCY_ORDER[a.urgency] ?? 4) - (URGENCY_ORDER[b.urgency] ?? 4)
    );
  }, [contradictions, actions]);

  if (sortedItems.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-32 text-zinc-600">
        <Inbox className="w-8 h-8 mb-2" />
        <span className="text-sm">No pending decisions</span>
      </div>
    );
  }

  return (
    <div className="space-y-3 overflow-y-auto h-full pr-1">
      {sortedItems.map(({ type, item }) =>
        type === 'contradiction' ? (
          <ContradictionCard key={item.id} alert={item as ContradictionAlert} />
        ) : (
          <ActionCard key={item.id} action={item as ActionRecommendation} />
        )
      )}
    </div>
  );
}
