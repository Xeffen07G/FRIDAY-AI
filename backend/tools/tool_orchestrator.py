import json
import logging
import time
import re
from backend.tools.tool_registry import tool_registry
from backend.llm.ollama_client import LLMClient

logger = logging.getLogger("friday.tools.orchestrator")

class ToolOrchestrator:
    def __init__(self):
        self.llm = LLMClient()
        # Pre-compile intent patterns for ultra-low latency
        self.conversation_patterns = re.compile(
            r"^(hello|hi|hey|greetings|morning|afternoon|evening|how are you|who are you|what are you|thanks|thank you|bye|goodbye|cool|nice|okay|ok|help|info)$", 
            re.IGNORECASE
        )

    def get_intent(self, prompt: str) -> str:
        """Lightweight intent classification using regex and keyword mapping."""
        clean_prompt = prompt.strip().lower()
        
        # 1. Conversational / Greeting Bypass
        if self.conversation_patterns.match(clean_prompt) or len(clean_prompt.split()) < 3:
            return "conversational"
        
        # 2. Tool-specific keywords (Direct Routing Hint)
        tool_keywords = {
            "calculator": ["calc", "math", "plus", "minus", "multiplied", "divided"],
            "terminal": ["run command", "terminal", "shell", "execute", "list files", "mkdir"],
            "file": ["read file", "write to file", "filesystem", "save to"],
            "system": ["system info", "cpu", "memory usage", "disk space"]
        }
        
        for intent, keywords in tool_keywords.items():
            if any(k in clean_prompt for k in keywords):
                return "tool_execution"
                
        # 3. Default to routing logic for complex queries
        return "routing_needed"

    def check_and_execute_tools(self, user_prompt: str, request_id: str = "UNKNOWN") -> str:
        """
        Quickly decides if a tool is needed. Bypasses LLM routing for greetings.
        Includes a 2.0s hard cap on decision logic.
        """
        start_time = time.time()
        
        # Step 1: Lightweight Intent Classification (Bypass)
        intent = self.get_intent(user_prompt)
        intent_duration = time.time() - start_time
        logger.info(f"[REQ:{request_id}] Intent classification: {intent} ({intent_duration*1000:.1f}ms)")
        
        if intent == "conversational":
            logger.info(f"[REQ:{request_id}] Bypassing tools for conversational prompt.")
            return None

        # Step 2: LLM Routing with 2.0s Hard Cap
        schemas = tool_registry.get_all_tools_schema()
        system_prompt = f"""You are a tool router. Available: {json.dumps(schemas)}
Rules: 
1. JSON ONLY: {{"tool": "name", "args": {{}}}} or {{"tool": "none"}}
2. No explanation."""
        
        try:
            logger.info(f"[REQ:{request_id}] Calling LLM for tool routing (2s cap).")
            # We use a shorter timeout for routing to ensure overall latency remains low
            # Note: Ollama doesn't support request-level timeouts in the generate API easily without cancelling, 
            # but we can check timing after the call or use a separate thread.
            
            routing_call_start = time.time()
            # Reduce max tokens or use a faster model check if possible
            response = self.llm.generate_json(user_prompt, system=system_prompt, request_id=request_id)
            routing_duration = time.time() - routing_call_start
            
            if routing_duration > 2.0:
                logger.warning(f"[REQ:{request_id}] Tool routing exceeded 2s ({routing_duration:.2f}s). Fallback to direct answer.")
                return None
                
            if not response or not response.strip() or response == "{}":
                return None
                
            data = json.loads(response)
            tool_name = data.get("tool")
            
            if tool_name and tool_name != "none":
                logger.info(f"[REQ:{request_id}] Executing tool: {tool_name}")
                args = data.get("args", {})
                
                # Execute tool
                result = tool_registry.execute_tool(tool_name, args)
                result_str = str(result)
                
                return f"--- TOOL EXECUTION RESULTS ---\nTool: {tool_name}\nResult: {result_str}\n-----------------------------"
                
        except Exception as e:
            logger.error(f"[REQ:{request_id}] Tool routing error: {e}")
            
        return None

tool_orchestrator = ToolOrchestrator()
