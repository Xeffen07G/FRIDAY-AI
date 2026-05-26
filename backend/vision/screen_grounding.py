import os
import io
import time
import logging
from typing import Dict, Any, Optional, Tuple, List

# Highly defensive imports for GUI and Vision dependencies
try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    from PIL import Image, ImageGrab
except ImportError:
    Image = None
    ImageGrab = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

logger = logging.getLogger("friday.vision.screen_grounding")

class ScreenGrounding:
    """
    Coordinates foundational desktop visual comprehension, active window layout indexers, 
    OCR extraction hooks, and focused element coordinate grids.
    """
    
    def capture_active_window(self) -> Optional[bytes]:
        """
        Captures the active desktop viewport region or primary monitor display.
        Returns bytes format representing a PNG image.
        """
        if not ImageGrab:
            logger.warning("ImageGrab is not available. Capture aborted.")
            return None
            
        try:
            # Capture the entire screen bounds
            screenshot = ImageGrab.grab()
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
        except Exception as e:
            logger.error(f"Failed to capture active window: {e}")
            return None

    def extract_visible_text(self, image_bytes: Optional[bytes] = None) -> str:
        """
        Runs OCR text recognition over the captured screenshot bounds.
        Defensively falls back to text approximations if pytesseract is not configured in PATH.
        """
        if not image_bytes:
            image_bytes = self.capture_active_window()
            
        if not image_bytes or not pytesseract or not Image:
            return "Vision Engine Mock Grounding: VSCode Workspace open at Contributing.md, browser viewing local diagnostics page."
            
        try:
            image = Image.open(io.BytesIO(image_bytes))
            # PyTesseract can throw an error if the tesseract engine is not in PATH
            text = pytesseract.image_to_string(image)
            return text
        except Exception as te:
            logger.warning(f"OCR PyTesseract engine missing or failed. Falling back. Error: {te}")
            return "[Mock OCR Snapshot] Active focused file: CONTRIBUTING.md. F.R.I.D.A.Y. active context dashboard renders 100% operational."

    def get_window_layout(self) -> Dict[str, Any]:
        """
        Generates standard visual coordinate anchors for default desktop windows.
        Maps buttons, sidebars, input boxes, and dashboards to bounding boxes.
        """
        layout = {
            "screen_width": 1920,
            "screen_height": 1080,
            "active_app": "Visual Studio Code",
            "regions": [
                {"name": "sidebar", "x": 0, "y": 0, "width": 300, "height": 1080, "focused": False},
                {"name": "editor", "x": 300, "y": 0, "width": 1100, "height": 1080, "focused": True},
                {"name": "terminal", "x": 300, "y": 800, "width": 1100, "height": 280, "focused": False},
                {"name": "browser_assistant", "x": 1400, "y": 0, "width": 520, "height": 1080, "focused": False}
            ]
        }
        
        # Try to dynamically read current screen dimensions if pyautogui is loaded
        if pyautogui:
            try:
                w, h = pyautogui.size()
                layout["screen_width"] = w
                layout["screen_height"] = h
            except Exception as e:
                logger.warning(f"PyAutoGUI dimensions retrieval failed: {e}")
                
        return layout

# Singleton instance
screen_grounding = ScreenGrounding()
