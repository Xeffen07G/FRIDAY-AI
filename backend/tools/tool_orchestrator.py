import json
import logging
from backend.tools.tool_registry import tool_registry
from backend.llm.ollama_client import LLMClient

logger = logging.getLogger("friday.tools.orchestrator")

class ToolOrchestrator:
    def __init__(self):
        self.llm = LLMClient()

    def check_and_execute_tools(self, user_prompt: str, request_id: str = "UNKNOWN") -> str:
        """
        Quickly asks the LLM if a tool is needed using zero-shot classification.
        Returns execution result string or None.
        """
        schemas = tool_registry.get_all_tools_schema()
        system_prompt = f"""You are a tool router. Decide if the user needs a tool.
Available tools:
{json.dumps(schemas, indent=2)}

Rules:
1. ONLY return valid JSON.
2. If tool needed: {{"tool": "tool_name", "args": {{"arg_name": "value"}}}}
3. If NO tool needed: {{"tool": "none"}}
4. Do NOT explain or output anything else.
"""
        
        try:
            logger.info(f"[REQ:{request_id}] Calling LLM for tool routing intent.")
            response = self.llm.generate_json(user_prompt, system=system_prompt, request_id=request_id)
            
            if not response or not response.strip():
                logger.warning(f"[REQ:{request_id}] Tool router returned empty response. Bypassing tools.")
                return None
                
            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                logger.warning(f"[REQ:{request_id}] Failed to parse tool JSON from LLM: {response}. Bypassing tools.")
                return None
            
            tool_name = data.get("tool")
            if tool_name and tool_name != "none":
                logger.info(f"[REQ:{request_id}] LLM requested tool: {tool_name}")
                args = data.get("args", {})
                
                # Execute tool securely via ThreadPool
                result = tool_registry.execute_tool(tool_name, args)
                
                # Force strictly to string to prevent dict injection hangs
                result_str = str(result)
                
                # Check if it returned an error JSON dict natively
                try:
                    res_json = json.loads(result_str)
                    if "error" in res_json:
                        logger.warning(f"[REQ:{request_id}] Tool {tool_name} returned error state: {res_json['error']}")
                except:
                    pass
                
                # Format exactly as requested for context injection
                return f"--- TOOL EXECUTION RESULTS ---\nTool Used: {tool_name}\nArguments: {json.dumps(args)}\nResult: {result_str}\n-----------------------------"
                
        except Exception as e:
            logger.error(f"[REQ:{request_id}] Tool routing failed catastrophically: {e}. Bypassing tools.", exc_info=True)
            
        # Fallback behavior: bypass tools and proceed
        return None

tool_orchestrator = ToolOrchestrator()
