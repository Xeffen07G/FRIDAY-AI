# Browser & Workflow Intelligence Architecture

## Overview
F.R.I.D.A.Y. implements a low-overhead, deterministic layer for workflow awareness. This system enables context-aware assistance without the need for cloud-based telemetry or autonomous agents.

## 1. Browser Context Awareness
- **Detection**: Uses `pygetwindow` and `psutil` to identify active browser processes (Chrome, Edge, Firefox).
- **Snapshotting**: Captures window titles and active states to build a "Research Session" snapshot.
- **Privacy**: No browsing history is scraped. Only titles and active tab states are analyzed upon explicit user request.

## 2. Developer Context
- **VS Code Integration**: Parses window titles to identify active project names and files.
- **Git Awareness**: (Planned) Integration with local git binaries to summarize branch states and recent commits.

## 3. Workflow Memory Core
- **Persistence**: Sessions are stored in the local SQLite `system_audit_log` table.
- **Recovery**: Enables "Continue where I left off" by querying the most recent session payloads.

## 4. Engineering Hub Integration
- **Workflow Tab**: Real-time visualization of active projects, browser snapshots, and continuity timelines.
