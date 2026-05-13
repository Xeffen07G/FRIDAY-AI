# F.R.I.D.A.Y. Safety & Privacy Model

## Principles of Operation
F.R.I.D.A.Y. is built on the principle of **Informed Consent** and **Data Sovereignty**. The Desktop Agent is designed to assist, not surveil.

## Security Controls

### 1. Zero-Continuous Surveillance
- **No Idle Captures**: The system does NOT capture screenshots, audio, or window titles in a continuous loop for the purpose of training or surveillance.
- **On-Demand Context**: Desktop context (active window, clipboard) is only retrieved when a tool requires it to satisfy a specific user request.

### 2. Explicit Permission Gating
- **Tool Confirmation**: All OS-level actions (opening apps, deleting files, capturing screen) require explicit user confirmation via the UI.
- **Audit Logs**: Every sensitive action is recorded in a local, tamper-evident audit trail accessible via the Engineering Hub.

### 3. Execution Sandboxing
- **Allowlisted Applications**: The agent can only launch applications defined in the `SAFE_APPS` allowlist.
- **Path Sanitization**: All file operations undergo strict path validation to prevent directory traversal attacks (`../`).
- **Standard User Privileges**: The agent runs with the privileges of the logged-in user and never requests administrative/root escalation.

### 4. Data Sovereignty
- **100% Local Inference**: All reasoning, planning, and vision analysis are performed on local hardware via Ollama and local CV libraries.
- **Local Memory**: Embeddings and metadata are stored in local SQLite and ChromaDB instances. No data is transmitted to external cloud providers.

## Privacy Guardrails
- **Clipboard Sanitization**: While the agent can see the clipboard, it is instructed to never persist sensitive patterns (passwords, credit card numbers) into long-term semantic memory.
- **Opt-in Indexing**: Users must explicitly specify folders for the `FileManager` to watch and index. System directories are excluded by default.
