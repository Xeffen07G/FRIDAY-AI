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
    Processes incoming messages with dynamic generation profiles and memory grounding.
    """
    def __init__(self):
        self.llm = LLMClient()
    
    def process_stream(self, session_id: str, user_input: str, request_id: str, background_tasks=None):
        """Streaming chat flow with latency-optimized profiles."""
        start_time = time.time()
        diagnostics = {}
        
        try:
            if not user_input or not user_input.strip():
                yield "Please provide a valid message."
                return
            
            # 1. Immediate DB Save
            save_message(session_id, "user", user_input)
            
            # 2. Intent Classification (Ultra Fast)
            intent_start = time.time()
            intent = tool_orchestrator.get_intent(user_input)
            diagnostics["intent_ms"] = int((time.time() - intent_start) * 1000)
            
            # 3. Background Embedding (Non-blocking)
            if background_tasks:
                background_tasks.add_task(memory_manager.extract_and_store_memory, user_input, "user", session_id)
            
            # 4. Memory Retrieval (Conditional)
            yield "[[STATUS:Searching memory...]]"
            retrieval_start = time.time()
            past_msgs = get_messages(session_id)
            
            if len(past_msgs) <= 1:
                update_session_title(session_id, user_input[:30] + ("..." if len(user_input) > 30 else ""))
                
            # Direct context window (Last 4 for FAST_CHAT, Last 8 for deep)
            window_size = 4 if intent == "conversational" else 7
            context_window = past_msgs[-(window_size+1):-1]
            memory_context = "\n".join([f"{'F.R.I.D.A.Y.' if m['sender']=='friday' else 'User'}: {m['text']}" for m in context_window])
            
            # Semantic search
            semantic_memories = memory_manager.get_relevant_context(user_input, limit=3)
            if semantic_memories:
                memory_context += "\n\n[MEMORIES]\n" + semantic_memories
            
            diagnostics["retrieval_ms"] = int((time.time() - retrieval_start) * 1000)
            
            # 5. Tool Routing (Capped)
            tool_results = None
            tool_duration = 0
            if intent != "conversational":
                yield "[[STATUS:Checking tools...]]"
                tool_start_time = time.time()
                tool_results = tool_orchestrator.check_and_execute_tools(user_input, request_id)
                tool_duration = int((time.time() - tool_start_time) * 1000)
                if tool_results:
                    memory_context += "\n\n[SYSTEM_ACTION]\n" + tool_results
                    extracted_info = tool_results.split('Result:')[0].replace('--- TOOL EXECUTION RESULTS ---', '').strip()
                    yield f"🤖 *Action executed...*\n> {extracted_info}\n\n"
            
            diagnostics["tool_ms"] = tool_duration
            
            # 6. Profile Selection
            # Profiles: FAST_CHAT, MEMORY_CHAT, TOOL_EXECUTION
            profile = "FAST_CHAT"
            options = {"temperature": 0.5, "num_predict": 150} # Default fast
            
            if semantic_memories:
                profile = "MEMORY_CHAT"
                options = {"temperature": 0.3, "num_predict": 256} # More precise
            if tool_results:
                profile = "TOOL_EXECUTION"
                options = {"temperature": 0.2, "num_predict": 512} # Detailed
            
            logger.info(f"[REQ:{request_id}] Profile selected: {profile}")
            
            # 7. LLM Generation
            yield "[[STATUS:Thinking...]]"
            system_prompt = PromptManager.get_system_prompt()
            
            # Assembly time
            assembly_start = time.time()
            formatted_user_prompt = PromptManager.format_user_prompt(user_input, memory_context)
            diagnostics["assembly_ms"] = int((time.time() - assembly_start) * 1000)
            
            llm_start_time = time.time()
            full_response = ""
            
            for chunk in self.llm.generate_stream(prompt=formatted_user_prompt, system=system_prompt, request_id=request_id, options=options):
                full_response += chunk
                yield chunk
                
            diagnostics["generation_ms"] = int((time.time() - llm_start_time) * 1000)
            
            # 8. Post-Processing (Background)
            if full_response:
                save_message(session_id, "friday", full_response)
                if background_tasks:
                    background_tasks.add_task(memory_manager.extract_and_store_memory, full_response, "friday", session_id)
            
            diagnostics["total_ms"] = int((time.time() - start_time) * 1000)
            logger.info(f"[REQ:{request_id}] Full Diagnostics: {json.dumps(diagnostics)}")
            
            yield f"\n\n[[METRICS:{json.dumps(diagnostics)}]]"
            yield ""
            
        except Exception as e:
            logger.error(f"[REQ:{request_id}] FATAL STREAM ERROR: {e}", exc_info=True)
            yield f"\n\n❌ **Core Error:** {str(e)}"
