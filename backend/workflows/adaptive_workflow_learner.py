import logging
from typing import Dict, Any, List

logger = logging.getLogger("friday.workflows.adaptive_learner")

class AdaptiveWorkflowLearner:
    """
    Observes consecutive user execution actions, tracks preferred terminal paths, 
    and synthesizes optimized layout execution pipelines.
    """
    def __init__(self):
        self.observed_sequences: List[str] = []
        self.learned_shortcuts: Dict[str, List[str]] = {}

    def observe_action(self, action_name: str):
        """Monitors execution history in real-time to locate workflow shortcuts."""
        self.observed_sequences.append(action_name)
        if len(self.observed_sequences) > 8:
            self.observed_sequences.pop(0)

        # Look for the classic sequence: VSCode focused followed by Vite dev server
        if len(self.observed_sequences) >= 2:
            last_two = self.observed_sequences[-2:]
            if "vscode" in last_two[0].lower() and "npm run dev" in last_two[1].lower():
                # Store dynamic shortcut pattern
                self.learned_shortcuts["fast_dev_boot"] = [
                    "Focus VSCode workspace", 
                    "Launch Dev server directly"
                ]
                logger.info("AdaptiveWorkflowLearner: Compiled dynamic shortcut pattern 'fast_dev_boot' from observations.")

    def get_learned_shortcuts(self) -> Dict[str, List[str]]:
        return self.learned_shortcuts.copy()

# Singleton instance
adaptive_workflow_learner = AdaptiveWorkflowLearner()
