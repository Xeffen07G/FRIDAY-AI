# F.R.I.D.A.Y. Agent Runtime Flow

## Runtime Lifecycle

### 1. Initialization (Boot Sequence)
1. **Core Validation**: `SystemValidator` checks GPU/RAM availability and service dependencies.
2. **Database Connect**: SQLite and ChromaDB connections are established.
3. **Background Agent Start**: The `BackgroundAgent` initializes its task queue and heartbeat.
4. **FileSystem Observer**: `FileManager` starts the `watchdog` threads for registered folders.
5. **UI Sync**: WebSocket establishes connection and pushes "System Online" notification.

### 2. Proactive Cycle (Background)
Every 30-60 seconds, the `BackgroundAgent` executes:
- **Task Health Check**: Verifies active async tasks are not hung.
- **Reminder Scan**: Checks the database for scheduled notifications.
- **Index Maintenance**: Performs low-priority incremental indexing of changed files.
- **Heartbeat**: Updates the `last_heartbeat` timestamp for the Engineering Hub.

### 3. Reactive Cycle (User Interaction)
1. **Request Intake**: User sends a command (Voice/Text).
2. **Intent Triage**: `ToolOrchestrator` detects if a Desktop Action is needed.
3. **Context Injection**: If needed, `ContextManager` pulls the active window title.
4. **Tool Execution**:
    - **Step A**: LLM plans the tool call (e.g., `open_app`).
    - **Step B**: UI presents a confirmation prompt (Permission Gate).
    - **Step C**: `SystemTools` executes the subprocess.
    - **Step D**: Action is logged to the Audit Trail.
5. **Response**: User is notified of the result via UI and Speech.

## Failure Recovery Paths
| Scenario | Detection | Recovery Action |
| :--- | :--- | :--- |
| **Watcher Crash** | Heartbeat mismatch | `FileManager` restarts Observer thread. |
| **Index Lock** | SQLite `OperationalError` | Retry with exponential backoff; fallback to memory-only. |
| **LLM Timeout** | `asyncio.TimeoutError` | Fallback to deterministic regex routing. |
| **GPU OOM** | Model Manager Telemetry | Purge context window; notify user of resource pressure. |
