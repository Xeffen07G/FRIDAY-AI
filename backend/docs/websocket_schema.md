# F.R.I.D.A.Y. WebSocket Event Schema

## 1. Client to Server (C2S)

| Event Type | Payload | Description |
| --- | --- | --- |
| `audio_chunk` | `{ "data": "base64", "session_id": "uuid" }` | Binary audio fragment for streaming STT |
| `audio_final` | `{ "data": "base64", "session_id": "uuid" }` | Final audio blob to trigger orchestration |
| `audio_cancel` | `{}` | Discards the current audio buffer |
| `interrupt` | `{}` | Stops current LLM generation and TTS playback |
| `pong` | `{ "ts": 123456789 }` | Heartbeat response |

## 2. Server to Client (S2C)

| Event Type | Payload | Description |
| --- | --- | --- |
| `status` | `"idle" | "listening" | "thinking" | "speaking"` | UI state indicator |
| `transcript_partial` | `"Hello world..."` | Real-time STT feedback |
| `transcript` | `"Hello world."` | Final STT result |
| `token` | `"I"` | LLM streaming token |
| `audio` | `"base64_wav"` | Synthesized speech chunk |
| `metrics` | `{ "stt_ms": 100, ... }` | Performance telemetry |
| `ping` | `{ "ts": 123456789 }` | Connection keep-alive |
| `error` | `"Message"` | System error alert |
