# F.R.I.D.A.Y. Architecture

## Overview
F.R.I.D.A.Y. is a local-first AI assistant optimized for single-user desktop environments. It utilizes Ollama for local LLM inference, ChromaDB for semantic memory, and SQLite for session persistence.

## System Components

### 1. Frontend (React + Vite)
- **State Management**: Custom `useChat` hook for streaming and session logic.
- **UI**: Tailwind CSS based "Boutique Engineering" aesthetic.
- **Streaming**: Real-time token rendering via EventSource-style streams.

### 2. Backend (FastAPI)
- **Routes**: Cleanly separated API endpoints for sessions, chat, and health.
- **Orchestrator**: The central brain that handles intent classification, memory retrieval, tool execution, and LLM prompting.
- **Memory System**: Dual-layer storage (SQLite for history, ChromaDB for semantic RAG).
- **Tool Registry**: Secure execution environment for local system tools.

## Request Lifecycle
1. **User Input** received via `/api/chat`.
2. **Intent Classification**: Quick regex check to bypass heavy processing for greetings.
3. **Memory Retrieval**:
   - Recent history from SQLite.
   - Semantic context from ChromaDB.
4. **Tool Selection**: Optional LLM routing to local tools (capped at 2s).
5. **Prompt Assembly**: Merging system rules, context, and user input.
6. **LLM Inference**: Streaming response from Ollama (`phi3:mini`).
7. **Post-Processing**: Background tasks for memory extraction and persistence.
