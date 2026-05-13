import asyncio
import uuid
import time
import os
import sqlite3
import json
from typing import Dict, Any, Callable, Coroutine
from core.logger import get_logger
from memory.database import get_connection
from datetime import datetime
import psutil

try:
    from plyer import notification
except ImportError:
    notification = None

logger = get_logger("core.task_manager")

class TaskManager:
    """Centralized manager for async tasks with timeout and cancellation support."""
    
    def __init__(self):
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._task_metadata: Dict[str, Dict[str, Any]] = {}

    async def run_task(self, name: str, coro: Coroutine, timeout: float = 30.0) -> str:
        """Runs a task with a timeout and tracks its lifecycle."""
        task_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Wrap the coroutine with a timeout
        wrapped_coro = asyncio.wait_for(coro, timeout=timeout)
        task = asyncio.create_task(wrapped_coro)
        
        self._active_tasks[task_id] = task
        self._task_metadata[task_id] = {
            "name": name,
            "start_time": start_time,
            "status": "running"
        }
        
        logger.info(f"[TASK:{task_id}] Started: {name}")
        
        # Register completion callback
        task.add_done_callback(lambda t: self._cleanup_task(task_id))
        
        return task_id

    def _cleanup_task(self, task_id: str):
        """Removes task from tracking and logs results."""
        if task_id in self._active_tasks:
            task = self._active_tasks.pop(task_id)
            meta = self._task_metadata.get(task_id, {})
            duration = time.time() - meta.get("start_time", 0)
            
            try:
                if task.cancelled():
                    logger.warning(f"[TASK:{task_id}] Cancelled after {duration:.2f}s")
                elif task.exception():
                    logger.error(f"[TASK:{task_id}] Failed after {duration:.2f}s: {task.exception()}")
                else:
                    logger.info(f"[TASK:{task_id}] Completed in {duration:.2f}s")
            except Exception as e:
                logger.error(f"[TASK:{task_id}] Error during cleanup: {e}")
            
            # Keep metadata for a short while for diagnostics, then prune
            meta["status"] = "finished"
            meta["duration"] = duration

    def cancel_task(self, task_id: str):
        """Cancels a specific running task."""
        if task_id in self._active_tasks:
            self._active_tasks[task_id].cancel()
            logger.info(f"[TASK:{task_id}] Cancellation requested")
            return True
        return False

    def get_diagnostics(self):
        """Returns statistics on active and recently finished tasks."""
        return {
            "active_count": len(self._active_tasks),
            "tasks": [
                {
                    "id": tid, 
                    "name": meta["name"], 
                    "age": time.time() - meta["start_time"],
                    "status": meta["status"]
                }
                for tid, meta in self._task_metadata.items()
                if meta["status"] == "running" or time.time() - meta["start_time"] < 60
            ]
        }

class BackgroundAgent:
    """Persistent agent runtime for background objectives and proactive checks."""
    def __init__(self, manager: TaskManager):
        self.manager = manager
        self.is_running = False
        self._loop_task: asyncio.Task = None
        self.proactive_queue = asyncio.Queue()
        self.last_heartbeat = time.time()

    async def start(self):
        if self.is_running: return
        self.is_running = True
        self._loop_task = asyncio.create_task(self._agent_loop())
        logger.info("BackgroundAgent Runtime: STARTED")
        self.notify("System Online", "F.R.I.D.A.Y. Desktop Agent is now active.")

    async def stop(self):
        self.is_running = False
        if self._loop_task:
            self._loop_task.cancel()
        logger.info("BackgroundAgent Runtime: STOPPED")

    def notify(self, title: str, message: str):
        """Dispatches a system notification."""
        logger.info(f"[NOTIFY] {title}: {message}")
        if notification:
            try:
                notification.notify(
                    title=f"F.R.I.D.A.Y. - {title}",
                    message=message,
                    app_name="FRIDAY AI",
                    timeout=5
                )
            except Exception as e:
                logger.error(f"Notification failed: {e}")

    async def _agent_loop(self):
        while self.is_running:
            try:
                self.last_heartbeat = time.time()
                # 1. Monitor active tasks
                await self._check_task_health()
                
                # 2. Process background queue (reminders, scheduled tasks)
                await self._recover_and_process_tasks()
                
                # 3. Idle processing: File Manager index sweep & Watcher Health
                from desktop.file_manager import file_manager
                # Phase 3: Developer Context Awareness
                from desktop.workflow_manager import workflow_manager
                dev_ctx = workflow_manager.get_dev_context()
                if dev_ctx.get("projects"):
                    from core.event_bus import event_bus
                    event_bus.emit("desktop", "dev_context", dev_ctx)
                
                if not file_manager._is_active:
                    file_manager.start()
                else:
                    # Phase 5: Resource Optimization - Throttle if high CPU
                    cpu_usage = psutil.cpu_percent()
                    if cpu_usage < 70:
                        file_manager.check_health()
                        self._cleanup_stale_watchers(file_manager)
                    else:
                        logger.debug("System load HIGH. Throttling background indexing.")
                
                await asyncio.sleep(30) # Run cycle every 30s
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Agent loop error: {e}")
                await asyncio.sleep(10)

    async def _check_task_health(self):
        diag = self.manager.get_diagnostics()
        if diag["active_count"] > 10:
            logger.warning(f"High task load detected: {diag['active_count']} tasks active.")

    def _cleanup_stale_watchers(self, fm):
        """Removes paths that no longer exist from the observer."""
        for path in list(fm.watched_paths):
            if not os.path.exists(path):
                logger.warning(f"Removing stale watcher for missing path: {path}")
                fm.watched_paths.remove(path)
                # Note: Actual watchdog unschedule is complex, we just stop tracking it
                # and it will be ignored in future crawls.

    async def _recover_and_process_tasks(self):
        """Phase 6: Persistence & Recovery - Hydrates tasks from SQLite."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM background_tasks WHERE status = 'pending' AND scheduled_at <= ?", (datetime.now().isoformat(),))
            tasks = cursor.fetchall()
            
            for t in tasks:
                logger.info(f"Recovering persistent task: {t['name']} ({t['id']})")
                # Mark as processing
                cursor.execute("UPDATE background_tasks SET status = 'processing' WHERE id = ?", (t['id'],))
                conn.commit()
                
                # Schedule in task manager
                if t['name'] == "reminder":
                    self.notify("F.R.I.D.A.Y. Reminder", t['payload'])
                    self.audit_log("REMINDER_PUSHED", "background_agent", {"message": t['payload']})
                
                await asyncio.sleep(0.1)
                cursor.execute("UPDATE background_tasks SET status = 'completed', completed_at = ? WHERE id = ?", (datetime.now().isoformat(), t['id']))
                conn.commit()
        except Exception as e:
            logger.error(f"Task recovery failed: {e}")
        finally:
            conn.close()

    def audit_log(self, event: str, component: str, metadata: dict = None):
        """Writes a verifiable audit record to the database."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO system_audit_log (id, event, component, metadata, timestamp) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4())[:8], event, component, json.dumps(metadata or {}), datetime.now().isoformat())
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Audit logging failed: {e}")
        finally:
            conn.close()

    def setup_autostart(self, enabled: bool = True):
        """Configures Windows startup-on-boot via Registry."""
        import sys
        import winreg
        
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "FRIDAY_Assistant"
        # Assuming we want to run the python interpreter with the main.py
        # In a real build, this would be the .exe path
        executable = sys.executable
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
        cmd = f'"{executable}" "{script_path}" --silent'
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
                logger.info(f"Autostart ENABLED: {cmd}")
            else:
                try: winreg.DeleteValue(key, app_name)
                except FileNotFoundError: pass
            winreg.CloseKey(key)
            return True
        except Exception as e:
            logger.error(f"Autostart config failed: {e}")
            return False

# Global instances
task_manager = TaskManager()
background_agent = BackgroundAgent(task_manager)

