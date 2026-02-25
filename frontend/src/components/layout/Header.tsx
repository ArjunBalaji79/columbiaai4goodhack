import { Activity, Wifi, WifiOff, Play, Pause, RotateCcw, Radio, LayoutDashboard, MessageSquare, Swords, Package, Mic } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useSituationGraph } from '../../hooks/useSituationGraph';
import { format } from 'date-fns';

export function Header() {
  const { isConnected, graph, simStatus, startSimulation, pauseSimulation, resumeSimulation, resetSimulation } = useSituationGraph();

  const stats = graph ? {
    incidents: Object.keys(graph.incidents).length,
    active: Object.values(graph.incidents).filter(i => i.status === 'active').length,
    resources: Object.values(graph.resources).filter(r => r.status === 'dispatched').length,
    pending: Object.values(graph.contradictions).filter(c => !c.resolved).length +
             Object.values(graph.pending_actions).filter(a => a.status === 'pending').length,
    contradictions: Object.values(graph.contradictions).filter(c => !c.resolved).length,
  } : { incidents: 0, active: 0, resources: 0, pending: 0, contradictions: 0 };

  const simTime = graph?.current_sim_time
    ? format(new Date(graph.current_sim_time), 'HH:mm:ss')
    : '--:--:--';

  return (
    <header className="bg-[#0a0a0f] border-b border-[#27272a] px-4 py-2 flex items-center justify-between flex-shrink-0">
      {/* Logo + Nav */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-red-400" />
          <span className="text-white font-bold text-lg tracking-tight">CrisisCore</span>
        </div>

        {/* Nav tabs */}
        <nav className="flex items-center gap-1">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                isActive
                  ? 'bg-zinc-700/80 text-zinc-100'
                  : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'
              }`
            }
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            Dashboard
          </NavLink>

          <NavLink
            to="/debate"
            className={({ isActive }) =>
              `flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors relative ${
                isActive
                  ? 'bg-zinc-700/80 text-zinc-100'
                  : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'
              }`
            }
          >
            <Swords className="w-3.5 h-3.5" />
            Debate Room
            {stats.contradictions > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-amber-500 text-[10px] font-bold text-black flex items-center justify-center">
                {stats.contradictions}
              </span>
            )}
          </NavLink>

          <NavLink
            to="/resources"
            className={({ isActive }) =>
              `flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                isActive
                  ? 'bg-zinc-700/80 text-zinc-100'
                  : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'
              }`
            }
          >
            <Package className="w-3.5 h-3.5" />
            Resources
          </NavLink>

          <NavLink
            to="/voice"
            className={({ isActive }) =>
              `flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                isActive
                  ? 'bg-zinc-700/80 text-zinc-100'
                  : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'
              }`
            }
          >
            <Mic className="w-3.5 h-3.5" />
            Voice
          </NavLink>

          <NavLink
            to="/copilot"
            className={({ isActive }) =>
              `flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                isActive
                  ? 'bg-zinc-700/80 text-zinc-100'
                  : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'
              }`
            }
          >
            <MessageSquare className="w-3.5 h-3.5" />
            Co-Pilot
          </NavLink>
        </nav>

        {simStatus?.running && (
          <span className="flex items-center gap-1.5 text-xs text-red-400 bg-red-500/10 border border-red-500/20 px-2 py-0.5 rounded">
            <Radio className="w-3 h-3" />
            LIVE
          </span>
        )}
      </div>

      {/* Stats */}
      <div className="flex items-center gap-6">
        <Stat label="Incidents" value={stats.incidents} color="text-zinc-300" />
        <Stat label="Active" value={stats.active} color="text-red-400" highlight={stats.active > 0} />
        <Stat label="Deployed" value={stats.resources} color="text-blue-400" />
        <Stat label="Pending" value={stats.pending} color="text-amber-400" highlight={stats.pending > 0} />
      </div>

      {/* Sim Controls + Time */}
      <div className="flex items-center gap-3">
        {/* Sim Time */}
        <div className="font-mono text-sm bg-[#1a1a25] px-3 py-1 rounded border border-[#27272a]">
          <span className="text-zinc-500 mr-1">T</span>
          <span className="text-zinc-200">{simTime}</span>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-1">
          {!simStatus?.running ? (
            <button
              onClick={() => startSimulation('scenario_hackathon_demo', 1.0)}
              className="p-1.5 rounded bg-green-500/20 hover:bg-green-500/30 text-green-400 transition-colors"
              title="Start Simulation"
            >
              <Play className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={pauseSimulation}
              className="p-1.5 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 transition-colors"
              title="Pause"
            >
              <Pause className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={resetSimulation}
            className="p-1.5 rounded bg-zinc-700/50 hover:bg-zinc-700 text-zinc-400 transition-colors"
            title="Reset"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>

        {/* Connection status */}
        <div className="flex items-center gap-1.5">
          {isConnected ? (
            <Wifi className="w-4 h-4 text-green-400" />
          ) : (
            <WifiOff className="w-4 h-4 text-red-400" />
          )}
          <span className={`text-xs ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
            {isConnected ? 'Connected' : 'Offline'}
          </span>
        </div>
      </div>
    </header>
  );
}

function Stat({ label, value, color, highlight }: {
  label: string; value: number; color: string; highlight?: boolean;
}) {
  return (
    <div className="text-center">
      <div className={`text-xl font-bold font-mono ${color} ${highlight ? 'pulse-critical' : ''}`}>
        {value}
      </div>
      <div className="text-xs text-zinc-500 uppercase tracking-wide">{label}</div>
    </div>
  );
}
