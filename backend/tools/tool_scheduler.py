import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from core.task_manager import task_manager

logger = logging.getLogger("friday.tools.scheduler")

class ToolScheduler:
    """Orchestrates parallel and prioritized tool execution with cancellation support."""
    
    def __init__(self):
        self.running_tools: Dict[str, asyncio.Task] = {}
        self.priority_queue = asyncio.PriorityQueue()
        self._loop_task = None
        self.is_active = False

    async def start(self):
        if self.is_active: return
        self.is_active = True
        self._loop_task = asyncio.create_task(self._scheduler_loop())
        logger.info("ToolScheduler: ACTIVE")

    async def stop(self):
        self.is_active = False
        if self._loop_task:
            self._loop_task.cancel()
        # Cancel all running tools
        for task_id in list(self.running_tools.keys()):
            self.cancel_tool(task_id)
        logger.info("ToolScheduler: STOPPED")

    async def schedule_tool(self, tool_id: str, tool_func, kwargs: dict, priority: int = 10) -> asyncio.Future:
        """Schedules a tool for execution with a given priority (lower is higher)."""
        future = asyncio.Future()
        await self.priority_queue.put((priority, tool_id, tool_func, kwargs, future))
        return future

    async def _scheduler_loop(self):
        while self.is_active:
            try:
                # Get next tool from priority queue
                priority, tool_id, tool_func, kwargs, future = await self.priority_queue.get()
                
                # Execute in background task
                task = asyncio.create_task(self._execute_tool_task(tool_id, tool_func, kwargs, future))
                self.running_tools[tool_id] = task
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(1)

    async def _execute_tool_task(self, tool_id: str, tool_func, kwargs: dict, future: asyncio.Future):
        start_time = time.time()
        try:
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**kwargs)
            else:
                result = await asyncio.to_thread(tool_func, **kwargs)
            
            if not future.done():
                future.set_result(result)
        except Exception as e:
            logger.error(f"Tool {tool_id} failed: {e}")
            if not future.done():
                future.set_exception(e)
        finally:
            self.running_tools.pop(tool_id, None)
            duration = time.time() - start_time
            logger.debug(f"Tool {tool_id} completed in {duration:.2f}s")

    def cancel_tool(self, tool_id: str):
        """Interrupts and terminates a running tool."""
        if tool_id in self.running_tools:
            self.running_tools[tool_id].cancel()
            logger.info(f"Tool {tool_id}: INTERRUPTED and cancelled.")
            return True
        return False

tool_scheduler = ToolScheduler()
