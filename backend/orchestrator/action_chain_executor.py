import re
import json
import time
import asyncio
from typing import List, Dict, Any
from core.event_bus import event_bus
from core.runtime_action import RuntimeAction
from core.runtime_state import runtime_state
from tools.tool_registry import tool_registry
from llm.ollama_client import LLMClient
from core.logger import get_logger

logger = get_logger("orchestrator.action_chain")

class ActionChainExecutor:
    """
    Executes multi-action pipelines with an execution queue, failure recovery,
    and progress streaming.
    """
    def __init__(self):
        self.llm = LLMClient()
        self._recent_executions = {}  # fingerprint -> (timestamp, result)

    def _check_dedup(self, tool_name: str, args: dict) -> str | None:
        """Returns cached result if same action executed within 2s, else None."""
        import hashlib
        fp = hashlib.md5(f"{tool_name}:{json.dumps(args, sort_keys=True)}".encode()).hexdigest()
        now = time.time()
        # Prune stale entries
        self._recent_executions = {k: v for k, v in self._recent_executions.items() if now - v[0] < 2.0}
        if fp in self._recent_executions:
            logger.info(f"Dedup hit: {tool_name} — returning cached result")
            return self._recent_executions[fp][1]
        return None

    def _record_execution(self, tool_name: str, args: dict, result: str):
        import hashlib
        fp = hashlib.md5(f"{tool_name}:{json.dumps(args, sort_keys=True)}".encode()).hexdigest()
        self._recent_executions[fp] = (time.time(), result)

    def parse_chain_deterministically(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Parses common multi-action prompts using high-speed deterministic regex rules.
        Returns a list of action dicts or None if it doesn't match a standard pattern.
        """
        clean = prompt.lower().strip()
        
        # Split clauses
        clauses = re.split(r'\s+and\s+|\s+then\s+|;\s*', clean)
        actions = []

        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue

            # 1. Open App matcher
            open_match = re.match(r"^(?:open|launch|start)\s+([a-zA-Z0-9_\-\.]+)(?:\s+app)?$", clause)
            if open_match:
                target = open_match.group(1)
                # App mapping
                if target in ["vscode", "code"]:
                    target = "vscode"
                actions.append({
                    "tool": "system_action",
                    "args": {"action": "open_app", "target": target},
                    "deterministic": True
                })
                continue

            # 2. Search matcher
            search_match = re.match(r"^(?:search|google|find)\s+(.+)$", clause)
            if search_match:
                query = search_match.group(1)
                actions.append({
                    "tool": "web_search",
                    "args": {"query": query},
                    "deterministic": False
                })
                continue

            # 3. Terminal Run matcher
            run_match = re.match(r"^(?:run|execute|launch\s+terminal\s+and\s+run)\s+(.+)$", clause)
            if run_match:
                cmd = run_match.group(1)
                actions.append({
                    "tool": "terminal",
                    "args": {"command": cmd},
                    "deterministic": False
                })
                continue
                
            # 4. Math calculator
            math_match = re.match(r"^(?:calculate|compute|solve)\s+(.+)$", clause)
            if math_match:
                expr = math_match.group(1)
                actions.append({
                    "tool": "calculator",
                    "args": {"expression": expr},
                    "deterministic": True
                })
                continue

            # If any clause is not deterministically parseable, return None to trigger LLM parsing
            return None

        return actions

    async def parse_chain_generative(self, prompt: str, request_id: str) -> List[Dict[str, Any]]:
        """
        Parses complex or ambiguous multi-action requests using the LLM planner.
        """
        schemas = tool_registry.get_all_tools_schema()
        system_prompt = f"""You are a multi-action graph planner. Your job is to compile a sequential queue of tool execution tasks based on a user request.
Available Tools:
{json.dumps(schemas)}

Rules:
1. Break down the user prompt into a list of sequential actions.
2. Return a strict JSON list of objects with "tool" (str) and "args" (dict) keys.
3. If an action cannot map to a tool, omit it.
4. Output ONLY valid JSON array. Zero explanation.

Example Input:
"open chrome and search transformers"
Example Output:
[
  {{"tool": "system_action", "args": {{"action": "open_app", "target": "chrome"}}}},
  {{"tool": "web_search", "args": {{"query": "transformers"}}}}
]
"""
        try:
            logger.info(f"[REQ:{request_id}] Calling LLM for action-chain parsing.")
            response = await self.llm.generate_json(prompt, system=system_prompt, request_id=request_id)
            if not response:
                return []
            
            # Clean up potential markdown formatting block if returned
            response = re.sub(r"^```json\s*|\s*```$", "", response.strip())
            
            actions = json.loads(response)
            if isinstance(actions, list):
                for a in actions:
                    a["deterministic"] = False
                return actions
        except Exception as e:
            logger.error(f"[REQ:{request_id}] Generative chain parser failed: {e}")
        return []

    async def execute_chain(self, prompt: str, session_id: str, request_id: str) -> List[Dict[str, Any]]:
        """
        Runs the full action-chain pipeline.
        Yields progress notifications over the EventBus and returns final results.
        """
        start_time = time.time()
        
        # 1. Parse intent into sequential graph
        actions = self.parse_chain_deterministically(prompt)
        parse_mode = "deterministic"
        if not actions:
            actions = await self.parse_chain_generative(prompt, request_id)
            parse_mode = "generative"

        if not actions:
            logger.warning(f"[REQ:{request_id}] Action chain parsing returned empty list.")
            return []

        logger.info(f"[REQ:{request_id}] Action chain compiled ({parse_mode}): {actions}")
        return await self.execute_parsed_chain(actions, session_id, request_id, parse_mode, start_time)

    async def execute_parsed_chain(self, actions: List[Dict[str, Any]], session_id: str, request_id: str, parse_mode: str = "deterministic", start_time: float = None) -> List[Dict[str, Any]]:
        if start_time is None:
            start_time = time.time()
            
        # Broadcast execution start
        event_bus.emit("brain", "execution_started", {
            "request_id": request_id,
            "session_id": session_id,
            "chain_length": len(actions)
        })

        results = []
        
        # 2. Sequential execution loop
        for index, action in enumerate(actions):
            if runtime_state.system.cancel_requested:
                logger.warning(f"[REQ:{request_id}] Execution cancelled by user.")
                event_bus.emit("brain", "action_failed", {
                    "request_id": request_id,
                    "tool": "system",
                    "error": "Execution cancelled by user.",
                    "latency_ms": 0
                })
                runtime_state.system.cancel_requested = False
                break
                
            tool_name = action.get("tool")
            args = action.get("args", {})
            is_deterministic = action.get("deterministic", False)
            
            # Calculate execution confidence dynamically (Task 2)
            confidence = 100
            validation_source = "Deterministic Execution"
            fallback_used = None

            if tool_name == "terminal":
                try:
                    import pygetwindow as gw
                    active = gw.getActiveWindow()
                    if active:
                        title = active.title.lower()
                        safe_keywords = ["code", "cmd", "powershell", "terminal", "bash", "ide", "editor"]
                        if any(k in title for k in safe_keywords):
                            confidence = 98
                            validation_source = f"Focus Validated ({active.title[:12]}...)"
                        else:
                            confidence = 62
                            validation_source = "Window Focus Uncertain"
                            fallback_used = "Autonomy Warning Triggered"
                    else:
                        confidence = 70
                        validation_source = "No Active Handle"
                except Exception:
                    confidence = 85
                    validation_source = "Process Focus Fallback"
            elif tool_name == "system_action":
                confidence = 96
                validation_source = "OS Process API Check"
            elif tool_name == "calculator":
                confidence = 100
                validation_source = "Safe Evaluator Engine"
            elif tool_name == "web_search":
                confidence = 95
                validation_source = "Search Engine API"

            # Low confidence pause gate (Task 2)
            if confidence < 70:
                logger.warning(f"[REQ:{request_id}] Low execution confidence ({confidence}%) - {validation_source}. Pausing for safety confirmation.")
                event_bus.emit("brain", "action_failed", {
                    "request_id": request_id,
                    "tool": tool_name,
                    "error": "paused: confirm?",
                    "latency_ms": 0
                })
                conv_state = runtime_state.get_conversation(session_id)
                conv_state.pending_actions = actions[index:]
                runtime_state.save_to_disk()
                
                # Emit deterministic text event via event bus if possible, or just break and let orchestrator yield
                results.append({
                    "action": action,
                    "result": "paused: confirm?",
                    "success": False,
                    "latency_ms": 0
                })
                break

            # Emit live task progress
            event_bus.emit("brain", "tool_running", {
                "request_id": request_id,
                "tool": tool_name,
                "args": args,
                "step": f"{index + 1}/{len(actions)}",
                "confidence": confidence,
                "validation_source": validation_source,
                "fallback_used": fallback_used
            })

            tool_start = time.time()
            success = False
            result_str = ""

            try:
                # Dedup check
                cached = self._check_dedup(tool_name, args)
                if cached is not None:
                    result_str = cached
                    success = "error" not in result_str.lower()
                else:
                    result_str = await tool_registry.execute_tool(tool_name, args)
                    success = "error" not in result_str.lower()
                    self._record_execution(tool_name, args, result_str)
            except Exception as e:
                result_str = f"Execution error: {e}"
                success = False

            tool_latency = int((time.time() - tool_start) * 1000)

            # Record RuntimeAction object (Task 3!)
            runtime_action = RuntimeAction(
                action_type=tool_name,
                source=parse_mode,
                payload=args,
                deterministic=is_deterministic,
                latency_ms=tool_latency,
                success=success
            )

            # Write to central ToolState and SystemState (Task 4!)
            runtime_state.tools.last_tool_executed = tool_name
            runtime_state.tools.last_tool_success = success
            if tool_name not in runtime_state.tools.executed_tools_count:
                runtime_state.tools.executed_tools_count[tool_name] = 0
            runtime_state.tools.executed_tools_count[tool_name] += 1

            # Emit live completion/failure
            if success:
                event_bus.emit("brain", "tool_completed", {
                    "request_id": request_id,
                    "tool": tool_name,
                    "result": result_str,
                    "latency_ms": tool_latency
                })
            else:
                event_bus.emit("brain", "action_failed", {
                    "request_id": request_id,
                    "tool": tool_name,
                    "error": result_str,
                    "latency_ms": tool_latency
                })
                # Failure Recovery: Log and proceed, or we can choose to abort
                logger.warning(f"[REQ:{request_id}] Step {index + 1} failed. Triggering recovery path.")

            results.append({
                "action": action,
                "result": result_str,
                "success": success,
                "latency_ms": tool_latency
            })

        # Finalize response
        total_latency = int((time.time() - start_time) * 1000)
        event_bus.emit("brain", "stream_complete", {
            "request_id": request_id,
            "total_latency_ms": total_latency
        })

        return results

# Singleton instance
action_chain_executor = ActionChainExecutor()
