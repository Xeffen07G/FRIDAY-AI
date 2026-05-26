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
         patch('backend.desktop.semantic_operator.psutil') as mock_psutil:
        
        # Clear mock states
        mock_gw.getActiveWindow.return_value = None
        mock_gw.getAllWindows.return_value = []
        
        op = SemanticOperator()
        # Mock database persist to avoid actual DB writes during unit tests
        op.persist_continuity_state = MagicMock()
        op.load_continuity_state = MagicMock()
        
        yield op

def test_strict_pre_action_validation(clean_operator):
    """Checks that verify_pre_action_state properly handles minimization and mismatch cases."""
    op = clean_operator
    
    # 1. No active window
    with patch('backend.desktop.semantic_operator.gw') as mock_gw:
        mock_gw.getActiveWindow.return_value = None
        valid, msg = op.verify_pre_action_state()
        assert not valid
        assert "no active foreground window" in msg

        # 2. Minimized window
        mock_win = MagicMock()
        mock_win.isMinimized = True
        mock_win.title = "Visual Studio Code"
        mock_gw.getActiveWindow.return_value = mock_win
        valid, msg = op.verify_pre_action_state()
        assert not valid
        assert "minimized" in msg

        # 3. Invalid/blank title
        mock_win.isMinimized = False
        mock_win.title = "   "
        valid, msg = op.verify_pre_action_state()
        assert not valid
        assert "blank or invalid" in msg

        # 4. Keyword mismatch
        mock_win.title = "Google Chrome"
        valid, msg = op.verify_pre_action_state("terminal")
        assert not valid
        assert "window focus mismatch" in msg

        # 5. Success case
        mock_win.title = "Administrator: Windows PowerShell"
        valid, msg = op.verify_pre_action_state("terminal")
        assert valid
        assert msg == "valid"

def test_duplicate_action_suppression(clean_operator):
    """Ensures check_and_suppress_duplicate suppresses same actions within cooldown window."""
    op = clean_operator
    
    # Trigger first click action
    payload = {"x": 500, "y": 600}
    is_dup1 = op.check_and_suppress_duplicate("click", payload, cooldown=0.5)
    assert not is_dup1
    
    # Trigger identical action immediately
    is_dup2 = op.check_and_suppress_duplicate("click", payload, cooldown=0.5)
    assert is_dup2
    
    # Trigger different action payload immediately
    is_dup3 = op.check_and_suppress_duplicate("click", {"x": 500, "y": 601}, cooldown=0.5)
    assert not is_dup3
    
    # Sleep to exceed cooldown and verify it is allowed again
    time.sleep(0.55)
    is_dup4 = op.check_and_suppress_duplicate("click", payload, cooldown=0.5)
    assert not is_dup4

def test_user_override_priority(clean_operator):
    """Validates user override priority when mouse shifts sharply or focus changes externally."""
    op = clean_operator
    
    # 1. No movement (distance = 0)
    with patch('backend.desktop.semantic_operator.pyautogui') as mock_pyautogui:
        mock_pyautogui.position.return_value = (100, 100)
        assert not op._check_user_interruption(last_mouse_pos=(100, 100))

        # 2. Small micro-drift (under 25px)
        assert not op._check_user_interruption(last_mouse_pos=(110, 110))

        # 3. Sharp mouse movement (distance > 25px)
        assert op._check_user_interruption(last_mouse_pos=(200, 200))

    # 4. External focus change
    with patch('backend.desktop.semantic_operator.gw') as mock_gw:
        mock_win = MagicMock()
        mock_win.title = "Calculator"
        mock_gw.getActiveWindow.return_value = mock_win
        
        # We expect a terminal app, but active app is Calculator
        assert op._check_user_interruption(expected_app="terminal")

def test_terminal_busy_state_intelligence(clean_operator):
    """Verifies that terminal activity, busy indicators, and scripts are correctly classified."""
    op = clean_operator
    
    with patch('backend.desktop.semantic_operator.gw') as mock_gw:
        # 1. Window is not a terminal
        mock_win = MagicMock()
        mock_win.title = "Visual Studio Code"
        mock_gw.getActiveWindow.return_value = mock_win
        ready, msg = op.is_terminal_ready()
        assert not ready
        assert "focused window is not terminal" in msg
        
        # 2. Window is terminal but busy (npm run)
        mock_win.title = "npm run dev - Windows PowerShell"
        ready, msg = op.is_terminal_ready()
        assert not ready
        assert "terminal busy running npm" in msg
        
        # 3. Window is idle powershell
        mock_win.title = "Windows PowerShell"
        ready, msg = op.is_terminal_ready()
        assert ready
        assert msg == "ready"

def test_keyboard_safe_delivery(clean_operator):
    """Ensures typing is aborted cleanly if focus is lost or if user override occurs."""
    op = clean_operator
    
    with patch('backend.desktop.semantic_operator.pyautogui') as mock_pyautogui, \
         patch('backend.desktop.semantic_operator.gw') as mock_gw:
        
        mock_pyautogui.position.return_value = (100, 100)
        mock_win = MagicMock()
        mock_win.isMinimized = False
        mock_win.title = "Windows PowerShell"
        mock_gw.getActiveWindow.return_value = mock_win
        
        # Case A: Correct focus, types successfully
        res = op.human_type_text("git status\n", expected_app="terminal")
        assert res
        assert op.current_state == ExecutionState.IDLE or op.current_state == ExecutionState.COMPLETED
        
        # Case B: Sharp mouse movement midpoint aborts typing
        mock_pyautogui.position.side_effect = [(100, 100), (200, 200)] # Sharp shift on second char read
        res = op.human_type_text("git diff\n", expected_app="terminal")
        assert not res
        assert op.current_state == ExecutionState.BLOCKED
