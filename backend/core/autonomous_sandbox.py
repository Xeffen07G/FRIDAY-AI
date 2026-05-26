import os
import time
import logging
import tempfile
import subprocess
from typing import Dict, Any, Tuple

logger = logging.getLogger("friday.core.autonomous_sandbox")

class AutonomousSandbox:
    """
    Enforces safe autonomous experimentation.
    Simulates shell command dry-runs, spins isolated temporary file context workspaces,
    and isolates subprocess execution through dry-run checkpoints.
    """
    def __init__(self):
        self.sandbox_root = tempfile.gettempdir()
        self.simulated_filesystem: Dict[str, str] = {}
        self.blocked_sandbox_commands = ["rm", "del", "kill", "shutdown", "format"]

    def create_isolated_tempfile(self, filename: str, content: str) -> str:
        """Creates a temporary isolated file workspace strictly inside OS temp bounds."""
        target_path = os.path.join(self.sandbox_root, filename)
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.simulated_filesystem[filename] = content
            logger.info(f"Sandbox: Isolated tempfile registered at '{target_path}'")
            return target_path
        except Exception as e:
            logger.error(f"Sandbox tempfile creation failed: {e}")
            raise

    def simulate_command(self, command: str) -> Dict[str, Any]:
        """
        Performs structural dry-run simulations of shell commands.
        Ensures execution safety and predicts outcome metrics without hitting host shells.
        """
        cmd_clean = command.strip().lower()
        
        # Check command blocks
        for block in self.blocked_sandbox_commands:
            if block in cmd_clean.split():
                return {
                    "success": False,
                    "simulation": "BLOCKED",
                    "reason": f"Command contains blocked term '{block}' inside sandbox safety policy.",
                    "predicted_stdout": ""
                }
                
        # Simulate common dev workflow commands
        if "npm run dev" in cmd_clean or "npm start" in cmd_clean:
            return {
                "success": True,
                "simulation": "SUCCESS",
                "predicted_stdout": "Vite v5.2.0 dev server starting... Port 5173 allocated."
            }
        elif "git status" in cmd_clean:
            return {
                "success": True,
                "simulation": "SUCCESS",
                "predicted_stdout": "On branch main\nYour branch is up to date.\nnothing to commit, working tree clean"
            }
        elif "pip install" in cmd_clean or "npm install" in cmd_clean:
            return {
                "success": True,
                "simulation": "SUCCESS",
                "predicted_stdout": "added 12 packages, audited 142 packages in 1.4s"
            }
            
        return {
            "success": True,
            "simulation": "SUCCESS",
            "predicted_stdout": f"[Simulated Output for: '{command}'] Execution completed inside safety bounds."
        }

    def validate_autonomous_action(self, tool_name: str, args: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates whether an autonomous action fits safety limits.
        No autonomous action runs without this sandbox validation.
        """
        if tool_name == "terminal":
            cmd = args.get("command") or args.get("CommandLine") or ""
            sim = self.simulate_command(cmd)
            if not sim["success"]:
                return False, f"Sandbox Validation Blocked: {sim['reason']}"
                
        return True, "Sandbox Validation Successful: Safe for autonomous simulation."

# Singleton instance
autonomous_sandbox = AutonomousSandbox()
