import sys
import os
from datetime import datetime

# CRITICAL: Set working directory
try:
    # Get Main directory
    main_root = os.path.dirname(os.path.abspath(__file__))
    
    def log(msg):
        """Print to console only (no file logging)"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {msg}")
    
    log("=" * 50)
    log(f"Main.py launched")
    log(f"Python: {sys.executable}")
    log(f"Version: {sys.version}")
    log(f"Current Working Dir Before: {os.getcwd()}")
    log(f"Main Root: {main_root}")
    
    # Change working directory
    if os.getcwd() != main_root:
        os.chdir(main_root)
        log(f"Working Directory changed to: {os.getcwd()}")
    else:
        log(f"Working Directory already correct: {os.getcwd()}")
    
    # Check if Apps folder exists
    apps_path = os.path.join(main_root, "Apps")
    log(f"Apps folder exists: {os.path.exists(apps_path)}")
    if os.path.exists(apps_path):
        log(f"Apps folder contents: {os.listdir(apps_path)[:5]}")  # First 5 items
    
except Exception as e:
    import traceback
    print(f"[Main] ERROR: {e}")
    traceback.print_exc()

from PySide6.QtWidgets import QApplication
from core.config_manager import ConfigManager
from launcher_ui.home_interface import HomeInterface
from launcher_ui.settings_interface import SettingsInterface
from launcher_ui.tools_interface import ToolsInterface
from launcher_ui.app_settings_interface import AppSettingsInterface
from launcher_ui.log_interface import LogInterface
from launcher_ui.main_window import MainWindow
from core.log_manager import LogManager

if __name__ == '__main__':
    # Initialize Logger
    LogManager.get_instance()
    
    app = QApplication(sys.argv)
    
    # ✅ STEP 1: Set Fluent Dark Theme
    from qfluentwidgets import setTheme, Theme
    setTheme(Theme.DARK)
    
    # ✅ STEP 2: Apply Dark Palette for non-Fluent widgets (QMessageBox, QDialog, etc.)
    from PySide6.QtGui import QPalette, QColor
    from PySide6.QtCore import Qt
    
    dark_palette = QPalette()
    dark_bg = QColor(32, 32, 32)      # Fluent standard dark background
    dark_text = QColor(255, 255, 255) # White text
    
    dark_palette.setColor(QPalette.Window, dark_bg)
    dark_palette.setColor(QPalette.WindowText, dark_text)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))  # Input/Table background
    dark_palette.setColor(QPalette.AlternateBase, dark_bg)
    dark_palette.setColor(QPalette.ToolTipBase, dark_text)
    dark_palette.setColor(QPalette.ToolTipText, dark_text)
    dark_palette.setColor(QPalette.Text, dark_text)
    dark_palette.setColor(QPalette.Button, dark_bg)
    dark_palette.setColor(QPalette.ButtonText, dark_text)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    
    app.setPalette(dark_palette)  # Apply globally
    
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
