import json
import asyncio
import time
import re
from backend.tools.tool_registry import tool_registry
from backend.llm.ollama_client import LLMClient
from backend.core.logger import get_logger

logger = get_logger("tools.orchestrator")

class ToolOrchestrator:
    def __init__(self):
        self.llm = LLMClient()
        # Pre-compile intent patterns for ultra-low latency
        self.conversation_patterns = re.compile(
            r"^(hello|hi|hey|greetings|morning|afternoon|evening|how are you|who are you|what are you|thanks|thank you|bye|goodbye|cool|nice|okay|ok|help|info)$", 
            re.IGNORECASE
        )
        # Memory save triggers
        self.memory_save_patterns = re.compile(
            r"(remember|favourite|favorite|i love|i like|i am learning|i work at|my name is|i prefer|my goal is|i want to learn)",
            re.IGNORECASE
        )

    def get_intent(self, prompt: str) -> str:
        """Lightweight intent classification using regex and keyword mapping."""
        clean_prompt = prompt.strip().lower()
        
        # 1. Conversational / Greeting Bypass
        if self.conversation_patterns.match(clean_prompt) or len(clean_prompt.split()) < 3:
            return "conversational"
        
        # 2. Memory Save Intent
        if self.memory_save_patterns.search(clean_prompt):
            if clean_prompt.startswith(("what", "who", "where", "how")):
                return "conversational"
            return "memory_save"
        
        # 3. Tool-specific keywords
        tool_keywords = {
            "calculator": ["calc", "math", "plus", "minus", "multiplied", "divided"],
            "terminal": ["run command", "terminal", "shell", "execute", "list files", "mkdir"],
            "file": ["read file", "write to file", "filesystem", "save to"],
            "system": ["system info", "cpu", "memory usage", "disk space"]
        }
        
        for intent, keywords in tool_keywords.items():
            if any(k in clean_prompt for k in keywords):
                return "tool_execution"
                
        return "routing_needed"

    async def check_and_execute_tools(self, user_prompt: str, request_id: str = "UNKNOWN") -> str:
        """
        Quickly decides if a tool is needed using async LLM call.
        """
        intent = self.get_intent(user_prompt)
        
        if intent in ["conversational", "memory_save"]:
            return None

        schemas = tool_registry.get_all_tools_schema()
        system_prompt = f"""You are a tool router. Available: {json.dumps(schemas)}
Rules: 
1. JSON ONLY: {{"tool": "name", "args": {{}}}} or {{"tool": "none"}}
2. No explanation."""
        
        try:
            logger.info(f"[REQ:{request_id}] Calling LLM for tool routing (2s cap).")
            # We await the async generate_json
            response = await self.llm.generate_json(user_prompt, system=system_prompt, request_id=request_id, timeout=3)
            
            if not response or not response.strip() or response == "{}":
                return None
                
            data = json.loads(response)
            tool_name = data.get("tool")
            
            if tool_name and tool_name != "none":
                logger.info(f"[REQ:{request_id}] Executing tool: {tool_name}")
                args = data.get("args", {})
                result = tool_registry.execute_tool(tool_name, args)
                return f"--- TOOL EXECUTION RESULTS ---\nTool: {tool_name}\nResult: {str(result)}\n-----------------------------"
                
        except Exception as e:
            logger.error(f"[REQ:{request_id}] Tool routing error: {e}")
            
        return None

tool_orchestrator = ToolOrchestrator()
