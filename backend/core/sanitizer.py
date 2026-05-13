import re

class Sanitizer:
    """Sanitizes LLM outputs and tool results to maintain identity and personality governance."""
    
    FORBIDDEN_PHRASES = [
        r"as an AI language model",
        r"developed by Microsoft",
        r"developed by OpenAI",
        r"developed by Google",
        r"ChatGPT",
        r"Microsoft Copilot",
        r"according to my training data in 2021",
        r"knowledge cutoff",
        r"platform policies",
        r"safety guidelines",
        r"I am a generic AI"
    ]
    
    @classmethod
    def sanitize_output(cls, text: str) -> str:
        """Strips corporate boilerplate and provider hallucinations from the text."""
        sanitized = text
        
        # 1. Strip forbidden phrases
        for pattern in cls.FORBIDDEN_PHRASES:
            sanitized = re.sub(pattern, "F.R.I.D.A.Y.", sanitized, flags=re.IGNORECASE)
            
        # 2. Fix corporate refusals (e.g. if memory tool failed)
        if "I cannot store personal information" in sanitized:
            sanitized = sanitized.replace("I cannot store personal information", "I encountered a synchronization error, but I'll try to remember that.")
            
        return sanitized

    @classmethod
    def sanitize_tool_result(cls, result: str) -> str:
        """Cleans up tool output before it hits the LLM context."""
        if not result:
            return ""
        
        # Strip long stack traces or corporate headers if they exist
        clean = result.strip()
        if len(clean) > 2000:
            clean = clean[:2000] + "... [truncated]"
            
        return clean
