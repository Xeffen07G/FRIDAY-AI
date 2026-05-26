import re
from datetime import datetime

class ResponseCompressor:
    """
    Task 1: Response Compression Engine
    Responsible for aggressively shortening, removing acknowledgements,
    removing meta-commentary/explanatory filler, collapsing greetings,
    and compressing confirmations.
    
    Enforces hard max length limits and rule-based overrides.
    """
    
    FORBIDDEN_PHRASES = [
        "within this context",
        "recognized and understood",
        "no further action required",
        "at this moment",
        "according to system",
        "it should be noted",
        "I can assist further",
        "please let me know",
        "how may I assist",
        "based on your request"
    ]
    
    # Deterministic mappings
    DETERMINISTIC_OVERRIDES = {
        "hello": "Hello.",
        "hi": "Hi.",
        "hey": "Hey.",
        "thanks": "You're welcome.",
        "thank you": "You're welcome.",
        "open chrome": "Opening Chrome.",
        "open vscode": "Opening VSCode.",
    }

    def __init__(self):
        pass

    def classify_intent(self, user_input: str) -> str:
        """
        Task 6: Lightweight classifier for simple intents:
        - greeting
        - calculator
        - launcher
        - confirmation
        - yes/no
        - utility
        """
        clean_in = user_input.strip().lower().rstrip('?.!')
        
        # 1. Greetings
        if clean_in in ["hello", "hi", "hey", "greetings", "howdy", "yo", "good morning", "good afternoon", "good evening"]:
            return "greeting"
            
        # 2. Utility (time/date/clock)
        time_queries = ["what time is it", "current time", "what's the time", "time", "date", "current date", "clock"]
        if clean_in in time_queries or any(pat in clean_in for pat in ["what time", "current time", "what date", "current date"]):
            return "utility"
            
        # 3. Calculator
        # check if it starts with calculate or is a pure math expression
        expr = clean_in
        if clean_in.startswith("calculate"):
            expr = clean_in[len("calculate"):].strip()
        if re.match(r'^[\d+\-*/().\s%*]+$', expr) and any(c.isdigit() for c in expr):
            return "calculator"
            
        # 4. Launcher
        if clean_in.startswith(("open ", "launch ", "start ", "run ")):
            return "launcher"
            
        # 5. Confirmation
        confirmations = ["thanks", "thank you", "ok", "okay", "sure", "done", "confirm", "perfect", "great", "awesome"]
        if clean_in in confirmations:
            return "confirmation"
            
        # 6. Yes/No
        if clean_in in ["yes", "no", "yep", "nope", "yeah", "nay"]:
            return "yes_no"
            
        return "general"

    def get_deterministic_response(self, user_input: str) -> str:
        """
        Task 2: deterministic short response overrides.
        If a direct match exists, return it with NO additional prose.
        """
        clean_in = user_input.strip().lower().rstrip('?.!')
        
        # Direct string overrides
        if clean_in in self.DETERMINISTIC_OVERRIDES:
            return self.DETERMINISTIC_OVERRIDES[clean_in]
            
        # Time queries
        if clean_in == "what time is it" or clean_in == "current time" or clean_in == "time":
            return datetime.now().strftime("%I:%M %p").lstrip('0')
            
        # Calculator math overrides
        expr = clean_in
        if clean_in.startswith("calculate"):
            expr = clean_in[len("calculate"):].strip()
        if re.match(r'^[\d+\-*/().\s%*]+$', expr) and any(c.isdigit() for c in expr):
            try:
                # Safely evaluate using clean environments
                res = eval(expr, {"__builtins__": None}, {})
                if isinstance(res, float) and res.is_integer():
                    res = int(res)
                return str(res)
            except Exception:
                pass
                
        # App launcher overrides
        if clean_in.startswith(("open ", "launch ", "start ", "run ")):
            for prefix in ["open ", "launch ", "start ", "run "]:
                if clean_in.startswith(prefix):
                    app = clean_in[len(prefix):].strip()
                    if app == "chrome":
                        return "Opening Chrome."
                    elif app in ["vscode", "visual studio code", "code"]:
                        return "Opening VSCode."
                    else:
                        return f"Opening {app.title()}."
                        
        # Confirmations
        if clean_in in ["thanks", "thank you"]:
            return "You're welcome."
        if clean_in in ["ok", "okay", "sure", "done", "confirm"]:
            return "Done."
            
        # Yes/No
        if clean_in == "yes":
            return "Yes."
        if clean_in == "no":
            return "No."
            
        return ""

    def compress_response(self, text: str, user_input: str) -> str:
        """
        Applies aggressive response compression, rule overrides, forbidden phrase filtering,
        and max-length caps.
        """
        if not text:
            return ""
            
        # Step 1: Check deterministic overrides first (Task 2)
        override = self.get_deterministic_response(user_input)
        if override:
            return override
            
        cleaned = text.strip()
        
        # Step 2: Strip bracket markers if any (like [GENERATIVE_RESPONSE] or [DETERMINISTIC_RESPONSE])
        cleaned = re.sub(r'^\[GENERATIVE_RESPONSE\]\s*', '', cleaned)
        cleaned = re.sub(r'^\[DETERMINISTIC_RESPONSE\]\s*', '', cleaned)
        
        # Step 3: Global forbidden phrases blocklist (Task 9)
        for phrase in self.FORBIDDEN_PHRASES:
            # Case-insensitive replacement
            cleaned = re.sub(r'\b' + re.escape(phrase) + r'\b', '', cleaned, flags=re.IGNORECASE)
            
        # Step 4: Collapse greetings and conversational preambles
        # Remove common greetings at the start
        greetings_regex = r'^(?:hello|hi|hey|greetings|dear user|sure|of course|certainly|no problem|ok|okay)(?:,?\s+there)?(?:!|\.|\?|,)?\s*'
        if len(re.sub(greetings_regex, "", cleaned, flags=re.IGNORECASE).strip()) > 0:
            cleaned = re.sub(greetings_regex, "", cleaned, flags=re.IGNORECASE)
        
        # Remove trailing assistant fillers/closing remarks
        closings = [
            r"how (can|may) I assist (you\s+)?further\??",
            r"let me know if you need anything else\.?",
            r"is there anything else I can do\??",
            r"feel free to ask\.?"
        ]
        for closing in closings:
            cleaned = re.sub(closing, "", cleaned, flags=re.IGNORECASE)
            
        # Clean consecutive punctuation marks/spaces left by replacements
        cleaned = re.sub(r'\.+', '.', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'\s+([.,;:?!])', r'\1', cleaned)
        cleaned = cleaned.strip()
        cleaned = re.sub(r'^[.,;:?!]+', '', cleaned).strip()
        
        # Step 5: Enforce hard max length caps based on intent (Task 3)
        intent = self.classify_intent(user_input)
        
        if intent == "greeting":
            # Greeting responses: MAX 2-4 words
            words = cleaned.split()
            if len(words) > 4 or not cleaned:
                cleaned = "Hello."
            elif len(words) < 1:
                cleaned = "Hello."
                
        elif intent == "utility":
            # Utility responses: MAX 1 sentence
            sentences = re.split(r'(?<=[.!?])\s+', cleaned)
            if sentences:
                cleaned = sentences[0]
                
        elif intent == "confirmation":
            # Simple tool confirmations: MAX 3-5 words
            words = cleaned.split()
            if len(words) > 5 or not cleaned:
                cleaned = "Done."
                
        elif intent == "launcher":
            # Launcher response: MAX 3-5 words
            words = cleaned.split()
            if len(words) > 5 or not cleaned:
                # Deduce app name from user input
                clean_in = user_input.strip().lower()
                app = "application"
                for prefix in ["open ", "launch ", "start ", "run "]:
                    if clean_in.startswith(prefix):
                        app = clean_in[len(prefix):].strip().title()
                        break
                cleaned = f"Opening {app}."
                
        elif intent == "calculator":
            # Calculator outputs: Numeric only
            # Search for numbers (or formulas) in the response, default to fallback eval
            num_match = re.search(r'\d+(?:\.\d+)?', cleaned)
            if num_match:
                cleaned = num_match.group(0)
            else:
                # If no number, try evaluating input again
                override_calc = self.get_deterministic_response(user_input)
                if override_calc:
                    cleaned = override_calc
                else:
                    cleaned = "Error."
                    
        elif intent == "yes_no":
            # Yes/No: MAX 1-2 words
            words = cleaned.split()
            if len(words) > 2 or not cleaned:
                cleaned = "Yes." if "yes" in user_input.lower() or "yep" in user_input.lower() or "yeah" in user_input.lower() else "No."
                
        # Never allow disclaimers, explanatory acknowledgements, or empty responses
        if not cleaned:
            cleaned = "Done."
            
        # Final blocklist clean to be absolutely safe
        for phrase in self.FORBIDDEN_PHRASES:
            cleaned = re.sub(r'\b' + re.escape(phrase) + r'\b', '', cleaned, flags=re.IGNORECASE)
            
        # Clean whitespace/hanging commas again
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'\s+([.,;:?!])', r'\1', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned

response_compressor = ResponseCompressor()
