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

logger = get_logger("orchestrator")

class Orchestrator:
    """Production-grade orchestrator with concurrency control and performance metrics."""
    
    # Session locks to prevent concurrent prompts for the same user
    _locks = {}

    def __init__(self):
        self.llm = LLMClient()
    
    async def process_stream(self, session_id: str, user_input: str, request_id: str, background_tasks=None):
        """Unified streaming pipeline with per-session locking and async execution."""
        
        # 0. Acquire Lock
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()
        
        if self._locks[session_id].locked():
            logger.warning(f"[REQ:{request_id}] Session {session_id} is busy.")
            yield "⚠️ **System Busy:** Please wait for my previous response to finish."
            return

        async with self._locks[session_id]:
            start_time = time.time()
            metrics = {"request_id": request_id}
            
            try:
                # 1. State Setup (Sync DB call is fast, but we keep it for now)
                save_message(session_id, "user", user_input)
                
                # 2. Intent Classification
                intent_start = time.time()
                intent = tool_orchestrator.get_intent(user_input)
                metrics["intent_ms"] = int((time.time() - intent_start) * 1000)
                
                # 3. Context Retrieval
                yield "[[STATUS:Searching memory...]]"
                retrieval_start = time.time()
                past_msgs = get_messages(session_id)
                
                # Context window size from settings
                window_size = settings.CONTEXT_WINDOW_SIZE
                recent_context = "\n".join([f"{'Assistant' if m['sender']=='friday' else 'User'}: {m['text']}" for m in past_msgs[-window_size:]])
                
                semantic_context = memory_manager.get_relevant_context(user_input)
                combined_context = f"{recent_context}\n{semantic_context}".strip()
                metrics["retrieval_ms"] = int((time.time() - retrieval_start) * 1000)
                
                # 4. Tool Execution
                tool_results = None
                if intent in ["tool_execution", "routing_needed"]:
                    yield "[[STATUS:Checking tools...]]"
                    tool_start = time.time()
                    # Await the async tool check
                    tool_results = await tool_orchestrator.check_and_execute_tools(user_input, request_id)
                    metrics["tool_ms"] = int((time.time() - tool_start) * 1000)
                    if tool_results:
                        combined_context += f"\n\n[TOOL_RESULT]\n{tool_results}"
                        yield f"🤖 *Executing system tool...*\n\n"

                # 5. Generation Setup
                yield "[[STATUS:Thinking...]]"
                system_prompt = PromptManager.get_system_prompt(intent)
                final_prompt = PromptManager.format_user_prompt(user_input, combined_context)
                
                # Dynamic options
                options = {"temperature": 0.6, "num_predict": 256}
                if intent == "memory_save":
                    options["temperature"] = 0.3
                
                # 6. Token Streaming
                llm_start = time.time()
                full_response = ""
                # Await the async generator
                async for token in self.llm.generate_stream(final_prompt, system_prompt, request_id, options):
                    full_response += token
                    yield token
                
                metrics["generation_ms"] = int((time.time() - llm_start) * 1000)
                
                # 7. Post-Processing (Background)
                if background_tasks:
                    background_tasks.add_task(save_message, session_id, "friday", full_response)
                    background_tasks.add_task(memory_manager.extract_and_store_memory, user_input, "user", session_id)
                    background_tasks.add_task(memory_manager.extract_and_store_memory, full_response, "friday", session_id)
                    if len(past_msgs) <= 1:
                        background_tasks.add_task(update_session_title, session_id, user_input[:30])

                metrics["total_ms"] = int((time.time() - start_time) * 1000)
                logger.info(f"[REQ:{request_id}] Completed in {metrics['total_ms']}ms. Intent: {intent}")
                yield f"\n\n[[METRICS:{json.dumps(metrics)}]]"
                
            except Exception as e:
                logger.error(f"[REQ:{request_id}] Orchestration crash: {e}", exc_info=True)
                yield f"\n\n❌ **Orchestrator Error:** {str(e)}"

# Singleton for reuse
friday_orchestrator = Orchestrator()
