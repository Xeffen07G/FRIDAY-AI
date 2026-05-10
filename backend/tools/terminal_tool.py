from backend.tools.base_tool import BaseTool
import subprocess
import logging

logger = logging.getLogger("friday.tools.terminal")

class TerminalTool(BaseTool):
    name = "terminal"
    description = "Executes safe shell commands. Use ONLY for reading system state (e.g. dir, ping). Do NOT execute destructive commands."
    parameters = {
        "command": "The shell command string to execute."
    }

    def execute(self, command: str = "", **kwargs) -> str:
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
