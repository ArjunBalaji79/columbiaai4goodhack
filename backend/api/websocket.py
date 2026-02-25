"""
WebSocket handler for real-time updates to dashboard clients.
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set
import json
from datetime import datetime

# Active connections
connections: Set[WebSocket] = set()


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.add(websocket)

    try:
        # Send initial state
        from main import get_coordinator
        coordinator = get_coordinator()
        if coordinator:
            await websocket.send_json({
                "type": "initial_state",
                "payload": coordinator.graph_manager.graph.model_dump(mode="json"),
                "timestamp": datetime.utcnow().isoformat()
            })
            await websocket.send_json({
                "type": "sim_status",
                "payload": coordinator.get_simulation_status(),
                "timestamp": datetime.utcnow().isoformat()
            })

        # Listen for messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                continue

            coordinator = get_coordinator()
            if not coordinator:
                continue

            msg_type = message.get("type")

            # Wrap each message handler so one bad message can't kill the connection
            try:
                if msg_type == "human_decision":
                    payload = message.get("payload", {})
                    item_type = payload.get("item_type")
                    item_id = payload.get("item_id")
                    decision = payload.get("decision")

                    if item_type == "contradiction":
                        from graph.schemas import HumanDecision
                        await coordinator.resolve_contradiction(
                            item_id,
                            HumanDecision(
                                item_type="contradiction",
                                item_id=item_id,
                                decision=decision,
                                decided_by=payload.get("decided_by", "operator")
                            )
                        )
                    elif item_type == "action":
                        if decision == "approved":
                            await coordinator.approve_action(item_id)
                        elif decision == "rejected":
                            await coordinator.reject_action(item_id, payload.get("reason"))

                elif msg_type == "request_refresh":
                    await websocket.send_json({
                        "type": "graph_update",
                        "payload": coordinator.graph_manager.graph.model_dump(mode="json"),
                        "timestamp": datetime.utcnow().isoformat()
                    })

                elif msg_type == "start_simulation":
                    payload = message.get("payload", {})
                    await coordinator.start_simulation(
                        payload.get("scenario_id", "earthquake_001"),
                        float(payload.get("speed", 1.0))
                    )

                elif msg_type == "pause_simulation":
                    await coordinator.pause_simulation()

                elif msg_type == "resume_simulation":
                    await coordinator.resume_simulation()

                elif msg_type == "reset_simulation":
                    await coordinator.reset_simulation()

            except Exception as e:
                print(f"WebSocket message handler error ({msg_type}): {e}")

    except WebSocketDisconnect:
        connections.discard(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        connections.discard(websocket)


async def broadcast(message_type: str, payload: dict):
    """Broadcast message to all connected clients."""
    message = {
        "type": message_type,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat()
    }

    disconnected = set()
    for ws in connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.add(ws)

    # Clean up disconnected
    for ws in disconnected:
        connections.discard(ws)
