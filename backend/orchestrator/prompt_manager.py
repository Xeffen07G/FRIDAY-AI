from backend.core.system_prompt import SystemPrompt

class PromptManager:
    """Orchestrates final prompt assembly using the centralized SystemPrompt layer."""
    
    @staticmethod
    def get_system_prompt(intent: str = "conversational") -> str:
        base = SystemPrompt.get_main_prompt()
        if intent == "memory_save":
            base += "\n\nCONTEXT: The user just shared a personal fact. Acknowledge and confirm storage."
        return base
        
    @staticmethod
    def format_user_prompt(user_input: str, memory_context: str = "") -> str:
        context_block = SystemPrompt.format_memory_context(memory_context)
        grounding = SystemPrompt.get_grounding_instruction() if memory_context else ""
        
        return f"{context_block}{grounding}\n\nUser: {user_input}"
