# Privacy Boundaries & Safety Guardrails

## Core Principles
1. **Local Processing Only**: All browser and project context analysis occurs on the user's machine. No data is sent to external servers.
2. **Explicit Permission**: Snapshots of research or dev sessions are only saved when the user triggers a "Snapshot" or "Save Session" intent.
3. **Deterministic Logic**: No autonomous agents are allowed to "explore" the browser or filesystem. Actions are restricted to predefined inspection tools.

## Gated Data Access
| Data Type | Inspection Method | Privacy Level |
| :--- | :--- | :--- |
| **Window Titles** | pygetwindow (Process Level) | LOW (Visible to OS) |
| **Active URLs** | UI Automation (Permission Required) | MEDIUM (Session Info) |
| **Filesystem Meta** | Watchdog (IO Events) | MEDIUM (Workspace Path) |
| **Clipboard** | Native API (On Request) | HIGH (User Content) |

## Audit Trail
Every contextual inspection is recorded in the `system_audit_log` with a component tag and timestamp, allowing the user to review exactly what information F.R.I.D.A.Y. has accessed.
