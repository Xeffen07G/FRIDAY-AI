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
    The Orchestrator processes incoming messages. 
    Optimized for speed with background embeddings and memory windows.
    """
    def __init__(self):
        self.llm = LLMClient()
    
    def process_stream(self, session_id: str, user_input: str, request_id: str, background_tasks=None):
        """Streaming chat flow with performance metrics and status updates."""
        start_time = time.time()
        logger.info(f"[REQ:{request_id}] [PHASE:1-START] Orchestrator started.")
        
        try:
            if not user_input or not user_input.strip():
                yield "Please provide a valid message."
                return
            
            # 1. Immediate DB Save
            save_message(session_id, "user", user_input)
            
            # 2. Background Embedding Storage
            if background_tasks:
                background_tasks.add_task(memory_manager.extract_and_store_memory, user_input, "user", session_id)
            
            # 3. Short-term Memory Window (Last 6 messages)
            yield "[[STATUS:Searching memory...]]"
            retrieval_start = time.time()
            past_msgs = get_messages(session_id)
            
            if len(past_msgs) <= 1:
                update_session_title(session_id, user_input[:30] + ("..." if len(user_input) > 30 else ""))
                
            # Direct context window (Last 6)
            context_window = past_msgs[-7:-1] # Exclude current message
            context_lines = []
            for msg in context_window:
                sender = "F.R.I.D.A.Y." if msg["sender"] == "friday" else "User"
                context_lines.append(f"{sender}: {msg['text']}")
            memory_context = "\n".join(context_lines) if context_lines else ""
            
            # 4. Conditional Semantic Memory Retrieval
            semantic_memories = memory_manager.get_relevant_context(user_input, limit=3)
            if semantic_memories:
                logger.info(f"[REQ:{request_id}] Injecting semantic memories.")
                memory_context += "\n\n--- RELEVANT PAST KNOWLEDGE ---\n" + semantic_memories
            
            retrieval_duration = time.time() - retrieval_start
            
            # 5. Tool Routing
            yield "[[STATUS:Checking tools...]]"
            tool_start_time = time.time()
            tool_results = tool_orchestrator.check_and_execute_tools(user_input, request_id)
            tool_duration = time.time() - tool_start_time
            
            if tool_results:
                memory_context += "\n\n" + tool_results
                extracted_info = tool_results.split('Result:')[0].replace('--- TOOL EXECUTION RESULTS ---', '').strip()
                yield f"🤖 *F.R.I.D.A.Y. executed a system action...*\n> {extracted_info}\n\n"
            
            # 6. LLM Generation
            yield "[[STATUS:Thinking...]]"
            system_prompt = PromptManager.get_system_prompt()
            formatted_user_prompt = PromptManager.format_user_prompt(user_input, memory_context)
            
            logger.info(f"[REQ:{request_id}] [PHASE:3-LLM_STREAM] Initiating Ollama stream.")
            llm_start_time = time.time()
            full_response = ""
            
            for chunk in self.llm.generate_stream(prompt=formatted_user_prompt, system=system_prompt, request_id=request_id):
                full_response += chunk
                yield chunk
                
            llm_duration = time.time() - llm_start_time
            
            # 7. Post-Processing (Background)
            if full_response:
                save_message(session_id, "friday", full_response)
                if background_tasks:
                    background_tasks.add_task(memory_manager.extract_and_store_memory, full_response, "friday", session_id)
            
            total_duration = time.time() - start_time
            metrics = {
                "retrieval_ms": int(retrieval_duration * 1000),
                "tool_ms": int(tool_duration * 1000),
                "generation_ms": int(llm_duration * 1000),
                "total_ms": int(total_duration * 1000)
            }
            logger.info(f"[REQ:{request_id}] Metrics: {json.dumps(metrics)}")
            yield f"\n\n[[METRICS:{json.dumps(metrics)}]]"
            yield "" # Final flush
            
        except Exception as e:
            logger.error(f"[REQ:{request_id}] FATAL STREAM ERROR: {e}", exc_info=True)
            yield f"\n\n❌ **System Error:** F.R.I.D.A.Y. core systems crashed. `{str(e)}`"
