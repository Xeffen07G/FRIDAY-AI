# Known Limitations: Desktop Agent Runtime

## Current Limitations (v1.5.0)

### 1. Filesystem Observation
- **Network Drives**: `watchdog` may not reliably detect events on network-mapped drives (SMB/NFS) depending on OS notification support.
- **Hidden Files**: Default indexing excludes hidden directories (`.git`, `.tmp`, etc.) to prevent database bloat.

### 2. Desktop Context
- **Admin Windows**: `pygetwindow` cannot retrieve titles or metadata for applications running with Elevated/Administrator privileges unless F.R.I.D.A.Y. is also elevated.
- **Multiple Monitors**: Context detection currently focuses on the primary active window; multi-focus detection is not supported.

### 3. Background Runtime
- **Process Persistence**: If the main Python process is forcefully killed (`SIGKILL`), the `BackgroundAgent` cannot perform final cleanup (e.g., closing open file handles).
- **Startup on Boot**: Autostart requires the user to have Registry write permissions.

### 4. Integration
- **Clipboard Formats**: Only text/string clipboard content is currently processed. Images or file paths copied to the clipboard are ignored.
- **Search Latency**: Large semantic queries (>100 results) may take up to 2 seconds due to vector store similarity calculations.

## Planned Improvements
- [ ] Support for OCR-based context analysis of inactive windows.
- [ ] Differential indexing for large binary files.
- [ ] Multi-user session isolation for background tasks.
