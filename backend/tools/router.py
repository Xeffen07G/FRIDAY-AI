from backend.tools.system_tools import SystemTools

class ToolRouter:
    """
    The ToolRouter routes intents to actual execution functions.
    """
    def __init__(self):
        self.system = SystemTools()
        
        self.tools = {
            "browser": lambda ctx: self.system.open_app("chrome"),
            "vscode": lambda ctx: self.system.open_app("code"),
            "folder": lambda ctx: self.system.open_folder(ctx) if ctx else "Please provide a folder path.",
        }
        
    def get_available_tools(self):
        return list(self.tools.keys())
        
    async def route(self, intent: str, context: str) -> str:
        intent_lower = intent.lower()
        
        if "chrome" in intent_lower or "browser" in intent_lower:
            return self.tools["browser"](context)
        elif "vscode" in intent_lower or "code" in intent_lower:
            return self.tools["vscode"](context)
        elif "folder" in intent_lower or "directory" in intent_lower:
            # Extract path from context or use a default
            path = context.replace("open folder", "").strip()
            return self.tools["folder"](path or "C:\\")
            
        return None
