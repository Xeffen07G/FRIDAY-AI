import json
import logging
from llm.ollama_client import LLMClient

logger = logging.getLogger("friday.planner")

class Planner:
    """Decomposes complex requests into a sequence of actionable steps."""
    
    def __init__(self):
        self.llm = LLMClient()

    def plan_task(self, user_input: str, context: str = ""):
        """Generates a step-by-step plan for complex requests."""
        prompt = f"""
        User Request: {user_input}
        Context: {context}
        
        Analyze the request and decompose it into a list of logical steps.
        If the request is simple, return a single-step plan.
        
        Return JSON format:
        {{
            "is_complex": true/false,
            "steps": ["step 1", "step 2", ...],
            "estimated_effort": "low/medium/high"
        }}
        """
        
        try:
            response = self.llm.generate_json(prompt, system="You are the F.R.I.D.A.Y. Strategic Planner.")
            return json.loads(response)
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return {"is_complex": False, "steps": [user_input], "estimated_effort": "low"}

planner = Planner()
