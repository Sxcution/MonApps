import sys
import os

# DPI Awareness Fix for Windows
if sys.platform.startswith("win"):
    import ctypes
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

# ensure console can display required debug glyphs
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="ignore")
13
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    # Request Admin Privileges
    if not is_admin():
        print("⚠️ Not running as Admin. Restarting with Admin privileges...")
        # Re-run the program with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    app = QApplication(sys.argv)
    app.setApplicationName("Macro Recorder")
    app.setOrganizationName("MonSoft")
    
    # CRITICAL: Prevent Qt from quitting when all windows are hidden
    # This is needed for the snipping tool which temporarily hides all windows
    app.setQuitOnLastWindowClosed(False)
    print("🔧 DEBUG: setQuitOnLastWindowClosed(False) - App will NOT auto-quit when windows hidden")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
