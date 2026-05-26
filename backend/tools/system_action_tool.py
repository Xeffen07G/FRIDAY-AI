import subprocess
import os
import platform
from tools.base_tool import BaseTool

class SystemActionTool(BaseTool):
    name = "system_action"
    description = "Perform local system actions like opening applications, listing files, or retrieving system time/info."
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["open_app", "list_files", "system_status", "workspace_search", "get_recent_activity", "create_note", "workspace_setup", "git_status", "inspect_logs", "project_structure", "get_time"]},
            "target": {"type": "string", "description": "Target keyword, path, or content"},
            "note_title": {"type": "string", "description": "Title for the note if action is create_note"}
        },
        "required": ["action"]
    }

    def execute(self, action: str, target: str = None, **kwargs) -> str:
        if action == "open_app":
            if not target: return "Error: No target application specified."
            try:
                if platform.system() == "Windows":
                    # Simple start command for common apps with aliases
                    app_map = {
                        "vscode": "code",
                        "browser": "start",
                        "chrome": "chrome",
                        "calc": "calc",
                        "calculator": "calc",
                        "notepad": "notepad"
                    }
                    cmd = app_map.get(target.lower(), target)
                    proc = subprocess.Popen(["cmd", "/c", f"start {cmd}"], shell=True)
                    from core.runtime_state import runtime_state
                    if not hasattr(runtime_state.tools, "active_subprocesses"):
                        runtime_state.tools.active_subprocesses = []
                    runtime_state.tools.active_subprocesses.append(proc.pid)
                else:
                    proc = subprocess.Popen(["open", "-a", target])
                    from core.runtime_state import runtime_state
                    if not hasattr(runtime_state.tools, "active_subprocesses"):
                        runtime_state.tools.active_subprocesses = []
                    runtime_state.tools.active_subprocesses.append(proc.pid)
                return f"Successfully triggered opening of {target}."
            except Exception as e:
                return f"Failed to open {target}: {str(e)}"
        
        elif action == "list_files":
            path = target or os.getcwd()
            try:
                files = os.listdir(path)
                return f"Files in {path}: " + ", ".join(files[:20])
            except Exception as e:
                return f"Error listing files: {str(e)}"
                
        elif action == "system_status":
            import psutil
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            from backend.desktop.file_manager import file_manager
            indexed_count = len(file_manager.get_recent_activity(100)) # Approximation
            return f"System Status: CPU {cpu}%, RAM {mem}%. Workspace Index: {indexed_count} activities tracked."
            
        elif action == "workspace_search":
            if not target: return "Error: No search query provided."
            from backend.desktop.file_manager import file_manager
            results = file_manager.search_files(target)
            if not results: return "No files found matching that query."
            return "Search Results:\n" + "\n".join([f"- {r['name']} ({r['path']})" for r in results])

        elif action == "get_recent_activity":
            from backend.desktop.file_manager import file_manager
            activities = file_manager.get_recent_activity(5)
            if not activities: return "No recent activity recorded."
            return "Recent Workspace Activity:\n" + "\n".join([f"- {a['action']} {os.path.basename(a['path'])} at {a['timestamp']}" for a in activities])

        elif action == "create_note":
            if not target: return "Error: No note content provided."
            title = kwargs.get("note_title", "note.txt")
            from backend.desktop.file_manager import file_manager
            # Simple direct implementation
            notes_dir = os.path.abspath("workspace/notes")
            os.makedirs(notes_dir, exist_ok=True)
            path = os.path.join(notes_dir, title)
            with open(path, "w", encoding="utf-8") as f:
                f.write(target)
            file_manager.log_activity(path, "CREATED")
            return f"Note created successfully at: {path}"

        elif action == "workspace_setup":
            if not target: return "Error: No project path specified."
            # Deterministic workflow: Open Folder + Open Terminal + (Optional) Open VS Code
            try:
                os.startfile(target)
                proc1 = subprocess.Popen(["powershell.exe", "-NoExit", "-Command", f"cd {target}"], shell=True)
                # Attempt to open VS Code if it's in PATH
                proc2 = subprocess.Popen(["code", target], shell=True)
                
                from core.runtime_state import runtime_state
                if not hasattr(runtime_state.tools, "active_subprocesses"):
                    runtime_state.tools.active_subprocesses = []
                runtime_state.tools.active_subprocesses.append(proc1.pid)
                runtime_state.tools.active_subprocesses.append(proc2.pid)
                
                return f"Workspace setup complete for {target}. Folder, Terminal, and VS Code launched."
            except Exception as e:
                return f"Partial success in workspace setup: {str(e)}"

        elif action == "git_status":
            path = target or os.getcwd()
            try:
                result = subprocess.check_output(["git", "status", "--short"], cwd=path, stderr=subprocess.STDOUT, text=True)
                return f"Git Status for {path}:\n{result or 'Working tree clean.'}"
            except Exception as e:
                return f"Failed to get git status: {str(e)}"

        elif action == "inspect_logs":
            # Simple log tail for the current project
            log_file = "logs/friday.log"
            if not os.path.exists(log_file): return "Error: Log file not found."
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()[-20:]
                return "Recent Log Output:\n" + "".join(lines)
            except Exception as e:
                return f"Failed to read logs: {str(e)}"

        elif action == "project_structure":
            path = target or os.getcwd()
            try:
                output = f"Project Structure for {path}:\n"
                for root, dirs, files in os.walk(path):
                    level = root.replace(path, '').count(os.sep)
                    indent = ' ' * 4 * (level)
                    output += f"{indent}{os.path.basename(root)}/\n"
                    subindent = ' ' * 4 * (level + 1)
                    for f in files[:5]: # Limit to 5 files per dir
                        output += f"{subindent}{f}\n"
                    if len(files) > 5:
                        output += f"{subindent}... and {len(files)-5} more\n"
                    if level >= 2: break # Limit depth
                return output
            except Exception as e:
                return f"Error mapping project structure: {str(e)}"

        elif action == "get_time":
            from datetime import datetime
            return f"Current time: {datetime.now().strftime('%I:%M %p, %B %d, %Y')}"

        return "Unknown system action."
