import { SituationGraph } from '../../types';
import { StatusBadge } from '../shared/StatusBadge';
import { Truck, Flame, Users, Wind } from 'lucide-react';

interface ResourcePanelProps {
  resources: SituationGraph['resources'];
  locations: SituationGraph['locations'];
}

function getResourceIcon(type: string) {
  const cls = 'w-3.5 h-3.5';
  if (type.includes('ambulance')) return <Truck className={`${cls} text-red-400`} />;
  if (type.includes('fire') || type.includes('engine') || type.includes('ladder')) return <Flame className={`${cls} text-orange-400`} />;
  if (type.includes('helicopter') || type.includes('heli')) return <Wind className={`${cls} text-purple-400`} />;
  return <Users className={`${cls} text-blue-400`} />;
}

export function ResourcePanel({ resources, locations }: ResourcePanelProps) {
  const resourceList = Object.values(resources);

  const byType: Record<string, typeof resourceList> = {};
  resourceList.forEach(r => {
    const type = r.resource_type;
    if (!byType[type]) byType[type] = [];
    byType[type].push(r);
  });

  const hospitals = Object.values(locations).filter(l => l.location_type === 'hospital');

  return (
    <div className="overflow-y-auto h-full space-y-3">
      {/* Hospital Status */}
      {hospitals.length > 0 && (
        <div>
          <div className="text-xs uppercase tracking-widest text-zinc-500 mb-2 px-1">Hospitals</div>
          <div className="space-y-1.5">
            {hospitals.map(h => {
              const used = h.capacity_used ?? 0;
              const total = h.capacity_total ?? 100;
              const pct = Math.round((used / total) * 100);
              const color = pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-amber-500' : 'bg-green-500';

              return (
                <div key={h.id} className="bg-[#12121a] rounded p-2">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-zinc-300 truncate">{h.location?.name || h.id}</span>
                    <span className="text-zinc-400 ml-2 font-mono">{used}/{total}</span>
                  </div>
                  <div className="h-1.5 bg-[#27272a] rounded-full overflow-hidden">
                    <div
                      className={`h-full ${color} transition-all duration-500`}
                      style={{ width: `${Math.min(100, pct)}%` }}
                    />
                  </div>
                  <div className="text-xs text-zinc-500 mt-0.5">{pct}% capacity</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Resources by type */}
      {Object.entries(byType).map(([type, items]) => (
        <div key={type}>
          <div className="flex items-center gap-2 text-xs uppercase tracking-widest text-zinc-500 mb-2 px-1">
            {getResourceIcon(type)}
            <span>{type.replace(/_/g, ' ')}s</span>
            <span className="ml-auto text-zinc-600 font-mono">
              {items.filter(r => r.status === 'available').length}/{items.length}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-1">
            {items.map(r => (
              <div
                key={r.id}
                className={`rounded p-1.5 text-xs ${
                  r.status === 'available' ? 'bg-[#12121a]' :
                  r.status === 'dispatched' ? 'bg-blue-500/10 border border-blue-500/20' :
                  r.status === 'on_scene' ? 'bg-purple-500/10 border border-purple-500/20' :
                  'bg-[#12121a] opacity-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-zinc-200">{r.unit_id}</span>
                  {r.eta_minutes && r.status === 'dispatched' && (
                    <span className="text-blue-400 font-mono">{r.eta_minutes}m</span>
                  )}
                </div>
                <div className="text-zinc-500 mt-0.5 capitalize">{r.status.replace('_', ' ')}</div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {resourceList.length === 0 && (
        <div className="text-zinc-600 text-sm text-center py-4">
          No resources loaded
        </div>
      )}
    </div>
  );
}
