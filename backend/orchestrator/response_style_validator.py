import re
import logging

logger = logging.getLogger(__name__)

class ResponseStyleValidator:
    """
    Validates that assistant responses conform to the calm, minimal,
    and premium senior-engineer tone. Rejects theatrical/sci-fi AI jargon.
    """
    
    PROHIBITED_PATTERNS = [
        r"\binitiating\s+protocols?\b",
        r"\bidentity\s+verification\b",
        r"\bfuture\s+capability\s+hooks?\b",
        r"\bgreetings\s+human\b",
        r"\bsimulated\s+operation\b",
        r"\bcognitive\s+execution\b",
        r"\bexecuting\s+cognitive\b",
        r"\boperational\s+framework\b",
        r"\bcapability\s+hooks?\b",
        r"\borchestration\s+layer\b",
        r"\bidentity\s+confirmed\b",
        r"\bsystem\s+protocols?\b",
        r"\blayered\s+cognition\b",
        r"\badvanced\s+engineering\s+runtime\b",
        r"\bsystem\s+narration\b",
        r"\bassistance\s+protocols?\b",
        r"\bpermissions\s+verified\b",
        r"\bbackground\s+cognition\b",
        r"\bsystem\s+analysis\s+complete\b",
        r"\boperational\s+status\b",
        r"\bas\s+an\s+ai\s+assistant\b",
        r"\bcognition\s+evolving\b"
    ]
    
    @classmethod
    def validate(cls, text: str) -> bool:
        """
        Returns True if the response is valid and meets the high-trust engineering guidelines.
        Returns False if prohibited theatrical or sci-fi patterns are found.
        """
        if not text:
            return True
            
        lower_text = text.lower()
        for pattern in cls.PROHIBITED_PATTERNS:
            if re.search(pattern, lower_text):
                logger.warning(f"[STYLE_VALIDATOR] Rejected response due to pattern: {pattern}")
                return False
                
        # Length check for simple tasks (Task 3: Response Length Control)
        if ("opened" in lower_text or "started" in lower_text) and len(text.split()) > 15:
            logger.warning(f"[STYLE_VALIDATOR] Rejected response due to excessive length on simple statement.")
            return False
            
        return True

    @classmethod
    def sanitize_or_fallback(cls, text: str) -> str:
        """
        Aggressively sanitizes a rejected response or returns a clean concise fallback.
        """
        from orchestrator.response_cleaner import response_cleaner
        cleaned = response_cleaner.clean(text)
        
        # If it still contains prohibited phrases, yield a minimal fallback
        lower_raw = text.lower()
        lower_cleaned = cleaned.lower()
        
        for pattern in cls.PROHIBITED_PATTERNS:
            if re.search(pattern, lower_cleaned) or re.search(pattern, lower_raw):
                if "vscode" in lower_raw or "visual studio code" in lower_raw:
                    return "VSCode opened."
                if "calc" in lower_raw or "calculator" in lower_raw:
                    return "Calculator opened."
                if "chrome" in lower_raw:
                    return "Chrome opened."
                if "hello" in lower_raw or "greetings" in lower_raw:
                    return "Hello."
                return "Done."
                
        return cleaned

# Singleton
response_style_validator = ResponseStyleValidator()

def sanitize_and_validate_output(text: str, user_input: str = "") -> str:
    """
    TASK 2 — SINGLE FINAL OUTPUT GATE
    Pipeline: raw_generation -> response_cleaner -> response_style_validator -> response_compressor
    """
    from orchestrator.response_cleaner import response_cleaner
    from orchestrator.response_compressor import response_compressor
    
    if not response_style_validator.validate(text):
        logger.warning(f"[SANITIZER] Style violation in raw text: '{text[:50]}'. Invoking emergency fallback.")
        fallback = response_style_validator.sanitize_or_fallback(text)
        return response_compressor.compress_response(fallback, user_input)
        
    cleaned = response_cleaner.clean(text)
    
    if not response_style_validator.validate(cleaned):
        logger.warning(f"[SANITIZER] Style violation in cleaned text: '{cleaned[:50]}'. Invoking emergency fallback.")
        cleaned = response_style_validator.sanitize_or_fallback(cleaned)
        
    # Final Compression (MUST happen after validation)
    return response_compressor.compress_response(cleaned, user_input)


class StreamFilter:
    """
    TASK 3 — HARD STREAM INTERCEPTION
    Buffers and filters tokens in real-time, holding back potential prohibited starters
    and outputting only fully sanitized and validated deltas.
    
    Performance: avoids O(n²) by only running full sanitize_and_validate_output
    at sentence boundaries or every 150 chars of buffer growth.
    """
    def __init__(self, user_input: str = ""):
        self.buffer = ""
        self.emitted = ""
        self.user_input = user_input
        self._last_validated_len = 0
        self.original_input = user_input
        self.prohibited_prefixes = [
            "initiating protocol",
            "identity verification",
            "future capability",
            "greetings human",
            "simulated operation",
            "cognitive execution",
            "executing cognitive",
            "operational framework",
            "capability hook",
            "orchestration layer",
            "identity confirmed",
            "system protocol",
            "layered cognition",
            "advanced engineering runtime",
            "system narration",
            "assistance protocol",
            "permissions verified",
            "background cognition",
            "system analysis complete",
            "operational status",
            "as an ai assistant",
            "cognition evolving",
            "within this context",
            "recognized and understood",
            "no further action required",
            "at this moment",
            "according to system",
            "it should be noted",
            "i can assist further",
            "please let me know",
            "how may i assist",
            "based on your request"
        ]

    def feed_and_filter(self, token: str) -> str:
        # Strip internal markers if they show up in raw generation
        if "[GENERATIVE_RESPONSE]" in token:
            token = token.replace("[GENERATIVE_RESPONSE]", "")
        if "[DETERMINISTIC_RESPONSE]" in token:
            token = token.replace("[DETERMINISTIC_RESPONSE]", "")

        self.buffer += token
        buffer_lower = self.buffer.lower().strip()

        # Check if the buffer is a prefix of any prohibited pattern
        is_prefix = False
        for pattern in self.prohibited_prefixes:
            if pattern.startswith(buffer_lower):
                is_prefix = True
                break

        # Check if the buffer contains a full prohibited pattern
        is_violation = False
        for pattern in self.prohibited_prefixes:
            if pattern in buffer_lower:
                is_violation = True
                break

        if is_violation:
            # Full validation/fallback
            validated = sanitize_and_validate_output(self.buffer, self.original_input)
            self._last_validated_len = len(self.buffer)
            
            delta = validated[len(self.emitted):] if validated.startswith(self.emitted) else validated
            self.emitted = validated
            return delta

        if is_prefix:
            # Hold it back! Return empty string
            return ""

        # Not a prefix, and not a violation.
        buffer_growth = len(self.buffer) - self._last_validated_len
        ends_sentence = self.buffer.rstrip().endswith(('.', '\n', '?', '!'))

        if ends_sentence or buffer_growth > 150:
            validated = sanitize_and_validate_output(self.buffer, self.original_input)
            self._last_validated_len = len(self.buffer)
            
            # Preserve original trailing whitespace if not fully compressed to short answer
            if self.buffer.endswith(" ") and not validated.endswith(" ") and len(validated.split()) > 4:
                validated += " "
            if self.buffer.endswith("\n") and not validated.endswith("\n") and len(validated.split()) > 4:
                validated += "\n"

            delta = validated[len(self.emitted):] if validated.startswith(self.emitted) else validated
            self.emitted = validated
            return delta
        else:
            # Emit delta directly
            delta = self.buffer[len(self.emitted):]
            self.emitted = self.buffer
            return delta
