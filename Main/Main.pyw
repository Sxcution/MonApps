import sys
import os
from datetime import datetime

# CRITICAL: Set working directory and create debug log
log_file = None
try:
    # Get Main directory
    main_root = os.path.dirname(os.path.abspath(__file__))
    
    # Create debug log
    log_path = os.path.join(main_root, "main_launch.log")
    log_file = open(log_path, "a", encoding="utf-8")
    
    def log(msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {msg}\n"
        if log_file:
            log_file.write(log_msg)
            log_file.flush()
        print(msg)
    
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
    if log_file:
        log(f"ERROR during setup: {e}")
        import traceback
        log_file.write(traceback.format_exc())
    print(f"[Main] ERROR: {e}")

# Global Exception Handler - prevents crashes from unhandled exceptions
def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Catch unhandled exceptions and display error dialog instead of crashing"""
    import traceback
    from datetime import datetime
    
    # Format exception
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # Log to file
    if log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"\n[{timestamp}] UNHANDLED EXCEPTION:\n{error_msg}\n")
        log_file.flush()
    
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
                f"Đã xảy ra lỗi:\n\n{exc_type.__name__}: {exc_value}\n\n"
                f"Chi tiết đã được ghi vào file log.\n\n"
                f"Ứng dụng sẽ tiếp tục chạy."
            )
    except:
        pass  # If Qt isn't available, just log

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
    
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
