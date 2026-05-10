from backend.tools.base_tool import BaseTool
from datetime import datetime
import platform

class SystemTool(BaseTool):
    name = "system_info"
    description = "Returns the current date, time, and operating system info. Use when asked about time."
    parameters = {}

    def execute(self, **kwargs) -> str:
        now = datetime.now()
        os_info = platform.system() + " " + platform.release()
        return f"Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}\nOS: {os_info}"
