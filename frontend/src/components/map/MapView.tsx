import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { SituationGraph } from '../../types';

const DARK_TILES = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const DEFAULT_CENTER: [number, number] = [37.78, -122.41];
const DEFAULT_ZOOM = 13;

interface MapViewProps {
  graph: SituationGraph | null;
}

function getUrgencyColor(urgency: string): string {
  const colors: Record<string, string> = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#f59e0b',
    low: '#3b82f6',
  };
  return colors[urgency] || '#71717a';
}

function getDamageRadius(damage: string): number {
  const radii: Record<string, number> = {
    catastrophic: 20,
    severe: 16,
    moderate: 12,
    minor: 8,
    none: 6,
  };
  return radii[damage] || 10;
}

function getResourceColor(type: string, status: string): string {
  if (status !== 'available' && status !== 'dispatched') return '#71717a';
  if (type.includes('ambulance')) return '#22c55e';
  if (type.includes('fire') || type.includes('engine')) return '#f97316';
  if (type.includes('helicopter')) return '#a855f7';
  return '#3b82f6';
}

export function MapView({ graph }: MapViewProps) {
  return (
    <MapContainer
      center={DEFAULT_CENTER}
      zoom={DEFAULT_ZOOM}
      className="h-full w-full"
      style={{ background: '#0a0a0f' }}
    >
      <TileLayer
        url={DARK_TILES}
        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        maxZoom={19}
      />

      {/* Incident markers */}
      {graph && Object.values(graph.incidents).map(incident => {
        const color = getUrgencyColor(incident.urgency);
        const radius = getDamageRadius(incident.damage_level);
        const hasContradiction = incident.contradictions.length > 0;

        return (
          <CircleMarker
            key={incident.id}
            center={[incident.location.lat, incident.location.lng]}
            radius={radius}
            pathOptions={{
              color: hasContradiction ? '#f59e0b' : color,
              fillColor: color,
              fillOpacity: incident.status === 'responding' ? 0.4 : 0.7,
              weight: hasContradiction ? 3 : 2,
              dashArray: hasContradiction ? '5, 5' : undefined,
            }}
          >
            <Tooltip>
              <div className="text-xs">
                <strong>{incident.incident_type.replace(/_/g, ' ')}</strong><br />
                Urgency: {incident.urgency}<br />
                Damage: {incident.damage_level}<br />
                Confidence: {Math.round(incident.confidence * 100)}%<br />
                {incident.trapped_min !== undefined && (
                  <>Trapped: {incident.trapped_min}-{incident.trapped_max}</>
                )}
              </div>
            </Tooltip>
            <Popup>
              <div style={{ minWidth: 180, fontSize: 12 }}>
                <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
                  {incident.incident_type.replace(/_/g, ' ').toUpperCase()}
                </div>
                <div>Sector {incident.location.sector}</div>
                <div>Status: <strong>{incident.status}</strong></div>
                <div>Urgency: <strong style={{ color }}>{incident.urgency}</strong></div>
                <div>Damage: {incident.damage_level}</div>
                <div>Confidence: {Math.round(incident.confidence * 100)}%</div>
                {incident.trapped_min !== undefined && (
                  <div>Trapped: {incident.trapped_min}–{incident.trapped_max}</div>
                )}
                {incident.assigned_resources.length > 0 && (
                  <div>Resources: {incident.assigned_resources.join(', ')}</div>
                )}
              </div>
            </Popup>
          </CircleMarker>
        );
      })}

      {/* Resource markers */}
      {graph && Object.values(graph.resources).map(resource => {
        const color = getResourceColor(resource.resource_type, resource.status);
        const isDispatched = resource.status === 'dispatched';

        return (
          <CircleMarker
            key={resource.id}
            center={[resource.current_location.lat, resource.current_location.lng]}
            radius={isDispatched ? 8 : 5}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity: resource.status === 'available' ? 0.8 : 0.5,
              weight: isDispatched ? 2 : 1,
            }}
          >
            <Tooltip>
              <div className="text-xs">
                <strong>{resource.unit_id}</strong><br />
                Type: {resource.resource_type}<br />
                Status: {resource.status}<br />
                {resource.eta_minutes && `ETA: ${resource.eta_minutes}m`}
              </div>
            </Tooltip>
          </CircleMarker>
        );
      })}

      {/* Location markers */}
      {graph && Object.values(graph.locations).map(loc => {
        const isHospital = loc.location_type === 'hospital';
        if (!loc.location?.lat) return null;

        const pct = loc.capacity_total
          ? (loc.capacity_used ?? 0) / loc.capacity_total
          : 0;
        const color = loc.status === 'destroyed' ? '#ef4444' :
                     loc.status === 'damaged' ? '#f59e0b' :
                     isHospital ? (pct > 0.9 ? '#ef4444' : '#22c55e') :
                     '#71717a';

        return (
          <CircleMarker
            key={loc.id}
            center={[loc.location.lat, loc.location.lng]}
            radius={isHospital ? 10 : 7}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity: 0.6,
              weight: 2,
            }}
          >
            <Tooltip>
              <div className="text-xs">
                <strong>{loc.location?.name || loc.id}</strong><br />
                Type: {loc.location_type}<br />
                Status: {loc.status}<br />
                {loc.capacity_total && `Capacity: ${loc.capacity_used}/${loc.capacity_total}`}
              </div>
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
