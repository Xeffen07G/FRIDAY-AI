# F.R.I.D.A.Y.
> **A Persistent Cognitive Operating System for Private, Realtime AI Presence.**

![F.R.I.D.A.Y. Banner]([[FILE:friday_github_banner_v1_5_0_1778653183392.png]])

[![Version](https://img.shields.io/badge/version-1.5.0--stable-blue.svg)](https://github.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React 19](https://img.shields.io/badge/react-19-61dafb.svg)](https://react.dev/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-white.svg)](https://ollama.ai/)
[![Docker](https://img.shields.io/badge/deployment-Docker-blue.svg)](https://www.docker.com/)

### **Instantly Interactive. Securely Local. Continuously Alive.**

F.R.I.D.A.Y. is a **Production-Grade Cognitive Operating System** engineered for the next generation of local AI interaction. It combines a cinematic React-based interface with a hardened streaming pipeline, providing a persistent digital presence that lives entirely on your hardware.

**Key Capabilities:**
- **Zero-Latency Voice**: Real-time STT/TTS streaming with sub-200ms loop duration.
- **Persistent Cognition**: Hierarchical memory (Episodic/Semantic) via ChromaDB.
- **Autonomous Reasoning**: Multi-step tool orchestration and deterministic planning.
- **Deep Observability**: Real-time telemetry and event inspection via the Engineering Hub.

### **Hero Architecture**
The core architecture is a **Distributed Cognitive Node** where the **Unified Orchestrator** manages intent flows across specialized engines. By isolating perception (WebSocket-based voice streams) from reasoning (Local GGUF/ExLlama inference) and memory (Vector persistence), F.R.I.D.A.Y. delivers a seamless, high-performance experience without ever leaking data to the cloud.

---

## ⚡ **Core Engineering Pillars**

### 🎙️ **Realtime Voice Pipeline (v2)**
Achieve human-like conversational latency with a streaming audio stack.
- **STT**: Faster-Whisper (Large-v3) with VAD-aware chunking.
- **TTS**: Piper TTS for sub-100ms synthesis.
- **Barge-in**: Robust interruption handling via real-time energy analysis.

### 🧠 **Hierarchical Memory System**
- **Working Memory**: Short-term session state for immediate context.
- **Episodic Memory**: Time-indexed logs of past interactions.
- **Semantic Memory**: Vector-based knowledge retrieval via **ChromaDB**.
- **Decay Engine**: Smart memory reinforcement and pruning.

### 🛠️ **Autonomous Reasoning & Planning**
- **Intent Classification**: Triage requests into DIRECT, TOOL-ASSISTED, or REASONING-GRAPH flows.
- **Safe Orchestration**: Sandboxed execution of OS controls, file management, and web research.
- **Deterministic Demos**: Integrated "Simulated Mode" for stable showcase environments.

### 📊 **Observability & Diagnostics**
- **Engineering Hub**: Real-time WebSocket event inspector and latency benchmarking.
- **Packet Tracing**: Full visibility into every "thought" and tool output.

---

## 🚀 **Quick Start**

### **Standard Startup (Windows)**
```powershell
./start_friday.ps1
```

### **Docker Orchestration (Universal)**
```bash
docker-compose up --build
```

---

## 🛠️ **Technology Stack**

- **Backend**: Python 3.10 / FastAPI / Pydantic / Asyncio
- **Frontend**: React 19 / Vite / TailwindCSS / Framer Motion / Lucide
- **Inference Engine**: Ollama (phi3:mini / llama3)
- **Persistence**: ChromaDB (Vector) + SQLite (Relational)
- **Containerization**: Docker / Docker Compose

---

## 🤝 **Professional Showcase**
- **[Demo Script](docs/demo_script.md)**: A structured guide for live demonstrations.
- **[Showcase Prompts](docs/showcase_prompts.md)**: Curated test cases for AI reasoning and memory.
- **[Architecture Deep-Dive](docs/FINAL_ARCHITECTURE.md)**: Comprehensive system diagrams.
- **[Release Notes](docs/RELEASE_NOTES_v1.md)**: What's new in v1.5.0.

---

## 🛡️ **Privacy & Security**
F.R.I.D.A.Y. is built on the principle of **Data Sovereignty**.
- **100% Offline**: Cognition, Voice, and Memory stay on your machine.
- **Audit Ready**: All tool calls are logged and require explicit permission (configurable).

---

**Designed by Advanced Agentic Coding.**
*"I'm already in your system, sir."*
