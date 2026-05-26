import re

class ResponseCleaner:
    """
    Cleaner to strip roleplay language, sci-fi/protocol jargon, filler prose,
    and verbose descriptions. Enforces a calm, minimal, precise tone.
    """
    
    @staticmethod
    def clean(text: str) -> str:
        if not text:
            return ""
            
        cleaned = text
        
        # Strip common sci-fi/theatrical roleplay prefixes and phrases first (Task 1)
        cleaned = re.sub(r'\binitiating\s+protocols?\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bidentity\s+verification\s+complete\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bidentity\s+verification\s+successful\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bexecuting\s+cognitive\s+remediation\s+workflow\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bexecuting\s+cognitive\s+process\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\banalyzing\s+your\s+request\s+through\s+layered\s+cognition\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bgreetings\s+human\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bfuture\s+capability\s+hooks?\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bsimulated\s+operation\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\baccording\s+to\s+operational\s+framework\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bcapability\s+hooks?\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\borchestration\s+layer\s+initialized\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bidentity\s+confirmed\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bsystem\s+protocols\s+active\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\blayered\s+cognition\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\badvanced\s+engineering\s+runtime\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bsystem\s+narration\b', '', cleaned, flags=re.IGNORECASE)
        
        # 1. Broad filler pattern list (Task 1)
        filler_patterns = [
            r"\bI am here to assist\b.*?\.",
            r"\bperhaps we can\b",
            r"\bwithin this environment\b",
            r"\bhow can I help you today\??",
            r"\bsure, I can help with that\.?",
            r"\bcertainly, let me\b",
            r"\bI have successfully\b",
            r"\bI'm happy to help\b",
            r"\bas an AI assistant\b.*?,",
            r"\bI will now\b",
            r"\blet me help you with\b",
            r"\bI have initiated opening\b",
            r"\bI've opened\b",
            r"\bI am happy to assist you with\b",
            r"\bSure! Here is the result:\b",
            r"\bOf course! \b",
            r"\bI am now initiating\b",
            r"\binitiating systems\b",
            r"\binitiating system\b"
        ]
        
        # Remove conversational greetings/filler at the start of the response (Task 4)
        cleaned = re.sub(r'^(?:hello|hi|hey|greetings|dear user|sure|of course|certainly)(?:,?\s+there)?(?:!|\.|\?|,)?\s*', "", cleaned, flags=re.IGNORECASE)

        for pattern in filler_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
            
        # Clean specific prohibited words (Task 1)
        cleaned = re.sub(r'\binitiating\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bprotocols?\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bhuman\s+user\b', 'user', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bsimulated\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\borchestration\s+layer\b', '', cleaned, flags=re.IGNORECASE)

        # Truncate simple actions to direct minimal statements (Task 3 Length Control)
        cleaned_lower = cleaned.lower()
        if "vscode" in cleaned_lower or "visual studio code" in cleaned_lower:
            return "VSCode opened."
        if "calc" in cleaned_lower or "calculator" in cleaned_lower:
            return "Calculator opened."
        if "chrome" in cleaned_lower:
            return "Chrome opened."
        if "backend restarted" in cleaned_lower or "restarting backend" in cleaned_lower:
            return "Backend restarted."
        if "websocket connection restored" in cleaned_lower:
            return "WebSocket connection restored."

        # Math sentence simplification
        math_sentence_patterns = [
            r"^(?:the\s+)?(?:result|answer)(?:\s+of\s+.*?|\s+is)?\s+(?:equals|is)\s+(\d+(?:\.\d+)?)$",
            r"^(?:the\s+)?(?:result|answer)\s+is\s+(\d+(?:\.\d+)?)$",
            r"^(?:the\s+)?result\s+of\s+.*?is\s+(\d+(?:\.\d+)?)$"
        ]
        for pat in math_sentence_patterns:
            match = re.match(pat, cleaned.strip(), re.IGNORECASE)
            if match:
                return match.group(1)

        # Clean consecutive punctuation marks left by replacements
        cleaned = re.sub(r'\.+', '.', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'\s+([.,;:?!])', r'\1', cleaned)
        cleaned = cleaned.strip()
        cleaned = re.sub(r'^[.,;:?!]+', '', cleaned).strip()
        
        if not cleaned:
            cleaned = "Done."

        return cleaned

# Singleton
response_cleaner = ResponseCleaner()
