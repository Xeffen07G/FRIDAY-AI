import sys
import json
import traceback
import logging
from typing import Dict, Any

logger = logging.getLogger("friday.core.diagnostics")

class DiagnosticsEngine:
    """
    Assembles production crash reports and bundles execution traces
    to simplify user debugging and self-healing.
    """
    def __init__(self):
        self.diagnostic_log_path = "friday_diagnostics.json"

    def compile_crash_report(self, exception: Exception, context: str = "general") -> Dict[str, Any]:
        """Packages exceptions, OS parameters, and stack traces into structured reports."""
        tb = traceback.format_exception(type(exception), exception, exception.__traceback__)
        report = {
            "version": "2.4.0",
            "context": context,
            "exception_type": type(exception).__name__,
            "message": str(exception),
            "traceback": tb,
            "python_version": sys.version,
            "subsystem_states": {
                "planner": "STABLE",
                "event_bus": "RUNNING"
            }
        }
        
        logger.error(f"DiagnosticsEngine: Core crash compiled: {type(exception).__name__}: {exception}")
        self._write_report(report)
        return report

    def _write_report(self, report: Dict[str, Any]):
        try:
            with open(self.diagnostic_log_path, "w") as f:
                json.dump(report, f, indent=4)
        except Exception as e:
            logger.error(f"DiagnosticsEngine: Failed to write crash diagnostics: {e}")

# Singleton instance
diagnostics_engine = DiagnosticsEngine()
