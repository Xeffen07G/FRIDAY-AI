# F.R.I.D.A.Y. Runtime Flow

## 1. Conversational Pipeline (Voice-to-Voice)

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend (Vite)
    participant B as Backend (FastAPI)
    participant C as Cognition (Orchestrator)
    participant M as Memory (ChromaDB)
    participant L as LLM (Ollama)

    U->>F: Speech
    F->>F: VAD (Voice Activity Detection)
    F->>B: WebSocket (audio_chunk)
    B->>B: Whisper STT (Streaming)
    B->>F: transcript_partial
    U->>F: Silence Detected
    F->>B: WebSocket (audio_final)
    B->>C: Process Input
    C->>M: Semantic Retrieval
    C->>L: Intent & Planning
    L->>C: Action/Tool Graph
    C->>B: Execute Tools
    C->>L: Generate Final Response
    L->>B: Text Stream
    B->>F: WebSocket (token)
    B->>B: Piper TTS (Synthesis)
    B->>F: WebSocket (audio_base64)
    F->>U: Audio Playback
```

## 2. Event Lifecycle
1. **`websocket_connected`**: Handshake and session initialization.
2. **`brain.thought`**: LLM starts reasoning.
3. **`brain.tool_start`**: External tool execution.
4. **`brain.tool_result`**: Data returned from tools.
5. **`websocket_disconnected`**: Cleanup and session persistence.

## 3. Resilience Mechanisms
- **Graceful Degradation**: If the reasoning graph fails, the system falls back to direct chat.
- **Auto-Reconnection**: The frontend attempts up to 5 retries if the WebSocket drops.
- **Heartbeat**: Pings every 30s to keep the connection alive.
