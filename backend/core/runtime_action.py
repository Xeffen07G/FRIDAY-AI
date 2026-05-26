from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

class RuntimeAction(BaseModel):
    """
    Structured action object representation for unified state, tracking,
    auditing, and frontend rendering.
    """
    action_type: str        # e.g., 'open_app', 'calculate', 'get_time', 'terminal_execute', 'filesystem_query'
    source: str             # e.g., 'hard_router', 'planner', 'user_direct'
    payload: Dict[str, Any] # Parameters passed or returned
    deterministic: bool     # Is the execution Layer 1 or purely deterministic
    latency_ms: int         # Milliseconds taken to execute
    success: bool           # Successful execution flag
    timestamp: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
