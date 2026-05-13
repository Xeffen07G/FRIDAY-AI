# F.R.I.D.A.Y. Troubleshooting Guide

## Common Issues

### 1. WebSocket Disconnected (Red indicator)
- **Cause**: Backend service is down or port 8001 is blocked.
- **Fix**: Check terminal running `uvicorn main:app`. Ensure firewall allows local WebSocket connections.

### 2. No Voice Response
- **Cause**: Ollama service is not running or model `phi3:mini` is not pulled.
- **Fix**: Run `ollama list` to verify. If missing, run `ollama pull phi3:mini`.

### 3. High Latency (>3s)
- **Cause**: System resource contention or large context window.
- **Fix**: 
    - Check CPU/RAM in Diagnostics Panel.
    - Reduce `CONTEXT_WINDOW_SIZE` in `.env`.
    - Ensure `num_thread` in `ollama_client.py` matches your CPU cores.

### 4. Audio "Barge-in" too sensitive
- **Cause**: `VAD_THRESHOLD` too low or high ambient noise.
- **Fix**: Increase `VAD_THRESHOLD` in `.env` (e.g., from 0.5 to 0.7).

### 5. Memory Retrieval Failure
- **Cause**: ChromaDB initialization error.
- **Fix**: Delete the `CHROMA_PATH` directory (defined in `.env`) and restart.

## Diagnostics Dashboard
Open the **Pulse** icon in the top right to view real-time system health, active background tasks, and loaded models.
