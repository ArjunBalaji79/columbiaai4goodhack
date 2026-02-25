export interface DebateTurn {
  turn_number: number;
  agent_name: string;
  role: 'defender' | 'challenger' | 'rebuttal' | 'synthesis';
  argument: string;
  confidence: number;
  timestamp: string;
  alert_id?: string;
  done?: boolean;
}
