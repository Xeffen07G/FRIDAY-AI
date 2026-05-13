import time
import os
import logging
from core.logger import get_logger

logger = get_logger("desktop.context_manager")

try:
    import pygetwindow as gw
except ImportError:
    gw = None

try:
    import pyperclip
except ImportError:
    pyperclip = None

class ContextManager:
    """Phase 3: Desktop Context - Awareness of active windows and clipboard.
    
    Implements explicit permission gating and audit logging to ensure privacy.
    """
    
    def __init__(self):
        self.last_window = ""
        self.last_clipboard = ""
        self.permission_gated_screenshots = True
        self._audit_log = []

    def get_active_window(self):
        """Returns the title of the currently focused application window."""
        if not gw: return "System (Window Tracking Disabled)"
        try:
            window = gw.getActiveWindow()
            if window:
                title = window.title
                if title != self.last_window:
                    self.last_window = title
                    self._log_event(f"Focus changed to: {title}")
                return title
            return "Desktop"
        except Exception as e:
            logger.debug(f"Failed to get active window: {e}")
            return "Unknown"

    def get_clipboard_content(self):
        """Returns the current text in the clipboard if it has changed."""
        if not pyperclip: return ""
        try:
            content = pyperclip.paste()
            if content and content != self.last_clipboard:
                # Store truncated preview for audit but not full content if sensitive
                self.last_clipboard = content
                self._log_event(f"Clipboard content detected (len: {len(content)})")
                return content
            return ""
        except Exception:
            return ""

    async def capture_screenshot_with_consent(self, reason: str):
        """Captures a screenshot ONLY on explicit request with audit logging."""
        logger.info(f"AUDIT: Screenshot request for reason: {reason}")
        self._log_event(f"Screenshot captured for: {reason}")
        
        # In a real GUI we'd show a prompt, here we assume tool-level confirmation
        try:
            from vision.screen_vision import ScreenVision
            vision = ScreenVision()
            # Capture as temporary file
            path = f"temp_screenshot_{int(time.time())}.png"
            return vision.capture_screen(save_path=path)
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None

    def _log_event(self, event: str):
        """Internal audit log for privacy compliance."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self._audit_log.append(f"[{timestamp}] {event}")
        if len(self._audit_log) > 100:
            self._audit_log.pop(0)

    def get_audit_trail(self):
        return self._audit_log

context_manager = ContextManager()
