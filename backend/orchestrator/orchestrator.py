import logging
from backend.llm.ollama_client import LLMClient
from backend.orchestrator.prompt_manager import PromptManager
from backend.memory.database import save_message, get_messages, update_session_title
from backend.memory.memory_manager import memory_manager
from backend.tools.tool_orchestrator import tool_orchestrator
import time

logger = logging.getLogger("friday.orchestrator")

class Orchestrator:
    """
    The Orchestrator processes incoming messages. 
    Currently simplified to directly route to Ollama for stability.
    """
    def __init__(self):
        self.llm = LLMClient()
    
    def process_stream(self, session_id: str, user_input: str, request_id: str):
        """Minimal working chat flow: Input -> LLM -> Output (Streaming)"""
        start_time = time.time()
        logger.info(f"[REQ:{request_id}] [PHASE:1-START] Orchestrator started.")
        try:
            if not user_input or not user_input.strip():
                yield "Please provide a valid message."
                return
            
            # Step 1: Save user message and fetch past context
            logger.info(f"[REQ:{request_id}] Saving user message to DB.")
            save_message(session_id, "user", user_input)
            memory_manager.extract_and_store_memory(user_input, "user", session_id)
            
            past_msgs = get_messages(session_id)
            
            if len(past_msgs) <= 1:
                update_session_title(session_id, user_input[:30] + ("..." if len(user_input) > 30 else ""))
                
            context_lines = []
            for msg in past_msgs[-11:-1]:
                sender = "F.R.I.D.A.Y." if msg["sender"] == "friday" else "User"
                context_lines.append(f"{sender}: {msg['text']}")
            memory_context = "\n".join(context_lines) if context_lines else ""
            
            # Inject long-term semantic context
            semantic_memories = memory_manager.get_relevant_context(user_input, limit=3)
            if semantic_memories:
                logger.info(f"[REQ:{request_id}] Injecting semantic memories into prompt.")
                memory_context += "\n\n--- RELEVANT PAST KNOWLEDGE ---\n" + semantic_memories
                
            # Tool Routing
            logger.info(f"[REQ:{request_id}] [PHASE:2-TOOL_ROUTING] Checking tools.")
            tool_start_time = time.time()
            tool_results = tool_orchestrator.check_and_execute_tools(user_input, request_id)
            if tool_results:
                tool_duration = time.time() - tool_start_time
                logger.info(f"[REQ:{request_id}] Tool execution completed in {tool_duration:.2f}s.")
                memory_context += "\n\n" + tool_results
                # Send animated UI indicator to frontend
                if "Tool execution timed out." in tool_results:
                    yield f"🤖 *F.R.I.D.A.Y. executed a system action...*\n> ⚠️ Tool execution timed out.\n\n"
                else:
                    extracted_info = tool_results.split('Result:')[0].replace('--- TOOL EXECUTION RESULTS ---', '').strip()
                    yield f"🤖 *F.R.I.D.A.Y. executed a system action...*\n> {extracted_info}\n\n"
            
            system_prompt = PromptManager.get_system_prompt()
            formatted_user_prompt = PromptManager.format_user_prompt(user_input, memory_context)
            
            # Step 2: Forward to LLM
            logger.info(f"[REQ:{request_id}] [PHASE:3-LLM_STREAM] Initiating Ollama stream.")
            llm_start_time = time.time()
            full_response = ""
            for chunk in self.llm.generate_stream(prompt=formatted_user_prompt, system=system_prompt, request_id=request_id):
                full_response += chunk
                yield chunk
                
            llm_duration = time.time() - llm_start_time
            if full_response:
                logger.info(f"[REQ:{request_id}] Saving assistant message to DB.")
                save_message(session_id, "friday", full_response)
                memory_manager.extract_and_store_memory(full_response, "friday", session_id)
            
            total_duration = time.time() - start_time
            logger.info(f"[REQ:{request_id}] [PHASE:4-END] Orchestrator finished in {total_duration:.2f}s (LLM: {llm_duration:.2f}s).")
            yield "" # Flush final chunk cleanly
            
        except Exception as e:
            logger.error(f"[REQ:{request_id}] FATAL STREAM ERROR in process_stream: {e}", exc_info=True)
            yield f"\n\n❌ **System Error:** F.R.I.D.A.Y. core systems crashed during execution. `{str(e)}`"
