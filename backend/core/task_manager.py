import asyncio
import uuid
import time
from typing import Dict, Any, Callable, Coroutine
from core.logger import get_logger

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

    async def start(self):
        if self.is_running: return
        self.is_running = True
        self._loop_task = asyncio.create_task(self._agent_loop())
        logger.info("BackgroundAgent Runtime: STARTED")

    async def stop(self):
        self.is_running = False
        if self._loop_task:
            self._loop_task.cancel()
        logger.info("BackgroundAgent Runtime: STOPPED")

    async def _agent_loop(self):
        while self.is_running:
            try:
                # Proactive objectives: 1. Monitor active tasks, 2. Check for reminders, 3. Idle processing
                await self._check_task_health()
                await asyncio.sleep(60) # Run every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Agent loop error: {e}")
                await asyncio.sleep(10)

    async def _check_task_health(self):
        diag = self.manager.get_diagnostics()
        if diag["active_count"] > 10:
            logger.warning(f"High task load detected: {diag['active_count']} tasks active.")

# Global instances
task_manager = TaskManager()
background_agent = BackgroundAgent(task_manager)

