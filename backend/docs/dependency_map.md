# F.R.I.D.A.Y. Dependency Map

## Core Backend Dependencies
| Module | Technology | Purpose |
| --- | --- | --- |
| **Ingress** | FastAPI / Uvicorn | High-performance async web framework |
| **Logic** | Pydantic v2 | Type safety and configuration validation |
| **LLM Interface** | Ollama (Local) | Local LLM inference (Default: phi3:mini) |
| **Vector Search** | ChromaDB / SentenceTransformers | Long-term semantic memory |
| **Speech-to-Text** | Faster-Whisper | Low-latency audio transcription |
| **Text-to-Speech** | Piper TTS | Ultra-fast local synthesis |
| **Monitoring** | psutil | System resource tracking |
| **Event Bus** | Custom Async PubSub | Internal decoupled communication |

## External Service Requirements (Optional/Grounded)
- **OpenWeatherMap API**: For real-time weather retrieval
- **Tavily / Google Search**: For web-grounded information retrieval

## Frontend Dependencies
- **React / Vite**: UI Framework
- **TailwindCSS**: Visual styling
- **Lucide React**: Icon system
- **Web Audio API**: Voice capture and playback
