# Runtime Failure Matrix & Recovery Procedures

## Failure Scenarios

| Component | Failure | Symptom | Recovery Action | Fallback State |
| :--- | :--- | :--- | :--- | :--- |
| **Tray Icon** | Init Crash | No tray menu | `_safe_start` fallback | Headless Mode |
| **Browser** | API Block | Snapshot error | Throttled polling | Title-only mode |
| **Indexing** | I/O Error | Missing files | Health cycle restart | Cache-only mode |
| **WebSocket** | Drop | UI Disconnect | Adaptive reconnect | Local Queueing |
| **Database** | Lock | Task failure | WAL Rollback | Read-only mode |

## Subsystem Isolation Gating
F.R.I.D.A.Y. now uses a "Circuit Breaker" pattern for desktop integrations. If a subsystem fails more than 3 times in a single session, it is automatically gated (disabled) to preserve core assistant functionality.

## Error Reporting
- **User-Facing**: Subtle status badges in the Engineering Hub.
- **Log-Level**: High-precision JSON logs in `logs/friday.log` for developer diagnostics.
