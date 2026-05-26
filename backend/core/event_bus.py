import asyncio
import json
import time
import uuid
import logging
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
from contracts.schemas import RuntimeEvent

logger = logging.getLogger("friday.core.event_bus")

class EventPriority:
    CRITICAL = 1
    HIGH = 5
    NORMAL = 10
    BACKGROUND = 20

class PrioritizedEvent:
    def __init__(self, priority: int, event: RuntimeEvent, trace_id: str = None, parent_id: str = None):
        self.priority = priority
        self.event = event
        self.timestamp = event.timestamp
        self.trace_id = trace_id or str(uuid.uuid4())
        self.parent_id = parent_id

    def __lt__(self, other):
        if self.priority == other.priority:
            return self.timestamp < other.timestamp
        return self.priority < other.priority

class UnifiedEventBus:
    """
    Hardened Multimodal Event Bus with prioritized scheduling, schema validation,
    dead-letter queueing (DLQ), trace lineage, and database replay support.
    """
    def __init__(self):
        self.listeners: List[Dict[str, Any]] = []
        self._event_queue = asyncio.PriorityQueue()
        self.is_active = False
        self._loop_task = None
        self._lock = asyncio.Lock()
        self.emitted_counts: Dict[str, int] = {}
        self.last_emit_time: Dict[str, float] = {}

    async def start(self):
        async with self._lock:
            if self.is_active: 
                return
            self.is_active = True
            self._loop_task = asyncio.create_task(self._process_events())
            logger.info("UnifiedEventBus: Hardened Core Lifecycle Active")

    async def stop(self):
        async with self._lock:
            self.is_active = False
            if self._loop_task:
                self._loop_task.cancel()
            logger.info("UnifiedEventBus: Offline")

    def emit(self, component: str, event_type: str, data: Any = None, priority: int = EventPriority.NORMAL, level: str = "INFO", trace_id: str = None, parent_id: str = None):
        """
        Emits an event into the prioritized queue.
        Validates event structure against Pydantic RuntimeEvent contract.
        """
        try:
            # Flood Suppression and Deduplication (Task 3)
            now = time.time()
            event_key = f"{component}:{event_type}"
            if event_key in self.last_emit_time and now - self.last_emit_time[event_key] < 0.02:
                # Suppress identical event storms
                return
            self.last_emit_time[event_key] = now
            self.emitted_counts[event_key] = self.emitted_counts.get(event_key, 0) + 1
            if self.emitted_counts[event_key] > 200:
                # Runaway emitter warning
                logger.warning(f"UnifiedEventBus: Suppressing runaway emitter for '{event_key}'")
                return

            # Validate schema contract (Task 9 & Task 6)
            validated_event = RuntimeEvent(
                id=str(uuid.uuid4()),
                timestamp=time.time(),
                component=component,
                type=event_type,
                data=data,
                level=level,
                priority=priority
            )
            
            p_event = PrioritizedEvent(
                priority=priority, 
                event=validated_event,
                trace_id=trace_id,
                parent_id=parent_id
            )

            # Thread-safe queue insertion
            try:
                loop = asyncio.get_running_loop()
                loop.call_soon_threadsafe(
                    lambda: self._event_queue.put_nowait(p_event)
                )
            except RuntimeError:
                self._event_queue.put_nowait(p_event)
                
        except Exception as ve:
            logger.error(f"EventBus validation/emit failure: {ve}")
            # Automatically route structural emit failures to the DLQ in database
            self.persist_dlq_sync(str(uuid.uuid4()), event_type, component, str(data), f"Schema validation error: {ve}")

    def subscribe(self, callback: Callable, component_filter: Optional[List[str]] = None, type_filter: Optional[List[str]] = None):
        """Subscribes an async/sync callback with optional filtering parameters."""
        self.listeners.append({
            "callback": callback,
            "components": component_filter,
            "types": type_filter
        })

    def unsubscribe(self, callback: Callable):
        self.listeners = [l for l in self.listeners if l["callback"] != callback]

    def persist_event_sync(self, event: RuntimeEvent, trace_id: str, parent_id: Optional[str]):
        """Persists the event to the system SQLite database audit log."""
        from memory.database import get_connection
        conn = get_connection()
        try:
            meta = {
                "data": event.data,
                "trace_id": trace_id,
                "parent_id": parent_id
            }
            conn.execute(
                "INSERT INTO system_audit_log (id, event, component, metadata, timestamp) VALUES (?, ?, ?, ?, ?)",
                (
                    event.id,
                    event.type,
                    event.component,
                    json.dumps(meta),
                    datetime.fromtimestamp(event.timestamp).isoformat()
                )
            )
            conn.commit()
        except Exception as e:
            logger.error(f"EventBus Persistence Failure: {e}")
        finally:
            conn.close()

    def persist_dlq_sync(self, id: str, event_type: str, component: str, metadata_str: str, error_msg: str):
        """Saves a failed event to the Dead-Letter Queue table."""
        from memory.database import get_connection
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO system_dlq (id, event, component, metadata, error, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (id, event_type, component, metadata_str, error_msg, datetime.now().isoformat())
            )
            conn.commit()
            logger.warning(f"EventBus DLQ Route Triggered: Event {event_type} registered.")
        except Exception as e:
            logger.error(f"EventBus DLQ Persistence Failure: {e}")
        finally:
            conn.close()

    def replay_events(self, limit: int = 50, component: Optional[str] = None) -> List[Dict[str, Any]]:
        """Replays historical events from system audit logs."""
        from memory.database import get_connection
        conn = get_connection()
        events = []
        try:
            query = "SELECT id, event, component, metadata, timestamp FROM system_audit_log "
            params = []
            if component:
                query += "WHERE component = ? "
                params.append(component)
            query += "ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)
            for row in cursor.fetchall():
                try:
                    meta = json.loads(row[3])
                    data = meta.get("data")
                except:
                    data = row[3]
                events.append({
                    "id": row[0],
                    "type": row[1],
                    "component": row[2],
                    "data": data,
                    "timestamp": row[4]
                })
        except Exception as e:
            logger.error(f"EventBus Replay Failure: {e}")
        finally:
            conn.close()
        return events

    async def _process_events(self):
        while self.is_active:
            try:
                p_event = await self._event_queue.get()
                event = p_event.event
                
                # Persistent logging asynchronously
                await asyncio.to_thread(self.persist_event_sync, event, p_event.trace_id, p_event.parent_id)

                # Broadcast to matching listeners
                for listener in self.listeners:
                    if listener["components"] and event.component not in listener["components"]:
                        continue
                    if listener["types"] and event.type not in listener["types"]:
                        continue
                    
                    try:
                        callback = listener["callback"]
                        # Convert event to dict style for backward-compatibility with existing consumers
                        legacy_event_dict = {
                            "id": event.id,
                            "timestamp": datetime.fromtimestamp(event.timestamp).isoformat(),
                            "component": event.component,
                            "type": event.type,
                            "data": event.data,
                            "level": event.level,
                            "priority": event.priority,
                            "trace_id": p_event.trace_id,
                            "parent_id": p_event.parent_id
                        }
                        
                        if asyncio.iscoroutinefunction(callback):
                            asyncio.create_task(callback(legacy_event_dict))
                        else:
                            callback(legacy_event_dict)
                    except Exception as le:
                        logger.error(f"EventBus consumer failure: {le}")
                        # Route failure to Dead Letter Queue asynchronously
                        await asyncio.to_thread(
                            self.persist_dlq_sync,
                            event.id,
                            event.type,
                            event.component,
                            json.dumps(event.data),
                            f"Consumer dispatch error: {str(le)}"
                        )

                self._event_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"EventBus runtime process loop failed: {e}")

# Singleton instance
event_bus = UnifiedEventBus()
