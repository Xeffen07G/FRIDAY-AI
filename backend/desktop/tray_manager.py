import pystray
from PIL import Image, ImageDraw
import threading
from core.logger import get_logger

logger = get_logger("desktop.tray")

def create_image():
    # Create a simple 64x64 icon for the tray
    image = Image.new('RGB', (64, 64), (15, 23, 42)) # Slate 900
    dc = ImageDraw.Draw(image)
    dc.ellipse([16, 16, 48, 48], fill=(59, 130, 246)) # Blue 500
    return image

class TrayManager:
    """Manages the system tray icon and quick actions."""
    
    def __init__(self):
        self.icon = None
        self._thread = None
        self._disabled = False

    def start(self):
        if self._thread or self._disabled: return
        
        try:
            # Note: pystray.Menu.SEPARATOR or None works for separators
            self.icon = pystray.Icon(
                "FRIDAY",
                create_image(),
                menu=pystray.Menu(
                    pystray.MenuItem("F.R.I.D.A.Y. Online", None, enabled=False),
                    pystray.MenuItem("---", None, enabled=False), # Alternative separator
                    pystray.MenuItem("Show Assistant", self._show_action, default=True),
                    pystray.MenuItem("Push to Talk", self._ptt_action),
                    pystray.MenuItem("Pause Listening", self._pause_action),
                    pystray.MenuItem("---", None, enabled=False),
                    pystray.MenuItem("Engineering Hub", self._hub_action),
                    pystray.MenuItem("Restart Runtime", self._restart_action),
                    pystray.MenuItem("Exit", self._exit_action)
                )
            )
            
            self._thread = threading.Thread(target=self.icon.run, daemon=True)
            self._thread.start()
            logger.info("Tray Manager: ONLINE")
        except Exception as e:
            logger.error(f"Tray Manager initialization failed: {e}")
            self._disabled = True
            raise e
        
    def _safe_start(self):
        try:
            self.start()
        except Exception as e:
            logger.error(f"Tray Manager failed: {e}. System will run in trayless mode.")
            self._disabled = True

    def _show_action(self, icon, item):
        from core.event_bus import event_bus
        event_bus.emit("desktop", "ui_focus_toggle", {"action": "show"})

    def _ptt_action(self, icon, item):
        from core.event_bus import event_bus
        event_bus.emit("desktop", "ptt_event", {"state": "pressed"})
        import time
        time.sleep(5) # Simulate hold
        event_bus.emit("desktop", "ptt_event", {"state": "released"})

    def _pause_action(self, icon, item):
        from core.event_bus import event_bus
        event_bus.emit("desktop", "status_update", {"state": "paused"})

    def _restart_action(self, icon, item):
        import sys
        import os
        os.execv(sys.executable, ['python'] + sys.argv)

    def _hub_action(self, icon, item):
        import webbrowser
        webbrowser.open("http://localhost:5173/assistant?tab=engineering")

    def _exit_action(self, icon, item):
        logger.info("System Exit via Tray requested.")
        icon.stop()
        import os
        os._exit(0)

tray_manager = TrayManager()
