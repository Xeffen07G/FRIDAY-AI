import logging
import time
import json
from backend.llm.ollama_client import LLMClient
from backend.orchestrator.prompt_manager import PromptManager
from backend.memory.database import save_message, get_messages, update_session_title
from backend.memory.memory_manager import memory_manager
from backend.tools.tool_orchestrator import tool_orchestrator

logger = logging.getLogger("friday.orchestrator")

class Orchestrator:
    """Lightweight orchestrator for local-first AI interactions."""
    
    def __init__(self):
        self.llm = LLMClient()
    
    def process_stream(self, session_id: str, user_input: str, request_id: str, background_tasks=None):
        """Unified streaming pipeline optimized for latency and grounding."""
        start_time = time.time()
        metrics = {"request_id": request_id}
        
        try:
            # 1. State Setup
            save_message(session_id, "user", user_input)
            
            # 2. Intent Classification (Bypass logic)
            intent_start = time.time()
            intent = tool_orchestrator.get_intent(user_input)
            metrics["intent_ms"] = int((time.time() - intent_start) * 1000)
            
            # 3. Memory & Context
            yield "[[STATUS:Searching memory...]]"
            retrieval_start = time.time()
            past_msgs = get_messages(session_id)
            
            # Context window management
            window_size = 4 if intent in ["conversational", "memory_save"] else 6
            recent_context = "\n".join([f"{'Assistant' if m['sender']=='friday' else 'User'}: {m['text']}" for m in past_msgs[-window_size:]])
            
            # Semantic RAG
            semantic_context = memory_manager.get_relevant_context(user_input)
            combined_context = f"{recent_context}\n{semantic_context}".strip()
            metrics["retrieval_ms"] = int((time.time() - retrieval_start) * 1000)
            
            # 4. Tool Execution
            tool_results = None
            if intent == "tool_execution" or intent == "routing_needed":
                yield "[[STATUS:Checking tools...]]"
                tool_start = time.time()
                tool_results = tool_orchestrator.check_and_execute_tools(user_input, request_id)
                metrics["tool_ms"] = int((time.time() - tool_start) * 1000)
                if tool_results:
                    combined_context += f"\n\n[TOOL_RESULT]\n{tool_results}"
                    yield f"🤖 *Executing tool...*\n\n"

            # 5. Dynamic Profile Selection
            # Optimized for phi3:mini
            if intent == "conversational":
                options = {"temperature": 0.6, "num_predict": 128}
            elif intent == "memory_save":
                options = {"temperature": 0.3, "num_predict": 100}
            else:
                options = {"temperature": 0.2, "num_predict": 512}
            
            # 6. Stream Generation
            yield "[[STATUS:Thinking...]]"
            system_prompt = PromptManager.get_system_prompt(intent)
            final_prompt = PromptManager.format_user_prompt(user_input, combined_context)
            
            llm_start = time.time()
            full_response = ""
            for token in self.llm.generate_stream(final_prompt, system_prompt, request_id, options):
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
            yield f"\n\n[[METRICS:{json.dumps(metrics)}]]"
            
        except Exception as e:
            logger.error(f"[REQ:{request_id}] Orchestration failed: {e}", exc_info=True)
            yield f"\n\n❌ **System Error:** {str(e)}"
