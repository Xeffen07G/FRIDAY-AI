from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

class ConversationState(BaseModel):
    session_id: str
    message_count: int = 0
    last_user_query: Optional[str] = None
    last_agent_response: Optional[str] = None
    active_intent: Optional[str] = None
    pending_actions: List[Dict[str, Any]] = Field(default_factory=list)

class SystemState(BaseModel):
    cpu_usage_pct: float = 0.0
    ram_usage_mb: float = 0.0
    latency_ms: int = 0
    active_connections: int = 0
    startup_time: str = Field(default_factory=lambda: datetime.now().isoformat())
    cancel_requested: bool = False
    stable_mode: bool = True

class ToolState(BaseModel):
    last_tool_executed: Optional[str] = None
    executed_tools_count: Dict[str, int] = {}
    last_tool_success: bool = True
    active_subprocesses: List[int] = [] # Track PIDs of active processes like servers/browsers

class MemoryState(BaseModel):
    cached_memories: List[Dict[str, Any]] = []
    short_term_context: Dict[str, Any] = {}
    last_memory_retrieval_ms: int = 0

class SessionState(BaseModel):
    session_id: str
    context_data: Dict[str, Any] = {}
    preferences: Dict[str, Any] = {}
    history_tokens_estimate: int = 0

class CentralRuntimeState:
    """
    Centralized Runtime State Management for persistent cognition.
    All orchestrators, planners, and tools must read/write through this layer.
    """
    def __init__(self):
        self._lock = asyncio.Lock()
        self.conversations: Dict[str, ConversationState] = {}
        self.system = SystemState()
        self.tools = ToolState()
        self.memory = MemoryState()
        self.sessions: Dict[str, SessionState] = {}
        self.load_from_disk()

    def get_conversation(self, session_id: str) -> ConversationState:
        if session_id not in self.conversations:
            self.conversations[session_id] = ConversationState(session_id=session_id)
        return self.conversations[session_id]

    def get_session(self, session_id: str) -> SessionState:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionState(session_id=session_id)
        return self.sessions[session_id]

    def update_system_telemetry(self, cpu: float, ram: float, latency: int, active_conns: int):
        self.system.cpu_usage_pct = cpu
        self.system.ram_usage_mb = ram
        self.system.latency_ms = latency
        self.system.active_connections = active_conns

    def save_to_disk(self):
        import json, os
        path = "workspace/runtime_state.json"
        os.makedirs("workspace", exist_ok=True)
        data = {
            "conversations": {k: v.model_dump() for k, v in self.conversations.items()}
        }
        with open(path, "w") as f:
            json.dump(data, f)
            
    def load_from_disk(self):
        import json, os
        path = "workspace/runtime_state.json"
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    for k, v in data.get("conversations", {}).items():
                        self.conversations[k] = ConversationState(**v)
            except Exception as e:
                print(f"Failed to load runtime state: {e}")

    def terminate_active_subprocesses(self):
        import psutil
        pids = list(self.tools.active_subprocesses)
        self.tools.active_subprocesses.clear()
        
        for pid in pids:
            try:
                proc = psutil.Process(pid)
                # Terminate recursively to prevent orphan processes
                for child in proc.children(recursive=True):
                    try:
                        child.kill()
                    except Exception:
                        pass
                try:
                    proc.kill()
                except Exception:
                    pass
                print(f"Successfully killed active subprocess PID: {pid}")
            except Exception as e:
                print(f"Failed to terminate PID {pid}: {e}")

# Singleton Instance
runtime_state = CentralRuntimeState()
