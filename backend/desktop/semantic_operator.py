import os
import re
import time
import socket
import logging
import random
import subprocess
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Tuple, List

# Dynamic GUI and system imports
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
    import psutil
except ImportError:
    psutil = None

try:
    from pywinauto import Desktop as PywinautoDesktop
except ImportError:
    PywinautoDesktop = None

from core.event_bus import event_bus
from core.runtime_state import runtime_state

logger = logging.getLogger("friday.desktop.semantic_operator")

class ExecutionState:
    IDLE = "IDLE"
    QUEUED = "QUEUED"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    RECOVERING = "RECOVERING"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"

class SemanticOperator:
    """
    F.R.I.D.A.Y.'s mature, native operating layer.
    Ensures long-session stability, verified port outcomes, buffered terminal
    ANSI stripping, persistent DB continuity, and human-cadence execution.
    """
    def __init__(self):
        # Default Context Values (survives restarts via SQLITE state recovery)
        self.workspace_path = "c:\\Users\\sayak\\Downloads\\JARVIS"
        self.active_project = "JARVIS"
        self.active_ports = [5173, 8000]
        self.active_branch = "main"
        self.open_editor_files = ["main.py", "observability.py", "ws_voice.py", "useVoiceWebSocket.js"]
        self.active_error_state = None
        
        # State Machine
        self.current_state = ExecutionState.IDLE
        
        # Incremental terminal stream buffering (Task 4)
        self.terminal_partial_buffer = ""
        self.last_terminal_output_time = time.time()
        
        # Learning/Memory limits
        self.recovery_memory = {
            "occupied_port": 0,
            "lost_focus": 0,
            "terminal_hidden": 0
        }
        self.successful_timings = {
            "vite_boot_ms": 1200,
            "backend_boot_ms": 800
        }

        # Element registry coordinates
        self.semantic_element_registry = {
            "vscode_sidebar": {"x": 20, "y": 300},
            "vscode_terminal": {"x": 600, "y": 850},
            "chrome_tab_area": {"x": 300, "y": 45},
            "chrome_devtools": {"x": 1600, "y": 500},
            "terminal_input": {"x": 500, "y": 950},
            "chat_input": {"x": 960, "y": 1000}
        }

        # Semantic key -> expected parent app titles for grounding
        self.ELEMENT_APP_MAP = {
            "terminal_input": ["powershell", "cmd", "terminal", "bash", "windows terminal"],
            "vscode_sidebar": ["visual studio code", "code"],
            "vscode_terminal": ["visual studio code", "code"],
            "chrome_tab_area": ["chrome", "google chrome"],
            "chrome_devtools": ["chrome", "google chrome"],
            "chat_input": ["friday", "jarvis"],
            # Generic app class keywords
            "terminal": ["powershell", "cmd", "terminal", "bash", "windows terminal"],
            "vscode": ["visual studio code", "code"],
            "editor": ["visual studio code", "code"],
            "browser": ["chrome", "google chrome", "edge", "firefox", "browser"],
            "explorer": ["explorer", "file explorer", "this pc"],
        }

        # Execution fingerprint guard (prevents duplicate actions)
        self._last_action_hash = None
        self._last_action_time = 0.0
        self._execution_fingerprints = {}

        # UI Automation search filters
        self.ELEMENT_UIA_MAP = {
            "vscode_sidebar": {"control_type": "Custom", "automation_id": "workbench.parts.activitybar"},
            "vscode_terminal": {"control_type": "Document", "automation_id": "terminal"},
            "chrome_tab_area": {"control_type": "Tab"},
            "chat_input": {"control_type": "Edit"},
            "terminal_input": {"control_type": "Edit"}
        }

        # Authoritative App State Map
        self.app_state_map = {
            "opened_apps": [],
            "focused_app": "Unknown",
            "minimized_apps": [],
            "crashed_apps": [],
            "hidden_windows": [],
            "active_workspaces": ["JARVIS"],
            "active_ports": [5173, 8000],
            "active_branches": ["main"]
        }

        # Anti-thrashing locks
        self.last_focus_time = 0.0
        self.last_focus_target = None
        
        # Coordinate reliability scoring (Task 2)
        self.coordinate_reliability = {k: 100 for k in self.semantic_element_registry.keys()}
        
        # Auto-load workspace state from SQLite upon initialization (Task 2)
        self.load_continuity_state()

    # ==========================================
    # TASK 2: SQLite PERSISTENCE ENGINE
    # ==========================================
    def persist_continuity_state(self):
        """Saves current active workspace state to SQLITE database."""
        from memory.database import get_connection
        
        state_payload = {
            "workspace_path": self.workspace_path,
            "active_project": self.active_project,
            "active_ports": self.active_ports,
            "active_branch": self.active_branch,
            "open_editor_files": self.open_editor_files,
            "active_error_state": self.active_error_state,
            "successful_timings": self.successful_timings,
            "semantic_element_registry": self.semantic_element_registry,
            "coordinate_reliability": self.coordinate_reliability
        }
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM system_audit_log WHERE component = 'workspace_continuity'")
            cursor.execute(
                "INSERT INTO system_audit_log (id, event, component, metadata, timestamp) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), "SAVE_STATE", "workspace_continuity", json.dumps(state_payload), datetime.now().isoformat())
            )
            conn.commit()
            logger.info("Workspace continuity persisted successfully to database.")
        except Exception as e:
            logger.error(f"Failed to persist continuity state: {e}")
        finally:
            conn.close()

    def load_continuity_state(self):
        """Loads the most recent workspace state from SQLITE database."""
        from memory.database import get_connection
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT metadata FROM system_audit_log WHERE component = 'workspace_continuity' LIMIT 1")
            row = cursor.fetchone()
            if row:
                payload = json.loads(row["metadata"])
                self.workspace_path = payload.get("workspace_path", self.workspace_path)
                self.active_project = payload.get("active_project", self.active_project)
                self.active_ports = payload.get("active_ports", self.active_ports)
                self.active_branch = payload.get("active_branch", self.active_branch)
                self.open_editor_files = payload.get("open_editor_files", self.open_editor_files)
                self.active_error_state = payload.get("active_error_state", self.active_error_state)
                self.successful_timings = payload.get("successful_timings", self.successful_timings)
                self.semantic_element_registry = payload.get("semantic_element_registry", self.semantic_element_registry)
                self.coordinate_reliability = payload.get("coordinate_reliability", self.coordinate_reliability)
                logger.info("Workspace continuity state restored from database.")
        except Exception as e:
            logger.error(f"Failed to load continuity state: {e}")
        finally:
            conn.close()

    def transition_to(self, new_state: str):
        old_state = self.current_state
        self.current_state = new_state
        logger.info(f"[OPERATOR_STATE]: {old_state} -> {new_state}")
        event_bus.emit("brain", "operator_state_changed", {
            "old_state": old_state,
            "new_state": new_state,
            "timestamp": time.time()
        })

    def _adaptive_wait(self, base_ms: int, label: str = ""):
        """Wait with natural jitter, calibrated by past success timings."""
        learned = self.successful_timings.get(label, base_ms)
        actual = learned * random.uniform(0.85, 1.15)
        time.sleep(actual / 1000.0)

    def _is_duplicate_action(self, action_key: str) -> bool:
        """Returns True if the same action was executed within 400ms."""
        import hashlib
        h = hashlib.md5(action_key.encode()).hexdigest()
        now = time.time()
        if h == self._last_action_hash and (now - self._last_action_time) < 0.4:
            logger.debug(f"Duplicate action suppressed: {action_key}")
            return True
        self._last_action_hash = h
        self._last_action_time = now
        return False

    # ==========================================
    # TASK 1: ACCESSIBILITY GROUNDING & Locking
    # ==========================================
    def resolve_accessibility_element(self, target_name: str, hwnd: int) -> Any:
        """
        Connects to the active window/app via UIA and finds descendants matching targets in self.ELEMENT_UIA_MAP.
        """
        if not PywinautoDesktop:
            logger.debug("PywinautoDesktop is not available.")
            return None
        
        try:
            desktop = PywinautoDesktop(backend="uia")
            window = desktop.window(handle=hwnd)
            if not window or not window.exists():
                logger.debug(f"Window handle {hwnd} does not exist in UIA.")
                return None
            
            filters = self.ELEMENT_UIA_MAP.get(target_name)
            if not filters:
                logger.debug(f"No UIA filters mapped for target: {target_name}")
                return None
            
            descendants = window.descendants(**filters)
            if descendants:
                logger.debug(f"Found {len(descendants)} UIA elements matching '{target_name}'.")
                return descendants[0]
            else:
                logger.debug(f"No UIA elements found matching target: {target_name}")
        except Exception as e:
            logger.warning(f"UIA resolution failed for {target_name}: {e}")
        return None

    def lock_and_verify_element_rect(self, element: Any) -> Tuple[bool, Dict[str, int]]:
        """
        Audits if the element is visible, enabled, and retrieves its screen bounds safely.
        """
        if not element:
            return False, {}
        try:
            if hasattr(element, "is_visible") and not element.is_visible():
                logger.warning("UIA element is not visible.")
                return False, {}
            if hasattr(element, "is_enabled") and not element.is_enabled():
                logger.warning("UIA element is disabled.")
                return False, {}
            
            if hasattr(element, "rectangle"):
                rect = element.rectangle()
                width = rect.width()
                height = rect.height()
                if width <= 0 or height <= 0:
                    logger.warning(f"UIA element has invalid bounds: {width}x{height}")
                    return False, {}
                
                x = rect.left + width // 2
                y = rect.top + height // 2
                
                if x < 0 or y < 0 or x > 5000 or y > 5000:
                    logger.warning(f"UIA coordinates out of bounds: ({x}, {y})")
                    return False, {}
                
                return True, {"x": x, "y": y, "left": rect.left, "top": rect.top, "right": rect.right, "bottom": rect.bottom}
        except Exception as e:
            logger.warning(f"UIA element rect verification error: {e}")
        return False, {}

    def get_grounded_coordinates(self, target_name: str) -> Tuple[int, int]:
        """
        Resolves screen coordinates prioritizing active window UIA querying (Drift Recovery V2).
        """
        if gw:
            active_win = gw.getActiveWindow()
            if active_win and hasattr(active_win, "_hWnd"):
                hwnd = active_win._hWnd
                element = self.resolve_accessibility_element(target_name, hwnd)
                if element:
                    ok, rect = self.lock_and_verify_element_rect(element)
                    if ok:
                        old_coords = self.semantic_element_registry.get(target_name, {})
                        new_x, new_y = rect["x"], rect["y"]
                        if old_coords.get("x") != new_x or old_coords.get("y") != new_y:
                            logger.info(f"Visual Drift Recovery V2: Dynamic remapping for '{target_name}' from {old_coords} to ({new_x}, {new_y})")
                            self.semantic_element_registry[target_name] = {"x": new_x, "y": new_y}
                        return new_x, new_y
        
        if target_name in self.semantic_element_registry:
            coords = self.semantic_element_registry[target_name]
            return coords["x"], coords["y"]
        return -1, -1

    def record_coordinate_success(self, target_name: str):
        """Increases coordinate reliability score up to 100."""
        score = self.coordinate_reliability.get(target_name, 100)
        self.coordinate_reliability[target_name] = min(100, score + 5)
        logger.debug(f"Coordinate success for '{target_name}': score={self.coordinate_reliability[target_name]}")
        self.persist_continuity_state()

    def record_coordinate_failure(self, target_name: str):
        """Decays coordinate reliability score. Prunes from registry if score < 50."""
        score = self.coordinate_reliability.get(target_name, 100)
        new_score = max(0, score - 15)
        self.coordinate_reliability[target_name] = new_score
        logger.warning(f"Coordinate failure/drift for '{target_name}': decayed score={new_score}")
        if new_score < 50:
            if target_name in self.semantic_element_registry:
                logger.warning(f"Coordinate reliability for '{target_name}' fell below 50. Pruning coordinates to force UIA re-grounding.")
                del self.semantic_element_registry[target_name]
        self.persist_continuity_state()

    def update_authoritative_app_state(self):
        """Updates the authoritative state mapping of open, minimized, and active applications."""
        if not gw and not psutil:
            return
        
        opened_apps = set()
        minimized_apps = set()
        focused_app = "Unknown"
        
        if gw:
            try:
                for w in gw.getAllWindows():
                    if w.title and w.title.strip():
                        opened_apps.add(w.title)
                        if hasattr(w, "isMinimized") and w.isMinimized:
                            minimized_apps.add(w.title)
                active = gw.getActiveWindow()
                if active and active.title:
                    focused_app = active.title
            except Exception as e:
                logger.debug(f"Error updating window map: {e}")
                
        crashed_apps = []
        if psutil:
            try:
                for proc in psutil.process_iter(['name', 'status']):
                    try:
                        if proc.info['status'] == psutil.STATUS_ZOMBIE:
                            crashed_apps.append(proc.info['name'])
                    except Exception:
                        pass
            except Exception as e:
                logger.debug(f"Error querying process states: {e}")

        # Git branch
        active_branch = "main"
        if os.path.exists(self.workspace_path):
            try:
                head_path = os.path.join(self.workspace_path, ".git", "HEAD")
                if os.path.exists(head_path):
                    with open(head_path, "r") as f:
                        content = f.read().strip()
                        if content.startswith("ref: "):
                            active_branch = content.split("/")[-1]
            except Exception:
                pass

        active_ports = []
        for port in [5173, 8000]:
            if self.verify_port_state(port):
                active_ports.append(port)

        self.app_state_map.update({
            "opened_apps": list(opened_apps),
            "focused_app": focused_app,
            "minimized_apps": list(minimized_apps),
            "crashed_apps": crashed_apps,
            "active_ports": active_ports,
            "active_branches": [active_branch]
        })

    def check_and_suppress_duplicate(self, action_type: str, payload: Any, cooldown: float = 0.8) -> bool:
        """Prevents duplicate clicks, launches, retries, commands, or enter presses."""
        import hashlib
        serialized = f"{action_type}:{json.dumps(payload, default=str)}"
        h = hashlib.md5(serialized.encode()).hexdigest()
        now = time.time()
        
        if h in self._execution_fingerprints:
            elapsed = now - self._execution_fingerprints[h]
            if elapsed < cooldown:
                logger.warning(f"Execution Fingerprint Suppression: duplicate {action_type} suppressed. Elapsed: {elapsed:.3f}s (cooldown: {cooldown}s)")
                return True
                
        self._execution_fingerprints[h] = now
        return False

    def verify_pre_action_state(self, expected_app: str = None) -> Tuple[bool, str]:
        """Strictly verifies active window, process, expected title, visibility and minimized/restored state."""
        if not gw:
            return True, "valid (mock)"
            
        active = gw.getActiveWindow()
        if not active:
            return False, "no active foreground window"
            
        if active.isMinimized:
            return False, "active window is minimized"
            
        if not active.title or active.title.strip() == "":
            return False, "blank or invalid active window title"
            
        if expected_app:
            expected_keywords = self.ELEMENT_APP_MAP.get(expected_app, [expected_app])
            title_lower = active.title.lower()
            if not any(k.lower() in title_lower for k in expected_keywords):
                return False, f"window focus mismatch: expected {expected_app}, active is '{active.title[:30]}'"
                
        return True, "valid"

    def _check_user_interruption(self, last_mouse_pos: Tuple[int, int] = None, expected_app: str = None) -> bool:
        """Returns True if user override (sharp mouse movement, keyboard action, or external focus shift) is detected."""
        if not pyautogui:
            return False
            
        # 1. Detect sharp mouse movement
        if last_mouse_pos:
            curr_pos = pyautogui.position()
            dist = ((curr_pos[0] - last_mouse_pos[0]) ** 2 + (curr_pos[1] - last_mouse_pos[1]) ** 2) ** 0.5
            if dist > 25:
                logger.warning(f"User override priority: sharp mouse movement detected ({dist:.1f}px shift)")
                return True
                
        # 2. Detect keyboard overrides via windll
        try:
            import ctypes
            # Esc (0x1B), Space (0x20), Control (0x11), Shift (0x10), Alt (0x12), A-Z (0x41-0x5A)
            for key_code in [0x1B, 0x20, 0x11, 0x10, 0x12] + list(range(0x41, 0x5B)):
                if ctypes.windll.user32.GetAsyncKeyState(key_code) & 0x8000:
                    logger.warning(f"User override priority: keyboard activity detected (key code {key_code})")
                    return True
        except Exception as e:
            logger.debug(f"Failed to check keyboard state: {e}")

        # 3. Detect external focus shift
        if gw and expected_app:
            active = gw.getActiveWindow()
            if active:
                expected_keywords = self.ELEMENT_APP_MAP.get(expected_app, [expected_app])
                title_lower = active.title.lower()
                if not any(k.lower() in title_lower for k in expected_keywords):
                    logger.warning(f"User override priority: external focus shift to '{active.title[:30]}'")
                    return True
            else:
                logger.warning("User override priority: lost foreground window focus")
                return True
                
        return False

    def _get_app_class_for_element(self, element_name: str) -> str:
        """Resolves semantic element names to their expected application category."""
        name_lower = element_name.lower()
        if "terminal" in name_lower:
            return "terminal"
        if "vscode" in name_lower or "sidebar" in name_lower:
            return "vscode"
        if "chrome" in name_lower or "browser" in name_lower or "tab" in name_lower:
            return "browser"
        if "chat" in name_lower:
            return "chat_input"
        return None


    # ==========================================
    # TASK 4: TERMINAL STREAM INTEGRITY
    # ==========================================
    def clean_ansi_characters(self, text: str) -> str:
        """Removes visual ANSI escape strings from logs dynamically."""
        ansi_regex = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
        return ansi_regex.sub('', text)

    def parse_terminal_line(self, line: str) -> Dict[str, Any]:
        """Cleans and incremental-parses raw stdout streams to track process hangs."""
        clean = self.clean_ansi_characters(line).strip()
        if not clean:
            return {"type": "empty"}

        # Record activity timestamp for silent hang checks
        self.last_terminal_output_time = time.time()

        # Prompt detection (Task 4)
        if re.search(r'(?:PS\s+)?[A-Z]:\\[^>]*>', clean):
            return {"type": "shell_prompt", "message": "Shell prompt detected. Ready."}

        # Command echo awareness (Task 4)
        if clean in ["npm run dev", "python main.py", "git branch", "pip install -r requirements.txt"]:
            return {"type": "command_echo", "content": clean}

        if "ready in" in clean.lower() or "local:" in clean.lower() or "http://localhost:" in clean.lower():
            return {"type": "vite_ready", "port": 5173, "message": "Vite dev server is ready."}
        
        if "address already in use" in clean.lower() or "eaddrinuse" in clean.lower():
            return {"type": "port_conflict", "message": "Port occupied by conflicting process."}

        if "traceback (most recent call last):" in clean.lower():
            return {"type": "python_traceback", "message": "Python traceback block started."}
        
        if "failed to compile" in clean.lower() or "syntaxerror" in clean.lower():
            return {"type": "syntax_error", "message": "Syntax compilation failure."}

        if "idealTree" in clean or "reify" in clean or "extract:" in clean:
            return {"type": "npm_progress", "message": "npm packages are installing..."}

        if "uvicorn running on" in clean.lower() or "application startup complete" in clean.lower():
            return {"type": "backend_ready", "port": 8000, "message": "Uvicorn FastAPI server ready."}

        return {"type": "stdout", "content": clean}

    def check_for_silent_hang(self, expected_duration: float = 5.0) -> bool:
        """Flags hang if terminal process expected output but remains quiet."""
        idle_duration = time.time() - self.last_terminal_output_time
        if idle_duration > expected_duration:
            logger.warning(f"Process hang suspected: silent for {idle_duration:.1f} seconds.")
            return True
        return False

    # ==========================================
    # TASK 3: ACTIVE SERVICE LIFECYCLE MANAGEMENT
    # ==========================================
    def is_terminal_ready(self) -> Tuple[bool, str]:
        """Checks if the active terminal is ready and not busy running another process."""
        if not gw:
            return True, "ready (mock)"

        active = gw.getActiveWindow()
        if not active:
            return False, "no active window"

        title_lower = active.title.lower()
        expected_terms = self.ELEMENT_APP_MAP.get("terminal_input", [])
        is_term = any(t in title_lower for t in expected_terms)
        if not is_term:
            return False, f"focused window is not terminal (active: {active.title[:20]})"

        # 1. Title bar busy indicator detection
        busy_indicators = ["npm run", "node", "vite", "python", "uvicorn", "ping", "ssh", "docker"]
        title_lower_clean = title_lower.strip()
        is_idle_shell = title_lower_clean in ["windows powershell", "powershell", "command prompt", "cmd", "cmd.exe", "powershell.exe", "mingw", "bash", "windows terminal"]
        if not is_idle_shell:
            for indicator in busy_indicators:
                if indicator in title_lower:
                    return False, f"terminal busy running {indicator} (detected in title)"

        # 2. Process state audits
        if psutil:
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cwd', 'status']):
                    try:
                        pinfo = proc.info
                        pname = (pinfo.get('name') or "").lower()
                        pcwd = (pinfo.get('cwd') or "").lower()
                        if pcwd and ("jarvis" in pcwd or "downloads\\jarvis" in pcwd):
                            if any(k in pname for k in ["npm", "node", "python", "uvicorn"]):
                                if pinfo.get('status') in [psutil.STATUS_RUNNING, psutil.STATUS_SLEEPING]:
                                    # Specifically catch active npm installs or scripts
                                    if "npm" in pname:
                                        return False, f"active npm script (pid: {pinfo.get('pid')})"
                    except Exception:
                        pass
            except Exception:
                pass

        # 3. TCP Port responsiveness checks
        # If Vite (5173) or FastAPI (8000) respond, let's verify if they are running healthy
        return True, "ready"

    def resume_frontend(self) -> Tuple[bool, str]:
        """Ensures NO duplicate Vite servers are launched by verifying ports first with progress retry degradation."""
        if self.check_and_suppress_duplicate("resume_frontend", {}, cooldown=1.5):
            return True, "frontend active (dedup)"

        self.transition_to(ExecutionState.QUEUED)

        # 1. Detect if Vite is ALREADY running
        if self.verify_port_state(5173):
            self.transition_to(ExecutionState.COMPLETED)
            return True, "frontend active"

        # 2. Free conflict port if occupied by non-vite orphan
        self.fix_occupied_port(5173)

        self.transition_to(ExecutionState.EXECUTING)

        # Acquire focus safely
        state = self.get_screen_semantic_state()
        if state["active_app"] != "Terminal":
            focused, msg = self.click_terminal_input()
            if not focused:
                self.transition_to(ExecutionState.FAILED)
                return False, "terminal focus failed"
        
        # Verify terminal readiness to avoid collision typing
        ready, reason = self.is_terminal_ready()
        if not ready:
            logger.warning(f"Terminal busy state: {reason}. Waiting for stabilization...")
            time.sleep(0.12)
            ready, reason = self.is_terminal_ready()
            if not ready:
                self.transition_to(ExecutionState.BLOCKED)
                return False, f"terminal busy: {reason}"

        # Strict Pre-action Validation
        valid, r_msg = self.verify_pre_action_state("terminal")
        if not valid:
            self.transition_to(ExecutionState.FAILED)
            return False, f"focus lock failed before typing: {r_msg}"

        typed_ok = self.human_type_text("npm run dev\n", expected_app="terminal")
        if not typed_ok:
            self.transition_to(ExecutionState.FAILED)
            return False, "typing failed (focus lock error or user override)"

        validated, _ = self.validate_action_outcome("launch_vite", {})
        if validated:
            self.persist_continuity_state()
            return True, "frontend restarted"

        # ----------------------------------------------------
        # RETRY DEGRADATION MODEL
        # ----------------------------------------------------
        # Attempt 1: Cautious Retry
        self.transition_to(ExecutionState.RECOVERING)
        attempt = 1
        wait_ms = int(800 * (1.5 ** attempt))
        logger.warning(f"Vite launch check failed. Initiating retry degradation attempt {attempt} (wait: {wait_ms}ms)")
        self._adaptive_wait(wait_ms, "vite_boot_ms")

        # Re-focus and deep audit terminal readiness
        self.click_terminal_input()
        ready, reason = self.is_terminal_ready()
        
        # Guarded keyboard delivery
        hotkey_ok = self.send_hotkey(["ctrl", "c"], expected_app="terminal")
        if hotkey_ok:
            self._adaptive_wait(400) # Cautious wait after key press
            self.human_type_text("npm run dev\n", expected_app="terminal")

        validated, _ = self.validate_action_outcome("launch_vite", {})
        if validated:
            self.persist_continuity_state()
            return True, "frontend restarted"

        # Attempt 2: Observant, Ultra-Slow Retry
        attempt = 2
        wait_ms = int(800 * (2.5 ** attempt))
        logger.error(f"Vite launch check failed twice. Initiating final slow retry degradation attempt {attempt} (wait: {wait_ms}ms)")
        self._adaptive_wait(wait_ms, "vite_boot_ms")

        # More observant audit - actively clear ports and re-verify
        self.fix_occupied_port(5173)
        self.click_terminal_input()
        
        # Extremely slow execution and final command key stroke
        hotkey_ok = self.send_hotkey(["ctrl", "c"], expected_app="terminal")
        if hotkey_ok:
            self._adaptive_wait(600)
            self.human_type_text("npm run dev\n", expected_app="terminal")

        validated, _ = self.validate_action_outcome("launch_vite", {})
        if validated:
            self.persist_continuity_state()
            return True, "frontend restarted"

        self.transition_to(ExecutionState.FAILED)
        return False, "vite failed to boot after progressive retry degradation"

    # ==========================================
    # TASK 5: STRICT OUTCOME VERIFICATION
    # ==========================================
    def validate_action_outcome(self, action_name: str, expected_params: Dict[str, Any]) -> Tuple[bool, str]:
        self.transition_to(ExecutionState.VERIFYING)
        self._adaptive_wait(400, "verify_wait_ms")
        
        state = self.get_screen_semantic_state()

        if action_name == "launch_vite" or action_name == "start_frontend":
            is_active = self.verify_port_state(5173)
            if is_active:
                self.transition_to(ExecutionState.COMPLETED)
                return True, "vite verified"
            self.transition_to(ExecutionState.RECOVERING)
            return False, "port 5173 offline"

        if action_name == "start_backend":
            is_active = self.verify_port_state(8000)
            if is_active:
                self.transition_to(ExecutionState.COMPLETED)
                return True, "backend verified"
            self.transition_to(ExecutionState.RECOVERING)
            return False, "port 8000 offline"

        if action_name == "focus_vscode":
            if state["active_app"] == "VSCode":
                self.transition_to(ExecutionState.COMPLETED)
                return True, "vscode focused"
            self.transition_to(ExecutionState.RECOVERING)
            return False, f"focus mismatch: {state['active_app']}"

        self.transition_to(ExecutionState.COMPLETED)
        return True, "done"

    # ==========================================
    # TASK 5: VISUAL CONFIDENCE
    # ==========================================
    def calculate_confidence_score(self, target_name: str, active_title: str) -> int:
        score = 100

        # Match against app class mapping instead of raw registry key
        expected_apps = self.ELEMENT_APP_MAP.get(target_name, [])
        if expected_apps:
            title_lower = active_title.lower()
            if not any(app in title_lower for app in expected_apps):
                score -= 30
        elif target_name.lower() not in active_title.lower():
            score -= 30

        if target_name in self.semantic_element_registry:
            coords = self.semantic_element_registry[target_name]
            if coords["x"] < 0 or coords["y"] < 0:
                score -= 15
        else:
            score -= 10

        if not pyautogui:
            score -= 20

        return max(0, min(100, score))

    # ==========================================
    # TASK 6: HUMAN PACING DRIVER
    # ==========================================
    def human_type_text(self, text: str, expected_app: str = None) -> bool:
        # Sync the app state
        self.update_authoritative_app_state()

        if not pyautogui:
            logger.info(f"Typed (Mock): {text}")
            return True

        # 1. Execution Fingerprint Suppression
        if self.check_and_suppress_duplicate("submit_command" if text.endswith('\n') else "type_burst", {"text": text, "app": expected_app}, cooldown=0.8):
            return True

        # 2. Strict Pre-action Validation
        valid, reason = self.verify_pre_action_state(expected_app)
        if not valid:
            logger.error(f"Pre-action validation mismatch: {reason}. Typing aborted.")
            self.transition_to(ExecutionState.BLOCKED)
            return False

        # Enforce execution guard confidence checking
        active_title = ""
        if gw:
            active = gw.getActiveWindow()
            if active:
                active_title = active.title
        target_name = expected_app if expected_app else (self.last_focus_target if self.last_focus_target else "terminal_input")
        confidence = self.calculate_confidence_score(target_name, active_title)
        if confidence < 70:
            logger.warning(f"Safety confirmation challenge: confidence is {confidence}% for typing '{target_name}'. Suspending execution.")
            self.transition_to(ExecutionState.BLOCKED)
            return False

        expected_keywords = []
        if expected_app:
            if expected_app in self.ELEMENT_APP_MAP:
                expected_keywords = self.ELEMENT_APP_MAP[expected_app]
            else:
                expected_keywords = [expected_app]
        elif self.last_focus_target:
            expected_keywords = [self.last_focus_target]

        # Focus Lock Verification and optional single quiet refocus
        if gw and expected_keywords:
            time.sleep(random.uniform(0.08, 0.12))
            active = gw.getActiveWindow()
            title_lower = active.title.lower() if active else ""
            focus_valid = active and any(keyword.lower() in title_lower for keyword in expected_keywords)
            
            if not focus_valid:
                refocus_target = expected_keywords[0]
                logger.warning(f"Focus lock drift detected. Expected: {expected_keywords}, Active: {active.title if active else 'None'}. Attempting single quiet refocus...")
                focused, _ = self.refocus_app_window(refocus_target, "")
                if not focused:
                    logger.error("Focus lock validation failed. Typing aborted for safety.")
                    self.transition_to(ExecutionState.FAILED)
                    return False

        # Input field settle wait - fast, calm, intentional
        time.sleep(random.uniform(0.08, 0.12))

        # Track start state for user override detection
        start_mouse = pyautogui.position()
        active_before = gw.getActiveWindow() if gw else None

        ends_with_newline = text.endswith('\n')
        content = text[:-1] if ends_with_newline else text

        for char in content:
            # 3. User Override Priority check before every character
            if self._check_user_interruption(start_mouse, expected_app):
                logger.warning("User override detected: aborting typing execution mid-burst.")
                self.transition_to(ExecutionState.BLOCKED)
                return False
                
            pyautogui.write(char)
            # Update expected mouse position to prevent micro-drifts from false triggering
            start_mouse = pyautogui.position()

            delay = random.uniform(0.012, 0.025)
            if char in [" ", ",", "."]:
                delay += random.uniform(0.02, 0.04)
            time.sleep(delay)

        if ends_with_newline:
            time.sleep(random.uniform(0.08, 0.12))
            
            # CRITICAL FOCUS SAFETY CHECK: One final verification right before hitting Enter!
            if gw and expected_keywords:
                active = gw.getActiveWindow()
                title_lower = active.title.lower() if active else ""
                focus_valid = active and any(keyword.lower() in title_lower for keyword in expected_keywords)
                if not focus_valid:
                    logger.error("Focus lock lost right before ENTER! Execution aborted to prevent catastrophic wrong-window commands.")
                    self.transition_to(ExecutionState.BLOCKED)
                    return False
            
            # User Override check right before pressing Enter
            if self._check_user_interruption(start_mouse, expected_app):
                logger.warning("User override detected right before ENTER. Aborting command execution.")
                self.transition_to(ExecutionState.BLOCKED)
                return False

            pyautogui.write('\n')

        # Post-typing stabilization
        time.sleep(0.06)
        return True

    def send_hotkey(self, keys: List[str] or str, expected_app: str = None) -> bool:
        """Sends a hotkey combo safely, verifying focus lock first to prevent rogue actions."""
        self.update_authoritative_app_state()

        if not pyautogui:
            logger.info(f"Hotkey (Mock): {keys}")
            return True

        # 1. Execution Fingerprint Suppression
        if self.check_and_suppress_duplicate("hotkey", {"keys": keys, "app": expected_app}, cooldown=0.8):
            return True

        # 2. Strict Pre-action Validation
        valid, reason = self.verify_pre_action_state(expected_app)
        if not valid:
            logger.error(f"Pre-action validation mismatch before hotkey {keys}: {reason}. Aborted.")
            self.transition_to(ExecutionState.BLOCKED)
            return False

        # Enforce execution confidence guard
        active_title = ""
        if gw:
            active = gw.getActiveWindow()
            if active:
                active_title = active.title
        target_name = expected_app if expected_app else (self.last_focus_target if self.last_focus_target else "terminal_input")
        confidence = self.calculate_confidence_score(target_name, active_title)
        if confidence < 70:
            logger.warning(f"Safety confirmation challenge: confidence is {confidence}% for hotkey '{target_name}'. Suspending execution.")
            self.transition_to(ExecutionState.BLOCKED)
            return False

        expected_keywords = []
        if expected_app:
            if expected_app in self.ELEMENT_APP_MAP:
                expected_keywords = self.ELEMENT_APP_MAP[expected_app]
            else:
                expected_keywords = [expected_app]
        elif self.last_focus_target:
            expected_keywords = [self.last_focus_target]

        if gw and expected_keywords:
            time.sleep(random.uniform(0.08, 0.12))
            active = gw.getActiveWindow()
            title_lower = active.title.lower() if active else ""
            focus_valid = active and any(keyword.lower() in title_lower for keyword in expected_keywords)
            
            if not focus_valid:
                refocus_target = expected_keywords[0]
                logger.warning(f"Focus lock drift detected before hotkey {keys}. Expected: {expected_keywords}, Active: {active.title if active else 'None'}. Refocusing...")
                focused, _ = self.refocus_app_window(refocus_target, "")
                if not focused:
                    logger.error(f"Focus lock validation failed for hotkey {keys}. Aborted.")
                    self.transition_to(ExecutionState.FAILED)
                    return False

        # User Override check
        start_mouse = pyautogui.position()
        if self._check_user_interruption(start_mouse, expected_app):
            logger.warning(f"User override detected before hotkey {keys}. Aborted.")
            self.transition_to(ExecutionState.BLOCKED)
            return False

        if isinstance(keys, list):
            pyautogui.hotkey(*keys)
        else:
            pyautogui.hotkey(keys)
        time.sleep(0.08)
        return True

    # ==========================================
    # GENERAL CONTROLS
    # ==========================================
    def click_terminal_input(self) -> Tuple[bool, str]:
        self.transition_to(ExecutionState.EXECUTING)
        
        # Early exit if terminal is already focused
        state = self.get_screen_semantic_state()
        if state["active_app"] == "Terminal":
            coords = self.semantic_element_registry["terminal_input"]
            return self._safe_click(coords["x"], coords["y"], "terminal_input")

        # Try powershell first, then cmd — but don't cascade full loops
        focused, msg = self.refocus_app_window("powershell", "terminal")
        if not focused:
            focused, msg = self.refocus_app_window("cmd", "terminal")
        if not focused:
            focused, msg = self.refocus_app_window("Windows Terminal", "terminal")

        if not focused:
            return self.recover_hidden_terminal()

        coords = self.semantic_element_registry["terminal_input"]
        return self._safe_click(coords["x"], coords["y"], "terminal_input")

    def click_vscode_sidebar(self) -> Tuple[bool, str]:
        self.transition_to(ExecutionState.EXECUTING)
        focused, msg = self.refocus_app_window("Visual Studio Code", "editor")
        if not focused:
            return False, "vscode not found"

        coords = self.semantic_element_registry["vscode_sidebar"]
        return self._safe_click(coords["x"], coords["y"], "VSCode Sidebar")

    def open_terminal_panel(self) -> Tuple[bool, str]:
        self.transition_to(ExecutionState.EXECUTING)
        focused, msg = self.refocus_app_window("Visual Studio Code", "editor")
        if not focused:
            return False, "vscode not found"

        if pyautogui:
            self.send_hotkey(["ctrl", "`"], expected_app="vscode_sidebar")
            time.sleep(0.25)
            return True, "VSCode integrated terminal drawer toggled."
        return True, "VSCode integrated terminal drawer toggled (Mock)."

    def focus_browser_tab(self, tab_title_keyword: str) -> Tuple[bool, str]:
        self.transition_to(ExecutionState.EXECUTING)
        focused, msg = self.refocus_app_window("chrome", "browser")
        if not focused:
            return False, "chrome not found"

        if not pyautogui:
            return True, f"Focused tab '{tab_title_keyword}' (Mock)."

        for attempt in range(8):
            window_state = self.get_screen_semantic_state()
            if tab_title_keyword.lower() in window_state.get("active_title", "").lower():
                self.transition_to(ExecutionState.COMPLETED)
                return True, f"Successfully focused browser tab: {tab_title_keyword}"
            self.send_hotkey(["ctrl", "tab"], expected_app="chrome_tab_area")
            time.sleep(0.15)

        return False, f"tab not found: {tab_title_keyword}"

    def focus_chat_input(self) -> Tuple[bool, str]:
        self.transition_to(ExecutionState.EXECUTING)
        focused, msg = self.refocus_app_window("FRIDAY", "chat")
        coords = self.semantic_element_registry["chat_input"]
        return self._safe_click(coords["x"], coords["y"], "Chat Input Field")

    def get_screen_semantic_state(self) -> Dict[str, Any]:
        state = {
            "active_app": "Unknown",
            "active_title": "System Desktop",
            "vscode_project": None,
            "port_listeners": {},
            "active_process_pids": [],
            "error_states": []
        }

        if gw:
            active_win = gw.getActiveWindow()
            if active_win:
                state["active_title"] = active_win.title
                title_lower = active_win.title.lower()
                if "visual studio code" in title_lower:
                    state["active_app"] = "VSCode"
                    parts = active_win.title.split(" - ")
                    if len(parts) >= 2:
                        state["vscode_project"] = parts[1]
                elif "chrome" in title_lower:
                    state["active_app"] = "Chrome"
                elif "powershell" in title_lower or "cmd" in title_lower:
                    state["active_app"] = "Terminal"
                else:
                    state["active_app"] = active_win.title[:20]

        for port in self.active_ports:
            state["port_listeners"][port] = self.verify_port_state(port)

        return state

    def verify_port_state(self, port: int) -> bool:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        try:
            s.connect(("127.0.0.1", port))
            s.close()
            return True
        except Exception:
            return False

    def recover_hidden_terminal(self) -> Tuple[bool, str]:
        self.transition_to(ExecutionState.RECOVERING)
        logger.warning("Terminal handle lost. Spawning powershell fallback...")
        try:
            self.recovery_memory["terminal_hidden"] += 1
            proc = subprocess.Popen(["powershell.exe"], shell=True)
            time.sleep(0.8)
            if self.refocus_app_window("powershell", "terminal")[0]:
                self.transition_to(ExecutionState.COMPLETED)
                return True, "terminal recovered"
        except Exception as e:
            logger.error(f"PowerShell spawn failed during recovery: {e}")
        
        self.transition_to(ExecutionState.FAILED)
        return False, "terminal recovery failed"

    def fix_occupied_port(self, port: int) -> Tuple[bool, str]:
        self.transition_to(ExecutionState.VERIFYING)
        if not self.verify_port_state(port):
            return True, f"port {port} free"

        self.transition_to(ExecutionState.RECOVERING)
        logger.warning(f"Port {port} conflict detected. Scanning process tree...")
        if not psutil:
            self.transition_to(ExecutionState.BLOCKED)
            return False, "port conflict: psutil missing"

        resolved = False
        self.recovery_memory["occupied_port"] += 1
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for conn in proc.connections(kind='inet'):
                    if conn.laddr.port == port:
                        logger.warning(f"killing pid {proc.pid} on port {port}")
                        proc.terminate()
                        proc.wait(timeout=2.0)
                        resolved = True
            except Exception:
                pass

        if resolved:
            time.sleep(0.3)
            self.transition_to(ExecutionState.COMPLETED)
            return True, f"port {port} freed"
        
        self.transition_to(ExecutionState.FAILED)
        return False, f"port {port} still occupied"

    def resume_workspace(self) -> Tuple[bool, str]:
        self.transition_to(ExecutionState.QUEUED)
        vscode_focused, msg = self.refocus_app_window("Visual Studio Code", "editor")
        if not vscode_focused:
            try:
                os.startfile(self.workspace_path)
                time.sleep(1.0)
            except Exception:
                pass
        
        self.resume_frontend()
        self.persist_continuity_state()
        return True, f"workspace resumed: project {self.active_project}"

    def refocus_app_window(self, title_keyword: str, app_class: str) -> Tuple[bool, str]:
        now = time.time()
        if self.last_focus_target == title_keyword and (now - self.last_focus_time) < 0.3:
            return True, "focus stable"

        if not gw:
            return True, "focused (mock)"

        # Early exit: already the active window and not minimized
        active = gw.getActiveWindow()
        if active and title_keyword.lower() in active.title.lower() and not active.isMinimized:
            self.last_focus_time = time.time()
            self.last_focus_target = title_keyword
            return True, f"already focused: {active.title[:30]}"

        # Find and activate once
        target_win = None
        for w in gw.getAllWindows():
            if title_keyword.lower() in w.title.lower():
                target_win = w
                break

        if not target_win:
            return False, f"window not found: {title_keyword}"

        try:
            # REAL WINDOW RESTORATION
            if hasattr(target_win, 'isMinimized') and target_win.isMinimized:
                logger.info(f"Window '{target_win.title[:20]}' is minimized. Restoring...")
                target_win.restore()
                # Settle wait for OS window manager to process unminimize
                time.sleep(0.12)
            target_win.activate()
        except Exception as e:
            logger.debug(f"Failed to restore/activate window: {e}")

        # Poll with exponential backoff for focus confirmation
        delays = [0.08, 0.12, 0.18, 0.25, 0.35]
        for delay in delays:
            time.sleep(delay)
            active = gw.getActiveWindow()
            if active and title_keyword.lower() in active.title.lower() and not active.isMinimized:
                self.last_focus_time = time.time()
                self.last_focus_target = title_keyword
                return True, f"focused: {active.title[:30]}"

        return False, f"focus timeout: {title_keyword}"

    def _safe_click(self, x: int, y: int, name: str) -> Tuple[bool, str]:
        # Sync the app state
        self.update_authoritative_app_state()

        # Perform dynamic grounding via UIA
        grounded_x, grounded_y = self.get_grounded_coordinates(name)
        if grounded_x != -1 and grounded_y != -1:
            x, y = grounded_x, grounded_y

        if x < 40 and y < 40:
            self.transition_to(ExecutionState.BLOCKED)
            return False, "click blocked: unsafe region"

        # 1. Execution Fingerprint Suppression
        if self.check_and_suppress_duplicate("click", {"x": x, "y": y}, cooldown=0.6):
            return True, f"clicked {name} (dedup)"

        # Lightweight confidence check — just title, no port scanning
        active_title = "Unknown"
        if gw:
            active = gw.getActiveWindow()
            if active:
                active_title = active.title

        confidence = self.calculate_confidence_score(name, active_title)
        if confidence < 70:
            logger.warning(f"Safety confirmation challenge: confidence {confidence}% < 70% for '{name}'. Suspending execution.")
            self.transition_to(ExecutionState.BLOCKED)
            return False, f"click blocked: low confidence ({confidence}%)"

        if not pyautogui:
            self.transition_to(ExecutionState.COMPLETED)
            self.record_coordinate_success(name)
            return True, f"clicked {name} (mock)"

        # Strict Pre-action Validation before movement or clicking
        app_class = self._get_app_class_for_element(name)
        valid, reason = self.verify_pre_action_state(app_class)
        if not valid:
            logger.error(f"Click pre-action validation failed: {reason}. Click aborted.")
            self.record_coordinate_failure(name)
            self.transition_to(ExecutionState.BLOCKED)
            return False, f"click blocked: {reason}"

        start_mouse = pyautogui.position()

        try:
            # 2. Cautious move with interruption priority check
            pyautogui.moveTo(x, y, duration=0.2)
            time.sleep(0.04)
            
            # Post-move coordinates check
            curr_pos = pyautogui.position()
            if abs(curr_pos[0] - x) > 10 or abs(curr_pos[1] - y) > 10:
                logger.warning("Click aborted: mouse moved away externally during movement.")
                self.record_coordinate_failure(name)
                self.transition_to(ExecutionState.BLOCKED)
                return False, "click blocked: mouse conflict"

            # Post-move focus verification
            valid, reason = self.verify_pre_action_state(app_class)
            if not valid:
                logger.error(f"Post-move focus lock lost: {reason}. Click aborted.")
                self.record_coordinate_failure(name)
                self.transition_to(ExecutionState.BLOCKED)
                return False, f"click blocked: {reason}"

            # Final user override check right before clicking
            if self._check_user_interruption(start_mouse, app_class):
                logger.warning("User override detected right before clicking. Click aborted.")
                self.record_coordinate_failure(name)
                self.transition_to(ExecutionState.BLOCKED)
                return False, "click blocked: user override"

            pyautogui.click(x, y)
            self.record_coordinate_success(name)
            self._adaptive_wait(80)
            self.transition_to(ExecutionState.COMPLETED)
            return True, f"clicked: {name}"
        except Exception as e:
            self.record_coordinate_failure(name)
            self.transition_to(ExecutionState.FAILED)
            return False, f"click failed: {name}"

# Singleton instance
semantic_operator = SemanticOperator()
