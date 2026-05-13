# Workflow Memory Model

## Data Structures

### 1. Research Session Payload
```json
{
  "timestamp": "2026-05-13T13:00:00",
  "tabs": [
    {"browser": "chrome", "title": "React Documentation", "is_active": true},
    {"browser": "chrome", "title": "Ollama API Reference", "is_active": false}
  ],
  "session_id": "uuid-v4"
}
```

### 2. Developer Context Payload
```json
{
  "active_project": "JARVIS",
  "open_files": ["main.py", "task_manager.py"],
  "git_branch": "main",
  "status": "DIRTY"
}
```

## Retrieval Strategy
- **Recency-First**: The `workflow_resume` tool prioritizes the most recent snapshot in the audit log.
- **Semantic Linkage**: (Future) Reminders and tasks can be linked to specific project or research sessions via the `background_tasks` foreign keys.
