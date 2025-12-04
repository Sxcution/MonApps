import sys
import os
import ctypes
from datetime import datetime

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# CRITICAL: Auto-elevate to Admin if not already
if not is_admin():
    # Re-run the program with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# CRITICAL: Set working directory
try:
    # Get Main directory
    main_root = os.path.dirname(os.path.abspath(__file__))
    
    def log(msg):
        """Print to console only (no file logging)"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {msg}")
    
    log("=" * 50)
    log(f"Main.pyw launched")
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

# Global Exception Handler - prevents crashes from unhandled exceptions
def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Catch unhandled exceptions and display error dialog instead of crashing"""
    import traceback
    
    # Format exception
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # Print to console
    print(f"\n{'='*50}")
    print("UNHANDLED EXCEPTION - App will continue running")
    print(f"{'='*50}")
    print(error_msg)
    
    # Show error dialog to user (if QApplication exists)
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        if QApplication.instance():
            QMessageBox.critical(
                None,
                "Lỗi Không Xử Lý Được",
                f"Đã xảy ra lỗi:{exc_type.__name__}: {exc_value}\n\n"
                f"Ứng dụng sẽ tiếp tục chạy."
            )
    except:
        pass  # If Qt isn't available, just print to console

# Install global exception handler
sys.excepthook = global_exception_handler


from PySide6.QtWidgets import QApplication, QMessageBox
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
    
    # ✅ SINGLE INSTANCE CHECK
    # Must be done before creating QApplication to avoid overhead
    from core.single_instance_manager import SingleInstanceManager
    instance_manager = SingleInstanceManager()
    if instance_manager.check_existing_instance():
        print("⚠️ Another instance is running. Activating it...")
        if instance_manager.activate_existing_instance():
            sys.exit(0)
        else:
            print("⚠️ Could not activate existing instance. Exiting anyway.")
            sys.exit(0)
            
    # Keep reference to prevent GC
    # instance_manager.mutex is held open as long as this object exists
    
    # CRITICAL: Set Windows AppUserModelID BEFORE creating QApplication
    # This ensures the taskbar icon displays correctly instead of showing Python icon
    try:
        import ctypes
        myappid = 'mon.toolhub.main.1.0'  # Arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        print(f"✓ Windows AppUserModelID set: {myappid}")
    except Exception as e:
        print(f"⚠️ Could not set AppUserModelID: {e}")
    
    app = QApplication(sys.argv)
    
    # ✅ Set Application Icon (for all windows)
    from PySide6.QtGui import QIcon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        print(f"✓ Application icon set: {icon_path}")
    else:
        print(f"⚠️ Application icon not found: {icon_path}")
    
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
