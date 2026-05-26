import asyncio
import os
import sys
import time
import logging
from typing import Dict, Any, Optional
from core.event_bus import event_bus, EventPriority
from desktop.context_manager import context_manager

logger = logging.getLogger("friday.core.context_engine")

class ContextEngine:
    """
    Task 1: Active Context Engine
    Continuous context awareness governing window focus, workspaces, git state, 
    terminal presence, clipboard, and browser activities.
    """
    def __init__(self):
        self.current_window = ""
        self.current_clipboard = ""
        self.current_workspace = ""
        self.current_git_repo = ""
        self.current_git_branch = ""
        self.is_running = False
        self._observer_task = None

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._observer_task = asyncio.create_task(self._context_loop())
        logger.info("ContextEngine: Active and Observing Desktop Context")

    async def stop(self):
        self.is_running = False
        if self._observer_task:
            self._observer_task.cancel()
        logger.info("ContextEngine: Paused")

    def get_live_context_snapshot(self) -> Dict[str, Any]:
        """Provides high-frequency snapshot metrics for active workflows."""
        return {
            "active_app": "VSCode" if "vscode" in self.current_window.lower() else "Chrome" if "chrome" in self.current_window.lower() else "Terminal",
            "workspace": self.current_git_repo or "JARVIS",
            "focused_file": os.path.basename(self.current_window) if self.current_window else "main.py",
            "git_branch": self.current_git_branch or "main",
            "terminal_active": True
        }

    def get_current_context(self) -> Dict[str, Any]:
        """Exposes the full current snapshot of active desktop and runtime context."""
        return {
            "active_window": self.current_window,
            "workspace": self.get_workspace_context(),
            "browser": self.get_browser_context(),
            "clipboard": self.get_clipboard_context(),
            "git": {
                "repository": self.current_git_repo,
                "branch": self.current_git_branch
            },
            "timestamp": time.time()
        }

    def get_workspace_context(self) -> Dict[str, Any]:
        """Gathers information regarding active workspace folder and directory structure."""
        # Detect active working directory
        cwd = os.getcwd()
        # Check if workspace is a git repo
        is_git = os.path.exists(os.path.join(cwd, ".git"))
        return {
            "path": cwd,
            "name": os.path.basename(cwd),
            "is_git": is_git
        }

    def get_browser_context(self) -> Dict[str, Any]:
        """Identifies URL and domain insights from focused browser window title."""
        title = self.current_window
        is_browser = False
        domain = "Unknown"
        
        lower_title = title.lower()
        if "chrome" in lower_title or "edge" in lower_title or "firefox" in lower_title or "browser" in lower_title:
            is_browser = True
            # Simple heuristic matching
            parts = title.split(" - ")
            if len(parts) > 1:
                domain = parts[-2]

        return {
            "is_browser_active": is_browser,
            "window_title": title,
            "detected_domain": domain
        }

    def get_clipboard_context(self) -> Dict[str, Any]:
        """Provides the current clipboard state."""
        return {
            "length": len(self.current_clipboard),
            "preview": self.current_clipboard[:200] if self.current_clipboard else "",
            "content": self.current_clipboard
        }

    async def _context_loop(self):
        """High-frequency observation loop to check for context shifts and emit events."""
        # Warmup delay
        await asyncio.sleep(2)
        while self.is_running:
            try:
                # 1. Check Window Focus
                active_win = await asyncio.to_thread(context_manager.get_active_window)
                if active_win and active_win != self.current_window:
                    old_window = self.current_window
                    self.current_window = active_win
                    event_bus.emit(
                        component="context_engine",
                        event_type="window_changed",
                        data={"old": old_window, "new": active_win},
                        priority=EventPriority.NORMAL
                    )

                # 2. Check Clipboard Changes
                clipboard = await asyncio.to_thread(context_manager.get_clipboard_content)
                if clipboard and clipboard != self.current_clipboard:
                    self.current_clipboard = clipboard
                    event_bus.emit(
                        component="context_engine",
                        event_type="clipboard_updated",
                        data={"preview": clipboard[:100]},
                        priority=EventPriority.NORMAL
                    )

                # 3. Check Git & Workspace Status periodically
                cwd = os.getcwd()
                if cwd != self.current_workspace:
                    old_ws = self.current_workspace
                    self.current_workspace = cwd
                    
                    # Detect repository
                    self._check_git_status(cwd)
                    event_bus.emit(
                        component="context_engine",
                        event_type="workspace_changed",
                        data={
                            "old_path": old_ws,
                            "new_path": cwd,
                            "git_repo": self.current_git_repo,
                            "branch": self.current_git_branch
                        },
                        priority=EventPriority.NORMAL
                    )

            except Exception as e:
                logger.error(f"ContextEngine loop encountered error: {e}")
                
            # Scan frequency - checks active window/clipboard every 1 second
            await asyncio.sleep(1.0)

    def _check_git_status(self, path: str):
        """Safely scans for .git files/directories and reads current active branch."""
        git_dir = os.path.join(path, ".git")
        if os.path.exists(git_dir):
            self.current_git_repo = os.path.basename(path)
            # Try reading HEAD file for branch name to avoid running slow CLI commands
            try:
                head_file = os.path.join(git_dir, "HEAD")
                if os.path.exists(head_file):
                    with open(head_file, "r") as f:
                        content = f.read().strip()
                        if content.startswith("ref:"):
                            self.current_git_branch = content.split("/")[-1]
                        else:
                            self.current_git_branch = content[:8]  # Detached HEAD SHA
            except Exception:
                self.current_git_branch = "unknown"
        else:
            self.current_git_repo = ""
            self.current_git_branch = ""

# Singleton instance
context_engine = ContextEngine()
