# F.R.I.D.A.Y. API Documentation

## Base URL: `http://127.0.0.1:8000`

### Chat Endpoints
- **POST `/api/chat`**
  - Payload: `{ "session_id": "string", "message": "string" }`
  - Response: `TextStream` (SSE-style) with `[[STATUS]]` and `[[METRICS]]` tokens.

### Session Management
- **GET `/api/sessions`**: List all sessions.
- **POST `/api/sessions`**: Create a new session.
- **GET `/api/sessions/{id}/messages`**: Retrieve history for a session.
- **DELETE `/api/sessions/{id}`**: Delete a session.

### Health & Diagnostics
- **GET `/api/health/deep`**: Returns status of LLM, SQLite, ChromaDB, and Tool Registry.
- **GET `/api/memories`**: List semantic memories stored in Vector DB.
- **DELETE `/api/memories/{id}`**: Delete a specific semantic memory.
