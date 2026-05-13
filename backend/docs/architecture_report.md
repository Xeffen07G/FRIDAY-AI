# F.R.I.D.A.Y. Architecture Report - v1 Normalization

## Executive Summary
F.R.I.D.A.Y. has evolved through rapid cognitive prototyping. This report outlines the structural normalization required to transition from an experimental codebase into a production-ready platform.

## 1. Structural Audit Findings

### 1.1 Duplicate Logic & Dead Code
- **Redundant Orchestrators**: Both `core/orchestrator.py` and `orchestrator/orchestrator.py` exist. The latter is the active cognitive version.
- **Outdated LLM Client**: `core/llm.py` is a synchronous stub; `llm/ollama_client.py` is the active async transport.
- **Nested Backend**: A `backend/backend/` directory exists with redundant subfolders (`memory`, `tools`, etc.).
- **Overlapping Tools**: `tools/system_tools.py` and `tools/system_tool.py` have overlapping logic for application launching.

### 1.2 Orchestration Paths
- **Current Flow**: `STT -> Intent -> Plan -> Retrieval -> Tool Graph -> LLM -> TTS`.
- **Optimization**: The `Intent` classification and `Plan` phase can be unified further to reduce latency.

### 1.3 Telemetry
- **Fragmented Emissions**: Events are emitted from `ws_voice.py`, `orchestrator.py`, and `tool_registry.py` with inconsistent naming (e.g., `brain` vs `thought`).
- **Standardization**: All cognitive events will now follow the `cognition.*` namespace.

---

## 2. Proposed Normalization Plan

### Phase 1: Codebase Consolidation
- [ ] Delete `backend/backend/` recursive directory.
- [ ] Delete `core/llm.py` and `core/orchestrator.py`.
- [ ] Merge `system_tools.py` and `system_tool.py` into a single `SystemActionTool`.

### Phase 2: Configuration Centralization
- [ ] Migrate all hardcoded timeouts and thresholds to `config/settings.py`.
- [ ] Create `.env.example`.

### Phase 3: Runtime Flow (Standardized)
1. **Ingress**: WebSocket / API
2. **Cognition**: `Planner` -> `ReasoningGraph`
3. **Action**: `ToolScheduler` (Prioritized)
4. **Synthesis**: `LLMClient` -> `Sanitizer`
5. **Egress**: TTS / EventBus

---

## 3. Dependency Map (Core)
- **FastAPI**: Ingress/Routing
- **Ollama**: LLM Inference
- **Piper**: TTS Synthesis
- **Faster-Whisper**: STT Processing
- **ChromaDB**: Vector Memory
- **SQLite**: Structured History
