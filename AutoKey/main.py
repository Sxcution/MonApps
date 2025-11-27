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

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Macro Recorder")
    app.setOrganizationName("MonSoft")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
