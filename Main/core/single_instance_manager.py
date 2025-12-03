import ctypes
import sys
import win32gui
import win32con
import win32api
import winerror
from core.config_manager import ConfigManager
import json
import os

class SingleInstanceManager:
    def __init__(self):
        self.mutex = None
        self.mutex_name = "Global\\MonToolHubMainApp"
        self.window_title = "Mon Tool Hub"
        self._load_config()

    def _load_config(self):
        """Load configuration from naming_registry.json if available"""
        try:
            registry_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "naming_registry.json")
            if os.path.exists(registry_path):
                with open(registry_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "SingleInstance" in data:
                        self.mutex_name = data["SingleInstance"].get("MutexName", self.mutex_name)
                        self.window_title = data["SingleInstance"].get("WindowTitle", self.window_title)
        except Exception as e:
            print(f"⚠️ Could not load naming_registry.json: {e}")

    def check_existing_instance(self):
        """
        Check if an instance is already running.
        Returns True if another instance is running, False otherwise.
        """
        try:
            # Create Named Mutex
            self.mutex = ctypes.windll.kernel32.CreateMutexW(None, False, self.mutex_name)
            last_error = ctypes.windll.kernel32.GetLastError()
            
            if last_error == winerror.ERROR_ALREADY_EXISTS:
                print(f"⚠️ Another instance is already running (Mutex: {self.mutex_name})")
                return True
            
            return False
        except Exception as e:
            print(f"❌ Error checking single instance: {e}")
            return False

    def activate_existing_instance(self):
        """Find and activate the existing application window"""
        try:
            hwnd = win32gui.FindWindow(None, self.window_title)
            if hwnd:
                print(f"✓ Found existing window: {hwnd}")
                
                # Define custom message (WM_USER + 1)
                WM_SHOW_APP = win32con.WM_USER + 1
                
                # Post message to the window to let it handle restoration safely
                # This avoids conflicts with FluentWindow's internal state
                win32api.PostMessage(hwnd, WM_SHOW_APP, 0, 0)
                
                # Also try to bring to foreground (harmless if it fails)
                try:
                    win32gui.SetForegroundWindow(hwnd)
                except:
                    pass
                    
                return True
            else:
                print(f"⚠️ Could not find window with title: {self.window_title}")
                return False
        except Exception as e:
            print(f"❌ Error activating existing instance: {e}")
            return False
