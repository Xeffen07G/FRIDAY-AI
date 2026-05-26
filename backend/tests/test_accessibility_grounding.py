import sys
import os
import time
import pytest
from unittest.mock import patch, MagicMock

# Ensure backend is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.desktop.semantic_operator import SemanticOperator, ExecutionState

@pytest.fixture
def clean_operator():
    """Returns a clean instance of SemanticOperator with mocked dependencies."""
    with patch('backend.desktop.semantic_operator.gw') as mock_gw, \
         patch('backend.desktop.semantic_operator.pyautogui') as mock_pyautogui, \
         patch('backend.desktop.semantic_operator.psutil') as mock_psutil, \
         patch('backend.desktop.semantic_operator.PywinautoDesktop') as mock_uia_desktop:
        
        mock_gw.getActiveWindow.return_value = None
        mock_gw.getAllWindows.return_value = []
        
        op = SemanticOperator()
        op.persist_continuity_state = MagicMock()
        op.load_continuity_state = MagicMock()
        
        yield op

def test_resolve_accessibility_element(clean_operator):
    """Verifies UIA element resolution returns mock descendants appropriately."""
    op = clean_operator
    
    with patch('backend.desktop.semantic_operator.PywinautoDesktop') as mock_uia_desktop:
        mock_desktop_instance = MagicMock()
        mock_uia_desktop.return_value = mock_desktop_instance
        
        mock_window = MagicMock()
        mock_window.exists.return_value = True
        mock_desktop_instance.window.return_value = mock_window
        
        mock_element = MagicMock()
        mock_window.descendants.return_value = [mock_element]
        
        res = op.resolve_accessibility_element("vscode_sidebar", hwnd=12345)
        assert res == mock_element
        mock_window.descendants.assert_called_once_with(control_type="Custom", automation_id="workbench.parts.activitybar")

def test_lock_and_verify_element_rect(clean_operator):
    """Verifies rect locking validations for visibility, enabled state, and dimension boundaries."""
    op = clean_operator
    
    # 1. Invalid element (None)
    ok, bounds = op.lock_and_verify_element_rect(None)
    assert not ok
    
    # 2. Hidden element
    mock_el = MagicMock()
    mock_el.is_visible.return_value = False
    mock_el.is_enabled.return_value = True
    ok, bounds = op.lock_and_verify_element_rect(mock_el)
    assert not ok
    
    # 3. Disabled element
    mock_el.is_visible.return_value = True
    mock_el.is_enabled.return_value = False
    ok, bounds = op.lock_and_verify_element_rect(mock_el)
    assert not ok
    
    # 4. Zero dimensions rectangle
    mock_el.is_visible.return_value = True
    mock_el.is_enabled.return_value = True
    mock_rect = MagicMock()
    mock_rect.width.return_value = 0
    mock_rect.height.return_value = 0
    mock_el.rectangle.return_value = mock_rect
    ok, bounds = op.lock_and_verify_element_rect(mock_el)
    assert not ok

    # 5. Out-of-bounds coordinates
    mock_rect.width.return_value = 100
    mock_rect.height.return_value = 50
    mock_rect.left = 10000
    mock_rect.top = 10000
    ok, bounds = op.lock_and_verify_element_rect(mock_el)
    assert not ok

    # 6. Perfect bounds
    mock_rect.left = 100
    mock_rect.top = 200
    ok, bounds = op.lock_and_verify_element_rect(mock_el)
    assert ok
    assert bounds["x"] == 150
    assert bounds["y"] == 225

def test_get_grounded_coordinates_drift_recovery(clean_operator):
    """Verifies dynamic Visual Drift Recovery V2 remapping coordinates in registry."""
    op = clean_operator
    
    # Mock active window and resolution
    with patch('backend.desktop.semantic_operator.gw') as mock_gw:
        mock_win = MagicMock()
        mock_win._hWnd = 9999
        mock_gw.getActiveWindow.return_value = mock_win
        
        mock_element = MagicMock()
        mock_element.is_visible.return_value = True
        mock_element.is_enabled.return_value = True
        
        mock_rect = MagicMock()
        mock_rect.width.return_value = 80
        mock_rect.height.return_value = 40
        mock_rect.left = 300
        mock_rect.top = 400
        mock_element.rectangle.return_value = mock_rect
        
        op.resolve_accessibility_element = MagicMock(return_value=mock_element)
        
        x, y = op.get_grounded_coordinates("vscode_sidebar")
        assert x == 340
        assert y == 420
        # Registry should be updated to new drift-recovered coordinates
        assert op.semantic_element_registry["vscode_sidebar"] == {"x": 340, "y": 420}

def test_coordinate_decay_scoring(clean_operator):
    """Verifies that coordinate reliability score decays and prunes low score element coordinates."""
    op = clean_operator
    
    # Starting score is 100
    assert op.coordinate_reliability["vscode_sidebar"] == 100
    
    # Record success increases score but caps at 100
    op.record_coordinate_success("vscode_sidebar")
    assert op.coordinate_reliability["vscode_sidebar"] == 100
    
    # Record failure decays score by 15
    op.record_coordinate_failure("vscode_sidebar")
    assert op.coordinate_reliability["vscode_sidebar"] == 85
    
    # Decay down below 50
    op.record_coordinate_failure("vscode_sidebar") # 70
    op.record_coordinate_failure("vscode_sidebar") # 55
    assert "vscode_sidebar" in op.semantic_element_registry
    
    op.record_coordinate_failure("vscode_sidebar") # 40
    # Reliability < 50 triggers pruning of coordinates
    assert "vscode_sidebar" not in op.semantic_element_registry

def test_authoritative_app_state_mapping(clean_operator):
    """Verifies update_authoritative_app_state compiles focused, minimized, open apps, branches, and ports."""
    op = clean_operator
    
    with patch('backend.desktop.semantic_operator.gw') as mock_gw, \
         patch('backend.desktop.semantic_operator.psutil') as mock_psutil:
        
        mock_w1 = MagicMock()
        mock_w1.title = "Visual Studio Code"
        mock_w1.isMinimized = False
        
        mock_w2 = MagicMock()
        mock_w2.title = "Windows PowerShell"
        mock_w2.isMinimized = True
        
        mock_gw.getAllWindows.return_value = [mock_w1, mock_w2]
        mock_gw.getActiveWindow.return_value = mock_w1
        
        op.verify_port_state = MagicMock(side_effect=lambda port: port == 5173)
        
        op.update_authoritative_app_state()
        
        assert "Visual Studio Code" in op.app_state_map["opened_apps"]
        assert "Windows PowerShell" in op.app_state_map["opened_apps"]
        assert "Windows PowerShell" in op.app_state_map["minimized_apps"]
        assert op.app_state_map["focused_app"] == "Visual Studio Code"
        assert 5173 in op.app_state_map["active_ports"]
        assert 8000 not in op.app_state_map["active_ports"]

def test_keyboard_override_ctypes_detection(clean_operator):
    """Verifies that windll user32 keyboard events interrupt executions midpoint."""
    op = clean_operator
    
    # Mock ctypes.windll.user32.GetAsyncKeyState
    with patch('backend.desktop.semantic_operator.gw') as mock_gw, \
         patch('ctypes.windll.user32.GetAsyncKeyState') as mock_async_state:
        
        mock_win = MagicMock()
        mock_win.title = "Windows PowerShell"
        mock_gw.getActiveWindow.return_value = mock_win
        
        # No keys pressed (bit 0x8000 is off)
        mock_async_state.return_value = 0
        assert not op._check_user_interruption(expected_app="terminal")
        
        # Escape key is down (bit 0x8000 is on)
        mock_async_state.side_effect = lambda code: 0x8000 if code == 0x1B else 0
        assert op._check_user_interruption(expected_app="terminal")

def test_strict_execution_confidence_guard(clean_operator):
    """Enforces that any click, typing burst, or hotkey with confidence < 70% gets instantly suspended to BLOCKED."""
    op = clean_operator
    
    # Mock confidence score to 60 (< 70%)
    op.calculate_confidence_score = MagicMock(return_value=60)
    
    # Mock verification tools
    with patch('backend.desktop.semantic_operator.gw') as mock_gw:
        mock_win = MagicMock()
        mock_win.title = "Calculator"
        mock_win.isMinimized = False
        mock_gw.getActiveWindow.return_value = mock_win
        
        # Typing is blocked
        res_type = op.human_type_text("some command", expected_app="vscode")
        assert not res_type
        assert op.current_state == ExecutionState.BLOCKED
        
        # Hotkey is blocked
        res_hotkey = op.send_hotkey("ctrl+c", expected_app="vscode")
        assert not res_hotkey
        assert op.current_state == ExecutionState.BLOCKED
        
        # Click is blocked
        res_click, click_msg = op._safe_click(100, 100, "vscode_sidebar")
        assert not res_click
        assert "low confidence" in click_msg
        assert op.current_state == ExecutionState.BLOCKED
