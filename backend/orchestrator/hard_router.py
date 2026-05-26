import re
import time
from typing import Optional, Tuple
from core.logger import get_logger
from tools.system_action_tool import SystemActionTool

logger = get_logger("hard_router")

class HardRouter:
    """
    Layer 1 — HARD ROUTER
    Deterministic keyword/regex interception layer.
    Executes BEFORE the planner, tool selection LLM, or conversational generation.
    Handles math expressions, app launches, and time/date requests with zero LLM usage.
    """
    
    def __init__(self):
        self.system_tool = SystemActionTool()
        self.app_aliases = {
            "vscode": "code",
            "calculator": "calc.exe",
            "chrome": "chrome",
        }

    def try_evaluate_math(self, expr: str) -> Optional[str]:
        """Safely evaluates pure math expressions."""
        # Ensure expression contains only digits, basic operators, brackets, decimals, and whitespace
        if re.match(r'^[\d+\-*/().\s%*]+$', expr) and any(c.isdigit() for c in expr):
            try:
                # Safely evaluate using clean globals/locals
                res = eval(expr, {"__builtins__": None}, {})
                return str(res)
            except Exception as e:
                logger.error(f"[HARD_ROUTER] Math evaluation failed for '{expr}': {e}")
                return f"Error: {str(e)}"
        return None

    def route(self, query: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Routes deterministic actions.
        Returns a tuple: (is_routed, response_text, selected_tool)
        """
        query_clean = query.strip().lower()

        # 1. TIME/DATE INTERCEPTION
        time_patterns = [
            r'\bwhat\s+(is\s+)?(the\s+)?time\b',
            r"\bwhat's\s+the\s+time\b",
            r'\bcurrent\s+time\b',
            r'\bwhat\s+(is\s+)?(the\s+)?date\b',
            r'\bcurrent\s+date\b',
            r'^time$',
            r'^date$',
            r'^clock$'
        ]
        if any(re.search(pat, query_clean) for pat in time_patterns):
            from datetime import datetime
            time_str = datetime.now().strftime('%I:%M %p, %B %d, %Y')
            response_text = f"[DETERMINISTIC_RESPONSE] Current time: {time_str}"
            logger.info(f"[HARD_ROUTER] Routed time/date query. Selected Tool: get_time")
            return True, response_text, "get_time"

        # 2. HARD CALCULATOR BYPASS
        is_calc = False
        expr = query_clean
        if query_clean.startswith("calculate"):
            expr = query_clean[len("calculate"):].strip()
            is_calc = True
            
        math_result = self.try_evaluate_math(expr)
        if math_result is not None:
            response_text = f"[DETERMINISTIC_RESPONSE] {math_result}"
            logger.info(f"[HARD_ROUTER] Routed math expression: '{expr}'. Selected Tool: calculator")
            return True, response_text, "calculator"
        elif is_calc:
            response_text = f"[DETERMINISTIC_RESPONSE] Error: Invalid math expression '{expr}'"
            logger.info(f"[HARD_ROUTER] Routed invalid math calculation: '{expr}'. Selected Tool: calculator")
            return True, response_text, "calculator"

        # 3. APP LAUNCH INTERCEPTION
        launch_match = re.match(r'^(open|launch|start|run)\s+(.+)$', query_clean)
        if launch_match:
            app_name = launch_match.group(2).strip()
            mapped_name = self.app_aliases.get(app_name.lower(), app_name)
            result = self.system_tool.execute(action="open_app", target=mapped_name)
            response_text = f"[DETERMINISTIC_RESPONSE] {result}"
            logger.info(f"[HARD_ROUTER] Routed app launch: '{app_name}' (mapped to '{mapped_name}'). Selected Tool: open_app")
            return True, response_text, "open_app"

        # 4. WORKSPACE CONTINUITY INTERCEPTION
        workspace_patterns = [
            r'\bcontinue\s+my\s+(\w+)\s+work\b',
            r'\brestore\s+yesterday\'s\s+([\w\s]+)\bresearch\b',
            r'\bopen\s+the\s+repo\s+I\s+worked\s+on\b',
            r'\bcontinue\s+my\s+work\b',
            r'\brestore\s+my\s+workspace\b'
        ]
        if any(re.search(pat, query_clean) for pat in workspace_patterns) or "last night" in query_clean:
            from memory.workspace_memory import workspace_memory
            ws = workspace_memory.query_workspace(query_clean)
            if ws:
                self.system_tool.execute(action="open_app", target="code")
                response_text = (
                    f"[DETERMINISTIC_RESPONSE] Restored project workspace:\n"
                    f"- **Project**: {ws['project_name']}\n"
                    f"- **Path**: `{ws['project_path']}`\n"
                    f"- **Git Branch**: `{ws['git_branch']}`\n"
                    f"- **Recent Files**: " + ", ".join([f"`{f}`" for f in ws['recent_files'][:3]]) + "\n"
                    f"Successfully restored workspace context in VSCode."
                )
            else:
                response_text = "[DETERMINISTIC_RESPONSE] No recently recorded workspaces found to restore."
            logger.info("[HARD_ROUTER] Routed workspace restoration query. Selected Tool: workspace_memory")
            return True, response_text, "workspace_memory"

        return False, None, None

# Singleton Instance
hard_router = HardRouter()
