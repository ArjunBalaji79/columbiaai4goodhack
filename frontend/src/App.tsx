import { useCallback, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Dashboard } from './components/layout/Dashboard';
import { Header } from './components/layout/Header';
import { DebatePage } from './pages/DebatePage';
import { CopilotPage } from './pages/CopilotPage';
import { ResourcesPage } from './pages/ResourcesPage';
import { VoicePage } from './pages/VoicePage';
import { useWebSocket } from './hooks/useWebSocket';
import { useSituationGraph } from './hooks/useSituationGraph';
import { SituationGraph, TimelineEvent, VoiceReport } from './types';
import { ProcessedSignal } from './components/signals/SignalIntelligence';
import { DebateTurn } from './types/debate';

const WS_URL = 'ws://localhost:8000/ws';

function AppContent() {
  const {
    setGraph,
    updateGraph,
    setConnected,
    setSimStatus,
    setWsRef,
    addTimelineEvent,
    addProcessedSignal,
    addDebateTurn,
    addVoiceReport,
    graph,
  } = useSituationGraph();

  const handleMessage = useCallback((message: unknown) => {
    const msg = message as { type: string; payload: unknown };

    switch (msg.type) {
      case 'initial_state':
      case 'graph_update':
        setGraph(msg.payload as SituationGraph);
        break;

      case 'new_incident':
        updateGraph({
          incidents: {
            ...(useSituationGraph.getState().graph?.incidents ?? {}),
            [(msg.payload as { id: string }).id]: msg.payload as SituationGraph['incidents'][string]
          }
        });
        break;

      case 'contradiction_alert': {
        const alert = msg.payload as SituationGraph['contradictions'][string];
        const currentGraph = useSituationGraph.getState().graph;
        if (currentGraph) {
          setGraph({
            ...currentGraph,
            contradictions: {
              ...currentGraph.contradictions,
              [alert.id]: alert
            }
          });
        }
        break;
      }

      case 'action_recommendation': {
        const action = msg.payload as SituationGraph['pending_actions'][string];
        const currentGraph = useSituationGraph.getState().graph;
        if (currentGraph) {
          setGraph({
            ...currentGraph,
            pending_actions: {
              ...currentGraph.pending_actions,
              [action.id]: action
            }
          });
        }
        break;
      }

      case 'sim_status':
        setSimStatus(msg.payload as Parameters<typeof setSimStatus>[0]);
        break;

      case 'timeline_event': {
        const payload = msg.payload as { events?: TimelineEvent[] };
        if (payload.events) {
          payload.events.forEach(e => addTimelineEvent(e));
        }
        break;
      }

      case 'signal_processed':
        addProcessedSignal(msg.payload as ProcessedSignal);
        break;

      case 'debate_turn':
        addDebateTurn(msg.payload as DebateTurn);
        break;

      case 'allocation_update':
      case 'camp_recommendation':
        // These trigger graph_update anyway, no special handling needed
        break;

      case 'voice_report':
        addVoiceReport(msg.payload as VoiceReport);
        break;

      case 'decision_made':
        break;
    }
  }, [setGraph, updateGraph, setConnected, setSimStatus, addTimelineEvent, addProcessedSignal, addDebateTurn, addVoiceReport]);

  const { isConnected, send } = useWebSocket({
    url: WS_URL,
    onMessage: handleMessage,
  });

  useEffect(() => {
    setConnected(isConnected);
  }, [isConnected, setConnected]);

  useEffect(() => {
    setWsRef({ send });
  }, [send, setWsRef]);

  return (
    <div className="flex flex-col h-screen bg-[#0a0a0f] overflow-hidden">
      <Header />
      <div className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/debate" element={<DebatePage />} />
          <Route path="/debate/:alertId" element={<DebatePage />} />
          <Route path="/resources" element={<ResourcesPage />} />
          <Route path="/voice" element={<VoicePage />} />
          <Route path="/copilot" element={<CopilotPage />} />
        </Routes>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}
