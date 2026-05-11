import json
import asyncio
import time
from backend.llm.ollama_client import LLMClient
from backend.orchestrator.prompt_manager import PromptManager
from backend.memory.database import save_message, get_messages, update_session_title
from backend.memory.memory_manager import memory_manager
from backend.tools.tool_orchestrator import tool_orchestrator
from backend.config.settings import settings
from backend.core.logger import get_logger
from backend.core.task_manager import task_manager
from backend.core.model_manager import model_manager

logger = get_logger("orchestrator")

class Orchestrator:
    """Production-grade orchestrator with concurrency control and performance metrics."""
    
    _locks = {}
    _last_access = {}

    def __init__(self):
        self.llm = LLMClient()
    
    async def _cleanup_locks(self):
        """Prunes inactive session locks to prevent memory leaks."""
        now = time.time()
        to_delete = [sid for sid, last in self._last_access.items() if now - last > 3600]
        for sid in to_delete:
            self._locks.pop(sid, None)
            self._last_access.pop(sid, None)

    async def process_stream(self, session_id: str, user_input: str, request_id: str, background_tasks=None):
        """Unified streaming pipeline with per-session locking and async execution."""
        
        # 0. Acquire Lock
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()
        self._last_access[session_id] = time.time()

        if len(self._locks) > 100:
            asyncio.create_task(self._cleanup_locks())
        
        if self._locks[session_id].locked():
            logger.warning(f"[REQ:{request_id}] Session {session_id} is busy.")
            yield "⚠️ **System Busy:** Please wait for my previous response to finish."
            return

        async with self._locks[session_id]:
            start_time = time.time()
            metrics = {"request_id": request_id}
            
            try:
                # 1. Model Health Check
                if not await model_manager.ensure_model(settings.MODEL_NAME):
                    logger.warning(f"[REQ:{request_id}] Model {settings.MODEL_NAME} might not be loaded. Triggering check.")

                # 2. State Setup (Save user msg early)
                await task_manager.run_task(f"save_user_msg_{request_id}", asyncio.to_thread(save_message, session_id, "user", user_input))
                
                # 3. Intent Classification
                intent_start = time.time()
                intent = tool_orchestrator.get_intent(user_input)
                metrics["intent_ms"] = int((time.time() - intent_start) * 1000)
                
                # 4. Context Retrieval (Lightweight Mode Check)
                yield "[[STATUS:Searching memory...]]"
                retrieval_start = time.time()
                past_msgs = await asyncio.to_thread(get_messages, session_id)
                
                # Dynamic context window based on RAM
                window_size = settings.CONTEXT_WINDOW_SIZE
                retrieval_limit = 3
                
                if model_manager.is_ram_under_pressure():
                    logger.warning(f"[REQ:{request_id}] RAM pressure detected. Scaling down context.")
                    window_size = max(4, window_size // 2)
                    retrieval_limit = 1
                    yield "[[STATUS:Lightweight mode active...]]"
                
                recent_context = "\n".join([f"{'Assistant' if m['sender']=='friday' else 'User'}: {m['text']}" for m in past_msgs[-window_size:]])
                
                semantic_context = await memory_manager.get_relevant_context(user_input, limit=retrieval_limit)
                combined_context = f"{recent_context}\n{semantic_context}".strip()
                metrics["retrieval_ms"] = int((time.time() - retrieval_start) * 1000)
                
                # 5. Tool Execution
                tool_results = None
                if intent in ["tool_execution", "routing_needed"]:
                    yield "[[STATUS:Checking tools...]]"
                    tool_start = time.time()
                    tool_results = await tool_orchestrator.check_and_execute_tools(user_input, request_id)
                    metrics["tool_ms"] = int((time.time() - tool_start) * 1000)
                    if tool_results:
                        combined_context += f"\n\n[TOOL_RESULT]\n{tool_results}"
                        yield f"🤖 *Executing system tool...*\n\n"

                # 6. Generation Setup
                yield "[[STATUS:Thinking...]]"
                system_prompt = PromptManager.get_system_prompt(intent)
                final_prompt = PromptManager.format_user_prompt(user_input, combined_context)
                
                options = {"temperature": 0.6, "num_predict": 256}
                if intent == "memory_save":
                    options["temperature"] = 0.3
                
                # 7. Token Streaming
                llm_start = time.time()
                full_response = ""
                async for token in self.llm.generate_stream(final_prompt, system_prompt, request_id, options):
                    full_response += token
                    yield token
                
                metrics["generation_ms"] = int((time.time() - llm_start) * 1000)
                
                # 8. Post-Processing (Background)
                # Using task_manager for robust background execution
                await task_manager.run_task(f"save_friday_msg_{request_id}", asyncio.to_thread(save_message, session_id, "friday", full_response))
                await task_manager.run_task(f"store_user_mem_{request_id}", memory_manager.extract_and_store_memory(user_input, "user", session_id))
                await task_manager.run_task(f"store_friday_mem_{request_id}", memory_manager.extract_and_store_memory(full_response, "friday", session_id))
                
                if len(past_msgs) > 0 and (len(past_msgs) + 1) % 10 == 0:
                    logger.info(f"[REQ:{request_id}] Triggering background session summarization.")
                    # Pass the messages properly
                    current_msgs = past_msgs + [{"sender": "user", "text": user_input}, {"sender": "friday", "text": full_response}]
                    await task_manager.run_task(f"summarize_{session_id}", memory_manager.summarize_session(session_id, current_msgs))
                
                if len(past_msgs) <= 1:
                    await task_manager.run_task(f"update_title_{session_id}", asyncio.to_thread(update_session_title, session_id, user_input[:30]))

                metrics["total_ms"] = int((time.time() - start_time) * 1000)
                logger.info(f"[REQ:{request_id}] Completed in {metrics['total_ms']}ms. Intent: {intent}")
                yield f"\n\n[[METRICS:{json.dumps(metrics)}]]"
                
            except GeneratorExit:
                logger.warning(f"[REQ:{request_id}] Client disconnected. Cancelling stream.")
                # We still want to save what we have if it's significant
                if len(full_response) > 10:
                    await task_manager.run_task(f"save_friday_msg_partial_{request_id}", asyncio.to_thread(save_message, session_id, "friday", full_response + "... [Interrupted]"))
                raise
            except Exception as e:
                logger.error(f"[REQ:{request_id}] Orchestration crash: {e}", exc_info=True)
                yield f"\n\n❌ **Orchestrator Error:** {str(e)}"

friday_orchestrator = Orchestrator()
