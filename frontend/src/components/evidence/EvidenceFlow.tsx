import { useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useSituationGraph } from '../../hooks/useSituationGraph';

export function EvidenceFlow() {
  const { graph } = useSituationGraph();

  const { nodes, edges } = useMemo(() => {
    if (!graph) return { nodes: [] as Node[], edges: [] as Edge[] };

    const resultNodes: Node[] = [];
    const resultEdges: Edge[] = [];

    let incidentX = 50;

    // Incident nodes
    Object.values(graph.incidents).forEach((incident, i) => {
      const urgencyColors: Record<string, string> = {
        critical: '#ef4444', high: '#f97316', medium: '#f59e0b', low: '#3b82f6',
      };
      const color = urgencyColors[incident.urgency] || '#71717a';

      resultNodes.push({
        id: incident.id,
        position: { x: incidentX + (i % 2) * 170, y: 50 + Math.floor(i / 2) * 130 },
        data: {
          label: (
            <div style={{ fontSize: 11 }}>
              <div style={{ color: '#ef4444', fontWeight: 600, fontSize: 10 }}>INCIDENT</div>
              <div style={{ color: '#e4e4e7', fontWeight: 500 }}>
                {incident.incident_type.replace(/_/g, ' ')}
              </div>
              <div style={{ color: '#a1a1aa' }}>Sector {incident.location.sector}</div>
              <div style={{ color }}>
                {incident.urgency.toUpperCase()} · {Math.round(incident.confidence * 100)}%
              </div>
            </div>
          )
        },
        style: {
          background: '#1a1a25',
          border: `2px solid ${color}`,
          borderRadius: 8,
          padding: '6px 10px',
          minWidth: 130,
          opacity: incident.status === 'resolved' ? 0.5 : 1,
        },
      });
    });

    // Contradiction nodes
    Object.values(graph.contradictions).forEach((alert, i) => {
      const nodeId = `contra_${alert.id}`;
      resultNodes.push({
        id: nodeId,
        position: { x: 380, y: 50 + i * 140 },
        data: {
          label: (
            <div style={{ fontSize: 11 }}>
              <div style={{ color: '#f59e0b', fontWeight: 600, fontSize: 10 }}>⚡ CONTRADICTION</div>
              <div style={{ color: '#e4e4e7', fontWeight: 500 }}>{alert.entity_name}</div>
              <div style={{ color: '#a1a1aa' }}>{alert.verdict}</div>
              {alert.resolved && (
                <div style={{ color: '#22c55e', fontSize: 10 }}>✓ Resolved</div>
              )}
            </div>
          )
        },
        style: {
          background: '#1a1a25',
          border: `2px solid ${alert.resolved ? '#27272a' : '#f59e0b'}`,
          borderRadius: 8,
          padding: '6px 10px',
          minWidth: 150,
          opacity: alert.resolved ? 0.6 : 1,
        },
      });
    });

    // Action nodes
    Object.values(graph.pending_actions).forEach((action, i) => {
      const nodeId = `action_${action.id}`;
      const statusColors: Record<string, string> = {
        pending: '#f59e0b', approved: '#22c55e', rejected: '#ef4444',
        executed: '#3b82f6', expired: '#71717a',
      };
      const color = statusColors[action.status] || '#f59e0b';

      resultNodes.push({
        id: nodeId,
        position: { x: 580, y: 50 + i * 140 },
        data: {
          label: (
            <div style={{ fontSize: 11 }}>
              <div style={{ color: '#3b82f6', fontWeight: 600, fontSize: 10 }}>RECOMMENDATION</div>
              <div style={{ color: '#e4e4e7', fontWeight: 500 }}>
                {action.action_type.replace(/_/g, ' ')}
              </div>
              <div style={{ color: '#a1a1aa' }}>
                {action.resources_to_allocate.slice(0, 2).join(', ')}
              </div>
              <div style={{ color, fontSize: 10 }}>
                {action.status.toUpperCase()} · {Math.round(action.confidence * 100)}%
              </div>
            </div>
          )
        },
        style: {
          background: '#1a1a25',
          border: `2px solid ${color}`,
          borderRadius: 8,
          padding: '6px 10px',
          minWidth: 140,
          opacity: action.status === 'pending' ? 1 : 0.7,
        },
      });

      if (action.target_incident_id && graph.incidents[action.target_incident_id]) {
        resultEdges.push({
          id: `e_${action.target_incident_id}_${nodeId}`,
          source: action.target_incident_id,
          target: nodeId,
          style: { stroke: '#3b82f6', strokeWidth: 1.5, strokeDasharray: '4 2' },
          animated: action.status === 'pending',
        });
      }
    });

    return { nodes: resultNodes, edges: resultEdges };
  }, [graph]);

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#1a1a25" />
        <Controls showInteractive={false} />
        <MiniMap
          style={{
            background: '#12121a',
            border: '1px solid #27272a',
            borderRadius: 4,
            width: 120,
            height: 80
          }}
          nodeColor={(n) => {
            const border = (n.style?.border as string) || '';
            if (border.includes('#ef4444')) return '#ef4444';
            if (border.includes('#f59e0b') || border.includes('#f97316')) return '#f59e0b';
            if (border.includes('#22c55e')) return '#22c55e';
            if (border.includes('#3b82f6')) return '#3b82f6';
            return '#27272a';
          }}
        />
      </ReactFlow>
    </div>
  );
}
