import os
import subprocess
import webbrowser
from datetime import datetime

class SystemController:
    """
    Handles system-level operations requested by the AI.
    """
    
    @staticmethod
    def shutdown_pc(seconds: int = 10):
        """Shutdown the PC after a delay."""
        print(f"🔌 SystemController: Shutting down in {seconds}s...")
        os.system(f"shutdown /s /t {seconds}")
        return f"PC will shutdown in {seconds} seconds. Save your work!"

    @staticmethod
    def restart_pc(seconds: int = 10):
        """Restart the PC after a delay."""
        print(f"🔄 SystemController: Restarting in {seconds}s...")
        os.system(f"shutdown /r /t {seconds}")
        return f"PC will restart in {seconds} seconds."

    @staticmethod
    def abort_shutdown():
        """Abort a scheduled shutdown/restart."""
        print("🛑 SystemController: Aborting shutdown...")
        os.system("shutdown /a")
        return "Shutdown/Restart sequence aborted."

    @staticmethod
    def open_app(app_name: str):
        """
        Open an application by name.
        Uses Windows 'start' command which is smart enough to find registered apps.
        """
        print(f"🚀 SystemController: Opening app '{app_name}'...")
        app_map = {
            "zalo": "zalo",
            "chrome": "chrome",
            "notepad": "notepad",
            "calculator": "calc",
            "explorer": "explorer",
            "cmd": "cmd",
            "powershell": "powershell",
            "word": "winword",
            "excel": "excel",
            "autokey": "AutoKey" # Placeholder, logic might need refinement
        }
        
        target = app_map.get(app_name.lower(), app_name)
        
        try:
            # os.startfile is Windows only and very convenient
            os.startfile(target)
            return f"Opening {app_name}..."
        except FileNotFoundError:
            # Fallback to shell execution
            try:
                subprocess.Popen(target, shell=True)
                return f"Attempting to open {app_name}..."
            except Exception as e:
                return f"Failed to open {app_name}: {str(e)}"
        except Exception as e:
            return f"Error opening {app_name}: {str(e)}"

    @staticmethod
    def open_url(url: str):
        """Open a URL in the default browser."""
        if not url.startswith("http"):
            url = "https://" + url
        print(f"🌐 SystemController: Opening URL '{url}'...")
        webbrowser.open(url)
        return f"Opening {url}"

    @staticmethod
    def create_note(content: str, filename: str = None):
        """Create a text note."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Note_{timestamp}.txt"
        
        # Save to Desktop for visibility or a specific Notes folder
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        filepath = os.path.join(desktop, filename)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Note saved to Desktop: {filename}"
        except Exception as e:
            return f"Failed to save note: {str(e)}"
