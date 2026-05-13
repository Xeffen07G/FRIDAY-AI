# Subsystem Dependency Graph

```mermaid
graph TD
    A[main.py] --> B[StartupValidator]
    B --> C[EventBus]
    B --> D[TaskManager]
    
    D --> E[BackgroundAgent]
    E --> F[FileManager]
    E --> G[WorkflowManager]
    E --> H[BrowserManager]
    
    C --> I[WS_Voice]
    I --> J[Frontend UI]
    
    E --> K[TrayManager]
    E --> L[HotkeyManager]
    
    F --> M[SQLite/ChromaDB]
    G --> M
```

## Initialization Order (Startup Stability Phase 5)
1. **Core Utilities**: Logger, Settings, EventBus.
2. **Data Layers**: Database connections (WAL mode), Indexers.
3. **Control Runtime**: TaskManager, BackgroundAgent.
4. **Desktop UX**: Tray, Hotkeys (Native threads).
5. **API Interface**: FastAPI server start.
6. **Telemetry**: Active event emission.
