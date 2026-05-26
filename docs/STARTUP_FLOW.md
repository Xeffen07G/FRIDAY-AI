# F.R.I.D.A.Y. Startup Flow & Lifecycle

## 1. Initialization Sequence
1. **Host Discovery**: `main.py` detects environment flags (e.g. `--silent`).
2. **Validator Pass**: `StartupValidator` checks:
   - Python dependencies (pygetwindow, watchdog, pystray)
   - SQLite table integrity
   - Environment secrets (Tavily, etc.)
3. **Core Services**:
   - `EventBus`: Initializes non-blocking telemetry stream.
   - `FileManager`: Restores folder watchers and checks index health.
   - `TaskManager`: Hydrates pending tasks and reminders from database.
4. **Desktop UX**:
   - `TrayManager`: Spawns native tray thread.
   - `HotkeyManager`: Binds global `Ctrl+Space` and `Caps Lock` (PTT).
5. **API Layer**: FastAPI server starts on port 8000.

## 2. Silent vs. Normal Mode
- **Normal Mode**: UI opens immediately on launch.
- **Silent Mode**: Background process starts minimized to tray; UI only appears on hotkey or tray action.

## 3. Failure Recovery
- **Database Corruption**: Automatic rollback of SQLite WAL if inconsistent.
- **Watcher Death**: `BackgroundAgent` health-cycle (30s) restarts failed filesystem observers.
- **Model Timeout**: `ModelManager` releases locks if inference stalls > 60s.
