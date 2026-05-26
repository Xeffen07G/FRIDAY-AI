import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger("friday.tools.terminal_intelligence")

class TerminalIntelligence:
    """
    Parses active terminal stdouts in real-time.
    Identifies stacktraces, WebSocket closures, build failures, and triggers automatic fixes.
    """
    def __init__(self):
        # Common error patterns
        self.exception_regex = re.compile(r"(Exception|Error|failed|invalid|stderr)", re.IGNORECASE)
        self.websocket_regex = re.compile(r"(websocket|ws://|disconnect|close)", re.IGNORECASE)
        self.node_err_regex = re.compile(r"(ERR_CONNECTION|npm ERR!|sh: 1:)", re.IGNORECASE)

    def classify_line(self, line: str) -> Dict[str, Any]:
        """Classifies command outputs and extracts exception frames."""
        category = "INFO"
        is_error = False
        error_type = None

        if self.exception_regex.search(line):
            category = "EXCEPTION"
            is_error = True
            error_type = "PythonException"
        elif self.websocket_regex.search(line):
            category = "WEBSOCKET"
            is_error = True
            error_type = "WebSocketDisconnect"
        elif self.node_err_regex.search(line):
            category = "NODE_BUILD"
            is_error = True
            error_type = "CompilationFailure"

        return {
            "line": line.strip(),
            "category": category,
            "is_error": is_error,
            "error_type": error_type
        }

    def parse_stream_for_errors(self, chunk: str) -> List[Dict[str, Any]]:
        """Parses stdout stream chunks and extracts structured failure events."""
        events = []
        lines = chunk.splitlines()
        for line in lines:
            cls = self.classify_line(line)
            if cls["is_error"]:
                events.append({
                    "type": "terminal_error",
                    "severity": "high",
                    "summary": cls["line"]
                })
        return events

    def summarize_stacktrace(self, log_lines: List[str]) -> str:
        """Slices repeating debug details and returns pure root exception lines."""
        errors = []
        for line in log_lines:
            cls = self.classify_line(line)
            if cls["is_error"]:
                errors.append(line.strip())
        
        if errors:
            return f"Captured Root Error: {errors[-1]}"
        return "No diagnostic failures detected."

# Singleton instance
terminal_intelligence = TerminalIntelligence()
