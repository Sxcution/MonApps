import os
import subprocess
import webbrowser
import ctypes
import time
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
            "zalo": os.path.join(os.getenv('LOCALAPPDATA'), 'Programs', 'Zalo', 'Zalo.exe'),
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

    @staticmethod
    def control_media(command: str, times: int = 1):
        """
        Control media/volume using Windows API key events.
        Commands: volume_up, volume_down, mute, play_pause, next, prev
        """
        # Ensure times is an integer
        times = int(times)
        print(f"🔊 SystemController: Media Command '{command}' x{times}...")
        
        VK_VOLUME_MUTE = 0xAD
        VK_VOLUME_DOWN = 0xAE
        VK_VOLUME_UP = 0xAF
        VK_MEDIA_NEXT_TRACK = 0xB0
        VK_MEDIA_PREV_TRACK = 0xB1
        VK_MEDIA_PLAY_PAUSE = 0xB3
        
        key_map = {
            "volume_up": VK_VOLUME_UP,
            "volume_down": VK_VOLUME_DOWN,
            "mute": VK_VOLUME_MUTE,
            "next": VK_MEDIA_NEXT_TRACK,
            "prev": VK_MEDIA_PREV_TRACK,
            "play_pause": VK_MEDIA_PLAY_PAUSE
        }
        
        vk_code = key_map.get(command.lower())
        if not vk_code:
            return f"Unknown media command: {command}"
            
        try:
            for _ in range(times):
                ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0) # Key down
                ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0) # Key up
                time.sleep(0.05) # Small delay
                
            return f"Executed {command} {times} times."
        except Exception as e:
            return f"Error executing media command: {str(e)}"
            return f"Executed {command} {times} times."
        except Exception as e:
            return f"Error executing media command: {str(e)}"

    @staticmethod
    def open_telegram_profiles(start: int, end: int, sample_path: str):
        """
        Open multiple Telegram instances based on a folder pattern.
        Pattern: Telegram - Copy (N)
        """
        print(f"🚀 SystemController: Opening Telegram profiles {start} to {end}...")
        
        try:
            # Clean up path (remove quotes if any)
            sample_path = sample_path.strip('"').strip("'")
            
            # Extract base directory
            # sample_path example: E:\Data Telegram\Telegram Desktop\M1\Telegram - Copy (2)\Telegram.exe
            # We need: E:\Data Telegram\Telegram Desktop\M1
            
            # Strategy: Go up 2 levels from the executable
            # Level 1: E:\Data Telegram\Telegram Desktop\M1\Telegram - Copy (2)
            # Level 2: E:\Data Telegram\Telegram Desktop\M1
            
            executable_dir = os.path.dirname(sample_path)
            base_dir = os.path.dirname(executable_dir)
            
            print(f"   → Base Directory: {base_dir}")
            
            success_count = 0
            failed_count = 0
            
            for i in range(start, end + 1):
                # Construct folder name
                # If i=1, usually it's just "Telegram" or "Telegram - Copy" depending on user naming
                # But based on user request "Telegram - Copy (N)", let's stick to that pattern for N >= 2
                # For safety, we can check a few variations if file not found
                
                folder_name = f"Telegram - Copy ({i})"
                exe_path = os.path.join(base_dir, folder_name, "Telegram.exe")
                
                if not os.path.exists(exe_path):
                    # Try alternative: maybe just "Telegram" for i=1?
                    if i == 1:
                         exe_path = os.path.join(base_dir, "Telegram", "Telegram.exe")
                
                if os.path.exists(exe_path):
                    print(f"   → Launching: {exe_path}")
                    try:
                        subprocess.Popen(exe_path, cwd=os.path.dirname(exe_path))
                        success_count += 1
                        time.sleep(1.5) # Delay to prevent CPU spike
                    except Exception as e:
                        print(f"   ❌ Failed to launch {i}: {e}")
                        failed_count += 1
                else:
                    print(f"   ⚠️ Path not found: {exe_path}")
                    failed_count += 1
            
            return f"Launched {success_count} Telegram instances. Failed: {failed_count}."
            
        except Exception as e:
            return f"Error launching Telegram profiles: {str(e)}"

    @staticmethod
    def search_file(filename: str, root_path: str = None):
        """
        Search for a file by name recursively.
        If root_path is not provided, searches Desktop, Documents, and Downloads.
        """
        print(f"🔍 SystemController: Searching for '{filename}'...")
        
        found_files = []
        search_roots = []
        
        if root_path:
            if os.path.exists(root_path):
                search_roots.append(root_path)
            else:
                return f"Error: Root path '{root_path}' does not exist."
        else:
            # Default search locations
            user_profile = os.path.expanduser("~")
            search_roots = [
                os.path.join(user_profile, "Desktop"),
                os.path.join(user_profile, "Documents"),
                os.path.join(user_profile, "Downloads")
            ]
            
        try:
            for root_dir in search_roots:
                if not os.path.exists(root_dir):
                    continue
                    
                print(f"   → Scanning: {root_dir}")
                # Walk through directory
                for root, dirs, files in os.walk(root_dir):
                    # Skip hidden directories and system folders to speed up
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ["Windows", "Program Files", "Program Files (x86)", "AppData"]]
                    
                    for file in files:
                        if filename.lower() in file.lower():
                            full_path = os.path.join(root, file)
                            found_files.append(full_path)
                            print(f"   ✓ Found: {full_path}")
                            
                            # Limit results
                            if len(found_files) >= 5:
                                return found_files
            
            if not found_files:
                return f"No files found matching '{filename}' in user directories."
                
            return found_files
            
        except Exception as e:
            return f"Error searching for file: {str(e)}"

    @staticmethod
    def open_file_path(path: str):
        """Open a specific file path."""
        print(f"📂 SystemController: Opening file '{path}'...")
        
        # Clean up path
        path = path.strip('"').strip("'")
        
        if not os.path.exists(path):
            return f"Error: File not found at '{path}'"
            
        try:
            os.startfile(path)
            return f"Opening {os.path.basename(path)}..."
        except Exception as e:
            return f"Error opening file: {str(e)}"

    @staticmethod
    def read_file_content(path: str):
        """Read the content of a text file."""
        print(f"📖 SystemController: Reading file '{path}'...")
        
        # Clean up path
        path = path.strip('"').strip("'")
        
        if not os.path.exists(path):
            return f"Error: File not found at '{path}'"
            
        try:
            # Try reading with utf-8 first
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Limit content length to prevent token overflow (e.g., 50KB)
            if len(content) > 50000:
                return f"File content (Truncated first 50000 chars):\n{content[:50000]}...\n\n(File too large)"
            
            return content
        except UnicodeDecodeError:
            return "Error: Cannot read binary file or unknown encoding."
        except Exception as e:
            return f"Error reading file: {str(e)}"

    @staticmethod
    def web_search(query: str):
        """
        Search the web using DuckDuckGo (Free API).
        Returns top 5 results.
        """
        print(f"🌍 SystemController: Searching web for '{query}'...")
        
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return "Error: 'duckduckgo-search' library not installed. Please run: pip install duckduckgo-search"
            
        try:
            results = []
            with DDGS() as ddgs:
                # Search for top 10 results using 'api' backend
                for r in ddgs.text(query, max_results=10, backend="api"):
                    results.append(f"- [{r['title']}]({r['href']})\n  {r['body']}")
            
            if not results:
                return f"No results found for '{query}'."
                
            return "Web Search Results:\n" + "\n\n".join(results)
            
        except Exception as e:
            return f"Error performing web search: {str(e)}"

    @staticmethod
    def run_terminal_command(command: str):
        """
        Execute a terminal command and return the output.
        Useful for advanced tasks like 'taskkill', 'adb', 'java', etc.
        """
        print(f"💻 SystemController: Running command '{command}'...")
        
        try:
            # Run command with timeout (e.g., 60 seconds)
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=60,
                encoding='utf-8', 
                errors='replace'
            )
            
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            response = ""
            if output:
                response += f"Output:\n{output}\n"
            if error:
                response += f"Error/Stderr:\n{error}\n"
                
            if not response:
                response = "Command executed successfully (no output)."
                
            return response
            
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 60 seconds."
        except Exception as e:
            return f"Error executing command: {str(e)}"
