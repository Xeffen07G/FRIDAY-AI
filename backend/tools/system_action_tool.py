import subprocess
import os
import platform
from tools.base_tool import BaseTool

class SystemActionTool(BaseTool):
    name = "system_action"
    description = "Perform local system actions like opening applications or listing files."
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["open_app", "list_files", "system_status"]},
            "target": {"type": "string", "description": "Application name or directory path"}
        },
        "required": ["action"]
    }

    def execute(self, action: str, target: str = None) -> str:
        if action == "open_app":
            if not target: return "Error: No target application specified."
            try:
                if platform.system() == "Windows":
                    # Simple start command for common apps
                    subprocess.Popen(["cmd", "/c", f"start {target}"], shell=True)
                else:
                    subprocess.Popen(["open", "-a", target])
                return f"Successfully triggered opening of {target}."
            except Exception as e:
                return f"Failed to open {target}: {str(e)}"
        
        elif action == "list_files":
            path = target or os.getcwd()
            try:
                files = os.listdir(path)
                return f"Files in {path}: " + ", ".join(files[:20])
            except Exception as e:
                return f"Error listing files: {str(e)}"
                
        elif action == "system_status":
            import psutil
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            return f"System Status: CPU Usage {cpu}%, Memory Usage {mem}%."
            
        return "Unknown system action."
