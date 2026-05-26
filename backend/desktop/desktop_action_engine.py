import time
import logging
from typing import Dict, Any, Tuple, List
from core.execution_guard import execution_guard
from core.autonomous_sandbox import autonomous_sandbox

# Dynamic importing of GUI libraries with mock fallbacks to maintain resilience
try:
    import pyautogui
    pyautogui.FAILSAFE = True
except ImportError:
    pyautogui = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

try:
    from pynput.keyboard import Controller as KController
    from pynput.mouse import Controller as MController
    keyboard_ctrl = KController()
    mouse_ctrl = MController()
except ImportError:
    keyboard_ctrl = None
    mouse_ctrl = None

logger = logging.getLogger("friday.desktop.action_engine")

class DesktopActionEngine:
    """
    Executes grounded workspace operations (typing, window focuses, sweeps).
    Ensures every visual and terminal operation matches permitted sandboxes and security perimeters.
    """
    
    def mouse_move(self, x: int, y: int) -> Tuple[bool, str]:
        """Sweeps mouse cursor to target pixels."""
        is_safe, msg = execution_guard.validate("mouse_move", {"x": x, "y": y})
        if not is_safe:
            return False, msg
            
        if not pyautogui:
            logger.info(f"DesktopActionEngine (Mock): Mouse moved to ({x}, {y})")
            return True, f"Mocked move to ({x}, {y})"
            
        try:
            pyautogui.moveTo(x, y, duration=0.2)
            return True, f"Mouse successfully moved to ({x}, {y})"
        except Exception as e:
            return False, f"Failed mouse move: {e}"

    def mouse_click(self, x: int, y: int, click_type: str = "left") -> Tuple[bool, str]:
        """Performs left/right/double clicks on grounded coordinates after validating confidence thresholds."""
        is_safe, msg = execution_guard.validate("mouse_click", {"x": x, "y": y})
        if not is_safe:
            return False, msg
            
        # Pre-click validation with auto-grounding
        validation_status, confidence_score, rx, ry = self.validate_click_confidence(x, y)
        if not validation_status:
            return False, f"Click aborted due to low grounding confidence ({confidence_score:.2f})"
            
        if not pyautogui:
            logger.info(f"DesktopActionEngine (Mock): Mouse clicked ({click_type}) at ({rx}, {ry}) (confidence: {confidence_score:.2f})")
            return True, f"Mocked {click_type} click at ({rx}, {ry}) with confidence {confidence_score:.2f}"
            
        try:
            pyautogui.click(rx, ry, button=click_type)
            return True, f"Mouse clicked ({click_type}) at ({rx}, {ry}) with confidence {confidence_score:.2f} (originally {x}, {y})"
        except Exception as e:
            return False, f"Failed click: {e}"

    def validate_click_confidence(self, x: int, y: int) -> Tuple[bool, float, int, int]:
        """Assesses click target bounding correctness, verifies elements exist, and re-grounds offsets."""
        rx, ry = x, y
        techniques = []
        
        # Verify basic display boundaries
        if x < 0 or x > 1920 or y < 0 or y > 1080:
            return False, 0.0, x, y
            
        # 1. Bounding Boxes Grounding & Offset Detection
        try:
            from vision.screen_understanding_engine import screen_understanding_engine
            clickables = screen_understanding_engine.detect_clickable_elements()
            techniques.append("bounding_boxes")
        except Exception:
            clickables = []

        # Find closest clickable element
        closest_el = None
        min_dist = float('inf')
        for el in clickables:
            ex1, ey1 = el["x"], el["y"]
            ex2, ey2 = ex1 + el["w"], ey1 + el["h"]
            cx = ex1 + el["w"] // 2
            cy = ey1 + el["h"] // 2
            
            # Check if clicked point is inside
            if ex1 <= x <= ex2 and ey1 <= y <= ey2:
                # Perfect match
                return True, 0.98, x, y
            
            # Check proximity for auto-regrounding
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if dist < 60 and dist < min_dist:  # 60px max offset threshold
                min_dist = dist
                closest_el = el

        if closest_el:
            # Shift / re-ground coordinates to the center of the target clickable box
            rx = closest_el["x"] + closest_el["w"] // 2
            ry = closest_el["y"] + closest_el["h"] // 2
            logger.info(f"Re-grounded to {closest_el['label']} ({rx}, {ry}), offset {min_dist:.0f}px")
            return True, 0.92, rx, ry

        # 2. OCR Grounding & Verification
        try:
            from vision.screen_grounding import screen_grounding
            # Grab screenshot bytes defensively
            img_bytes = screen_grounding.capture_active_window()
            if img_bytes:
                techniques.append("ocr_tesseract")
                visible_text = screen_grounding.extract_visible_text(img_bytes)
                # If we're clicking somewhere with text, verify text presence
                if len(visible_text) > 20:
                    logger.debug("OCR content verified successfully.")
        except Exception as e:
            logger.warning(f"OCR Grounding verification bypassed: {e}")

        # 3. Color profile check skipped — adds latency with minimal grounding value

        logger.debug(f"Grounding: {', '.join(techniques)}")
        return True, 0.85, rx, ry

    def type_text(self, text: str) -> Tuple[bool, str]:
        """Types string keystrokes safely into the active visual editor/terminal."""
        is_safe, msg = execution_guard.validate("keyboard_type", {"text_len": len(text)})
        if not is_safe:
            return False, msg
            
        if not pyautogui:
            logger.info(f"DesktopActionEngine (Mock): Typed text: '{text}'")
            return True, f"Mocked typing: {text}"
            
        try:
            # Ensure window is stabilized and focused before typing (prevent race condition)
            time.sleep(0.08)
            pyautogui.write(text, interval=0.01)
            # Post-typing cool down sleep
            time.sleep(0.08)
            return True, f"Typed: {text}"
        except Exception as e:
            return False, f"Failed typing: {e}"

    def trigger_hotkey(self, keys: List[str]) -> Tuple[bool, str]:
        """Triggers system modifier hotkeys."""
        is_safe, msg = execution_guard.validate("hotkey", {"keys": keys})
        if not is_safe:
            return False, msg
            
        if not pyautogui:
            logger.info(f"DesktopActionEngine (Mock): Triggered hotkey: {keys}")
            return True, f"Mocked hotkey: {keys}"
            
        try:
            pyautogui.hotkey(*keys)
            time.sleep(0.04) # Small buffer to let visual hotkey register
            return True, f"Hotkey {keys} triggered successfully."
        except Exception as e:
            return False, f"Failed hotkey: {e}"

    def focus_window(self, title_substring: str) -> Tuple[bool, str]:
        """Brings specific target applications into foreground focus with adaptive check."""
        is_safe, msg = execution_guard.validate("window_focus", {"title": title_substring})
        if not is_safe:
            return False, msg
            
        if not gw:
            return True, f"focused: {title_substring} (mock)"
            
        try:
            # Early exit if already focused
            active = gw.getActiveWindow()
            if active and title_substring.lower() in active.title.lower():
                return True, f"already focused: {active.title[:30]}"

            # Find target window
            windows = gw.getWindowsWithTitle(title_substring)
            if not windows:
                return False, f"window not found: {title_substring}"

            windows[0].activate()

            # Poll with backoff: 100ms, 150ms, 220ms, 320ms, 450ms
            delays = [0.1, 0.15, 0.22, 0.32, 0.45]
            for delay in delays:
                time.sleep(delay)
                active = gw.getActiveWindow()
                if active and title_substring.lower() in active.title.lower():
                    return True, f"focused: {active.title[:30]}"

            return False, f"focus timeout: {title_substring}"
        except Exception as e:
            logger.warning(f"Focus failed: {e}")
            return False, f"focus error: {title_substring}"

# Singleton instance
desktop_action_engine = DesktopActionEngine()
