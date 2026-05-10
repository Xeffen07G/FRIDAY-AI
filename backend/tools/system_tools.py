import subprocess
import os
import platform

class SystemTools:
    """Handles executing local applications and workflows."""
    
    def __init__(self):
        self.os_type = platform.system()
        
    def open_app(self, app_name: str) -> str:
        """Launches a known application."""
        app_name_lower = app_name.lower()
        
        try:
            if self.os_type == "Windows":
                if "chrome" in app_name_lower:
                    subprocess.Popen(["start", "chrome"], shell=True)
                    return "Opened Google Chrome."
                elif "code" in app_name_lower or "vscode" in app_name_lower:
                    subprocess.Popen(["code"], shell=True)
                    return "Opened Visual Studio Code."
                elif "spotify" in app_name_lower:
                    subprocess.Popen(["start", "spotify"], shell=True)
                    return "Opened Spotify."
                else:
                    # Attempt generic start
                    subprocess.Popen(["start", app_name], shell=True)
                    return f"Attempted to open {app_name}."
            else:
                return f"App launching not fully implemented for {self.os_type} yet."
        except Exception as e:
            return f"Failed to open {app_name}: {str(e)}"
            
    def open_folder(self, folder_path: str) -> str:
        """Opens a directory in the file explorer."""
        try:
            if not os.path.exists(folder_path):
                return f"Folder does not exist: {folder_path}"
                
            if self.os_type == "Windows":
                subprocess.Popen(["explorer", os.path.normpath(folder_path)])
            elif self.os_type == "Darwin": # macOS
                subprocess.Popen(["open", folder_path])
            else: # Linux
                subprocess.Popen(["xdg-open", folder_path])
                
            return f"Opened folder: {folder_path}"
        except Exception as e:
            return f"Failed to open folder: {str(e)}"
