import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Callable

logger = logging.getLogger("friday.core.event_bus")

class UnifiedEventBus:
    """Centralized high-performance event bus for system-wide observability."""
    
    def __init__(self):
        self.listeners: List[Callable] = []
        self._event_queue = asyncio.Queue()
        self.is_active = False
        self._loop_task = None

    async def start(self):
        if self.is_active: return
        self.is_active = True
        self._loop_task = asyncio.create_task(self._process_events())
        logger.info("UnifiedEventBus: ONLINE")

    async def stop(self):
        self.is_active = False
        if self._loop_task:
            self._loop_task.cancel()
        logger.info("UnifiedEventBus: OFFLINE")

    def emit(self, component: str, event_type: str, data: Any = None, level: str = "INFO"):
        """Synchronously queue an event for emission."""
        event = {
            "timestamp": time.time(),
            "component": component,
            "type": event_type,
            "data": data,
            "level": level
        }
        self._event_queue.put_nowait(event)

    def subscribe(self, callback: Callable):
        self.listeners.append(callback)

    async def _process_events(self):
        while self.is_active:
            try:
                event = await self._event_queue.get()
                
                # Notify all listeners (e.g. WebSocket, Logger, Metrics)
                for listener in self.listeners:
                    try:
                        if asyncio.iscoroutinefunction(listener):
                            asyncio.create_task(listener(event))
                        else:
                            listener(event)
                    except Exception as le:
                        logger.error(f"Listener error: {le}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"EventBus error: {e}")

event_bus = UnifiedEventBus()
