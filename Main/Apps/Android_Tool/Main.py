"""
Main Hub - Module Manager
Version: 1.0
By: Mon

Quản lý tất cả các tool modules trong một giao diện duy nhất.
"""
import sys
import os
import io
import json
import logging
import traceback
from datetime import datetime
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, 
    QVBoxLayout, QLabel, QMessageBox, QPushButton, QHBoxLayout, QMenu,
    QSplitter, QTextEdit, QScrollBar
)
from PySide6.QtGui import QFont, QIcon, QAction, QCursor, QTextCursor
from PySide6.QtCore import Qt

# Icon path
ICONS_DIR = os.path.join(os.path.dirname(__file__), "icons")

def get_icon(icon_name):
    """Get QIcon from icons folder."""
    icon_path = os.path.join(ICONS_DIR, f"{icon_name}.png")
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    return None


class AutoScrollTextEdit(QTextEdit):
    """QTextEdit with auto-scroll to bottom when text is appended."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Connect textChanged to auto-scroll
        self.textChanged.connect(self.auto_scroll)
    
    def auto_scroll(self):
        """Scroll to bottom automatically."""
        # Get the vertical scrollbar
        scrollbar = self.verticalScrollBar()
        # Scroll to maximum (bottom)
        scrollbar.setValue(scrollbar.maximum())
    
    def append(self, text):
        """Override append to ensure cursor at end before appending."""
        # Move cursor to end
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)
        # Append text
        super().append(text)

# =============================================================================
# LOGGING SYSTEM
# =============================================================================
class CrashLogger:
    """Quản lý logging và crash reports."""
    
    def __init__(self):
        # Tạo thư mục logs
        self.logs_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Tạo log file với timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.logs_dir, f"app_log_{timestamp}.txt")
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration."""
        # File handler only - không log vào terminal
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S'))
        
        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler]
        )
        
        # Suppress verbose DEBUG logs from external libraries
        logging.getLogger('telethon').setLevel(logging.WARNING)
        logging.getLogger('PySide6').setLevel(logging.WARNING)
        logging.info("=" * 60)
        logging.info("🚀 TOOL HUB STARTED")
        logging.info("=" * 60)
    
    def log_exception(self, exc_type, exc_value, exc_traceback):
        """Log uncaught exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logging.critical("❌ UNCAUGHT EXCEPTION:", exc_info=(exc_type, exc_value, exc_traceback))
        logging.critical("=" * 60)
    
    def get_latest_log(self):
        """Get path to latest log file."""
        return self.log_file
    
    def open_latest_log(self):
        """Open latest log file in default text editor."""
        try:
            if sys.platform == "win32":
                os.startfile(self.log_file)
            elif sys.platform == "darwin":  # macOS
                os.system(f"open '{self.log_file}'")
            else:  # Linux
                os.system(f"xdg-open '{self.log_file}'")
            logging.info(f"📂 Opened log file: {self.log_file}")
        except Exception as e:
            logging.error(f"❌ Could not open log file: {e}")

# Initialize global logger
crash_logger = CrashLogger()

# Set exception hook
sys.excepthook = crash_logger.log_exception

# Add modules directory to path
modules_dir = os.path.join(os.path.dirname(__file__), "modules")
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

# Import các module tools
try:
    # Import ModAndroid tool
    import importlib.util
    
    # Load ModAndroid module from modules/ModAndroid/ directory
    modandroid_path = os.path.join(modules_dir, "ModAndroid", "ModAndroid.pyw")
    spec = importlib.util.spec_from_file_location("ModAndroid", modandroid_path)
    modandroid_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modandroid_module)
    
    # Get MainWindow class from ModAndroid
    MainWindowModAndroid = modandroid_module.MainWindow
    HAS_MODANDROID = True
except Exception as e:
    logging.warning(f"Warning: Không load được ModAndroid module: {e}")
    HAS_MODANDROID = False

# Import Telegram module (nếu có)
try:
    telegram_module_path = os.path.join(modules_dir, "Telegram", "telegram_module.py")
    if os.path.exists(telegram_module_path):
        spec_telegram = importlib.util.spec_from_file_location("telegram_module", telegram_module_path)
        telegram_module = importlib.util.module_from_spec(spec_telegram)
        spec_telegram.loader.exec_module(telegram_module)
        TelegramToolWidget = telegram_module.TelegramToolWidget
        HAS_TELEGRAM = True
    else:
        HAS_TELEGRAM = False
        print("Warning: Không tìm thấy telegram_module.py")
except Exception as e:
    HAS_TELEGRAM = False
    print(f"Warning: Không load được telegram_module: {e}")




class MainHub(QMainWindow):
    """Main window quản lý tất cả các tool modules."""
    
    def __init__(self, is_embedded=False):
        super().__init__()
        self.is_embedded = is_embedded
        self.setWindowTitle("🚀 Tool Hub - Module Manager v1.0 by Mon")
        
        # Window settings file
        self.window_settings_file = os.path.join(os.path.dirname(__file__), "window_settings.json")
        
        if not self.is_embedded:
            # Load window size from settings or use default
            self.load_window_settings()
            self.setMinimumSize(1000, 600)
            self.center_window()
        else:
            # If embedded, just set a reasonable minimum size for the widget
            self.setMinimumSize(800, 500)
        
        # Apply global dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QWidget {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QLineEdit {
                background-color: #0d0d0d;
                color: #ffffff;
                border: 2px solid #333333;
                padding: 5px;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 2px solid #00aaff;
                box-shadow: 0 0 8px #00aaff;
            }
            QTextEdit {
                background-color: #0d0d0d;
                color: #ffffff;
                border: 2px solid #333333;
                border-radius: 3px;
            }
            QTextEdit:focus {
                border: 2px solid #00aaff;
                box-shadow: 0 0 8px #00aaff;
            }
            QPushButton {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #333333;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                border: 1px solid #444444;
            }
            QPushButton:pressed {
                background-color: #0d0d0d;
            }
            QPushButton:checked {
                background-color: #2a2a2a;
                border: 1px solid #555555;
            }
            QPushButton:disabled {
                background-color: #0d0d0d;
                color: #555555;
            }
            QComboBox {
                background-color: #0d0d0d;
                color: #ffffff;
                border: 2px solid #333333;
                padding: 5px;
                border-radius: 3px;
            }
            QComboBox:focus {
                border: 2px solid #00aaff;
                box-shadow: 0 0 8px #00aaff;
            }
            QComboBox:hover {
                border: 2px solid #555555;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #1a1a1a;
            }
            QComboBox QAbstractItemView {
                background-color: #0d0d0d;
                color: #ffffff;
                selection-background-color: #2a2a2a;
                border: 1px solid #333333;
            }
            QTableWidget {
                background-color: #0d0d0d;
                color: #ffffff;
                border: 1px solid #333333;
                gridline-color: #222222;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #2a2a2a;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #333333;
            }
            QCheckBox {
                color: #ffffff;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #555555;
                border-radius: 4px;
                background-color: #1a1a1a;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #00aaff;
                background-color: #2a2a2a;
            }
            QCheckBox::indicator:checked {
                background-color: #1a1a1a;
                border: 2px solid #00aaff;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #0099dd;
                border: 2px solid #0099dd;
            }
            QLabel {
                color: #ffffff;
            }
            QListWidget {
                background-color: #0d0d0d;
                color: #ffffff;
                border: 1px solid #333333;
            }
            QListWidget::item:selected {
                background-color: #2a2a2a;
            }
            QScrollBar:vertical {
                background-color: #0d0d0d;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #333333;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #444444;
            }
            QScrollBar:horizontal {
                background-color: #0d0d0d;
                height: 12px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background-color: #333333;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #444444;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                border: none;
                background: none;
            }
            QMenu {
                background-color: #0d0d0d;
                color: #ffffff;
                border: 1px solid #333333;
            }
            QMenu::item:selected {
                background-color: #2a2a2a;
            }
            QMessageBox {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QMessageBox QPushButton {
                min-width: 80px;
            }
            QDateTimeEdit {
                background-color: #0d0d0d;
                color: #ffffff;
                border: 1px solid #333333;
                padding: 5px;
                border-radius: 3px;
            }
            QDateTimeEdit::drop-down {
                background-color: #1a1a1a;
                border: none;
            }
            QCalendarWidget {
                background-color: #0d0d0d;
                color: #ffffff;
            }
            QCalendarWidget QTableView {
                background-color: #0d0d0d;
                color: #ffffff;
                selection-background-color: #2a2a2a;
            }
            QSpinBox {
                background-color: #0d0d0d;
                color: #ffffff;
                border: 1px solid #333333;
                padding: 5px;
                border-radius: 3px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #1a1a1a;
                border: none;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #2a2a2a;
            }
            QTabBar::tab {
                outline: none !important;
                border: 2px solid #404040;
                border-radius: 6px;
                padding: 6px 12px;
                margin: 2px;
                background-color: #2d2d2d;
                color: #aaaaaa;
            }
            QTabBar::tab:focus {
                outline: none !important;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabWidget:focus {
                outline: none !important;
                border: none !important;
            }
            QTabBar::tab:selected {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 2px solid #00aaff !important;
                box-shadow: 0 0 10px #00aaff, inset 0 0 5px #00aaff;
                outline: none !important;
            }
            QTabBar::tab:hover:!selected {
                background-color: #353535;
                border: 2px solid #555555;
            }
            QTabBar:focus {
                outline: none !important;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter (Trái: Tabs, Phải: Log chức năng)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === LEFT SIDE: Tab Widget ===
        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")  # Set ID để target RIÊNG
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        
        # CHỈ tăng tab CHÍNH - KHÔNG ảnh hưởng tabs con bên trong ModAndroid
        # Dùng #objectName selector để KHÔNG cascade xuống nested tabs
        # Tăng chiều cao +10% bằng padding (từ 8px -> 9px)
        self.tabs.setStyleSheet("""
            #mainTabs > QTabBar::tab {
                font-size: 12pt;
                font-weight: 500;
                padding: 9px 16px;
                margin-right: 4px;
                margin-top: 4px;
                border-radius: 8px;
                background-color: #2d2d2d;
                color: #aaaaaa;
                border: 2px solid #404040;
                outline: none !important;
            }
            
            #mainTabs > QTabBar::tab:selected {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 2px solid #00aaff !important;
                box-shadow: 0 0 12px #00aaff, inset 0 0 6px #00aaff;
                outline: none !important;
            }
            
            #mainTabs > QTabBar::tab:hover:!selected {
                background-color: #353535;
                color: #dddddd;
                border: 2px solid #555555;
            }
            
            #mainTabs > QTabBar::tab:focus {
                outline: none !important;
            }
            
            #mainTabs::pane {
                border: 1px solid #555555;
                background-color: #2d2d2d;
            }
        """)
        
        # Settings button ở góc phải cùng hàng với tabs
        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.setFont(QFont('Segoe UI', 9))
        self.settings_btn.setMaximumWidth(100)
        self.settings_btn.clicked.connect(self.show_settings_menu)
        self.tabs.setCornerWidget(self.settings_btn, Qt.Corner.TopRightCorner)
        
        # === RIGHT SIDE: Shared Log Panel cho các chức năng ===
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(5, 5, 5, 5)
        
        # Log header
        log_header = QLabel("📋 Function Log Output")
        log_header.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
        log_layout.addWidget(log_header)
        
        # Shared log display with auto-scroll
        self.shared_log = AutoScrollTextEdit()
        self.shared_log.setReadOnly(True)
        self.shared_log.setFont(QFont('Consolas', 9))
        self.shared_log.setStyleSheet("""
            QTextEdit {
                background-color: #000000;
                color: #00ff00;
                border: 1px solid #333;
            }
        """)
        log_layout.addWidget(self.shared_log)
        
        # Clear log button
        clear_btn = QPushButton("🗑️ Clear Log")
        clear_btn.clicked.connect(lambda: self.shared_log.clear())
        clear_btn.setMaximumWidth(120)
        log_layout.addWidget(clear_btn)
        
        # Add welcome tab
        self.add_welcome_tab()
        
        
        # Add ModAndroid tab (MUST be after shared_log is created)
        if HAS_MODANDROID:
            self.add_modandroid_tab()
        
        # Add Telegram tab
        if HAS_TELEGRAM:
            self.add_telegram_tab()
        
        # Add placeholder for future modules
        self.add_placeholder_tab("💬 Module 3", "Module 3 sẽ được thêm vào đây...", "wechat")
        self.add_placeholder_tab("🔧 Module 4", "Module 4 sẽ được thêm vào đây...", "settings")
        
        # Add to splitter
        splitter.addWidget(self.tabs)
        splitter.addWidget(log_container)
        
        # Set initial sizes (65% tabs, 35% log)
        splitter.setSizes([780, 420])
        
        main_layout.addWidget(splitter)
        
        # Show startup message
        self.show_startup_info()
    
    def center_window(self):
        """Center window on screen."""
        if self.screen():
            screen_geometry = self.screen().availableGeometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)
    
    def load_window_settings(self):
        """Load window size and position from settings file."""
        try:
            if os.path.exists(self.window_settings_file):
                with open(self.window_settings_file, 'r') as f:
                    settings = json.load(f)
                    
                # Get saved size
                width = settings.get('width', 1200)
                height = settings.get('height', 700)
                x = settings.get('x', 100)
                y = settings.get('y', 100)
                
                # Apply saved geometry
                self.setGeometry(x, y, width, height)
                logging.info(f"📐 Đã load kích thước cửa sổ: {width}x{height}")
            else:
                # Default size for first time
                self.setGeometry(100, 100, 1200, 700)
                logging.info("📐 Sử dụng kích thước mặc định: 1200x700")
        except Exception as e:
            logging.error(f"❌ Lỗi khi load window settings: {e}")
            self.setGeometry(100, 100, 1200, 700)
    
    def save_window_settings(self):
        """Save window size and position to settings file."""
        try:
            settings = {
                'width': self.width(),
                'height': self.height(),
                'x': self.x(),
                'y': self.y()
            }
            
            with open(self.window_settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
                
            logging.info(f"💾 Đã lưu kích thước cửa sổ: {self.width()}x{self.height()}")
        except Exception as e:
            logging.error(f"❌ Lỗi khi lưu window settings: {e}")
    
    def closeEvent(self, event):
        """Handle window close event - save settings before closing."""
        self.save_window_settings()
        logging.info("👋 Đóng tool - Đã lưu cài đặt")
        event.accept()
    
    def add_welcome_tab(self):
        """Add welcome/home tab."""
        welcome_widget = QWidget()
        layout = QVBoxLayout(welcome_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title
        title = QLabel("🚀 TOOL HUB - MODULE MANAGER")
        title.setFont(QFont('Segoe UI', 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("by Mon - Version 1.0")
        subtitle.setFont(QFont('Segoe UI', 10))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)
        
        # Description
        description = QLabel(
            "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Quản lý tất cả các tool modules trong một giao diện\n\n"
            "📱 Mod Android - Công cụ mod ROM Android\n"
            "💬 Telegram - Công cụ quản lý Telegram\n"
            "🔧 Và nhiều module khác...\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Chọn tab phía trên để bắt đầu sử dụng!"
        )
        description.setFont(QFont('Segoe UI', 10))
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setStyleSheet("color: #333; line-height: 1.6;")
        layout.addWidget(description)
        
        # Add tab with icon
        icon = get_icon('home')
        if icon:
            self.tabs.addTab(welcome_widget, icon, "Trang chủ")
        else:
            self.tabs.addTab(welcome_widget, "🏠 Trang chủ")
    
    def add_modandroid_tab(self):
        """Add ModAndroid tool tab."""
        try:
            # Create ModAndroid widget instance
            modandroid_widget = MainWindowModAndroid()
            
            # Remove window decorations since it's embedded
            modandroid_widget.setWindowFlags(Qt.WindowType.Widget)
            
            # Remove fixed size constraint to allow resizing
            from PySide6.QtWidgets import QSizePolicy
            modandroid_widget.setMinimumSize(700, 550)  # Set minimum instead of fixed
            modandroid_widget.setMaximumSize(16777215, 16777215)  # Remove max limit
            modandroid_widget.setSizePolicy(
                QSizePolicy.Policy.Expanding, 
                QSizePolicy.Policy.Expanding
            )
            
            # Share log display với ModAndroid - REDIRECT tất cả log outputs
            if hasattr(modandroid_widget, 'set_shared_log_output'):
                modandroid_widget.set_shared_log_output(self.shared_log)
                logging.info("📱 Shared log output connected to ModAndroid")
            
            # Store reference
            self.modandroid_widget = modandroid_widget
            
            # Add to tabs with icon
            icon = get_icon('android')
            if icon:
                self.tabs.addTab(modandroid_widget, icon, "Mod Android")
            else:
                self.tabs.addTab(modandroid_widget, "📱 Mod Android")
            
            logging.info("✅ ModAndroid module loaded successfully")
        except Exception as e:
            error_widget = self.create_error_widget(
                "📱 Mod Android",
                f"Lỗi khi load ModAndroid module:\n{str(e)}"
            )
            icon = get_icon('android')
            if icon:
                self.tabs.addTab(error_widget, icon, "Mod Android")
            else:
                self.tabs.addTab(error_widget, "📱 Mod Android")
            print(f"❌ Error loading ModAndroid: {e}")
    
    def add_telegram_tab(self):
        """Add Telegram tool tab."""
        try:
            telegram_widget = TelegramToolWidget()
            
            # Create custom logging handler to redirect Telegram logs to shared_log
            telegram_logger = logging.getLogger('telegram_module')
            telegram_logger.setLevel(logging.INFO)
            
            # Custom handler to write to shared_log panel
            class SharedLogHandler(logging.Handler):
                def __init__(self, log_widget):
                    super().__init__()
                    self.log_widget = log_widget
                    
                def emit(self, record):
                    try:
                        msg = self.format(record)
                        # Only show INFO and higher, skip timestamps
                        if record.levelno >= logging.INFO:
                            # Extract just the message part (after timestamp)
                            if '|' in msg:
                                msg = msg.split('|', 2)[-1].strip()
                            self.log_widget.append(msg)
                    except:
                        pass
            
            # Add handler to telegram logger
            handler = SharedLogHandler(self.shared_log)
            handler.setFormatter(logging.Formatter('%(message)s'))
            telegram_logger.addHandler(handler)
            
            # Store handler reference to prevent garbage collection
            telegram_widget._log_handler = handler
            
            # Add tab with icon
            icon = get_icon('telegram')
            if icon:
                self.tabs.addTab(telegram_widget, icon, "Telegram")
            else:
                self.tabs.addTab(telegram_widget, "💬 Telegram")
            logging.info("✅ Telegram module loaded successfully")
        except Exception as e:
            error_widget = self.create_error_widget(
                "💬 Telegram",
                f"Lỗi khi load Telegram module:\n{str(e)}"
            )
            icon = get_icon('telegram')
            if icon:
                self.tabs.addTab(error_widget, icon, "Telegram")
            else:
                self.tabs.addTab(error_widget, "💬 Telegram")
            logging.error(f"❌ Error loading Telegram: {e}")
    

    
    def add_placeholder_tab(self, tab_name, description, icon_file='module'):
        """Add placeholder tab for future modules."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label = QLabel(f"🔧 {description}")
        label.setFont(QFont('Segoe UI', 12))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #999;")
        layout.addWidget(label)
        
        info = QLabel("\nModule này sẽ được phát triển trong tương lai.")
        info.setFont(QFont('Segoe UI', 9))
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #bbb;")
        layout.addWidget(info)
        
        # Add tab with icon
        icon = get_icon(icon_file)
        clean_name = tab_name.split()[-1] if ' ' in tab_name else tab_name
        if icon:
            self.tabs.addTab(widget, icon, clean_name)
        else:
            self.tabs.addTab(widget, tab_name)
    
    def show_settings_menu(self):
        """Show settings dropdown menu."""
        menu = QMenu(self)
        
        # View Log action
        view_log_action = QAction("📄 View Log", self)
        view_log_action.triggered.connect(self.open_latest_log)
        menu.addAction(view_log_action)
        
        # Open logs folder action
        open_logs_folder_action = QAction("📂 Open Logs Folder", self)
        open_logs_folder_action.triggered.connect(self.open_logs_folder)
        menu.addAction(open_logs_folder_action)
        
        menu.addSeparator()
        
        # About action
        about_action = QAction("ℹ️ About", self)
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)
        
        # Show menu at button position
        menu.exec(QCursor.pos())
    
    def open_latest_log(self):
        """Open latest log file."""
        crash_logger.open_latest_log()
        logging.info("📂 User opened log file")
    
    def open_logs_folder(self):
        """Open logs folder."""
        try:
            logs_dir = crash_logger.logs_dir
            if sys.platform == "win32":
                os.startfile(logs_dir)
            elif sys.platform == "darwin":  # macOS
                os.system(f"open '{logs_dir}'")
            else:  # Linux
                os.system(f"xdg-open '{logs_dir}'")
            logging.info(f"📂 Opened logs folder: {logs_dir}")
        except Exception as e:
            logging.error(f"❌ Could not open logs folder: {e}")
            QMessageBox.warning(self, "Lỗi", f"Không thể mở thư mục logs:\n{e}")
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Tool Hub",
            f"<h3>🚀 Tool Hub - Module Manager</h3>"
            f"<p><b>Version:</b> 1.0</p>"
            f"<p><b>Author:</b> Mon</p>"
            f"<p><b>AI Assistant:</b> Claude Sonnet 4.5 (Anthropic)</p>"
            f"<p>Quản lý tất cả các tool modules Android trong một giao diện duy nhất.</p>"
            f"<p><b>Log file:</b><br>{crash_logger.get_latest_log()}</p>"
        )
    
    def create_error_widget(self, module_name, error_message):
        """Create error display widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        error_label = QLabel(f"❌ Lỗi load module: {module_name}")
        error_label.setFont(QFont('Segoe UI', 12, QFont.Weight.Bold))
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: #ff0000;")
        layout.addWidget(error_label)
        
        detail_label = QLabel(error_message)
        detail_label.setFont(QFont('Consolas', 9))
        detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail_label.setStyleSheet("color: #666;")
        detail_label.setWordWrap(True)
        layout.addWidget(detail_label)
        
        return widget
    
    def show_startup_info(self):
        """Show startup information."""
        loaded_modules = []
        failed_modules = []
        
        if HAS_MODANDROID:
            loaded_modules.append("📱 Mod Android")
        else:
            failed_modules.append("📱 Mod Android")
        
        if HAS_TELEGRAM:
            loaded_modules.append("💬 Telegram")
        else:
            failed_modules.append("💬 Telegram")
        
        # Log to file only, not terminal
        logging.info("="*60)
        logging.info("🚀 TOOL HUB - MODULE MANAGER v1.0")
        logging.info("="*60)
        
        if loaded_modules:
            logging.info(f"✅ Loaded modules ({len(loaded_modules)}):")
            for module in loaded_modules:
                logging.info(f"   - {module}")
        
        if failed_modules:
            logging.info(f"⚠️ Failed to load ({len(failed_modules)}):")
            for module in failed_modules:
                logging.info(f"   - {module}")
        
        logging.info("="*60)


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Tool Hub - Module Manager")
    app.setOrganizationName("Mon")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = MainHub()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

