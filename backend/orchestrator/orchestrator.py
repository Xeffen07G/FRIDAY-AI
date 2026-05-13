import json
import asyncio
import time
import re
from llm.ollama_client import LLMClient
from orchestrator.prompt_manager import PromptManager
from memory.database import save_message, get_messages, update_session_title
from memory.memory_manager import memory_manager
from tools.tool_orchestrator import tool_orchestrator
from config.settings import settings
from core.logger import get_logger
from core.task_manager import task_manager
from core.model_manager import model_manager

logger = get_logger("orchestrator")

class Orchestrator:
    """Production-grade orchestrator with concurrency control and performance metrics."""
    
    _locks = {}
    _last_access = {}

    def __init__(self):
        self.llm = LLMClient()
    
    async def _cleanup_locks(self):
        """Prunes inactive session locks to prevent memory leaks."""
        now = time.time()
        to_delete = [sid for sid, last in self._last_access.items() if now - last > 3600]
        for sid in to_delete:
            self._locks.pop(sid, None)
            self._last_access.pop(sid, None)

    async def process_stream(self, session_id: str, user_input: str, request_id: str, background_tasks=None):
        """Unified streaming pipeline with per-session locking and async execution."""
        
        # 0. Acquire Lock
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()
        self._last_access[session_id] = time.time()

        if len(self._locks) > 100:
            asyncio.create_task(self._cleanup_locks())
        
        if self._locks[session_id].locked():
            logger.warning(f"[REQ:{request_id}] Session {session_id} is busy.")
            yield "⚠️ **System Busy:** Please wait for my previous response to finish."
            return

        async with self._locks[session_id]:
            start_time = time.time()
            metrics = {"request_id": request_id}
            
            try:
                # 0. Demo Mode Check (Phase 6: Demo Mode)
                if settings.DEMO_MODE:
                    try:
                        with open("core/demo_data.json", "r") as f:
                            demo_data = json.load(f)
                        
                        clean_input = user_input.lower().strip().replace("?", "").replace(".", "")
                        if clean_input in demo_data:
                            logger.info(f"[REQ:{request_id}] DEMO_MODE: Matching snapshot found for '{clean_input}'")
                            snapshot = demo_data[clean_input]
                            yield "[[STATUS:Thinking (Simulated)...]]"
                            await asyncio.sleep(0.5)
                            
                            # Simulate tool execution if requested
                            if snapshot.get("tools"):
                                yield "[[STATUS:Orchestrating (Simulated)...]]"
                                await asyncio.sleep(0.8)
                            
                            # Yield response in chunks to simulate streaming
                            words = snapshot["text"].split(" ")
                            for i, word in enumerate(words):
                                yield word + (" " if i < len(words) - 1 else "")
                                await asyncio.sleep(0.05)
                            
                            metrics["total_ms"] = int((time.time() - start_time) * 1000)
                            metrics["is_simulated"] = True
                            yield f"[[METRICS:{json.dumps(metrics)}]]"
                            return
                    except Exception as de:
                        logger.error(f"Demo Mode Error: {de}")

                # 1. Model Health Check
                if not await model_manager.ensure_model(settings.MODEL_NAME):
                    logger.warning(f"[REQ:{request_id}] Model {settings.MODEL_NAME} might not be loaded. Triggering check.")

                # 2. State Setup (Save user msg early)
                await task_manager.run_task(f"save_user_msg_{request_id}", asyncio.to_thread(save_message, session_id, "user", user_input))
                # 3. Intent Classification (Restored for system prompt selection)
                intent_start = time.time()
                intent = tool_orchestrator.get_intent(user_input)
                metrics["intent_ms"] = int((time.time() - intent_start) * 1000)

                # HARD DEBUG BYPASS (Task 5)
                debug_triggers = ["time", "clock", "date"]
                if any(t in user_input.lower() for t in debug_triggers):
                    print(f">>> DEBUG [REQ:{request_id}] HARD BYPASS TRIGGERED for {user_input}")
                    from datetime import datetime
                    response_text = f"Current time: {datetime.now().strftime('%I:%M %p, %B %d, %Y')}"
                    
                    yield "[[STATUS:Finalizing...]]"
                    yield f"[DETERMINISTIC_RESPONSE] {response_text}"
                    
                    metrics["execution_mode"] = "deterministic_bypass"
                    metrics["llm_bypassed"] = True
                    metrics["total_ms"] = int((time.time() - start_time) * 1000)
                    
                    await task_manager.run_task(f"save_friday_msg_{request_id}", asyncio.to_thread(save_message, session_id, "friday", response_text))
                    yield f"[[METRICS:{json.dumps(metrics)}]]"
                    return

                # 4. Planning Phase (Phase 3: Failure Recovery - Graceful Degradation)
                from core.planner import planner
                from core.event_bus import event_bus
                
                try:
                    plan = planner.plan(user_input, [])
                    event_bus.emit("brain", "planning_started", {"request_id": request_id, "plan": plan})
                except Exception as pe:
                    logger.error(f"Planning Engine failure: {pe}")
                    plan = {"complexity": "conversational", "strategy": "direct", "require_scratchpad": False, "latency_budget": 2.0}
                    event_bus.emit("brain", "planning_fallback", {"request_id": request_id, "error": str(pe)})
                
                # 4. Context Retrieval
                retrieval_start = time.time()
                past_msgs = await asyncio.to_thread(get_messages, session_id)
                
                # Prompt Compression: Dynamic context trimming
                window_size = settings.CONTEXT_WINDOW_SIZE
                if model_manager.is_ram_under_pressure():
                    window_size = 4

                semantic_context = ""
                try:
                    if plan["strategy"] != "direct":
                        yield "[[STATUS:Searching memory...]]"
                        event_bus.emit("brain", "thought", {"request_id": request_id, "thought": "Analyzing context."})
                        semantic_context = await memory_manager.get_relevant_context(user_input, limit=2)
                except Exception as re:
                    logger.warning(f"Memory retrieval failure: {re}")
                    event_bus.emit("brain", "retrieval_failure", {"request_id": request_id})
                
                metrics["retrieval_ms"] = int((time.time() - retrieval_start) * 1000)

                # 5. Tool Orchestration (Phase 3: Resilience)
                tool_data = None
                if plan["strategy"] == "reasoning_graph":
                    try:
                        tool_start = time.time()
                        yield "[[STATUS:Orchestrating...]]"
                        event_bus.emit("brain", "thought", {"request_id": request_id, "thought": "Executing graph reasoning."})
                        
                        # DEBUG LOGS
                        print(f">>> DEBUG [REQ:{request_id}] Strategy: {plan['strategy']}")
                        print(f">>> DEBUG [REQ:{request_id}] Intent: {intent}")
                        
                        tool_data = await tool_orchestrator.check_and_execute_tools(user_input, request_id)
                        metrics["tool_ms"] = int((time.time() - tool_start) * 1000)
                        
                        if tool_data:
                            print(f">>> DEBUG [REQ:{request_id}] Tool Selected: {tool_data['tool']}")
                            metrics["tool_used"] = True
                            metrics["tool_name"] = tool_data["tool"]
                            
                            # DETERMINISTIC BYPASS (Mandatory Architecture Change)
                            deterministic_tools = ['calculator', 'system_action', 'desktop_agent', 'terminal']
                            if tool_data["tool"] in deterministic_tools:
                                print(f">>> DEBUG [REQ:{request_id}] Entering DETERMINISTIC BYPASS")
                                logger.info(f"[REQ:{request_id}] DETERMINISTIC BYPASS: Returning {tool_data['tool']} result directly.")
                                yield "[[STATUS:Finalizing...]]"
                                
                                # Yield the direct tool result
                                response_text = tool_data["result"]
                                if isinstance(response_text, dict):
                                    response_text = json.dumps(response_text, indent=2)
                                
                                # HARD MARKER
                                yield f"[DETERMINISTIC_RESPONSE] {response_text}"
                                
                                # Telemetry & Persistence
                                metrics["execution_mode"] = "deterministic"
                                metrics["llm_bypassed"] = True
                                metrics["total_ms"] = int((time.time() - start_time) * 1000)
                                
                                await task_manager.run_task(f"save_friday_msg_{request_id}", asyncio.to_thread(save_message, session_id, "friday", response_text))
                                yield f"[[METRICS:{json.dumps(metrics)}]]"
                                return
                            
                            event_bus.emit("brain", "tool_result", {"request_id": request_id, "result": tool_data["formatted"][:200]})
                        else:
                            print(f">>> DEBUG [REQ:{request_id}] No tool selected by orchestrator")
                            metrics["tool_used"] = False
                            metrics["tool_fallback"] = "no_tool_selected"
                    except Exception as te:
                        logger.error(f"Reasoning Graph failure: {te}")
                        event_bus.emit("brain", "orchestration_fallback", {"request_id": request_id, "error": str(te)})
                        tool_data = {"formatted": f"Warning: I encountered an error while using my tools ({str(te)}). I will proceed with my current knowledge."}

                # 6. Generation Setup (Generative Mode)
                print(f">>> DEBUG [REQ:{request_id}] Entering GENERATIVE MODE")
                metrics["execution_mode"] = "generative"
                metrics["llm_bypassed"] = False
                
                yield "[[STATUS:Thinking...]]"
                # HARD MARKER START
                yield "[GENERATIVE_RESPONSE] "
                from core.sanitizer import Sanitizer
                event_bus.emit("brain", "thought", {"request_id": request_id, "thought": "Finalizing response."})
                
                system_prompt = PromptManager.get_system_prompt(intent)
                
                # Hard Identity Check (Phase 1: Trace Prompt Injection)
                logger.info(f"[REQ:{request_id}] Execution Strategy: {plan['strategy']}")
                logger.info(f"[REQ:{request_id}] Identity Layer First 200: {system_prompt[:200]}")
                
                # Active Session State: Inject continuous context
                from memory.session_state import session_state_manager
                session_state = session_state_manager.get_session(session_id)
                active_context = session_state.get_context_string()
                
                messages = [{"role": "system", "content": system_prompt}]
                
                if active_context:
                    messages.append({"role": "system", "content": f"ACTIVE SESSION STATE:\n{active_context}"})
                
                # Scratchpad (Phase 3: Internal Scratchpad)
                if plan["require_scratchpad"]:
                    scratchpad_context = f"INTERNAL PLAN:\nComplexity: {plan['complexity']}\nStrategy: {plan['strategy']}\nBudget: {plan['latency_budget']}s"
                    messages.append({"role": "system", "content": f"SCRATCHPAD (Hidden Reasoning):\n{scratchpad_context}"})
                
                if semantic_context:
                    messages.append({"role": "system", "content": f"RELEVANT PAST KNOWLEDGE:\n{semantic_context}"})
                
                # History Trimming
                for m in past_msgs[-window_size:]:
                    role = "assistant" if m['sender'] == 'friday' else "user"
                    messages.append({"role": role, "content": m['text'][:500]})
                    
                current_msg = user_input
                if tool_data:
                    # Phase 4: Tool Response Sandboxing
                    safe_tool_results = Sanitizer.sanitize_tool_result(tool_data["formatted"])
                    current_msg += f"\n\n[TOOL_RESULT]\n{safe_tool_results}"
                
                messages.append({"role": "user", "content": current_msg})
                
                logger.info(f"[REQ:{request_id}] Message Array Length: {len(messages)}")
                logger.info(f"[REQ:{request_id}] Roles: {[m['role'] for m in messages]}")

                options = {"temperature": 0.4, "num_predict": 120}
                if intent == "memory_save":
                    options["temperature"] = 0.3
                
                # 7. Response Streaming
                full_response = ""
                token_count = 0
                gen_start = time.time()
                
                async for token in self.llm.generate_stream(messages, options=options, request_id=request_id):
                    if not metrics.get("first_token_ms"):
                        metrics["first_token_ms"] = int((time.time() - gen_start) * 1000)
                    
                    full_response += token
                    token_count += 1
                    # Phase 4: Output Sanitization (streaming chunks might be hard to sanitize mid-word, so we'll do a final check if needed, but for now we'll trust the prompt)
                    yield token
                
                # Final pass sanitization for the persisted response
                full_response = Sanitizer.sanitize_output(full_response)
                
                metrics["generation_ms"] = int((time.time() - gen_start) * 1000)
                metrics["token_count"] = token_count
                
                event_bus.emit("brain", "planning_finished", {"request_id": request_id, "status": "success"})
                
                # Update Session State with results
                session_state.update_from_interaction(user_input, full_response, intent)
                
                # 8. Post-Processing & Persistence
                metrics["total_ms"] = int((time.time() - start_time) * 1000)
                await task_manager.run_task(f"save_friday_msg_{request_id}", asyncio.to_thread(save_message, session_id, "friday", full_response))
                await task_manager.run_task(f"store_user_mem_{request_id}", memory_manager.extract_and_store_memory(user_input, "user", session_id))
                await task_manager.run_task(f"store_friday_mem_{request_id}", memory_manager.extract_and_store_memory(full_response, "friday", session_id))
                
                if len(past_msgs) > 0 and (len(past_msgs) + 1) % 10 == 0:
                    logger.info(f"[REQ:{request_id}] Triggering background session summarization.")
                    # Pass the messages properly
                    current_msgs = past_msgs + [{"sender": "user", "text": user_input}, {"sender": "friday", "text": full_response}]
                    await task_manager.run_task(f"summarize_{session_id}", memory_manager.summarize_session(session_id, current_msgs))
                
                if len(past_msgs) <= 1:
                    await task_manager.run_task(f"update_title_{session_id}", asyncio.to_thread(update_session_title, session_id, user_input[:30]))

                metrics["total_ms"] = int((time.time() - start_time) * 1000)
                logger.info(f"[REQ:{request_id}] Completed in {metrics['total_ms']}ms. Intent: {intent}")
                
                # Production Telemetry: Record and persist metrics
                from core.metrics_manager import metrics_manager
                
                # Phase 7: Bottleneck Detection
                if metrics.get("total_ms", 0) > 5000:
                    slow_phase = max(metrics, key=lambda k: metrics[k] if isinstance(metrics[k], int) and k.endswith('_ms') else 0)
                    logger.warning(f"[REQ:{request_id}] PERFORMANCE ALERT: Total latency {metrics['total_ms']}ms. Bottleneck in {slow_phase}.")
                    metrics["is_bottleneck"] = True
                
                metrics_manager.record_request(metrics)
                
                yield f"[[METRICS:{json.dumps(metrics)}]]"
                
            except GeneratorExit:
                logger.warning(f"[REQ:{request_id}] Client disconnected. Cancelling stream.")
                # We still want to save what we have if it's significant
                if len(full_response) > 10:
                    await task_manager.run_task(f"save_friday_msg_partial_{request_id}", asyncio.to_thread(save_message, session_id, "friday", full_response + "... [Interrupted]"))
                raise
            except Exception as e:
                logger.error(f"[REQ:{request_id}] Orchestration crash: {e}", exc_info=True)
                yield f"\n\n❌ **Orchestrator Error:** {str(e)}"

friday_orchestrator = Orchestrator()
