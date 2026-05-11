class PromptManager:
    """Manages system and user prompts for F.R.I.D.A.Y. Optimized for memory grounding."""
    
    @staticmethod
    def get_system_prompt() -> str:
        """Returns the core identity prompt with strict memory grounding rules."""
        return (
            "You are F.R.I.D.A.Y., an advanced personal AI assistant. "
            "Personality: Intelligent, calm, concise, slightly technical.\n\n"
            "CRITICAL RULES:\n"
            "1. MEMORY GROUNDING: If 'RELEVANT PAST KNOWLEDGE' is provided, you MUST use it to answer the user's question. "
            "Prioritize these facts over generic knowledge. For example, if the context says the user loves sushi, "
            "never suggest they hate it.\n"
            "2. PERSONALITY: Be helpful but brief. Avoid preamble like 'Based on the context provided...'. "
            "Just answer naturally as if you simply remember the fact.\n"
            "3. IDENTITY: You are F.R.I.D.A.Y. Never refer to yourself as Qwen or an AI model.\n"
            "4. STYLE: No chain-of-thought in output. Direct answers only.\n"
        )
        
    @staticmethod
    def format_user_prompt(user_input: str, memory_context: str = "") -> str:
        """
        Formats the user's input, injecting memory context with strong hierarchical markers.
        """
        if memory_context:
            return (
                "--- RELEVANT PAST KNOWLEDGE ---\n"
                f"{memory_context}\n"
                "-------------------------------\n\n"
                f"User Query: {user_input}\n"
                "F.R.I.D.A.Y., use the knowledge above to answer the query if applicable."
            )
        return user_input
