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

def exception_hook(exctype, value, traceback):
    import traceback as tb
    error_msg = "".join(tb.format_exception(exctype, value, traceback))
    print(error_msg)
    with open("error.log", "a") as f:
        f.write(error_msg + "\n")
    sys.excepthook = sys.__excepthook__
    sys.excepthook(exctype, value, traceback)

sys.excepthook = exception_hook

def qt_message_handler(mode, context, message):
    if "QFont::setPointSize" in message:
        return
    # Forward other messages to default handler (or just print them)
    # Since we can't easily call the default handler from Python, we'll just print non-suppressed warnings
    # to stderr if they are warnings/critical
    if mode in (1, 2, 3): # Warning, Critical, Fatal
        print(f"Qt Msg: {message}")

def main():
    # Request Admin Privileges
    if not is_admin():
        print("⚠️ WARNING: Not running as Admin.")
        print("   Hotkeys and Recording might not work correctly.")
        print("   Please run your terminal/IDE as Administrator if you encounter issues.")
        # ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        # sys.exit()

    # Install Message Handler
    from PyQt6.QtCore import qInstallMessageHandler
    qInstallMessageHandler(qt_message_handler)

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
