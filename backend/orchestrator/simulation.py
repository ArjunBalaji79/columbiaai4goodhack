"""
Demo simulation engine - plays back the earthquake scenario timeline.
"""
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Optional
import uuid

from graph.schemas import (
    IncidentNode, ResourceNode, LocationNode, SourceReference,
    DamageLevel, Urgency, SourceType, Location, ContradictionAlert,
    ActionRecommendation, Verdict, ActionType
)


async def run_simulation(coordinator, scenario_id: str, speed: float = 1.0):
    """Run the demo simulation."""
    from api.websocket import broadcast

    # Load scenario
    scenario = _load_scenario(scenario_id)
    if not scenario:
        print(f"Scenario {scenario_id} not found, using default")
        scenario = _get_default_scenario()

    # Initialize graph metadata
    now = datetime.utcnow()
    coordinator.graph_manager.graph.scenario_id = scenario_id
    coordinator.graph_manager.graph.scenario_name = scenario.get("scenario_name", "Metro City Earthquake")
    coordinator.graph_manager.graph.scenario_start_time = now
    coordinator.graph_manager.graph.current_sim_time = now

    # Load initial resources
    await _load_initial_resources(coordinator, scenario.get("initial_resources", {}), now)

    # Load initial locations
    await _load_initial_locations(coordinator, scenario.get("initial_locations", []), now)

    await broadcast("graph_update", coordinator.graph_manager.graph.model_dump(mode="json"))
    await broadcast("sim_status", coordinator.get_simulation_status())

    print(f"Starting simulation: {scenario.get('scenario_name')}")

    # Process events in order
    events = scenario.get("events", [])

    try:
        for event in events:
            if not coordinator.simulation_running:
                # Wait if paused
                while coordinator.simulation_paused:
                    await asyncio.sleep(0.2)
                if not coordinator.simulation_running and not coordinator.simulation_paused:
                    break

            offset = event.get("time_offset_seconds", 0)

            # Wait per-event delay (human-observable pacing)
            demo_delay = event.get("demo_delay_seconds", 3.0)
            actual_wait = max(0.3, demo_delay / speed)
            await asyncio.sleep(actual_wait)

            # Update simulation time
            sim_time_offset = timedelta(seconds=offset)
            coordinator.graph_manager.graph.current_sim_time = now + sim_time_offset

            event_type = event.get("event_type")

            # Signal events: fire as background tasks so API calls don't block pacing
            if event_type in ("signal", "signal_batch"):
                asyncio.create_task(_process_sim_event(coordinator, event, now + sim_time_offset))
            else:
                # Non-signal events (contradiction_inject, aftershock, etc.) are lightweight — await them
                await _process_sim_event(coordinator, event, now + sim_time_offset)

            await broadcast("sim_status", coordinator.get_simulation_status())

    except Exception as e:
        import traceback
        print(f"Simulation error: {e}")
        traceback.print_exc()

    coordinator.simulation_running = False
    print("Simulation complete")


async def _process_sim_event(coordinator, event: dict, sim_time: datetime):
    """Process a single simulation event."""
    event_type = event.get("event_type")
    data = event.get("data", {})

    if event_type == "signal":
        await _process_signal_event(coordinator, data, sim_time)

    elif event_type == "signal_batch":
        signals = data.get("signals", [])
        for signal in signals:
            await _process_signal_event(coordinator, signal, sim_time)
            await asyncio.sleep(0.3)  # Small delay between batch signals

    elif event_type == "aftershock":
        await _process_aftershock(coordinator, data, sim_time)

    elif event_type == "resource_change":
        await _process_resource_change(coordinator, data)

    elif event_type == "contradiction_inject":
        await _inject_contradiction(coordinator, data, sim_time)

    elif event_type == "time_marker":
        from api.websocket import broadcast
        coordinator._add_event("time_marker", {"label": data.get("label", "")})
        await broadcast("timeline_event", {"events": coordinator.recent_events[-10:]})


async def _process_signal_event(coordinator, data: dict, sim_time: datetime):
    """Process an incoming signal event."""
    signal_type = data.get("type", "text")
    location_data = data.get("location", {})
    raw_metadata = data.get("metadata", {})
    metadata = {
        "location": location_data,
        "sector": data.get("sector") or location_data.get("sector"),
        "source": raw_metadata.get("source", "simulation"),
        "source_type": data.get("source_type", ""),
        "transcript": data.get("transcript", ""),
        "sim_time": sim_time.isoformat(),
        "asset_file": raw_metadata.get("asset_file"),
    }

    # For demo, use pre-defined content instead of real files
    content = data.get("content", "")
    if not content:
        content = data.get("description", "Simulated emergency signal")

    from api.websocket import broadcast

    # For text signals, use the content directly
    if signal_type == "text":
        metadata["source_type"] = data.get("source_type", "unverified")
        await coordinator.process_signal("text", content, metadata)

    elif signal_type == "audio":
        transcript = data.get("transcript", content)
        metadata["transcript"] = transcript
        await coordinator.process_signal("audio", "", metadata)

    elif signal_type == "image":
        # For demo, we process as text description
        metadata["description"] = content
        await coordinator.process_signal("image", "", metadata)

    await broadcast("graph_update", coordinator.graph_manager.graph.model_dump(mode="json"))


async def _process_aftershock(coordinator, data: dict, sim_time: datetime):
    """Handle aftershock event."""
    from api.websocket import broadcast

    magnitude = data.get("magnitude", 4.2)
    coordinator._add_event("aftershock", {
        "magnitude": magnitude,
        "sim_time": sim_time.isoformat()
    })

    # Decay confidences
    coordinator.graph_manager.decay_confidences(5.0)

    # Broadcast update
    await broadcast("graph_update", coordinator.graph_manager.graph.model_dump(mode="json"))
    await broadcast("timeline_event", {
        "events": coordinator.recent_events[-10:],
        "alert": {
            "type": "aftershock",
            "message": f"⚡ AFTERSHOCK {magnitude}M - Updating confidence levels",
            "severity": "warning"
        }
    })


async def _process_resource_change(coordinator, data: dict):
    """Handle resource status change."""
    from api.websocket import broadcast

    resource_id = data.get("resource_id")
    updates = data.get("updates", {})

    if resource_id and resource_id in coordinator.graph_manager.graph.resources:
        coordinator.graph_manager.update_resource(resource_id, updates)
        await broadcast("resource_update", {
            "resource_id": resource_id,
            "updates": updates
        })


async def _inject_contradiction(coordinator, data: dict, sim_time: datetime):
    """Inject a pre-scripted contradiction into the system."""
    from api.websocket import broadcast

    entity_name = data.get("entity", "Unknown")
    claims = data.get("claims", [])
    print(f"[CONTRADICTION INJECT] Starting injection for entity: {entity_name}")

    # Add claims to the signal_claims tracker
    if entity_name not in coordinator.signal_claims:
        coordinator.signal_claims[entity_name] = []

    for claim in claims:
        coordinator.signal_claims[entity_name].append({
            **claim,
            "timestamp": sim_time.strftime("%H:%M")
        })

    # Run verification
    if len(coordinator.signal_claims[entity_name]) >= 2:
        verification_input = {
            "entity": entity_name,
            "entity_type": data.get("entity_type", "infrastructure"),
            "claims": coordinator.signal_claims[entity_name]
        }

        try:
            ver_output = await coordinator.verification_agent.process(verification_input)
            ver_data = ver_output.data

            # Build contradiction alert
            alert_id = f"alert_{str(uuid.uuid4())[:8]}"
            verdict_map = {
                "CONTRADICTION": Verdict.CONTRADICTION,
                "TEMPORAL_GAP": Verdict.TEMPORAL_GAP,
                "CONSISTENT": Verdict.CONSISTENT,
                "UNCERTAIN": Verdict.UNCERTAIN
            }
            action_map = {
                "REQUEST_VERIFICATION": ActionType.REQUEST_VERIFICATION,
                "FLAG_FOR_HUMAN": ActionType.FLAG_FOR_HUMAN,
                "ACCEPT": ActionType.ACCEPT,
                "WAIT": ActionType.WAIT
            }

            # Force verdict for bridge demo
            verdict_str = ver_data.get("verdict", data.get("force_verdict", "CONTRADICTION"))

            alert = ContradictionAlert(
                id=alert_id,
                entity_id=entity_name.lower().replace(" ", "_"),
                entity_type=data.get("entity_type", "infrastructure"),
                entity_name=entity_name,
                claims=coordinator.signal_claims[entity_name],
                verdict=verdict_map.get(verdict_str, Verdict.CONTRADICTION),
                severity="high",
                temporal_analysis=ver_data.get("temporal_analysis") or data.get("temporal_analysis", ""),
                recommended_action=action_map.get(
                    ver_data.get("recommended_action", "REQUEST_VERIFICATION"),
                    ActionType.REQUEST_VERIFICATION
                ),
                recommended_action_details=ver_data.get("recommended_action_details", "Deploy aerial verification"),
                urgency=Urgency.HIGH,
                created_at=sim_time
            )

            coordinator.graph_manager.add_contradiction(alert)
            coordinator.handled_contradictions.add(entity_name)
            del coordinator.signal_claims[entity_name]
            print(f"[CONTRADICTION INJECT] Successfully injected and handled: {entity_name}")

            await broadcast("contradiction_alert", alert.model_dump(mode="json"))
            coordinator._add_event("contradiction_detected", {
                "alert_id": alert_id,
                "entity": entity_name
            })
            await broadcast("graph_update", coordinator.graph_manager.graph.model_dump(mode="json"))

        except Exception as e:
            import traceback
            print(f"Error in contradiction injection for '{entity_name}': {e}")
            traceback.print_exc()
            # Clean up claims on error to prevent repeated processing
            if entity_name in coordinator.signal_claims:
                del coordinator.signal_claims[entity_name]


async def _load_initial_resources(coordinator, resources_data: dict, now: datetime):
    """Load initial resources from scenario."""
    resource_locations = {
        "1": {"lat": 37.790, "lng": -122.402},
        "2": {"lat": 37.780, "lng": -122.410},
        "3": {"lat": 37.772, "lng": -122.418},
        "4": {"lat": 37.760, "lng": -122.405},
        "5": {"lat": 37.755, "lng": -122.415},
    }

    for resource_type, items in resources_data.items():
        if not isinstance(items, list):
            continue
        for item in items:
            sector = item.get("sector", "1")
            loc = resource_locations.get(str(sector), {"lat": 37.78, "lng": -122.41})

            resource = ResourceNode(
                id=item.get("id", str(uuid.uuid4())[:8]),
                resource_type=resource_type.rstrip("s"),  # ambulances -> ambulance
                unit_id=item.get("id", "UNIT-?"),
                current_location=Location(
                    lat=loc["lat"] + (hash(item.get("id", "")) % 50 - 25) * 0.0005,
                    lng=loc["lng"] + (hash(item.get("id", "")[::-1]) % 50 - 25) * 0.0005,
                    sector=str(sector)
                ),
                status=item.get("status", "available"),
                personnel=item.get("personnel", 2),
                capacity_remaining=2,
                updated_at=now
            )
            coordinator.graph_manager.add_resource(resource)


async def _load_initial_locations(coordinator, locations_data: list, now: datetime):
    """Load initial key locations."""
    # Default locations from DEMO_SCENARIO.md
    default_locations = [
        {
            "id": "loc_metro_general",
            "location_type": "hospital",
            "name": "Metro General Hospital",
            "lat": 37.7850, "lng": -122.4050,
            "capacity_total": 200, "capacity_used": 90,
            "status": "operational"
        },
        {
            "id": "loc_st_marys",
            "location_type": "hospital",
            "name": "St. Mary's Medical",
            "lat": 37.7620, "lng": -122.4180,
            "capacity_total": 150, "capacity_used": 45,
            "status": "operational"
        },
        {
            "id": "loc_main_bridge",
            "location_type": "bridge",
            "name": "Main Street Bridge",
            "lat": 37.7800, "lng": -122.4100,
            "status": "operational",
            "accessibility": "accessible"
        },
    ]

    locs_to_load = locations_data if locations_data else default_locations

    for loc_data in locs_to_load:
        location = LocationNode(
            id=loc_data.get("id", str(uuid.uuid4())[:8]),
            location=Location(
                lat=loc_data.get("lat", 37.78),
                lng=loc_data.get("lng", -122.41),
                name=loc_data.get("name")
            ),
            location_type=loc_data.get("location_type", "infrastructure"),
            capacity_total=loc_data.get("capacity_total"),
            capacity_used=loc_data.get("capacity_used"),
            status=loc_data.get("status", "operational"),
            accessibility=loc_data.get("accessibility", "accessible"),
            confidence=0.9,
            updated_at=now
        )
        coordinator.graph_manager.add_location(location)


def _load_scenario(scenario_id: str) -> Optional[dict]:
    """Load scenario from JSON file."""
    # Try multiple paths
    paths = [
        os.path.join(os.path.dirname(__file__), "..", "demo_data", f"{scenario_id}.json"),
        os.path.join(os.path.dirname(__file__), "..", "demo_data", "scenario_earthquake.json"),
    ]

    for path in paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            with open(abs_path) as f:
                return json.load(f)

    return None


def _get_default_scenario() -> dict:
    """Return hardcoded default scenario."""
    return {
        "scenario_id": "earthquake_001",
        "scenario_name": "Metro City 6.8 Earthquake",
        "description": "Major earthquake strikes Metro City.",
        "city_name": "Metro City",
        "demo_compression": 30,
        "initial_resources": {
            "ambulances": [
                {"id": "AMB-1", "sector": "1", "status": "available"},
                {"id": "AMB-2", "sector": "1", "status": "available"},
                {"id": "AMB-3", "sector": "2", "status": "available"},
                {"id": "AMB-4", "sector": "2", "status": "available"},
                {"id": "AMB-5", "sector": "3", "status": "available"},
                {"id": "AMB-6", "sector": "3", "status": "available"},
                {"id": "AMB-7", "sector": "4", "status": "available"},
                {"id": "AMB-8", "sector": "4", "status": "available"},
                {"id": "AMB-9", "sector": "5", "status": "available"},
                {"id": "AMB-10", "sector": "5", "status": "available"},
                {"id": "AMB-11", "sector": "1", "status": "available"},
                {"id": "AMB-12", "sector": "3", "status": "available"}
            ],
            "fire_trucks": [
                {"id": "ENGINE-1", "sector": "1", "status": "available"},
                {"id": "ENGINE-2", "sector": "2", "status": "available"},
                {"id": "ENGINE-3", "sector": "3", "status": "available"},
                {"id": "ENGINE-4", "sector": "4", "status": "available"},
                {"id": "LADDER-1", "sector": "1", "status": "available"},
                {"id": "LADDER-2", "sector": "3", "status": "available"}
            ],
            "search_teams": [
                {"id": "SAR-1", "sector": "1", "personnel": 6, "status": "available"},
                {"id": "SAR-2", "sector": "2", "personnel": 6, "status": "available"},
                {"id": "SAR-3", "sector": "3", "personnel": 6, "status": "available"},
                {"id": "SAR-4", "sector": "4", "personnel": 6, "status": "available"}
            ],
            "helicopters": [
                {"id": "HELI-1", "sector": "central", "status": "available"},
                {"id": "HELI-2", "sector": "central", "status": "available"}
            ]
        },
        "initial_locations": [],
        "events": [
            {
                "time_offset_seconds": 5,
                "demo_delay_seconds": 2,
                "event_type": "signal",
                "data": {
                    "type": "image",
                    "location": {"lat": 37.790, "lng": -122.402, "sector": "4"},
                    "content": "Building collapse at 500 Market Street. Multi-story pancake collapse visible. Heavy debris field. Smoke rising from eastern section.",
                    "description": "collapse_severe_001.jpg",
                    "metadata": {"source": "first_responder_camera"}
                }
            },
            {
                "time_offset_seconds": 8,
                "demo_delay_seconds": 1.5,
                "event_type": "signal",
                "data": {
                    "type": "text",
                    "content": "OMG major collapse on Market Street!! Everyone stay away!! Building completely down!! #MetroCityQuake",
                    "source_type": "social_media",
                    "location": {"name": "500 Market Street"}
                }
            },
            {
                "time_offset_seconds": 12,
                "demo_delay_seconds": 2,
                "event_type": "signal",
                "data": {
                    "type": "audio",
                    "transcript": "Unit 7 to dispatch - we have multiple people trapped on the 4th floor at 500 Market Street. Stairwells are compromised. Pancake collapse on floors 2 through 4. Requesting search and rescue and minimum 3 ambulances. We can hear voices in the debris.",
                    "location": {"lat": 37.790, "lng": -122.402, "sector": "4"},
                    "source_type": "first_responder"
                }
            },
            {
                "time_offset_seconds": 15,
                "demo_delay_seconds": 2,
                "event_type": "signal",
                "data": {
                    "type": "image",
                    "location": {"lat": 37.772, "lng": -122.418, "sector": "3"},
                    "content": "Active fire visible from residential building in Sector 3. Smoke column rising. Adjacent structures at risk.",
                    "description": "fire_smoke_001.jpg",
                    "metadata": {"source": "drone_camera"}
                }
            },
            {
                "time_offset_seconds": 18,
                "demo_delay_seconds": 1.5,
                "event_type": "signal",
                "data": {
                    "type": "text",
                    "content": "Metro General Hospital Status Update: Current ER capacity at 45%. Accepting trauma cases. Recommend diverting non-critical to St. Mary's Medical. All surgical teams on standby.",
                    "source_type": "official_report",
                    "location": {"name": "Metro General Hospital"}
                }
            },
            {
                "time_offset_seconds": 22,
                "demo_delay_seconds": 2,
                "event_type": "signal",
                "data": {
                    "type": "audio",
                    "transcript": "This is civilian calling 911 - we are trapped in our apartment on Oak Street, third floor. The staircase has collapsed. There are 4 of us including 2 children. Please help us.",
                    "location": {"lat": 37.775, "lng": -122.420, "sector": "3"},
                    "source_type": "civilian"
                }
            },
            {
                "time_offset_seconds": 32,
                "demo_delay_seconds": 3,
                "event_type": "contradiction_inject",
                "data": {
                    "entity": "Main Street Bridge",
                    "entity_type": "infrastructure",
                    "temporal_analysis": "Satellite image predates audio report by 21 minutes. Bridge collapse may have occurred after image capture.",
                    "force_verdict": "CONTRADICTION",
                    "claims": [
                        {
                            "source": "audio_report",
                            "source_type": "first_responder",
                            "claim": "Bridge collapsed, completely impassable - confirmed collapse of main span",
                            "confidence": 0.72
                        },
                        {
                            "source": "satellite_img_14:40",
                            "source_type": "satellite",
                            "claim": "Bridge appears structurally intact, no visible collapse",
                            "confidence": 0.89
                        }
                    ]
                }
            },
            {
                "time_offset_seconds": 55,
                "demo_delay_seconds": 2,
                "event_type": "signal",
                "data": {
                    "type": "image",
                    "location": {"lat": 37.780, "lng": -122.410, "sector": "2"},
                    "content": "AERIAL VERIFICATION: Main Street Bridge - Main span has collapsed. Deck failure on western section confirmed. Bridge is impassable. Debris in waterway.",
                    "description": "bridge_collapsed_aerial.jpg",
                    "metadata": {"source": "HELI-1_aerial_verification"}
                }
            },
            {
                "time_offset_seconds": 68,
                "demo_delay_seconds": 3,
                "event_type": "signal",
                "data": {
                    "type": "text",
                    "content": "911 Transcript: Caller reports family trapped in apartment building, 3rd floor, Oak Street and 5th Avenue. Building partially collapsed. 4 people including 2 children. Can hear other voices in building.",
                    "source_type": "911_transcript",
                    "location": {"name": "Oak Street Building"}
                }
            },
            {
                "time_offset_seconds": 72,
                "demo_delay_seconds": 1,
                "event_type": "time_marker",
                "data": {"label": "Planning Agent generating recommendations..."}
            },
            {
                "time_offset_seconds": 120,
                "demo_delay_seconds": 3,
                "event_type": "aftershock",
                "data": {"magnitude": 4.2}
            },
            {
                "time_offset_seconds": 125,
                "demo_delay_seconds": 2,
                "event_type": "signal",
                "data": {
                    "type": "image",
                    "location": {"lat": 37.772, "lng": -122.418, "sector": "3"},
                    "content": "Secondary building collapse in Sector 3 following aftershock. Three-story residential structure partially collapsed. Active fire nearby.",
                    "description": "collapse_secondary.jpg",
                    "metadata": {"source": "ground_camera"}
                }
            },
            {
                "time_offset_seconds": 130,
                "demo_delay_seconds": 2,
                "event_type": "signal",
                "data": {
                    "type": "text",
                    "content": "PG&E Alert: Gas leak detected at intersection of Oak Street and Elm Avenue, Sector 3. Field crews dispatched. Recommend immediate 200-meter evacuation radius.",
                    "source_type": "utility_company",
                    "location": {"name": "Oak/Elm Intersection"}
                }
            }
        ]
    }
