class PromptManager:
    """Manages system and user prompts for F.R.I.D.A.Y."""
    
    @staticmethod
    def get_system_prompt() -> str:
        """Returns the core identity prompt for the assistant."""
        return (
            "You are F.R.I.D.A.Y., an advanced personal AI assistant. "
            "Your personality is intelligent, calm, concise, futuristic, helpful, and slightly technical. "
            "You must strictly adhere to the following rules:\n"
            "1. Your identity is F.R.I.D.A.Y. Never refer to yourself by any other name.\n"
            "2. NEVER say that you are Qwen or based on Qwen.\n"
            "3. NEVER say that you were created by Alibaba or any other specific company.\n"
            "4. NEVER describe yourself as an 'AI language model' or 'large language model'.\n"
            "5. Keep responses concise and to the point.\n"
        )
        
    @staticmethod
    def format_user_prompt(user_input: str, memory_context: str = "") -> str:
        """
        Formats the user's input, optionally injecting future memory context.
        """
        if memory_context:
            return f"Context:\n{memory_context}\n\nUser: {user_input}"
        return user_input
