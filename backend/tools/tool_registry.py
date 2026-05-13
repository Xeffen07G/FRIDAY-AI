from tools.calculator_tool import CalculatorTool
from tools.terminal_tool import TerminalTool
from tools.web_search_tool import WebSearchTool
from tools.weather_tool import WeatherTool
from tools.system_action_tool import SystemActionTool
from tools.screen_capture_tool import ScreenCaptureTool
from tools.desktop_agent_tool import DesktopAgentTool
import logging
import asyncio
import json
import inspect
import uuid

logger = logging.getLogger("friday.tools.registry")

class ToolRegistry:
    def __init__(self):
        self.tools = {
            "calculator": CalculatorTool(),
            "terminal": TerminalTool(),
            "web_search": WebSearchTool(),
            "weather_lookup": WeatherTool(),
            "system_action": SystemActionTool(),
            "screen_perception": ScreenCaptureTool(),
            "desktop_agent": DesktopAgentTool()
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

    async def execute_tool(self, name: str, kwargs: dict) -> str:
        if name not in self.tools:
            return json.dumps({"error": f"Tool {name} not found."})

        tool = self.tools[name]
        
        # Phase 7: Safety & Control - Permission Check
        if getattr(tool, "requires_confirmation", False):
            return json.dumps({
                "type": "permission_request",
                "tool": name,
                "args": kwargs,
                "message": f"I need your permission to execute {name} with these parameters."
            })

        logger.info(f"Tool Execution Started: {name} with args {kwargs}")

        try:
            # Phase 3: Tool Scheduling & Prioritization
            from tools.tool_scheduler import tool_scheduler
            
            # Determine priority: 1=Critical, 5=Realtime, 10=Standard, 20=Background
            priority = 10
            if name in ["web_search", "weather_lookup"]: priority = 5
            elif name == "terminal": priority = 1
            
            tool_id = f"{name}_{str(uuid.uuid4())[:6]}"
            future = await tool_scheduler.schedule_tool(tool_id, tool.execute, kwargs, priority=priority)
            
            # Wait for result with timeout
            result = await asyncio.wait_for(future, timeout=15.0)
            
            if not isinstance(result, str):
                result = json.dumps({"result": result})
            return result
                
        except asyncio.TimeoutError:
            logger.error(f"Tool Execution Timeout: {name}")
            return json.dumps({"error": "Tool execution timed out."})
        except Exception as e:
            logger.error(f"Tool Execution Failed: {name} | Error: {e}", exc_info=True)
            return json.dumps({"error": str(e)})

tool_registry = ToolRegistry()
