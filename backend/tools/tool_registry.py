from backend.tools.calculator_tool import CalculatorTool
from backend.tools.system_tool import SystemTool
from backend.tools.terminal_tool import TerminalTool
import logging
import concurrent.futures
import json

logger = logging.getLogger("friday.tools.registry")

class ToolRegistry:
    def __init__(self):
        self.tools = {
            "calculator": CalculatorTool(),
            "system_info": SystemTool(),
            "terminal": TerminalTool()
        }

    def get_all_tools_schema(self):
        schema = []
        for name, tool in self.tools.items():
            schema.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            })
        return schema

    def execute_tool(self, name: str, kwargs: dict) -> str:
        if name not in self.tools:
            return json.dumps({"error": f"Tool {name} not found."})

        logger.info(f"Tool Selected: {name}")
        logger.info(f"Tool Execution Started: {name} with args {kwargs}")

        def run_tool():
            return self.tools[name].execute(**kwargs)

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_tool)
                result = future.result(timeout=5.0)
                logger.info(f"Tool Execution Finished: {name}")
                
                # Ensure result is stringified JSON for consistent parsing if it's not a string already
                if not isinstance(result, str):
                    result = json.dumps({"result": result})
                    
                return result
                
        except concurrent.futures.TimeoutError:
            logger.error(f"Tool Execution Timeout: {name} exceeded 5 seconds.")
            return json.dumps({"error": "Tool execution timed out."})
        except Exception as e:
            logger.error(f"Tool Execution Failed: {name} | Error: {e}", exc_info=True)
            return json.dumps({"error": str(e)})

tool_registry = ToolRegistry()
