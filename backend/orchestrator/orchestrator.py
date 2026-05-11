import logging
from backend.llm.ollama_client import LLMClient
from backend.orchestrator.prompt_manager import PromptManager
from backend.memory.database import save_message, get_messages, update_session_title
from backend.memory.memory_manager import memory_manager
from backend.tools.tool_orchestrator import tool_orchestrator
import time
import json

logger = logging.getLogger("friday.orchestrator")

class Orchestrator:
    """
    Processes messages with explicit memory-save detection and dynamic profiles.
    """
    def __init__(self):
        self.llm = LLMClient()
    
    def process_stream(self, session_id: str, user_input: str, request_id: str, background_tasks=None):
        """Streaming chat flow with explicit memory-intent handling."""
        start_time = time.time()
        diagnostics = {}
        
        try:
            if not user_input or not user_input.strip():
                yield "Please provide a valid message."
                return
            
            # 1. Immediate DB Save
            save_message(session_id, "user", user_input)
            
            # 2. Intent Classification
            intent_start = time.time()
            intent = tool_orchestrator.get_intent(user_input)
            diagnostics["intent_ms"] = int((time.time() - intent_start) * 1000)
            
            # 3. Background Embedding (Non-blocking)
            if background_tasks:
                background_tasks.add_task(memory_manager.extract_and_store_memory, user_input, "user", session_id)
            
            # 4. Memory Retrieval & Context Assembly
            yield "[[STATUS:Searching memory...]]"
            retrieval_start = time.time()
            past_msgs = get_messages(session_id)
            
            if len(past_msgs) <= 1:
                update_session_title(session_id, user_input[:30] + ("..." if len(user_input) > 30 else ""))
                
            # Sliding window context
            window_size = 4 if intent in ["conversational", "memory_save"] else 7
            context_window = past_msgs[-(window_size+1):-1]
            memory_context = "\n".join([f"{'F.R.I.D.A.Y.' if m['sender']=='friday' else 'User'}: {m['text']}" for m in context_window])
            
            # Semantic search
            semantic_memories = memory_manager.get_relevant_context(user_input, limit=3)
            if semantic_memories:
                memory_context += "\n\n[RETRIEVED_MEMORIES]\n" + semantic_memories
            
            diagnostics["retrieval_ms"] = int((time.time() - retrieval_start) * 1000)
            
            # 5. Tool / Memory-Save Handling
            tool_results = None
            if intent == "memory_save":
                yield "[[STATUS:Saving memory...]]"
                # Memory save doesn't need external tools, but we want the LLM to acknowledge it
                logger.info(f"[REQ:{request_id}] Detected memory-save intent. Using MEMORY_CHAT profile.")
            elif intent != "conversational":
                yield "[[STATUS:Checking tools...]]"
                tool_start_time = time.time()
                tool_results = tool_orchestrator.check_and_execute_tools(user_input, request_id)
                diagnostics["tool_ms"] = int((time.time() - tool_start_time) * 1000)
                if tool_results:
                    memory_context += "\n\n[SYSTEM_ACTION]\n" + tool_results
                    extracted_info = tool_results.split('Result:')[0].replace('--- TOOL EXECUTION RESULTS ---', '').strip()
                    yield f"🤖 *Action executed...*\n> {extracted_info}\n\n"
            
            # 6. Profile & Prompt Assembly
            # If it's a memory save, we use a specific instruction to confirm it
            profile = "FAST_CHAT"
            options = {"temperature": 0.5, "num_predict": 150}
            
            system_prompt = PromptManager.get_system_prompt()
            
            if intent == "memory_save":
                profile = "MEMORY_SAVE"
                system_prompt += "\nINSTRUCTION: The user just shared a personal fact or preference. Acknowledge it briefly and confirm you've stored it."
                options = {"temperature": 0.3, "num_predict": 100}
            elif semantic_memories:
                profile = "MEMORY_CHAT"
                options = {"temperature": 0.3, "num_predict": 250}
            elif tool_results:
                profile = "TOOL_EXECUTION"
                options = {"temperature": 0.2, "num_predict": 400}
            
            logger.info(f"[REQ:{request_id}] Profile selected: {profile}")
            
            # 7. LLM Generation
            yield "[[STATUS:Thinking...]]"
            formatted_user_prompt = PromptManager.format_user_prompt(user_input, memory_context)
            
            llm_start_time = time.time()
            full_response = ""
            
            for chunk in self.llm.generate_stream(prompt=formatted_user_prompt, system=system_prompt, request_id=request_id, options=options):
                full_response += chunk
                yield chunk
                
            diagnostics["generation_ms"] = int((time.time() - llm_start_time) * 1000)
            
            # 8. Post-Processing
            if full_response:
                save_message(session_id, "friday", full_response)
                if background_tasks:
                    background_tasks.add_task(memory_manager.extract_and_store_memory, full_response, "friday", session_id)
            
            diagnostics["total_ms"] = int((time.time() - start_time) * 1000)
            yield f"\n\n[[METRICS:{json.dumps(diagnostics)}]]"
            yield ""
            
        except Exception as e:
            logger.error(f"[REQ:{request_id}] FATAL STREAM ERROR: {e}", exc_info=True)
            yield f"\n\n❌ **Core Error:** {str(e)}"
