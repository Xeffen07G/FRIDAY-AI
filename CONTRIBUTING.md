# Contributing to F.R.I.D.A.Y.

Thank you for your interest in contributing to the F.R.I.D.A.Y. Cognitive OS! We are building a high-performance, local-first AI assistant, and we value your help in making it better.

## 🛠️ Development Environment

### Setup
1. Fork the repository.
2. Clone your fork: `git clone https://github.com/your-username/JARVIS.git`
3. Follow the installation guide in the `README.md`.

### Architecture Standards
- **Backend**: Use `FastAPI` for routes and `Pydantic v2` for data models. Follow the `BaseTool` pattern for new tool additions.
- **Frontend**: Use functional React components with TailwindCSS. Avoid ad-hoc styling; use our predefined design tokens in `index.css`.
- **Async First**: Ensure all I/O bound operations (especially LLM and Tool calls) are non-blocking.

## 🤝 Workflow
1. **Branching**: Create a feature branch (`feat/your-feature` or `fix/your-fix`).
2. **Commit Messages**: Use [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat: add vision support`, `fix: resolve websocket timeout`).
3. **Tests**: Ensure `python tests/identity_test.py` passes before submitting.
4. **PR**: Open a Pull Request with a clear description of your changes.

## 🧩 Adding New Tools
1. Create a new file in `backend/tools/`.
2. Inherit from `BaseTool`.
3. Implement `execute()` and define the `parameters` JSON schema.
4. Register the tool in `backend/tools/tool_registry.py`.

## 📜 Code of Conduct
Please be respectful and professional in all interactions.

---

**Happy Coding!**
