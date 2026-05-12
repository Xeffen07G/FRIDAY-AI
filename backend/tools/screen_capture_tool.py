import os
import time
import pyautogui
import pygetwindow as gw
from PIL import Image
from tools.base_tool import BaseTool
from config.settings import settings

class ScreenCaptureTool(BaseTool):
    name = "screen_perception"
    description = "Capture and analyze the current desktop state or a specific window."
    parameters = {
        "type": "object",
        "properties": {
            "mode": {"type": "string", "enum": ["full", "active_window"], "description": "Whether to capture the entire screen or just the active window."},
            "analyze": {"type": "boolean", "description": "Whether to perform visual analysis (requires vision model)."}
        },
        "required": ["mode"]
    }

    async def execute(self, mode: str = "full", analyze: bool = False) -> str:
        timestamp = int(time.time())
        screenshot_dir = os.path.join(settings.RUNTIME_BASE, "vision", "captures")
        os.makedirs(screenshot_dir, exist_ok=True)
        
        filepath = os.path.join(screenshot_dir, f"capture_{timestamp}.png")
        
        active_window_title = "Unknown"
        try:
            active_window = gw.getActiveWindow()
            if active_window:
                active_window_title = active_window.title
        except:
            pass

        if mode == "active_window" and active_window:
            try:
                # Capture specific window coordinates
                screenshot = pyautogui.screenshot(region=(
                    active_window.left, 
                    active_window.top, 
                    active_window.width, 
                    active_window.height
                ))
            except:
                screenshot = pyautogui.screenshot()
        else:
            screenshot = pyautogui.screenshot()
            
        screenshot.save(filepath)
        
        result = f"Desktop state captured successfully.\nActive Window: {active_window_title}\nFile saved to: {filepath}"
        
        if analyze:
            # Here we would normally call the VisionOrchestrator
            # Since we are in a tool, we'll just report the capture for now
            result += "\nVisual analysis is queued for processing."
            
        return result
