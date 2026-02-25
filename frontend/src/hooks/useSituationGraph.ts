import { create } from 'zustand';
import { SituationGraph, ContradictionAlert, ActionRecommendation, TimelineEvent, VoiceReport } from '../types';
import { ProcessedSignal } from '../components/signals/SignalIntelligence';
import { DebateTurn } from '../types/debate';

interface SimStatus {
  running: boolean;
  paused: boolean;
  scenario_id: string;
  scenario_name: string;
  current_time: string;
  elapsed_seconds: number;
}

interface SituationGraphState {
  graph: SituationGraph | null;
  isConnected: boolean;
  simStatus: SimStatus | null;
  timelineEvents: TimelineEvent[];
  wsRef: { send: (msg: unknown) => void } | null;

  processedSignals: ProcessedSignal[];
  addProcessedSignal: (signal: ProcessedSignal) => void;

  // Debate state: keyed by alertId
  debateTurns: Record<string, DebateTurn[]>;
  addDebateTurn: (turn: DebateTurn) => void;
  clearDebate: (alertId: string) => void;

  // Setters
  setGraph: (graph: SituationGraph) => void;
  updateGraph: (partial: Partial<SituationGraph>) => void;
  setConnected: (connected: boolean) => void;
  setSimStatus: (status: SimStatus) => void;
  setWsRef: (ref: { send: (msg: unknown) => void }) => void;
  addTimelineEvent: (event: TimelineEvent) => void;

  // Decision actions
  resolveContradiction: (id: string, resolution: string) => void;
  approveAction: (id: string) => void;
  rejectAction: (id: string, reason?: string) => void;

  // Voice reports
  voiceReports: VoiceReport[];
  addVoiceReport: (report: VoiceReport) => void;

  // Simulation controls
  startSimulation: (scenarioId?: string, speed?: number) => void;
  pauseSimulation: () => void;
  resumeSimulation: () => void;
  resetSimulation: () => void;
}

export const useSituationGraph = create<SituationGraphState>((set, get) => ({
  graph: null,
  isConnected: false,
  simStatus: null,
  timelineEvents: [],
  wsRef: null,
  processedSignals: [],
  debateTurns: {},
  voiceReports: [],

  addProcessedSignal: (signal) => set((state) => ({
    processedSignals: [signal, ...state.processedSignals].slice(0, 20)
  })),

  addDebateTurn: (turn) => set((state) => {
    const alertId = turn.alert_id ?? 'current';
    const existing = state.debateTurns[alertId] ?? [];
    // Avoid duplicate turn numbers
    const filtered = existing.filter(t => t.turn_number !== turn.turn_number);
    return {
      debateTurns: {
        ...state.debateTurns,
        [alertId]: [...filtered, turn].sort((a, b) => a.turn_number - b.turn_number)
      }
    };
  }),

  clearDebate: (alertId) => set((state) => ({
    debateTurns: { ...state.debateTurns, [alertId]: [] }
  })),

  setGraph: (graph) => set({ graph }),

  updateGraph: (partial) => set((state) => ({
    graph: state.graph ? { ...state.graph, ...partial } : null
  })),

  setConnected: (connected) => set({ isConnected: connected }),
  setSimStatus: (status) => set({ simStatus: status }),
  setWsRef: (ref) => set({ wsRef: ref }),

  addTimelineEvent: (event) => set((state) => ({
    timelineEvents: [event, ...state.timelineEvents].slice(0, 50)
  })),

  resolveContradiction: (id, resolution) => {
    const { wsRef, graph } = get();
    // Optimistic update — mark resolved immediately so it leaves Decision Queue
    if (graph?.contradictions[id]) {
      set(state => ({
        graph: state.graph ? {
          ...state.graph,
          contradictions: {
            ...state.graph.contradictions,
            [id]: { ...state.graph.contradictions[id], resolved: true, resolution }
          }
        } : null
      }));
    }
    wsRef?.send({
      type: 'human_decision',
      payload: {
        item_type: 'contradiction',
        item_id: id,
        decision: resolution,
        decided_by: 'operator'
      }
    });
  },

  approveAction: (id) => {
    const { wsRef, graph } = get();
    // Optimistic update so the button changes immediately
    if (graph?.pending_actions[id]) {
      set(state => ({
        graph: state.graph ? {
          ...state.graph,
          pending_actions: {
            ...state.graph.pending_actions,
            [id]: { ...state.graph.pending_actions[id], status: 'approved' }
          }
        } : null
      }));
    }
    wsRef?.send({
      type: 'human_decision',
      payload: {
        item_type: 'action',
        item_id: id,
        decision: 'approved',
        decided_by: 'operator'
      }
    });
  },

  rejectAction: (id, reason) => {
    const { wsRef, graph } = get();
    // Optimistic update
    if (graph?.pending_actions[id]) {
      set(state => ({
        graph: state.graph ? {
          ...state.graph,
          pending_actions: {
            ...state.graph.pending_actions,
            [id]: { ...state.graph.pending_actions[id], status: 'rejected' }
          }
        } : null
      }));
    }
    wsRef?.send({
      type: 'human_decision',
      payload: {
        item_type: 'action',
        item_id: id,
        decision: 'rejected',
        reason,
        decided_by: 'operator'
      }
    });
  },

  startSimulation: (scenarioId = 'earthquake_001', speed = 1.0) => {
    const { wsRef } = get();
    wsRef?.send({
      type: 'start_simulation',
      payload: { scenario_id: scenarioId, speed }
    });
  },

  pauseSimulation: () => {
    const { wsRef } = get();
    wsRef?.send({ type: 'pause_simulation', payload: {} });
  },

  resumeSimulation: () => {
    const { wsRef } = get();
    wsRef?.send({ type: 'resume_simulation', payload: {} });
  },

  addVoiceReport: (report) => set((state) => ({
    voiceReports: [report, ...state.voiceReports].slice(0, 20)
  })),

  resetSimulation: () => {
    const { wsRef } = get();
    wsRef?.send({ type: 'reset_simulation', payload: {} });
    set({ timelineEvents: [], processedSignals: [], debateTurns: {}, voiceReports: [] });
  },
}));
