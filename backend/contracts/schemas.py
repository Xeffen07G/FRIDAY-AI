from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import time

class RuntimeAction(BaseModel):
    id: str
    action_type: str
    args: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)

class RuntimeEvent(BaseModel):
    id: str
    timestamp: float = Field(default_factory=time.time)
    component: str
    type: str
    data: Any = None
    level: str = "INFO"
    priority: int = 10

class ContextSnapshot(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    active_window: str
    workspace_path: str
    git_branch: str
    browser_url: str
    clipboard_hash: str

class PlannerDecision(BaseModel):
    complexity: str
    strategy: str
    require_scratchpad: bool = False
    latency_budget: float = 2.0
    selected_tools: List[str] = Field(default_factory=list)

class ToolExecution(BaseModel):
    tool_name: str
    args: Dict[str, Any] = Field(default_factory=dict)
    called_at: float = Field(default_factory=time.time)
    session_id: str
    request_id: str

class MemoryReference(BaseModel):
    reference_id: str
    query: str
    score: float
    timestamp: float = Field(default_factory=time.time)
    context: str
