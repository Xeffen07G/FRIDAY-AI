import logging
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger("friday.core.planner")

class IntentComplexity(Enum):
    TRIVIAL = "trivial" # Quick chat, greetings
    CONVERSATIONAL = "conversational" # Normal chat, no tools
    RETRIEVAL = "retrieval" # Needs memory lookup
    TOOL_ASSISTED = "tool_assisted" # Needs 1-2 tool calls
    MULTI_STEP = "multi_step" # Complex planning, many tools
    AGENTIC = "agentic" # Autonomous task, background work

class ExecutionStrategy(Enum):
    DIRECT = "direct"
    REASONING_GRAPH = "reasoning_graph"
    AGENT_TASK = "agent_task"
    DEFERRED = "deferred"

class PlanningEngine:
    """Classifies intent complexity and determines execution strategy."""
    
    def __init__(self):
        # Keywords to signal complexity
        self.complex_triggers = ["build", "create", "search for", "find", "analyze", "explain why", "how do i", "monitor"]
        self.agent_triggers = ["keep checking", "every hour", "remind me when", "in the background", "autonomous"]

    def plan(self, user_input: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes input and returns a plan object."""
        lower_input = user_input.lower()
        
        # 1. Classify Complexity
        complexity = IntentComplexity.CONVERSATIONAL
        
        if len(user_input) < 10 and not any(q in lower_input for q in ["who", "what", "where", "how"]):
            complexity = IntentComplexity.TRIVIAL
        elif any(t in lower_input for t in self.agent_triggers):
            complexity = IntentComplexity.AGENTIC
        elif any(t in lower_input for t in self.complex_triggers) or len(user_input) > 100:
            complexity = IntentComplexity.MULTI_STEP
        elif any(t in lower_input for t in ["search", "weather", "open", "run", "status", "time", "date", "clock", "reminder", "summarize"]):
            complexity = IntentComplexity.TOOL_ASSISTED
        elif any(t in lower_input for t in ["remember", "recall", "last time", "preferences"]):
            complexity = IntentComplexity.RETRIEVAL

        # 2. Determine Strategy
        strategy = ExecutionStrategy.DIRECT
        if complexity in [IntentComplexity.MULTI_STEP, IntentComplexity.TOOL_ASSISTED, IntentComplexity.RETRIEVAL]:
            strategy = ExecutionStrategy.REASONING_GRAPH
        elif complexity == IntentComplexity.AGENTIC:
            strategy = ExecutionStrategy.AGENT_TASK

        # 3. Estimate Latency Budget
        latency_map = {
            IntentComplexity.TRIVIAL: 0.5,
            IntentComplexity.CONVERSATIONAL: 1.5,
            IntentComplexity.RETRIEVAL: 2.5,
            IntentComplexity.TOOL_ASSISTED: 5.0,
            IntentComplexity.MULTI_STEP: 15.0,
            IntentComplexity.AGENTIC: 60.0
        }
        
        plan = {
            "complexity": complexity.value,
            "strategy": strategy.value,
            "latency_budget": latency_map.get(complexity, 2.0),
            "require_scratchpad": complexity in [IntentComplexity.MULTI_STEP, IntentComplexity.AGENTIC],
            "estimated_steps": 1 if complexity in [IntentComplexity.TRIVIAL, IntentComplexity.CONVERSATIONAL] else 3
        }
        
        logger.info(f"PLAN: {plan['complexity']} via {plan['strategy']} | Budget: {plan['latency_budget']}s")
        return plan

planner = PlanningEngine()
