# RELEASE NOTES - F.R.I.D.A.Y. v1.5.0 (Stable)

## 🚀 Overview
F.R.I.D.A.Y. v1.5.0 marks the transition from an experimental cognitive prototype to a production-grade Local AI Operating System. This release focuses on stability, deterministic reasoning, and premium observability.

## ✨ Key Features
- **Cinematic Frontend**: A glassmorphic, React-based interface with high-fidelity animations and responsive design.
- **Cognitive Engine v2**: Enhanced hierarchical memory (Short/Episodic/Semantic) with automatic decay and semantic retrieval.
- **Engineering Hub**: Real-time WebSocket observability with event inspection and performance metrics.
- **Simulated Mode**: Deterministic demo playback for stable showcases and testing.
- **Unified Tooling**: Multi-step tool orchestration with parallel execution and failure recovery.
- **Privacy First**: 100% local inference via Ollama; no data ever leaves the host.

## 🛠️ Internal Improvements
- **Codebase Normalization**: Removed 30+ stale artifacts, debug scripts, and redundant imports.
- **Pipeline Stabilization**: Hardened voice WebSocket logic with robust interruption (barge-in) support.
- **Observability**: Added end-to-end latency tracking across all cognitive modules.

## 📦 Deployment
- **Docker Support**: Full containerization via `docker-compose`.
- **Setup Scripts**: Re-engineered `start_friday.ps1` for smoother local onboarding.

---
**Advanced Agentic Coding**
*"The future is locally hosted."*
