import re
import os
import time
import logging
from typing import Dict, Any, Tuple, List

logger = logging.getLogger("friday.core.execution_guard")

class ExecutionGuard:
    """
    Enforces a strict safety perimeter on F.R.I.D.A.Y.'s tool runner.
    Vows filesystem restrictions, command analysis, rate limiting, and rollback triggers.
    """
    def __init__(self):
        self.allowed_workspace = "c:\\users\\sayak\\downloads\\jarvis"
        self.allowed_workspace_alt = "c:/users/sayak/downloads/jarvis"
        
        self.system_directories = [
            "c:\\windows",
            "c:\\program files",
            "c:\\program files (x86)",
            "c:\\users\\sayak\\appdata\\local\\microsoft",
            "system32",
            "/etc",
            "/bin",
            "/usr"
        ]

        self.dangerous_commands = [
            r"\brm\s+-rf\b",
            r"\brmdir\s+/s\b",
            r"\bdel\s+/s\b",
            r"\bformat\b",
            r"\breg\s+add\b",
            r"\breg\s+delete\b",
            r"\bnet\s+user\b",
            r"\bshutdown\b",
            r"\bpowershell\s+-exec\b",
            r"\bkill\b"
        ]

        # Rate limiting state
        self.action_timestamps: List[float] = []
        self.max_rate_actions = 10     # Max actions
        self.rate_window = 10.0       # sliding window in seconds

        # Task 12: Safety Hardening states
        self.recent_commands: List[str] = []
        self.consecutive_rapid_actions = 0
        self.last_action_time = 0.0

    def is_path_safe(self, target_path: str) -> bool:
        if not target_path:
            return True
        norm_path = os.path.abspath(target_path).lower()
        for sys_dir in self.system_directories:
            if sys_dir in norm_path:
                return False
        if norm_path.startswith(self.allowed_workspace) or norm_path.startswith(self.allowed_workspace_alt):
            return True
        if "antigravity" in norm_path or "gemini" in norm_path:
            return True
        return False

    def is_command_safe(self, command: str) -> Tuple[bool, str]:
        if not command:
            return True, ""
        command_clean = command.strip().lower()
        
        # Privilege Escalation Blocking
        if "runas" in command_clean or "elevate" in command_clean or "sudo" in command_clean:
            return False, "Blocked: Privilege escalation command parameters detected."

        for pattern in self.dangerous_commands:
            if re.search(pattern, command_clean):
                return False, f"Blocked: Matches dangerous pattern regex '{pattern}'"
                
        if "rm " in command_clean and "-r" in command_clean:
            return False, "Blocked: Recursive delete operations are prohibited."
            
        return True, ""

    def validate_click_coordinates(self, x: int, y: int) -> Tuple[bool, str]:
        """Prevents clicks into dangerous system-critical UI coordinates (e.g. top-left close menus)."""
        if x < 40 and y < 40:
            return False, "Blocked: Action falls inside system close menu quadrant (0-40px)."
        return True, "Safe coordinate path."

    def validate_hotkey(self, keys: List[str]) -> Tuple[bool, str]:
        """Filters out high-risk or destructive shortcut keys."""
        keys_clean = [k.lower() for k in keys]
        if "alt" in keys_clean and "f4" in keys_clean:
            return False, "Blocked: Alt+F4 destructive hotkey filtered."
        if "ctrl" in keys_clean and "alt" in keys_clean and "delete" in keys_clean:
            return False, "Blocked: Ctrl+Alt+Del secure channel hotkey filtered."
        return True, "Safe hotkey sequence."

    def detect_runaway_loops(self, tool_name: str, args: Dict[str, Any]) -> Tuple[bool, str]:
        """Provides anti-loop protection and runaway execution gate filters."""
        now = time.time()
        
        # 1. Runaway Execution Rate Limits
        if now - self.last_action_time < 0.2:  # consecutive action within 200ms
            self.consecutive_rapid_actions += 1
            if self.consecutive_rapid_actions > 5:
                return False, "Blocked: Runaway execution loop identified (consecutive action latency < 200ms)."
        else:
            self.consecutive_rapid_actions = 0
            
        self.last_action_time = now

        # 2. Command Duplication Loop Detection
        if tool_name == "terminal":
            cmd = args.get("command") or args.get("CommandLine") or ""
            self.recent_commands.append(cmd)
            if len(self.recent_commands) > 4:
                self.recent_commands.pop(0)
            if len(self.recent_commands) == 4 and len(set(self.recent_commands)) == 1:
                return False, f"Blocked: Repeating command loop detected on '{cmd}'."
                
        return True, "Safe execution loops."

    def check_rate_limit(self) -> bool:
        now = time.time()
        self.action_timestamps = [t for t in self.action_timestamps if now - t < self.rate_window]
        if len(self.action_timestamps) >= self.max_rate_actions:
            return False
        self.action_timestamps.append(now)
        return True

    def validate(self, tool_name: str, args: Dict[str, Any]) -> Tuple[bool, str]:
        if not self.check_rate_limit():
            return False, f"Blocked: Rate limit exceeded. (Max {self.max_rate_actions} calls per {self.rate_window}s)"

        # Anti-loop checks
        loop_ok, loop_msg = self.detect_runaway_loops(tool_name, args)
        if not loop_ok:
            return False, loop_msg

        # Coordinates check
        if tool_name == "mouse_click" or tool_name == "mouse_move":
            x = int(args.get("x") or 0)
            y = int(args.get("y") or 0)
            ok, msg = self.validate_click_coordinates(x, y)
            if not ok:
                return False, msg

        # Hotkeys check
        if tool_name == "hotkey":
            keys = args.get("keys") or []
            ok, msg = self.validate_hotkey(keys)
            if not ok:
                return False, msg

        # Terminal check
        if tool_name == "terminal" or tool_name == "system_action":
            command = args.get("command") or args.get("cmd") or args.get("CommandLine") or ""
            is_safe, reason = self.is_command_safe(command)
            if not is_safe:
                return False, reason

        # Filesystem check
        target_file = args.get("TargetFile") or args.get("path") or args.get("file_path") or args.get("Cwd")
        if target_file and isinstance(target_file, str):
            if not self.is_path_safe(target_file):
                return False, f"Blocked: Target path '{target_file}' lies outside permitted workspaces."

        # Emit audit event
        from core.event_bus import event_bus
        event_bus.emit(
            component="execution_guard",
            event_type="safety_evaluated",
            data={"tool": tool_name, "approved": True},
            level="INFO"
        )
        
        return True, "Safety check successful."

execution_guard = ExecutionGuard()
