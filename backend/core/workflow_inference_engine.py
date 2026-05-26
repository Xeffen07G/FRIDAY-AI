from typing import Dict, Any
from core.context_engine import context_engine
from core.runtime_error_memory import runtime_error_memory

class WorkflowInferenceEngine:
    """
    Task 3: Passive Workflow Understanding
    Infers current active workflow patterns from live desktop context and error history.
    """
    def __init__(self):
        self.state_cache: Dict[str, Any] = {}

    def current_workflow_state(self) -> Dict[str, Any]:
        """Exposes the currently inferred user workflow and cognitive confidence level."""
        snapshot = context_engine.get_live_context_snapshot()
        app = snapshot.get("active_app", "")
        focused_file = snapshot.get("focused_file", "")
        
        # 1. Check for recurring websocket disconnects
        ws_failures = runtime_error_memory.get_repeated_failure_count("websocket", seconds=60)
        if ws_failures >= 3:
            return {
                "inferred_workflow": "connection debugging",
                "confidence": 0.95,
                "description": "WebSocket disconnecting repeatedly, active terminal errors present.",
                "suppression_active": False
            }

        # 2. Check for git merge conflicts
        if "conflict" in focused_file.lower() or "merge" in focused_file.lower():
            return {
                "inferred_workflow": "repository repair workflow",
                "confidence": 0.85,
                "description": "Git merge conflict file open in active workspace.",
                "suppression_active": False
            }

        # 3. Check for frontend development
        if "vscode" in app.lower() or "chrome" in app.lower():
            if "frontend" in snapshot.get("workspace", "").lower() or "vite" in focused_file.lower() or "js" in focused_file.lower() or "jsx" in focused_file.lower():
                return {
                    "inferred_workflow": "frontend development session",
                    "confidence": 0.90,
                    "description": "Working on React/Vite code inside active VSCode editor.",
                    "suppression_active": True  # Suppress alerts during deep development focus
                }

        # Default fallback
        return {
            "inferred_workflow": "general software development",
            "confidence": 0.70,
            "description": "Active environment: General workspace.",
            "suppression_active": False
        }

workflow_inference_engine = WorkflowInferenceEngine()
