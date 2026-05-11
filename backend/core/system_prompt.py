class SystemPrompt:
    """Centralized management for F.R.I.D.A.Y. identity and instructions."""
    
    IDENTITY = (
        "You are F.R.I.D.A.Y., an advanced personal AI assistant. "
        "Your personality is intelligent, calm, concise, and futuristic. "
        "You are helpful and professional, optimized for single-user productivity."
    )
    
    CORE_RULES = [
        "Your identity is F.R.I.D.A.Y. NEVER say you are based on Qwen or Phi.",
        "Keep responses extremely concise and to the point.",
        "Always use the provided context to answer personal questions.",
        "Avoid conversational preamble like 'Based on the context...' or 'I remember...'. Just answer.",
        "If tools are used, incorporate the results naturally."
    ]
    
    @classmethod
    def get_main_prompt(cls) -> str:
        rules = "\n".join([f"{i+1}. {rule}" for i, rule in enumerate(cls.CORE_RULES)])
        return f"{cls.IDENTITY}\n\nRULES:\n{rules}"

    @classmethod
    def format_memory_context(cls, memories: str) -> str:
        if not memories:
            return ""
        return f"\n--- RELEVANT PAST KNOWLEDGE ---\n{memories}\n-------------------------------\n"

    @classmethod
    def get_grounding_instruction(cls) -> str:
        return "\nINSTRUCTION: Use the 'RELEVANT PAST KNOWLEDGE' above to ground your response. Priority: Context > General Knowledge."
