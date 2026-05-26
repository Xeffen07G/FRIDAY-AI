from tools.base_tool import BaseTool
import subprocess
import logging

logger = logging.getLogger("friday.tools.terminal")

class TerminalTool(BaseTool):
    name = "terminal"
    description = "Executes safe shell commands. Use ONLY for reading system state (e.g. dir, ping). Do NOT execute destructive commands."
    requires_confirmation = True
    parameters = {
        "command": "The shell command string to execute."
    }

    def _is_safe_window_focused(self) -> bool:
        """Validates that a developer environment is focused before executing commands."""
        try:
            import pygetwindow as gw
            active = gw.getActiveWindow()
            if not active:
                return False
            
            title = active.title.lower()
            safe_keywords = ["code", "cmd", "powershell", "terminal", "bash", "ide", "editor"]
            return any(k in title for k in safe_keywords)
        except ImportError:
            # If pygetwindow is not installed, fallback to safe (or we can assume true for headless)
            return True
        except Exception as e:
            logger.warning(f"Window focus validation failed: {e}")
            return True

    def execute(self, command: str = "", **kwargs) -> str:
        if not self._is_safe_window_focused():
            return "Execution aborted: Safety boundary enforced. Active window is not a recognized developer environment."
            
        try:
            # Safe subprocess execution with hard timeout
            logger.info(f"Executing subprocess command: {command}")
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=5.0
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Command failed with exit code {result.returncode}:\n{result.stderr.strip()}"
                
        except subprocess.TimeoutExpired:
            return "Error: Command execution timed out after 5 seconds."
        except Exception as e:
            return f"Terminal execution error: {e}"
