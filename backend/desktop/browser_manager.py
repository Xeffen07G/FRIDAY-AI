import pygetwindow as gw
import win32gui
import win32process
import psutil
from core.logger import get_logger

logger = get_logger("desktop.browser")

class BrowserManager:
    """Detects and manages browser context for Chrome, Edge, and Firefox."""
    
    SUPPORTED_BROWSERS = ["chrome.exe", "msedge.exe", "firefox.exe"]

    def get_active_tabs(self):
        """Returns a list of detected browser tabs from open windows."""
        tabs = []
        try:
            for win in gw.getWindowsWithTitle(''):
                try:
                    handle = win._hWnd
                    _, pid = win32process.GetWindowThreadProcessId(handle)
                    process = psutil.Process(pid)
                    if process.name().lower() in self.SUPPORTED_BROWSERS:
                        tabs.append({
                            "browser": process.name().lower(),
                            "title": win.title,
                            "is_active": win.isActive
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                    continue
        except Exception as e:
            logger.error(f"Failed to poll browser windows: {e}")
        return tabs

    def get_research_snapshot(self):
        """Creates a snapshot of the current research session."""
        tabs = self.get_active_tabs()
        if not tabs: return "No active browser sessions detected."
        
        snapshot = "Research Session Snapshot:\n"
        for t in tabs:
            status = "[ACTIVE]" if t['is_active'] else ""
            snapshot += f"- {t['browser'].replace('.exe', '').capitalize()}: {t['title']} {status}\n"
        return snapshot

browser_manager = BrowserManager()
