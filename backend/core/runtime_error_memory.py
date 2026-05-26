import time
from typing import Dict, Any, List

class RuntimeErrorMemory:
    """
    Task 5: Live Error Memory
    Persists recurring failures, failed commands, broken imports, websocket issues,
    and recurring terminal crashes to adapt recovery behavior.
    """
    def __init__(self):
        self.error_log: List[Dict[str, Any]] = []

    def record_error(self, category: str, message: str, metadata: Dict[str, Any] = None):
        """Records an error instance with context and timestamp."""
        self.error_log.append({
            "timestamp": time.time(),
            "category": category,
            "message": message,
            "metadata": metadata or {}
        })

    def get_errors_in_last_seconds(self, seconds: float) -> List[Dict[str, Any]]:
        """Retrieves recorded error logs within a recent window."""
        now = time.time()
        return [err for err in self.error_log if (now - err["timestamp"]) <= seconds]

    def get_repeated_failure_count(self, category: str, message_substring: str = None, seconds: float = 300) -> int:
        """Counts matching errors in a given window to detect repeating patterns."""
        recent = self.get_errors_in_last_seconds(seconds)
        count = 0
        for err in recent:
            if err["category"] == category:
                if message_substring is None or message_substring.lower() in err["message"].lower():
                    count += 1
        return count

    def clear(self):
        self.error_log.clear()

runtime_error_memory = RuntimeErrorMemory()
