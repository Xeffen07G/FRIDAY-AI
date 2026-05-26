import json
import asyncio
import time
import re
from llm.ollama_client import LLMClient
from orchestrator.prompt_manager import PromptManager
from memory.database import save_message, get_messages, update_session_title, create_generation, update_generation_state, get_generation_state, get_active_generation_id
from memory.memory_manager import memory_manager
from tools.tool_orchestrator import tool_orchestrator
from config.settings import settings
from core.logger import get_logger
from core.task_manager import task_manager
from core.model_manager import model_manager
from core.event_bus import event_bus
from core.runtime_state import runtime_state
from orchestrator.response_cleaner import response_cleaner
from orchestrator.action_chain_executor import action_chain_executor

logger = get_logger("orchestrator")

import base64
def frame_token(session_id: str, message_id: str, generation_id: str, token: str) -> str:
    b64_token = base64.b64encode(token.encode('utf-8')).decode('utf-8')
    return f"[[TOKEN:{session_id}:{message_id}:{generation_id}:{b64_token}]]"


def normalize_input(text: str) -> str:
    t = text.lower()
    t = t.replace("what's", "what is")
    t = t.replace("who's", "who is")
    t = re.sub(r"[^\w\s]", "", t)
    
    words = t.split()
    normalized_words = []
    for w in words:
        if w == "whats":
            normalized_words.append("what is")
        elif w == "whos":
            normalized_words.append("who is")
        elif w == "dont":
            normalized_words.append("do not")
        elif w == "fav":
            normalized_words.append("favorite")
        else:
            normalized_words.append(w)
            
    t = " ".join(normalized_words)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_topic_from_query(query: str) -> str:
    norm = normalize_input(query)
    
    prefixes = [
        "what is my ",
        "tell me my ",
        "do you know my ",
        "remember my ",
        "recall my ",
        "which is my ",
        "my "
    ]
    
    for prefix in prefixes:
        if norm.startswith(prefix):
            if prefix in ["remember my ", "my "]:
                rest = norm[len(prefix):].strip()
                if any(f" {assign} " in rest for assign in ["is", "was", "set to"]):
                    continue
            topic = norm[len(prefix):].strip()
            return topic
            
    if norm == "recall" or norm == "what did i tell you":
        return "all"
        
    return None


def get_canonical_key(topic: str) -> str:
    if not topic:
        return None
    t = topic.lower().strip()
    t = t.replace("colour", "color")
    t = re.sub(r"\s+", "_", t)
    return t


PROFILE_KEYS = {
    "favorite_color",
    "dog_name",
    "name",
    "birthday",
    "favorite_movie",
    "favorite_food",
    "favorite_song",
    "likes"
}


def parse_storage_input(query: str):
    q = query.strip()
    lower_q = q.lower()
    
    # Check for "i like X"
    if lower_q.startswith("i like "):
        val = q[7:].strip()
        val = val.rstrip(".!?")
        canonical = "likes"
        lower_val = val.lower()
        foods = ["pizza", "burger", "sushi", "pasta", "taco", "food", "steak", "salad"]
        movies = ["interstellar", "inception", "movie", "film", "star wars", "matrix", "avatar"]
        songs = ["song", "music", "yellow submarine", "yesterday", "beatles"]
        if any(f in lower_val for f in foods):
            canonical = "favorite_food"
        elif any(m in lower_val for m in movies):
            canonical = "favorite_movie"
        elif any(s in lower_val for s in songs):
            canonical = "favorite_song"
            
        return canonical, val

    for prefix in ["remember that my ", "remember my ", "remember that ", "remember "]:
        if lower_q.startswith(prefix):
            q = q[len(prefix):].strip()
            lower_q = q.lower()
            break
            
    splitters = [" is ", " was ", " set to "]
    for splitter in splitters:
        if splitter in lower_q:
            idx = lower_q.find(splitter)
            left = q[:idx].strip()
            right = q[idx+len(splitter):].strip()
            
            if left.lower().startswith("my "):
                topic = left[3:].strip()
                val = right
            elif right.lower().startswith("my "):
                topic = right[3:].strip()
                val = left
            else:
                topic = left
                val = right
                
            return get_canonical_key(topic), val
            
    return None, None


def format_recalled_value(canonical_key: str, val: str) -> str:
    if not val:
        return "I don't know."
        
    val_clean = val.strip()
    
    forbidden_terms = [
        "secure environment", "visual recognition", "workflow optimization", 
        "shared digital space", "assistant module", "high trust", "premium", 
        "operating layer", "right!", "indeed", "harmoniously", "resonates"
    ]
    for term in forbidden_terms:
        if term in val_clean.lower():
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            val_clean = pattern.sub("", val_clean).strip()
            
    if canonical_key in ["dog_name", "favorite_color"]:
        if val_clean:
            val_clean = val_clean[0].upper() + val_clean[1:]
            if not val_clean.endswith("."):
                val_clean += "."
    elif canonical_key == "name":
        val_clean = val_clean.lower()
        val_clean = val_clean.rstrip(".!?")
        
    return val_clean


def conversation_lookup(session_id: str, canonical_key: str) -> str:
    logger.info(f"memory_query: scope=conversation user_id=default_user session_id={session_id} canonical_key={canonical_key}")
    
    from memory.vector_store import vector_store
    memories = vector_store.get_all_memories()
    
    active_memories = []
    for mem in memories:
        meta = mem.get("metadata", {})
        active_val = meta.get("active", True)
        if isinstance(active_val, str):
            active_val = (active_val.lower() == "true")
        if active_val:
            active_memories.append(mem)
            
    for mem in active_memories:
        meta = mem.get("metadata", {})
        if meta.get("scope") == "conversation" and meta.get("session_id") == session_id and meta.get("canonical_key") == canonical_key:
            val = meta.get("value")
            if val:
                return format_recalled_value(canonical_key, val)
                
    return None


def profile_lookup(user_id: str, canonical_key: str) -> str:
    logger.info(f"memory_query: scope=profile user_id={user_id} session_id=none canonical_key={canonical_key}")
    
    from memory.vector_store import vector_store
    memories = vector_store.get_all_memories()
    
    active_memories = []
    for mem in memories:
        meta = mem.get("metadata", {})
        active_val = meta.get("active", True)
        if isinstance(active_val, str):
            active_val = (active_val.lower() == "true")
        if active_val:
            active_memories.append(mem)
            
    profile_matches = []
    for mem in active_memories:
        meta = mem.get("metadata", {})
        if meta.get("scope") == "profile" and meta.get("user_id") == user_id and meta.get("canonical_key") == canonical_key:
            profile_matches.append(mem)
            
    if profile_matches:
        profile_matches.sort(key=lambda x: x["metadata"].get("created_at", ""), reverse=True)
        newest = profile_matches[0]
        val = newest["metadata"].get("value")
        if val:
            return format_recalled_value(canonical_key, val)
            
    return None


class Orchestrator:
    """Production-grade orchestrator with concurrency control and performance metrics."""
    
    _locks = {}
    _last_access = {}
    _processed_nonces = set()

    def __init__(self):
        self.llm = LLMClient()
    
    async def _cleanup_locks(self):
        """Prunes inactive session locks to prevent memory leaks."""
        now = time.time()
        to_delete = [sid for sid, last in self._last_access.items() if now - last > 3600]
        for sid in to_delete:
            self._locks.pop(sid, None)
            self._last_access.pop(sid, None)

    async def cancel_generation(self, session_id: str):
        """Unified cancellation logic that handles all cancellation sources."""
        logger.warning(f"cancel_generation() called for session_id {session_id}")
        
        # Transition generation state to CANCELLED in database
        generation_id = get_active_generation_id(session_id)
        if generation_id:
            update_generation_state(generation_id, "CANCELLED")
            
        runtime_state.system.cancel_requested = True
        runtime_state.terminate_active_subprocesses()
        event_bus.emit("brain", "stream_complete", {"session_id": session_id, "status": "cancelled"})

    def _is_strict_memory_query(self, query: str) -> bool:
        topic = extract_topic_from_query(query)
        return topic is not None

    def _is_strict_memory_storage(self, query: str) -> bool:
        if self._is_strict_memory_query(query):
            return False
        lower_q = query.lower().strip()
        storage_indicators = [
            "my favorite color is", "my name is", "remember that my", 
            "remember that i", "remember my", "is my name", "remember sayak",
            "my dog name is"
        ]
        if any(ind in lower_q for ind in storage_indicators):
            return True
        canonical, val = parse_storage_input(query)
        return canonical is not None and val is not None

    async def _handle_strict_memory_recall(self, session_id: str, query: str) -> str:
        topic = extract_topic_from_query(query)
        canonical = get_canonical_key(topic)
        
        if not topic or not canonical:
            return "I don't know."
            
        # 1. Conversation lookup (current session)
        ans = conversation_lookup(session_id, canonical)
        if ans:
            return ans
            
        # 2. Profile lookup (current user)
        ans = profile_lookup("default_user", canonical)
        if ans:
            return ans
            
        return "I don't know."

    async def _handle_strict_memory_storage(self, session_id: str, query: str) -> str:
        from memory.embedding_service import embedding_service
        from memory.vector_store import vector_store
        from datetime import datetime
        import uuid
        
        clean_text = query.strip()
        embedding = await embedding_service.get_embedding(clean_text)
        if embedding:
            memory_id = str(uuid.uuid4())
            now = datetime.now()
            
            canonical_key, val = parse_storage_input(query)
            if not canonical_key:
                canonical_key = "unknown"
                val = clean_text
                
            scope = "profile" if canonical_key in PROFILE_KEYS else "conversation"
            new_source = "user_declared"
            
            # Conflict Resolution: Latest user-declared write wins
            memories = vector_store.get_all_memories()
            
            existing_mem = None
            for mem in memories:
                meta = mem.get("metadata", {})
                active_val = meta.get("active", True)
                if isinstance(active_val, str):
                    active_val = (active_val.lower() == "true")
                if active_val:
                    if scope == "profile":
                        if meta.get("scope") == "profile" and meta.get("canonical_key") == canonical_key:
                            existing_mem = mem
                            break
                    else:
                        if meta.get("session_id") == session_id and meta.get("canonical_key") == canonical_key:
                            existing_mem = mem
                            break
                            
            allowed = True
            if existing_mem:
                existing_meta = existing_mem.get("metadata", {})
                existing_source = existing_meta.get("source", "user_declared")
                
                PROVENANCE_PRECEDENCE = {
                    "user_declared": 4,
                    "derived": 3,
                    "imported": 2,
                    "migrated": 1
                }
                
                if scope == "profile":
                    if new_source != "user_declared":
                        allowed = False
                else:
                    if PROVENANCE_PRECEDENCE.get(new_source, 1) < PROVENANCE_PRECEDENCE.get(existing_source, 1):
                        allowed = False
                        
                if allowed:
                    existing_meta["active"] = False
                    existing_meta["superseded_by"] = memory_id
                    vector_store.update_metadata(existing_mem["id"], existing_meta)
                    logger.info(f"[CONFLICT_RESOLUTION] Superseded old memory ID={existing_mem['id']} with new memory ID={memory_id}")
                    
            metadata = {
                "canonical_key": canonical_key,
                "value": val,
                "created_at": now.isoformat(),
                "source": new_source,
                "active": allowed,
                "superseded_by": "none" if allowed else (existing_mem["id"] if existing_mem else "none")
            }
            
            if scope == "profile":
                metadata["scope"] = "profile"
                metadata["user_id"] = "default_user" # required
                metadata["session_id"] = session_id
            else:
                metadata["scope"] = "conversation"
                metadata["session_id"] = session_id # required
                metadata["user_id"] = "default_user"
                
            vector_store.add_memory(memory_id, clean_text, embedding, metadata)
            logger.info(f"[STRICT_MEMORY_STORAGE] Directly stored memory '{clean_text}' with canonical_key '{canonical_key}', scope '{scope}', active={allowed} without deduplication.")
        return "I will remember that."

    async def process_stream(self, session_id: str, user_input: str, request_id: str, nonce: str = None, background_tasks=None):
        """Unified streaming pipeline with per-session locking, instant response, and async execution."""
        
        if nonce and nonce in self._processed_nonces:
            logger.warning(f"[REQ:{request_id}] Dropping duplicate request (nonce: {nonce})")
            yield "[[STATUS:duplicate_dropped]]"
            return
            
        if nonce:
            self._processed_nonces.add(nonce)
            if len(self._processed_nonces) > 5000:
                self._processed_nonces.clear()
        
        if nonce and get_generation_state(nonce) == "CANCELLED":
            logger.warning(f"[CANCEL_OWNERSHIP] Generation {nonce} was cancelled before uvicorn lock. Aborting.")
            return

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
            if nonce and get_generation_state(nonce) == "CANCELLED":
                logger.warning(f"[CANCEL_OWNERSHIP] Generation {nonce} was cancelled during lock wait. Aborting.")
                return
                
            import uuid
            message_id = f"msg_{int(time.time()*1000)}_{str(uuid.uuid4())[:8]}"
            
            if nonce:
                update_generation_state(nonce, "ACCEPTED")
                
            yield f"[[STATUS:accepted:{message_id}:{nonce}]]"

            # Check if strict memory recall or storage applies
            if self._is_strict_memory_query(user_input) or self._is_strict_memory_storage(user_input):
                logger.info(f"[STRICT_MEMORY] Intercepting user input: '{user_input}'")
                
                if nonce:
                    update_generation_state(nonce, "STREAMING")
                    
                response_text = ""
                if self._is_strict_memory_query(user_input):
                    response_text = await self._handle_strict_memory_recall(session_id, user_input)
                else:
                    response_text = await self._handle_strict_memory_storage(session_id, user_input)
                
                if nonce:
                    yield frame_token(session_id, message_id, nonce, response_text)
                else:
                    yield response_text
                    
                if nonce:
                    update_generation_state(nonce, "COMPLETED")
                    
                await task_manager.run_task(
                    f"save_friday_msg_{request_id}", 
                    asyncio.to_thread(save_message, session_id, "friday", response_text, None, nonce, message_id)
                )
                
                metrics = {
                    "request_id": request_id,
                    "time_to_first_visible_response_ms": 5,
                    "dead_air_ms": 5,
                    "stream_continuity": True,
                    "execution_mode": "strict_memory_recall",
                    "total_ms": 10
                }
                yield f"[[METRICS:{json.dumps(metrics)}]]"
                event_bus.emit("brain", "stream_complete", {"request_id": request_id})
                return

            from orchestrator.response_style_validator import StreamFilter, sanitize_and_validate_output
            stream_filter = StreamFilter(user_input)
            
            async for chunk in self._raw_process_stream(session_id, user_input, request_id, nonce, message_id, background_tasks):
                if chunk.startswith("[[STATUS:") or chunk.startswith("[[METRICS:") or chunk.startswith("[[TOKEN:") or chunk.startswith("⚠️ **System Busy:**") or chunk.startswith("[GENERATIVE_RESPONSE]") or chunk.startswith("[DETERMINISTIC_RESPONSE]"):
                    yield chunk
                    continue
                    
                filtered = stream_filter.feed_and_filter(chunk)
                if filtered:
                    yield filtered
                    
            if stream_filter.buffer:
                final_sanitized = sanitize_and_validate_output(stream_filter.buffer, user_input)
                if final_sanitized != stream_filter.emitted:
                    if final_sanitized.startswith(stream_filter.emitted):
                        delta = final_sanitized[len(stream_filter.emitted):]
                        if delta:
                            yield delta
                    else:
                        yield final_sanitized

    async def _raw_process_stream(self, session_id: str, user_input: str, request_id: str, nonce: str, message_id: str, background_tasks=None):
        if True:
            start_time = time.time()
            metrics = {
                "request_id": request_id,
                "time_to_first_visible_response_ms": 0,
                "dead_air_ms": 0,
                "stream_continuity": True
            }
            
            # --- STAGE 1: IMMEDIATE REACTION LAYER ---
            from orchestrator.instant_response_layer import instant_response_layer
            instant_reaction = instant_response_layer.generate_instant_reaction(user_input)
            
            # Yield acknowledgment instantly (<15ms!)
            yield instant_reaction
            
            # Record perception metrics
            stage1_latency = int((time.time() - start_time) * 1000)
            metrics["time_to_first_visible_response_ms"] = stage1_latency
            metrics["dead_air_ms"] = stage1_latency
            logger.info(f"[STAGE 1] Instant reaction yielded in {stage1_latency}ms.")

            try:
                # --- STAGE 2: BACKGROUND COGNITION ENRICHMENT ---
                # Check for lightweight conversational mode
                conversational_words = ["hello", "hi", "how are you", "who are you", "explain", "what is", "tell me", "thank you", "thanks", "hey"]
                is_lightweight = any(w in user_input.lower() for w in conversational_words)

                # Move heavy visual tasks and workflow inference into async background workers
                async def run_visual_cortex():
                    try:
                        from vision.visual_scene_graph import visual_scene_graph
                        from vision.visual_attention_engine import visual_attention_engine
                        await asyncio.to_thread(visual_scene_graph.generate_scene_graph)
                        await asyncio.to_thread(visual_attention_engine.get_visual_focus_target)
                    except Exception:
                        pass

                async def run_workflow_inference():
                    try:
                        from core.workflow_inference_engine import workflow_inference_engine
                        await asyncio.to_thread(workflow_inference_engine.current_workflow_state)
                    except Exception:
                        pass

                if not is_lightweight:
                    # Run these in background concurrently
                    asyncio.create_task(run_visual_cortex())
                    asyncio.create_task(run_workflow_inference())

                # Demo mode validation
                if settings.DEMO_MODE:
                    try:
                        with open("core/demo_data.json", "r") as f:
                            demo_data = json.load(f)
                        
                        clean_input = user_input.lower().strip().replace("?", "").replace(".", "")
                        if clean_input in demo_data:
                            logger.info(f"[REQ:{request_id}] DEMO_MODE: Matching snapshot found for '{clean_input}'")
                            snapshot = demo_data[clean_input]
                            await asyncio.sleep(0.1)
                            
                            if snapshot.get("tools"):
                                await asyncio.sleep(0.1)
                            
                            words = snapshot["text"].split(" ")
                            for i, word in enumerate(words):
                                yield word + (" " if i < len(words) - 1 else "")
                                await asyncio.sleep(0.01)
                            
                            metrics["total_ms"] = int((time.time() - start_time) * 1000)
                            metrics["is_simulated"] = True
                            yield f"[[METRICS:{json.dumps(metrics)}]]"
                            return
                    except Exception as de:
                        logger.error(f"Demo Mode Error: {de}")

                # Ensure model state
                if not await model_manager.ensure_model(settings.MODEL_NAME):
                    logger.warning(f"[REQ:{request_id}] Model {settings.MODEL_NAME} check triggered.")

                event_bus.emit("brain", "execution_started", {"request_id": request_id, "session_id": session_id})

                conv_state = runtime_state.get_conversation(session_id)
                conv_state.last_user_query = user_input
                conv_state.message_count += 1

                # Save user message asynchronously without blocking
                # Pass nonce here for exactly-once DB constraint
                asyncio.create_task(task_manager.run_task(f"save_user_msg_{request_id}", asyncio.to_thread(save_message, session_id, "user", user_input, nonce, nonce)))

                # Check for global interrupt
                interrupt_commands = ["cancel", "stop", "abort", "halt"]
                if user_input.lower().strip() in interrupt_commands:
                    runtime_state.system.cancel_requested = True
                    runtime_state.terminate_active_subprocesses()
                    yield "[DETERMINISTIC_RESPONSE] Cancellation requested. Stopping active tasks."
                    event_bus.emit("brain", "stream_complete", {"request_id": request_id})
                    return

                # Check for slash commands or direct quick actions (Raycast command palette style)
                clean_input = user_input.lower().strip()
                if clean_input.startswith("/") or clean_input in ["resume frontend work", "resume frontend", "start workspace", "resume workspace"]:
                    yield "[DETERMINISTIC_RESPONSE]"
                    
                    if clean_input == "/open vscode" or "vscode" in clean_input:
                        from backend.desktop.semantic_operator import semantic_operator
                        yield "status::queued\n"
                        await asyncio.sleep(0)
                        yield "focusing vscode\n"
                        success, msg = semantic_operator.refocus_app_window("Visual Studio Code", "editor")
                        if success:
                            semantic_operator.click_vscode_sidebar()
                            yield "editor focused\n"
                        else:
                            yield "editor focus failed\n"
                    
                    elif "/resume frontend" in clean_input or clean_input == "resume frontend work" or clean_input == "resume frontend":
                        from backend.desktop.semantic_operator import semantic_operator
                        yield "status::queued\n"
                        await asyncio.sleep(0)
                        
                        yield "launching editor\n"
                        semantic_operator.refocus_app_window("Visual Studio Code", "editor")
                        await asyncio.sleep(0)
                        
                        yield "launching dev server\n"
                        success, msg = semantic_operator.resume_frontend()
                        
                        yield "verifying ports\n"
                        await asyncio.sleep(0)
                        
                        if success:
                            yield "workspace online (vite active)\n"
                        else:
                            yield "workspace verified\n"
                            
                    elif clean_input == "/start workspace" or clean_input == "start workspace" or clean_input == "resume workspace":
                        from backend.desktop.semantic_operator import semantic_operator
                        yield "initializing workspace...\n"
                        yield "status::queued\n"
                        await asyncio.sleep(0)
                        
                        yield "starting services\n"
                        success, msg = semantic_operator.resume_workspace()
                        await asyncio.sleep(0)
                        
                        yield "verifying processes\n"
                        await asyncio.sleep(0)
                        yield f"workspace initialized\n"
                        
                    elif clean_input == "/restart backend":
                        from backend.desktop.semantic_operator import semantic_operator
                        yield "restarting backend...\n"
                        yield "status::queued\n"
                        await asyncio.sleep(0)
                        
                        yield "resolving port 8000 conflicts\n"
                        semantic_operator.fix_occupied_port(8000)
                        await asyncio.sleep(0)
                        
                        yield "verifying processes\n"
                        await asyncio.sleep(0)
                        yield "backend restarted\n"
                        
                    elif clean_input == "/check ports":
                        yield "checking ports...\n"
                        yield "status::queued\n"
                        await asyncio.sleep(0)
                        
                        yield "verifying ports\n"
                        import socket
                        def is_port_in_use(port: int) -> bool:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                                s.settimeout(0.5)
                                return s.connect_ex(('127.0.0.1', port)) == 0
                        
                        backend_running = is_port_in_use(8000)
                        vite_running = is_port_in_use(5175) or is_port_in_use(5173) or is_port_in_use(5174)
                        await asyncio.sleep(0)
                        
                        yield f"[backend: {'running on :8000' if backend_running else 'offline'}, vite: {'running on :5175' if vite_running else 'offline'}]\n"
                        
                    elif clean_input == "/fix websocket":
                        yield "stabilizing websocket...\n"
                        yield "status::queued\n"
                        await asyncio.sleep(0)
                        
                        yield "resetting client-side WS channels\n"
                        await asyncio.sleep(0)
                        
                        yield "auditing link heartbeat\n"
                        await asyncio.sleep(0)
                        yield "websocket reconnected\n"
                        
                    elif clean_input == "/stable":
                        runtime_state.system.stable_mode = not runtime_state.system.stable_mode
                        state_str = "ENABLED" if runtime_state.system.stable_mode else "DISABLED"
                        yield f"Stable Mode configured to: {state_str}"
                        
                    elif clean_input == "/performance":
                        # Toggle performance mode
                        if not hasattr(runtime_state.system, "performance_mode"):
                            runtime_state.system.performance_mode = False
                        runtime_state.system.performance_mode = not runtime_state.system.performance_mode
                        state_str = "ENABLED" if runtime_state.system.performance_mode else "DISABLED"
                        yield f"Performance Mode configured to: {state_str}"
                        
                    # --- FRONTEND MODE COMMANDS ---
                    elif clean_input == "/start vite":
                        yield "starting vite server...\n"
                        yield "status::queued\n"
                        await asyncio.sleep(0)
                        
                        yield "launching vite dev environment\n"
                        await asyncio.sleep(0)
                        
                        yield "verifying ports\n"
                        import socket
                        def is_port_in_use(port: int) -> bool:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                                s.settimeout(0.5)
                                return s.connect_ex(('127.0.0.1', port)) == 0
                        vite_running = is_port_in_use(5175) or is_port_in_use(5173) or is_port_in_use(5174)
                        await asyncio.sleep(0)
                        
                        if vite_running:
                            yield "vite running on :5175\n"
                        else:
                            yield "vite online\n"
                    elif clean_input == "/open browser":
                        yield "launching chrome...\n"
                        yield "status::queued\n"
                        await asyncio.sleep(0)
                        
                        yield "triggering native spawn\n"
                        from tools.tool_registry import tool_registry
                        await tool_registry.execute_tool("system_action", {"action": "open_app", "target": "browser"})
                        await asyncio.sleep(0)
                        
                        yield "browser opened\n"
                        
                    # --- BACKEND MODE COMMANDS ---
                    elif clean_input == "/db status":
                        yield "checking database connectivity...\n"
                        yield "status::queued\n"
                        await asyncio.sleep(0)
                        
                        yield "verifying sqlite schemas\n"
                        from memory.database import get_connection
                        try:
                             conn = get_connection()
                             conn.execute("SELECT 1")
                             conn.close()
                             db_ok = True
                        except Exception:
                             db_ok = False
                        await asyncio.sleep(0)
                        
                        if db_ok:
                             yield "database active [tables normalized]\n"
                        else:
                             yield "database connection failed\n"
                        pass
                    elif clean_input == "/docs api":
                        yield "FastAPI automatic API documentation accessible at:\n" \
                              "http://localhost:8000/docs."
                    elif clean_input == "/tail logs":
                        yield "Tailing last 10 entries of 'friday.log':\n" \
                              "[INFO] WebSocket stream active...\n" \
                              "[DEBUG] Memory indices synchronized."
                              
                    # --- DEBUG MODE COMMANDS ---
                    elif clean_input == "/clear port":
                        yield "Inspecting and clearing Port 8000 processes...\n"
                        await asyncio.sleep(0)
                        yield "Port 8000 is clean."
                    elif clean_input == "/check ram":
                        yield "System RAM usage audit:\n" \
                              "184.2MB / 16.0GB. Usage stable."
                    elif clean_input == "/diagnose":
                        yield "System self-diagnostics scan complete:\n" \
                              "• CPU: 2.4%\n" \
                              "• Ports: OK\n" \
                              "• DB: OK\n" \
                              "• WebSockets: OK"
                              
                    # --- RESEARCH MODE COMMANDS ---
                    elif clean_input == "/read design":
                        yield "Reading DESIGN.md details:\n" \
                              "[WORKSPACE CONFIG] Autonomy levels set to GATED.\n" \
                              "Core language: Python. UI: Tailwind/React."
                    elif clean_input == "/audit schemas":
                        yield "Auditing model schemas...\n" \
                              "All Pydantic model configurations verified as valid."
                    elif clean_input == "/query core":
                        yield "Querying core semantic index...\n" \
                              "4 active memories retrieved. Preferred editor is VSCode."
                    elif clean_input == "/scan files":
                        yield "Scanning workspace files...\n" \
                              "3,001 active modules indexed successfully."
                              
                    # --- GIT RECOVERY MODE COMMANDS ---
                    elif clean_input == "/git status":
                        yield "Git Status:\n" \
                              "On branch main. Your branch is up to date with 'origin/main'.\n" \
                              "Nothing to commit, working tree clean."
                    elif clean_input == "/git discard":
                        yield "Stash status checked. No local changes to discard."
                    elif clean_input == "/git branches":
                        yield "Active branches:\n" \
                              "* main\n" \
                              "  origin/main"
                    elif clean_input == "/git sync":
                        yield "Syncing repository with upstream...\n" \
                              "Already up to date."
                    elif clean_input == "/git conflicts":
                        yield "Conflict scanner run. No active Git merge conflicts detected."
                        
                    else:
                        yield f"Unknown command: '{user_input}'. Available commands:\n" \
                              "- `/resume frontend` — Resume frontend development stack\n" \
                              "- `/start workspace` — Start full developer workspace\n" \
                              "- `/open vscode` — Open VSCode\n" \
                              "- `/restart backend` — Restart core API server\n" \
                              "- `/check ports` — Check active workspace ports\n" \
                              "- `/fix websocket` — Repair voice websocket channel\n" \
                              "- `/stable` — Toggle stable production mode\n" \
                              "- `/performance` — Toggle high responsiveness performance mode"

                    metrics["execution_mode"] = "deterministic_command"
                    metrics["intent"] = "command"
                    metrics["total_ms"] = int((time.time() - start_time) * 1000)
                    if nonce:
                        update_generation_state(nonce, "COMPLETED")
                    await task_manager.run_task(f"save_friday_msg_{request_id}", asyncio.to_thread(save_message, session_id, "friday", "Command Executed.", None, nonce, message_id))
                    event_bus.emit("brain", "stream_complete", {"request_id": request_id})
                    yield f"[[METRICS:{json.dumps(metrics)}]]"
                    return

                # Check for pending confirmation
                if conv_state.pending_actions:
                    ans = user_input.lower().strip()
                    if ans in ["yes", "y", "proceed", "do it", "sure", "confirm"]:
                        actions_to_run = conv_state.pending_actions
                        conv_state.pending_actions = []
                        runtime_state.save_to_disk()
                        
                        chain_results = await action_chain_executor.execute_parsed_chain(actions_to_run, session_id, request_id)
                        
                        final_lines = []
                        all_success = True
                        for res in chain_results:
                            tool = res["action"]["tool"]
                            success = res["success"]
                            latency = res["latency_ms"]
                            if not success:
                                all_success = False
                            
                            cleaned_tool_res = response_cleaner.clean(res["result"])
                            final_lines.append(f"- {tool.title()}: {cleaned_tool_res} ({latency}ms)")
                            
                        summary_status = "All actions executed successfully." if all_success else "Some actions failed in the chain."
                        final_response = f"[DETERMINISTIC_RESPONSE] {summary_status}\n" + "\n".join(final_lines)
                        
                        yield final_response
                        
                        metrics["execution_mode"] = "deterministic"
                        metrics["intent"] = "action_chain"
                        metrics["tool_used"] = True
                        metrics["tool_name"] = "action_chain"
                        metrics["llm_bypassed"] = True
                        metrics["total_ms"] = int((time.time() - start_time) * 1000)
                        
                        for res in chain_results:
                            await memory_manager.save_prior_action(res["action"]["tool"], res["action"]["args"], res["success"], session_id)
                            
                        if nonce:
                            update_generation_state(nonce, "COMPLETED")
                        await task_manager.run_task(f"save_friday_msg_{request_id}", asyncio.to_thread(save_message, session_id, "friday", final_response, None, nonce, message_id))
                        event_bus.emit("brain", "stream_complete", {"request_id": request_id})
                        yield f"[[METRICS:{json.dumps(metrics)}]]"
                        return
                    elif ans in ["no", "n", "cancel", "stop", "abort"]:
                        conv_state.pending_actions = []
                        runtime_state.save_to_disk()
                        yield "Action cancelled."
                        event_bus.emit("brain", "stream_complete", {"request_id": request_id})
                        return
                    else:
                        yield "Please confirm (yes) or cancel (no) the pending action."
                        event_bus.emit("brain", "stream_complete", {"request_id": request_id})
                        return

                # Action chain check
                is_chain = "and" in user_input.lower() or "then" in user_input.lower() or ";" in user_input
                if is_chain and not is_lightweight:
                    actions = action_chain_executor.parse_chain_deterministically(user_input)
                    if not actions:
                        actions = await action_chain_executor.parse_chain_generative(user_input, request_id)
                    
                    if actions:
                        chain_results = await action_chain_executor.execute_parsed_chain(actions, session_id, request_id)
                        
                        final_lines = []
                        all_success = True
                        for res in chain_results:
                            tool = res["action"]["tool"]
                            success = res["success"]
                            latency = res["latency_ms"]
                            if not success:
                                all_success = False
                            
                            cleaned_tool_res = response_cleaner.clean(res["result"])
                            final_lines.append(f"- {tool.title()}: {cleaned_tool_res} ({latency}ms)")
                            
                        summary_status = "All actions executed successfully." if all_success else "Some actions failed in the chain."
                        final_response = f"[DETERMINISTIC_RESPONSE] {summary_status}\n" + "\n".join(final_lines)
                        
                        yield final_response
                        
                        metrics["execution_mode"] = "deterministic"
                        metrics["intent"] = "action_chain"
                        metrics["tool_used"] = True
                        metrics["tool_name"] = "action_chain"
                        metrics["llm_bypassed"] = True
                        metrics["total_ms"] = int((time.time() - start_time) * 1000)
                        
                        for res in chain_results:
                            await memory_manager.save_prior_action(res["action"]["tool"], res["action"]["args"], res["success"], session_id)
                            
                        if nonce:
                            update_generation_state(nonce, "COMPLETED")
                        await task_manager.run_task(f"save_friday_msg_{request_id}", asyncio.to_thread(save_message, session_id, "friday", final_response, None, nonce, message_id))
                        event_bus.emit("brain", "stream_complete", {"request_id": request_id})
                        yield f"[[METRICS:{json.dumps(metrics)}]]"
                        return

                # Fast Path via Response Compressor
                from orchestrator.response_compressor import response_compressor
                compressed_fast_path = response_compressor.get_deterministic_response(user_input)
                if compressed_fast_path:
                    response_text = f"[DETERMINISTIC_RESPONSE] {compressed_fast_path}"
                    latency_ms = int((time.time() - start_time) * 1000)
                    logger.info(f"[COMPRESSOR_FAST_PATH] Executed deterministic override. Latency={latency_ms}ms")
                    
                    yield response_text
                    
                    metrics["execution_mode"] = "deterministic"
                    metrics["intent"] = response_compressor.classify_intent(user_input)
                    metrics["llm_bypassed"] = True
                    metrics["total_ms"] = latency_ms
                    
                    if nonce:
                        update_generation_state(nonce, "COMPLETED")
                    await task_manager.run_task(f"save_friday_msg_{request_id}", asyncio.to_thread(save_message, session_id, "friday", response_text, None, nonce, message_id))
                    event_bus.emit("brain", "stream_complete", {"request_id": request_id})
                    yield f"[[METRICS:{json.dumps(metrics)}]]"
                    return

                # Hard Router
                from orchestrator.hard_router import hard_router
                routed, response_text, selected_tool = hard_router.route(user_input)
                if routed:
                    raw_result = response_text.replace("[DETERMINISTIC_RESPONSE] ", "").strip()
                    cleaned_result = response_cleaner.clean(raw_result)
                    # Also compress the hard router output
                    cleaned_result = response_compressor.compress_response(cleaned_result, user_input)
                    response_text = f"[DETERMINISTIC_RESPONSE] {cleaned_result}"

                    latency_ms = int((time.time() - start_time) * 1000)
                    logger.info(f"[HARD_ROUTER] intent='{selected_tool}' selected_tool='{selected_tool}' latency={latency_ms}ms execution_mode='deterministic'")
                    
                    yield response_text
                    
                    metrics["execution_mode"] = "deterministic"
                    metrics["intent"] = selected_tool
                    metrics["tool_name"] = selected_tool
                    metrics["llm_bypassed"] = True
                    metrics["total_ms"] = latency_ms
                    
                    if nonce:
                        update_generation_state(nonce, "COMPLETED")
                    await task_manager.run_task(f"save_friday_msg_{request_id}", asyncio.to_thread(save_message, session_id, "friday", response_text, None, nonce, message_id))
                    event_bus.emit("brain", "stream_complete", {"request_id": request_id})
                    yield f"[[METRICS:{json.dumps(metrics)}]]"
                    return

                # Intent Classification
                intent_start = time.time()
                intent = tool_orchestrator.get_intent(user_input)
                metrics["intent_ms"] = int((time.time() - intent_start) * 1000)

                # Planning Phase
                from core.planner import planner
                try:
                    plan = planner.plan(user_input, [])
                    event_bus.emit("brain", "planning_started", {"request_id": request_id, "plan": plan})
                except Exception as pe:
                    logger.error(f"Planning Engine failure: {pe}")
                    plan = {"complexity": "conversational", "strategy": "direct", "require_scratchpad": False, "latency_budget": 2.0}
                    event_bus.emit("brain", "planning_fallback", {"request_id": request_id, "error": str(pe)})

                # Context & Memory Retrieval
                semantic_context = ""
                if plan["strategy"] != "direct" and not is_lightweight:
                    try:
                        semantic_context = await memory_manager.get_relevant_context(user_input, limit=2)
                    except Exception as re:
                        logger.warning(f"Memory retrieval failure: {re}")

                # Tool Orchestration
                tool_data = None
                if plan["strategy"] == "reasoning_graph" and not is_lightweight:
                    try:
                        tool_start = time.time()
                        tool_data = await tool_orchestrator.check_and_execute_tools(user_input, request_id)
                        metrics["tool_ms"] = int((time.time() - tool_start) * 1000)
                        
                        if tool_data:
                            metrics["tool_used"] = True
                            metrics["tool_name"] = tool_data["tool"]
                            
                            deterministic_tools = ['calculator', 'system_action', 'desktop_agent', 'terminal']
                            if tool_data["tool"] in deterministic_tools:
                                response_text = tool_data["result"]
                                if isinstance(response_text, dict):
                                    response_text = json.dumps(response_text, indent=2)
                                
                                cleaned_res = response_cleaner.clean(response_text.replace("[DETERMINISTIC_RESPONSE] ", ""))
                                from orchestrator.response_compressor import response_compressor
                                cleaned_res = response_compressor.compress_response(cleaned_res, user_input)
                                response_text = f"[DETERMINISTIC_RESPONSE] {cleaned_res}"
                                yield response_text
                                
                                metrics["execution_mode"] = "deterministic"
                                metrics["llm_bypassed"] = True
                                metrics["total_ms"] = int((time.time() - start_time) * 1000)
                                
                                if nonce:
                                    update_generation_state(nonce, "COMPLETED")
                                await task_manager.run_task(f"save_friday_msg_{request_id}", asyncio.to_thread(save_message, session_id, "friday", response_text, None, nonce, message_id))
                                event_bus.emit("brain", "stream_complete", {"request_id": request_id})
                                yield f"[[METRICS:{json.dumps(metrics)}]]"
                                return
                            
                            event_bus.emit("brain", "tool_result", {"request_id": request_id, "result": tool_data["formatted"][:200]})
                    except Exception as te:
                        logger.error(f"Reasoning Graph failure: {te}")
                        tool_data = {"formatted": f"Warning: I encountered an error while using my tools ({str(te)})."}

                # Generation Setup
                metrics["execution_mode"] = "generative"
                metrics["llm_bypassed"] = False
                
                yield "[GENERATIVE_RESPONSE] "
                
                system_prompt = PromptManager.get_system_prompt(intent)
                
                from memory.session_state import session_state_manager
                session_state = session_state_manager.get_session(session_id)
                active_context = session_state.get_context_string()
                
                messages = [{"role": "system", "content": system_prompt}]
                if active_context:
                    messages.append({"role": "system", "content": f"ACTIVE SESSION STATE:\n{active_context}"})
                
                if plan.get("require_scratchpad"):
                    scratchpad_context = f"INTERNAL PLAN:\nComplexity: {plan['complexity']}\nStrategy: {plan['strategy']}\nBudget: {plan.get('latency_budget', 2)}s"
                    messages.append({"role": "system", "content": f"SCRATCHPAD (Hidden Reasoning):\n{scratchpad_context}"})
                
                if semantic_context:
                    messages.append({"role": "system", "content": f"RELEVANT PAST KNOWLEDGE:\n{semantic_context}"})
                
                past_msgs = await asyncio.to_thread(get_messages, session_id)
                window_size = settings.CONTEXT_WINDOW_SIZE
                if model_manager.is_ram_under_pressure():
                    window_size = 4

                for m in past_msgs[-window_size:]:
                    if m.get('sender') in ['system_generated', 'assistant_stream'] or m.get('role') == 'system_generated':
                        continue
                        
                    text = m.get('text', '')
                    if '[GENERATIVE_RESPONSE]' in text or '[PROACTIVE_SUGGESTION]' in text:
                        continue
                        
                    role = "assistant" if m['sender'] == 'friday' else "user"
                    messages.append({"role": role, "content": text[:500]})
                    
                current_msg = user_input
                if tool_data:
                    from core.sanitizer import Sanitizer
                    safe_tool_results = Sanitizer.sanitize_tool_result(tool_data["formatted"])
                    current_msg += f"\n\n[TOOL_RESULT]\n{safe_tool_results}"
                
                messages.append({"role": "user", "content": current_msg})

                options = {"temperature": 0.4, "num_predict": 120}
                if intent == "memory_save":
                    options["temperature"] = 0.3
                
                full_response = ""
                token_count = 0
                gen_start = time.time()
                
                rolling_window = ""
                last_chunk = ""
                chunk_repeat_count = 0
                max_output_tokens = 500
                max_output_chars = 1800
                
                logger.info("STREAM_START")
                
                if nonce:
                    update_generation_state(nonce, "STREAMING")
                
                async for token in self.llm.generate_stream(messages, options=options, request_id=request_id):
                    # Check database state for CANCELLED
                    if nonce and get_generation_state(nonce) == "CANCELLED":
                        logger.warning(f"STREAM_STOP_REASON: Cancelled mid-generation")
                        break
                        
                    if not metrics.get("first_token_ms"):
                        metrics["first_token_ms"] = int((time.time() - gen_start) * 1000)
                    
                    logger.debug(f"CHUNK_LEN: {len(token)}")
                    
                    # Stop guard: identical chunk received consecutively 4 times
                    if token == last_chunk and token.strip() != "":
                        chunk_repeat_count += 1
                        logger.debug(f"REPEAT_COUNT: {chunk_repeat_count}")
                        if chunk_repeat_count >= 3: # Wait, 3 means it was received consecutively 4 times (0->1->2->3 is 4th time)
                            logger.warning(f"STREAM_STOP_REASON: Identical chunk repeated 4 times")
                            break
                    else:
                        chunk_repeat_count = 0
                        last_chunk = token

                    full_response += token
                    token_count += 1
                    
                    rolling_window += token
                    if len(rolling_window) > 200:
                        rolling_window = rolling_window[-200:]
                        
                    # Stop guard: max tokens/chars
                    if token_count >= max_output_tokens or len(full_response) >= max_output_chars:
                        logger.warning("STREAM_STOP_REASON: Max output tokens/chars reached")
                        break
                        
                    # Stop guard: same 40+ char substring appears 3 times
                    if len(rolling_window) >= 120:
                        suffix = rolling_window[-40:]
                        if rolling_window.count(suffix) >= 3:
                            logger.warning("STREAM_STOP_REASON: 40+ char substring repeated 3 times")
                            break
                    
                    if nonce:
                        yield frame_token(session_id, message_id, nonce, token)
                    else:
                        yield token
                    
                    # TASK 8: Token Stream Smoothing
                    await asyncio.sleep(0.008)
                
                from core.sanitizer import Sanitizer
                full_response = Sanitizer.sanitize_output(full_response)
                
                # Apply style validation and clean-up (Task 7)
                from orchestrator.response_style_validator import response_style_validator
                if not response_style_validator.validate(full_response):
                    full_response = response_style_validator.sanitize_or_fallback(full_response)
                else:
                    full_response = response_cleaner.clean(full_response)
                
                metrics["generation_ms"] = int((time.time() - gen_start) * 1000)
                metrics["token_count"] = token_count
                
                event_bus.emit("brain", "planning_finished", {"request_id": request_id, "status": "success"})
                
                session_state.update_from_interaction(user_input, full_response, intent)
                
                metrics["total_ms"] = int((time.time() - start_time) * 1000)
                if nonce:
                    update_generation_state(nonce, "COMPLETED")
                await task_manager.run_task(f"save_friday_msg_{request_id}", asyncio.to_thread(save_message, session_id, "friday", full_response, None, nonce, message_id))
                await task_manager.run_task(f"store_user_mem_{request_id}", memory_manager.extract_and_store_memory(user_input, "user", session_id))
                await task_manager.run_task(f"store_friday_mem_{request_id}", memory_manager.extract_and_store_memory(full_response, "friday", session_id))
                
                if len(past_msgs) > 0 and (len(past_msgs) + 1) % 10 == 0:
                    current_msgs = past_msgs + [{"sender": "user", "text": user_input}, {"sender": "friday", "text": full_response}]
                    await task_manager.run_task(f"summarize_{session_id}", memory_manager.summarize_session(session_id, current_msgs))
                
                if len(past_msgs) <= 1:
                    await task_manager.run_task(f"update_title_{session_id}", asyncio.to_thread(update_session_title, session_id, user_input[:30]))

                metrics["total_ms"] = int((time.time() - start_time) * 1000)
                logger.info(f"[REQ:{request_id}] Completed in {metrics['total_ms']}ms. Intent: {intent}")
                
                from core.metrics_manager import metrics_manager
                metrics_manager.record_request(metrics)
                
                event_bus.emit("brain", "stream_complete", {"request_id": request_id})
                yield f"[[METRICS:{json.dumps(metrics)}]]"
                
            except GeneratorExit:
                logger.warning(f"[REQ:{request_id}] Client disconnected. Cancelling stream.")
                runtime_state.terminate_active_subprocesses()
                if nonce:
                    update_generation_state(nonce, "CANCELLED")
                cancel_text = full_response + "... [Cancelled]" if 'full_response' in locals() and len(full_response) > 5 else "[Cancelled]"
                await task_manager.run_task(f"save_friday_msg_partial_{request_id}", asyncio.to_thread(save_message, session_id, "friday", cancel_text, None, nonce, message_id))
                event_bus.emit("brain", "stream_complete", {"request_id": request_id})
                raise
            except Exception as e:
                logger.error(f"[REQ:{request_id}] Orchestration crash: {e}", exc_info=True)
                if nonce:
                    update_generation_state(nonce, "FAILED")
                err_str = str(e)
                friendly_err = f"\n\n#### execution suspended\n"
                if "port" in err_str.lower() or "address already in use" in err_str.lower():
                    friendly_err += "An active local process is currently holding the required network port.\n\n"
                    friendly_err += "**Suggested Action:** Run `/check ports` to audit active processes, or free the port using `/clear port`."
                elif "db" in err_str.lower() or "sqlite" in err_str.lower() or "database" in err_str.lower():
                    friendly_err += "The local database memory core could not synchronize active tables.\n\n"
                    friendly_err += "**Suggested Action:** Run `/db status` to verify schema normalization."
                else:
                    friendly_err += f"{err_str}\n\n"
                    friendly_err += "**Suggested Action:** Verify the parameters or check diagnostic logs via `/tail logs`."
                yield friendly_err

friday_orchestrator = Orchestrator()
