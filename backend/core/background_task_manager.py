import asyncio
import json
import uuid
import time
import os
import psutil
from typing import Dict, Any, List, Optional, Coroutine
from datetime import datetime, timedelta
from core.event_bus import event_bus, EventPriority
from memory.database import get_connection

class BackgroundTaskManager:
    """
    Task 3: Background Task Engine
    Governs async scheduling, persistent registry recovery, heartbeat tracking,
    cancellation tokens, and long-running monitors (clipboard, browser, processes, files).
    """
    def __init__(self):
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._heartbeats: Dict[str, float] = {}
        self.is_active = False
        self._monitor_tasks: List[asyncio.Task] = []

    async def start(self):
        if self.is_active:
            return
        self.is_active = True
        
        # 1. Initialize SQLite Database Schema if missing
        self._init_db()

        # 2. Recover pending persistent tasks
        await self.recover_pending_tasks()

        # 3. Spin up long-running monitors
        self._monitor_tasks.append(asyncio.create_task(self._clipboard_observer()))
        self._monitor_tasks.append(asyncio.create_task(self._browser_observer()))
        self._monitor_tasks.append(asyncio.create_task(self._process_observer()))
        self._monitor_tasks.append(asyncio.create_task(self._heartbeat_logger()))
        
        event_bus.emit("desktop", "task_engine_started", {"timestamp": time.time()})

    async def stop(self):
        self.is_active = False
        # Cancel all observers
        for t in self._monitor_tasks:
            t.cancel()
        self._monitor_tasks.clear()

        # Cancel all active scheduled tasks
        for tid, task in list(self._active_tasks.items()):
            task.cancel()
            self._update_db_task_status(tid, "cancelled")
        self._active_tasks.clear()

    def _init_db(self):
        conn = get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS background_tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    payload TEXT,
                    status TEXT NOT NULL,
                    scheduled_at TEXT NOT NULL,
                    completed_at TEXT
                )
            """)
            conn.commit()
        except Exception as e:
            pass
        finally:
            conn.close()

    def schedule_task(self, name: str, payload: Dict[str, Any], delay_seconds: int = 0) -> str:
        """Schedules a task for persistent async execution."""
        task_id = str(uuid.uuid4())[:8]
        scheduled_time = datetime.now() + timedelta(seconds=delay_seconds)
        
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO background_tasks (id, name, payload, status, scheduled_at) VALUES (?, ?, ?, ?, ?)",
                (task_id, name, json.dumps(payload), "pending", scheduled_time.isoformat())
            )
            conn.commit()
        except Exception as e:
            pass
        finally:
            conn.close()

        # If delay is small, start task immediately
        if delay_seconds <= 0:
            self._start_async_task(task_id, name, payload)
        else:
            asyncio.create_task(self._schedule_delayed_start(task_id, name, payload, delay_seconds))

        return task_id

    async def _schedule_delayed_start(self, task_id: str, name: str, payload: Dict[str, Any], delay: int):
        await asyncio.sleep(delay)
        if self.is_active:
            self._start_async_task(task_id, name, payload)

    def _start_async_task(self, task_id: str, name: str, payload: Dict[str, Any]):
        """Creates the runtime execution coroutine for a registered task."""
        task = asyncio.create_task(self._execute_persistent_task(task_id, name, payload))
        self._active_tasks[task_id] = task
        self._heartbeats[task_id] = time.time()
        task.add_done_callback(lambda t: self._active_tasks.pop(task_id, None))

    async def _execute_persistent_task(self, task_id: str, name: str, payload: Dict[str, Any]):
        try:
            self._update_db_task_status(task_id, "processing")
            event_bus.emit("desktop", "task_started", {"task_id": task_id, "name": name})

            # Mock execution strategies based on types
            if name == "reminder":
                msg = payload.get("message", "Reminder Event Triggered")
                # Push event & OS notification
                event_bus.emit("desktop", "reminder_triggered", {"message": msg}, priority=EventPriority.HIGH)
                from core.task_manager import background_agent
                background_agent.notify("F.R.I.D.A.Y. Reminder", msg)
            elif name == "file_index":
                from desktop.file_manager import file_manager
                await asyncio.to_thread(file_manager.crawl_and_index)
            else:
                # Custom general task delay emulation
                await asyncio.sleep(2.0)

            self._update_db_task_status(task_id, "completed", datetime.now().isoformat())
            event_bus.emit("desktop", "task_completed", {"task_id": task_id, "name": name})
        except asyncio.CancelledError:
            self._update_db_task_status(task_id, "cancelled")
            event_bus.emit("desktop", "task_cancelled", {"task_id": task_id})
        except Exception as e:
            self._update_db_task_status(task_id, "failed")
            event_bus.emit("desktop", "task_failed", {"task_id": task_id, "error": str(e)}, priority=EventPriority.HIGH)

    def _update_db_task_status(self, task_id: str, status: str, completed_at: Optional[str] = None):
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE background_tasks SET status = ?, completed_at = ? WHERE id = ?",
                (status, completed_at, task_id)
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    async def recover_pending_tasks(self):
        """Phase 6: Persistence & Recovery - Re-starts incomplete or missed tasks."""
        conn = get_connection()
        tasks = []
        try:
            cursor = conn.execute(
                "SELECT id, name, payload FROM background_tasks WHERE status = 'pending' OR status = 'processing'"
            )
            for row in cursor.fetchall():
                try:
                    payload = json.loads(row[2])
                except:
                    payload = {}
                tasks.append((row[0], row[1], payload))
        except Exception:
            pass
        finally:
            conn.close()

        for tid, name, payload in tasks:
            self._start_async_task(tid, name, payload)

    def cancel_task(self, task_id: str) -> bool:
        if task_id in self._active_tasks:
            self._active_tasks[task_id].cancel()
            return True
        return False

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        return [
            {
                "task_id": tid,
                "uptime": int(time.time() - self._heartbeats.get(tid, time.time()))
            }
            for tid in self._active_tasks.keys()
        ]

    # Observers
    async def _clipboard_observer(self):
        """Listens to context engine clipboard changes and triggers proactive indexing/flows."""
        from core.context_engine import context_engine
        last_clip = ""
        while self.is_active:
            try:
                clip = context_engine.current_clipboard
                if clip and clip != last_clip:
                    last_clip = clip
                    event_bus.emit(
                        component="context_engine",
                        event_type="clipboard_updated",
                        data={"length": len(clip), "preview": clip[:150]},
                        priority=EventPriority.NORMAL
                    )
            except Exception:
                pass
            await asyncio.sleep(1.0)

    async def _browser_observer(self):
        """Listens to browser window changes in context engine and broadcasts context."""
        from core.context_engine import context_engine
        last_domain = ""
        while self.is_active:
            try:
                b_ctx = context_engine.get_browser_context()
                if b_ctx["is_browser_active"] and b_ctx["detected_domain"] != last_domain:
                    last_domain = b_ctx["detected_domain"]
                    event_bus.emit(
                        component="context_engine",
                        event_type="browser_navigated",
                        data=b_ctx,
                        priority=EventPriority.NORMAL
                    )
            except Exception:
                pass
            await asyncio.sleep(2.0)

    async def _process_observer(self):
        """Scans for CPU-heavy processes and triggers alarms if resources exceed thresholds."""
        while self.is_active:
            try:
                cpu_percent = psutil.cpu_percent()
                if cpu_percent > 85.0:
                    event_bus.emit(
                        component="desktop",
                        event_type="high_cpu_detected",
                        data={"cpu_percentage": cpu_percent},
                        priority=EventPriority.HIGH
                    )
            except Exception:
                pass
            await asyncio.sleep(5.0)

    async def _heartbeat_logger(self):
        """Logs engine heartbeat to EventBus periodically."""
        while self.is_active:
            for tid in list(self._active_tasks.keys()):
                self._heartbeats[tid] = time.time()
            event_bus.emit("desktop", "task_heartbeat", {"active_tasks_count": len(self._active_tasks)})
            await asyncio.sleep(10.0)

# Singleton instance
background_task_manager = BackgroundTaskManager()
