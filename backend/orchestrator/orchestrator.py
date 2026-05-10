import logging
from backend.llm.ollama_client import LLMClient
from backend.orchestrator.prompt_manager import PromptManager
from backend.memory.database import save_message, get_messages, update_session_title

logger = logging.getLogger("friday.orchestrator")

class Orchestrator:
    """
    The Orchestrator processes incoming messages. 
    Currently simplified to directly route to Ollama for stability.
    """
    def __init__(self):
        self.llm = LLMClient()
    
    def process_stream(self, session_id: str, user_input: str):
        """Minimal working chat flow: Input -> LLM -> Output (Streaming)"""
        if not user_input or not user_input.strip():
            yield "Please provide a valid message."
            return
            
        logger.info(f"Orchestrator processing new message (streaming) for session {session_id}.")
        
        # Step 1: Save user message and fetch past context
        save_message(session_id, "user", user_input)
        past_msgs = get_messages(session_id)
        
        if len(past_msgs) <= 1:
            update_session_title(session_id, user_input[:30] + ("..." if len(user_input) > 30 else ""))
            
        context_lines = []
        for msg in past_msgs[-11:-1]:
            sender = "F.R.I.D.A.Y." if msg["sender"] == "friday" else "User"
            context_lines.append(f"{sender}: {msg['text']}")
        memory_context = "\n".join(context_lines) if context_lines else ""
        
        system_prompt = PromptManager.get_system_prompt()
        formatted_user_prompt = PromptManager.format_user_prompt(user_input, memory_context)
        
        # Step 2: Forward to LLM
        full_response = ""
        for chunk in self.llm.generate_stream(prompt=formatted_user_prompt, system=system_prompt):
            full_response += chunk
            yield chunk
            
        if full_response:
            save_message(session_id, "friday", full_response)
        
        logger.info("Orchestrator finished streaming response from LLM.")
