import keyboard
import threading
from core.event_bus import event_bus
from core.logger import get_logger

logger = get_logger("desktop.hotkey")

class HotkeyManager:
    """Manages global system hotkeys for daily driver ergonomics."""
    
    def __init__(self):
        self.hotkey = "ctrl+space"
        self._is_active = False

    def start(self):
        if self._is_active: return
        self._is_active = True
        
        try:
            keyboard.add_hotkey(self.hotkey, self._on_hotkey_pressed)
            logger.info(f"Hotkey Manager: Listening for '{self.hotkey}'")
            
            # PTT Mode Listener (Caps Lock for example)
            keyboard.on_press_key("caps lock", self._on_ptt_press)
            keyboard.on_release_key("caps lock", self._on_ptt_release)
            
        except Exception as e:
            logger.error(f"Hotkey Manager failed to start: {e}")

    def _on_hotkey_pressed(self):
        logger.info("Global Hotkey Triggered: Focusing F.R.I.D.A.Y.")
        event_bus.emit("desktop", "ui_focus_toggle", {"action": "toggle"})

    def _on_ptt_press(self, e):
        event_bus.emit("desktop", "ptt_event", {"state": "pressed"})

    def _on_ptt_release(self, e):
        event_bus.emit("desktop", "ptt_event", {"state": "released"})

hotkey_manager = HotkeyManager()
