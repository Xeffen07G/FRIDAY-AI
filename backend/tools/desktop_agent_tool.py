from tools.base_tool import BaseTool
import asyncio
import os
import json

class DesktopAgentTool(BaseTool):
    name = "desktop_agent"
    description = "Advanced workspace intelligence: find files by content, summarize folders, or detect active window context."
    parameters = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["find_by_content", "summarize_folder", "get_active_context", "schedule_reminder", "semantic_lookup", "summarize_document", "browser_snapshot", "workflow_resume", "click_terminal_input", "click_vscode_sidebar", "open_terminal_panel", "focus_browser_tab", "focus_chat_input", "resume_frontend", "resume_workspace", "fix_occupied_port"]},
            "query": {"type": "string", "description": "Search query or folder/file path"},
            "time": {"type": "string", "description": "Time for reminder (e.g. '2026-05-13 14:00')"},
            "message": {"type": "string", "description": "Reminder message"}
        },
        "required": ["action"]
    }

    async def execute(self, action: str, query: str = None, **kwargs) -> str:
        from backend.desktop.file_manager import file_manager
        from backend.desktop.context_manager import context_manager
        
        if action == "find_by_content":
            if not query: return "Error: No query provided for content search."
            results = await file_manager.semantic_search(query)
            if not results: return "No matching content found in your documents."
            
            output = "Found relevant content in these files:\n"
            for r in results:
                output += f"- {r['name']} ({r['path']})\n  Snippet: {r['snippet']}\n"
            return output

        elif action == "summarize_folder":
            if not query: return "Error: No folder path provided."
            files = file_manager.search_files(query)
            if not files: return f"No files found in {query}."
            
            summary = f"Folder Summary: {query}\nTotal indexed files: {len(files)}\n"
            summary += "Recent items:\n" + "\n".join([f"- {f['name']}" for f in files[:5]])
            return summary

        elif action == "get_active_context":
            window = context_manager.get_active_window()
            clipboard = context_manager.get_clipboard_content()
            
            context = f"Active Window: {window}"
            if clipboard:
                context += f"\nClipboard Content (First 100 chars): {clipboard[:100]}..."
            return context

        elif action == "schedule_reminder":
            msg = kwargs.get("message")
            rem_time = kwargs.get("time")
            if not msg or not rem_time: return "Error: Message and time are required."
            
            from backend.memory.database import get_connection
            import uuid
            conn = get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO background_tasks (id, name, payload, status, scheduled_at) VALUES (?, ?, ?, ?, ?)",
                    (str(uuid.uuid4())[:8], "reminder", msg, "pending", rem_time)
                )
                conn.commit()
                return f"Reminder scheduled for {rem_time}: {msg}"
            finally:
                conn.close()

        elif action == "semantic_lookup":
            if not query: return "Error: No query provided."
            results = await file_manager.semantic_search(query)
            meta_results = file_manager.search_files(query)
            
            output = f"Semantic Lookup for '{query}':\n"
            if results:
                output += "\n--- Content Matches ---\n" + "\n".join([f"- {r['name']}: {r['snippet']}" for r in results[:3]])
            if meta_results:
                output += "\n--- Filename Matches ---\n" + "\n".join([f"- {f['name']} ({f['path']})" for f in meta_results[:3]])
            return output

        elif action == "summarize_document":
            if not query or not os.path.exists(query):
                return "Error: Document path is invalid or missing."
            try:
                ext = os.path.splitext(query)[1].lower()
                content = ""
                if ext == ".txt":
                    with open(query, "r", encoding="utf-8") as f:
                        content = f.read(2000)
                elif ext == ".pdf":
                    content = f"[PDF Content Extraction for {os.path.basename(query)} - requires PyPDF]"
                else:
                    return f"Unsupported file type: {ext}"
                return f"Document Content Preview:\n{content}\n\nPlease summarize this."
            except Exception as e:
                return f"Extraction failed: {str(e)}"

        elif action == "browser_snapshot":
            from backend.desktop.browser_manager import browser_manager
            from backend.desktop.workflow_manager import workflow_manager
            
            snapshot = browser_manager.get_research_snapshot()
            workflow_manager.save_session("research", snapshot)
            return snapshot + "\n(Research session saved to workflow memory)"

        elif action == "workflow_resume":
            from backend.desktop.workflow_manager import workflow_manager
            last_research = workflow_manager.get_last_session("research")
            last_dev = workflow_manager.get_last_session("dev")
            
            output = "Recent Workflow Context:\n"
            if last_research:
                output += f"- Last Research ({last_research['timestamp']}): {last_research['payload'][:100]}...\n"
            if last_dev:
                output += f"- Last Dev Session: {last_dev['payload'][:100]}...\n"
            
            return output if (last_research or last_dev) else "No previous sessions found to resume."

        elif action == "click_terminal_input":
            from backend.desktop.semantic_operator import semantic_operator
            success, msg = semantic_operator.click_terminal_input()
            return msg
        elif action == "click_vscode_sidebar":
            from backend.desktop.semantic_operator import semantic_operator
            success, msg = semantic_operator.click_vscode_sidebar()
            return msg
        elif action == "open_terminal_panel":
            from backend.desktop.semantic_operator import semantic_operator
            success, msg = semantic_operator.open_terminal_panel()
            return msg
        elif action == "focus_browser_tab":
            from backend.desktop.semantic_operator import semantic_operator
            success, msg = semantic_operator.focus_browser_tab(query or "localhost")
            return msg
        elif action == "focus_chat_input":
            from backend.desktop.semantic_operator import semantic_operator
            success, msg = semantic_operator.focus_chat_input()
            return msg
        elif action == "resume_frontend":
            from backend.desktop.semantic_operator import semantic_operator
            success, msg = semantic_operator.resume_frontend()
            return msg
        elif action == "resume_workspace":
            from backend.desktop.semantic_operator import semantic_operator
            success, msg = semantic_operator.resume_workspace()
            return msg
        elif action == "fix_occupied_port":
            from backend.desktop.semantic_operator import semantic_operator
            try:
                port = int(query)
            except Exception:
                port = 5173
            success, msg = semantic_operator.fix_occupied_port(port)
            return msg

        return "Unknown desktop agent action."
