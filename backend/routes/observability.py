import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.event_bus import event_bus

logger = logging.getLogger("friday.routes.observability")
router = APIRouter()

@router.websocket("/api/ws/observability")
async def observability_endpoint(websocket: WebSocket):
    """WebSocket endpoint for realtime system-wide observability events."""
    await websocket.accept()
    logger.info("Observability client connected.")
    
    # Listener function for the event bus
    async def event_listener(event: dict):
        try:
            await websocket.send_json(event)
        except Exception:
            # Client probably disconnected
            pass

    # Subscribe to the event bus
    event_bus.subscribe(event_listener)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("Observability client disconnected.")
    finally:
        # Unsubscribe (we need a way to unsubscribe in event_bus)
        if event_listener in event_bus.listeners:
            event_bus.listeners.remove(event_listener)
