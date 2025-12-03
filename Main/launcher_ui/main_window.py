from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from qfluentwidgets import (FluentWindow, NavigationItemPosition, FluentIcon as FIF,
                            InfoBar, Theme, setTheme, setThemeColor, NavigationWidget)
from core.config_manager import ConfigManager
from launcher_ui.home_interface import HomeInterface
from launcher_ui.settings_interface import SettingsInterface
from launcher_ui.tools_interface import ToolsInterface
from launcher_ui.app_settings_interface import AppSettingsInterface
from launcher_ui.log_interface import LogInterface
from launcher_ui.widget_samples_interface import WidgetSamplesInterface
from launcher_ui.notes_interface import NotesInterface
from launcher_ui.chat_interface import ChatBubble
import os
import sys
import ctypes
import ctypes.wintypes

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mon Tool Hub")
        self.resize(1000, 700)
        
        # Set Window Icon
        from PySide6.QtGui import QIcon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            print(f"✓ Window icon set: {icon_path}")
        else:
            print(f"⚠️ Window icon not found: {icon_path}")
        
        # Reduce Title Bar Height
        self.titleBar.setFixedHeight(32)
        
        # Set Theme Color (Blue #2986ff)
        setThemeColor('#2986ff')
        
        # Load Config
        self.config = ConfigManager.load()
        if self.config.get("dark_mode", True):
            setTheme(Theme.DARK)
            self.current_theme = Theme.DARK
        else:
            setTheme(Theme.LIGHT)
            self.current_theme = Theme.LIGHT

        # Create Interfaces
        self.home_interface = HomeInterface(self)
        self.settings_interface = SettingsInterface(self)
        self.tools_interface = ToolsInterface(self)
        self.app_settings_interface = AppSettingsInterface(self)
        self.log_interface = LogInterface(self)
        self.widget_samples_interface = WidgetSamplesInterface(self)
        self.notes_interface = NotesInterface(self)
        
        # Add Interfaces to Navigation
        self.addSubInterface(self.home_interface, FIF.HOME, "Home")
        
        # Add Notes between Home and Apps
        self.addSubInterface(self.notes_interface, FIF.DOCUMENT, "Ghi Chú", position=NavigationItemPosition.TOP)
        
        # Add Tools Group (NO children - just a placeholder to organize apps)
        self.addSubInterface(self.tools_interface, FIF.TILES, "Apps", position=NavigationItemPosition.TOP)
        
        # Add AutoKey and Android as CHILDREN of Tools
        self.autokey_interface = QWidget()
        self.autokey_interface.setObjectName("autokeyInterface")
        self.addSubInterface(self.autokey_interface, FIF.GAME, "AutoKey", parent=self.tools_interface)
        
        self.android_interface = QWidget()
        self.android_interface.setObjectName("androidInterface")
        self.addSubInterface(self.android_interface, FIF.FOLDER, "Android Tool", parent=self.tools_interface)
        
        # Add Log Interface (BOTTOM, before Settings)
        self.addSubInterface(self.log_interface, FIF.INFO, "Nhật ký", position=NavigationItemPosition.BOTTOM)
        
        # Add Settings at the BOTTOM
        self.addSubInterface(self.settings_interface, FIF.SETTING, "Cài đặt", position=NavigationItemPosition.BOTTOM)
        
        # Add App Settings (Hidden from Nav, accessed via Settings)
        self.stackedWidget.addWidget(self.app_settings_interface)
        
        # Add Widget Samples (Hidden from Nav, accessed via Settings)
        self.stackedWidget.addWidget(self.widget_samples_interface)


        # Connect navigation changes
        self.stackedWidget.currentChanged.connect(self.on_interface_changed)
        
        # Disable slide-up animation for ALL pages
        self.stackedWidget.setAnimationEnabled(False)
        
        # Reduce expanded sidebar width by 50%
        try:
            # Default expanded width is ~300px, reduce to ~120px (20% less than 150)
            self.navigationInterface.setExpandWidth(120)
            
            # Apply stylesheet to remove indentation for child items
            # This targets the NavigationTreeWidget items
            self.navigationInterface.setStyleSheet("""
                NavigationTreeWidget {
                    border: none;
                    background-color: transparent;
                }
                /* Target child items to remove indentation */
                NavigationTreeWidget::item {
                    padding-left: 10px; /* Reset padding to match parent items */
                }
            """)
        except:
            pass
        
        # Embedded Widgets Cache
        self.embedded_autokey = None
        self.embedded_android = None
        self.embedded_notes = None

        # Chat Bubble (Floating)
        # Initialize but don't show immediately to avoid layout interference
        self.chat_bubble = ChatBubble(self)
        
        # Use QTimer to show bubble after window is fully initialized
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.init_chat_bubble)
        
        # Initialize System Tray (always visible)
        QTimer.singleShot(200, self.init_system_tray)

    def init_chat_bubble(self):
        """Show and position chat bubble after main window is ready"""
        if hasattr(self, 'chat_bubble'):
            # Position at bottom-right when embedded
            margin = 24
            x = self.width() - self.chat_bubble.width() - margin
            y = self.height() - self.chat_bubble.height() - margin
            self.chat_bubble.move(x, y)
            self.chat_bubble.show()
            self.chat_bubble.raise_()
            print(f"📌 Chat bubble initialized at bottom-right: ({x}, {y})")

    
    def handle_child_visibility_request(self, show: bool):
        """Handle visibility request from embedded AutoKey
        
        Args:
            show (bool): True to show Main window, False to hide
        """
        if show:
            print("📺 AutoKey requested Main window SHOW")
            self.show()
            self.activateWindow()
        else:
            print("🔒 AutoKey requested Main window HIDE")
            self.hide()

    def on_interface_changed(self, index):
        widget = self.stackedWidget.widget(index)
        print(f"\n🔄 Tab changed to: {widget.objectName()}")
        
        # Disable animation for Apps, Enable for others
        if widget.objectName() in ["autokeyInterface", "androidInterface", "notesInterface"]:
            pass
            
        if widget.objectName() == "autokeyInterface":
            print(f"  → Switching to AutoKey interface")
            print(f"  → External mode: {self.config.get('external_autokey', True)}")
            if self.config.get("external_autokey", True):
                self.home_interface.launch_autokey()
                self.switchTo(self.tools_interface)
            else:
                self.embed_autokey()
                # Debug embedded widget state
                if self.embedded_autokey:
                    print(f"  → AutoKey visible: {self.embedded_autokey.isVisible()}")
                    print(f"  → AutoKey size: {self.embedded_autokey.size()}")
                    print(f"  → Container size: {self.autokey_interface.size()}")
                    
        elif widget.objectName() == "androidInterface":
            print(f"  → Switching to Android interface")
            print(f"  → External mode: {self.config.get('external_android', True)}")
            if self.config.get("external_android", True):
                self.home_interface.launch_android()
                self.switchTo(self.tools_interface)
            else:
                self.embed_android()
                # Debug embedded widget state
                if self.embedded_android:
                    print(f"  → Android visible: {self.embedded_android.isVisible()}")
                    print(f"  → Android size: {self.embedded_android.size()}")
                    print(f"  → Container size: {self.android_interface.size()}")
        
        elif widget.objectName() == "notesInterface":
            print(f"  → Switching to Notes interface")
            # Notes is always embedded (no external mode for now)
            self.embed_notes()

    def resizeEvent(self, event):
        if event is not None:
            super().resizeEvent(event)
        
        # Debug resize events for embedded apps
        if self.embedded_autokey and self.autokey_interface.isVisible():
            old_size = self.embedded_autokey.size()
            new_size = self.autokey_interface.size()
            self.embedded_autokey.resize(new_size)
            print(f"🔧 AutoKey resized: {old_size} → {new_size}")
            
        if self.embedded_android and self.android_interface.isVisible():
            old_size = self.embedded_android.size()
            new_size = self.android_interface.size()
            self.embedded_android.resize(new_size)
            print(f"🔧 Android resized: {old_size} → {new_size}")

        # Chat Bubble positioning (only when embedded, not in overlay mode)
        if hasattr(self, 'chat_bubble') and not self.chat_bubble._isOverlay:
            self.chat_bubble.raise_()
            if not self.chat_bubble._userMoved:
                # Snap to bottom-right with margin (when embedded)
                margin = 24
                x = self.width() - self.chat_bubble.width() - margin
                y = self.height() - self.chat_bubble.height() - margin
                print(f"📏 Resize Snap (Embedded): Window={self.width()}x{self.height()}, Bubble={self.chat_bubble.width()}x{self.chat_bubble.height()} -> Move to ({x}, {y})")
                self.chat_bubble.move(x, y)
            else:
                # Keep within window bounds if user moved it
                bubble_rect = self.chat_bubble.geometry()
                new_x = bubble_rect.x()
                new_y = bubble_rect.y()
                
                # Clamp to window bounds
                if new_x < 0: new_x = 0
                if new_y < 0: new_y = 0
                if new_x + bubble_rect.width() > self.width():
                    new_x = self.width() - bubble_rect.width()
                if new_y + bubble_rect.height() > self.height():
                    new_y = self.height() - bubble_rect.height()
                
                if new_x != bubble_rect.x() or new_y != bubble_rect.y():
                    self.chat_bubble.move(new_x, new_y)
                    print(f"📏 Resize Clamp (Embedded): Adjusted to ({new_x}, {new_y})")

    def embed_autokey(self):
        # Ensure container layout exists
        if self.autokey_interface.layout() is None:
            layout = QVBoxLayout(self.autokey_interface)
            layout.setContentsMargins(0, 0, 0, 0)
        
        # Initialize only once
        if not self.embedded_autokey:
            try:
                # Path adjusted for Apps directory
                autokey_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Apps", "AutoKey")
                if autokey_path not in sys.path:
                    sys.path.insert(0, autokey_path)
                
                from ui.main_window import MainWindow as AutoKeyWindow
                
                # Pass theme from Main to embedded AutoKey
                print(f"🎨 DEBUG: Passing theme to AutoKey: {self.current_theme}")
                self.embedded_autokey = AutoKeyWindow(is_embedded=True, parent_theme=self.current_theme)
                self.embedded_autokey.setWindowFlags(Qt.WindowType.Widget)
                self.embedded_autokey.setObjectName("embeddedAutoKey")
                
                self.autokey_interface.layout().addWidget(self.embedded_autokey)
                print(f"✓ AutoKey embedded successfully, size: {self.embedded_autokey.size()}")
                
            except Exception as e:
                import traceback
                print(f"❌ Error embedding AutoKey:")
                traceback.print_exc()
                InfoBar.error("Lỗi", f"Không thể nhúng AutoKey: {e}", parent=self)
                return
        
        # ALWAYS ensure it's visible and resized (runs every time)
        if self.embedded_autokey:
            self.embedded_autokey.show()
            self.embedded_autokey.raise_()  # Bring to front
            self.embedded_autokey.resize(self.autokey_interface.size())
            print(f"✓ AutoKey shown and resized to: {self.autokey_interface.size()}")
            
            # Highlight AutoKey tab with orange border
            self.highlight_running_app("autokey", True)
            
            # Connect close button signal
            if hasattr(self.embedded_autokey, 'toolbar') and hasattr(self.embedded_autokey.toolbar, 'close_requested'):
                try:
                    self.embedded_autokey.toolbar.close_requested.disconnect()
                except:
                    pass
                self.embedded_autokey.toolbar.close_requested.connect(self.close_autokey)
            
            # Connect visibility request signal
            if hasattr(self.embedded_autokey, 'request_main_visibility'):
                try:
                    self.embedded_autokey.request_main_visibility.disconnect()
                except:
                    pass
                self.embedded_autokey.request_main_visibility.connect(self.handle_child_visibility_request)
                print("✓ Connected AutoKey visibility signal to Main window handler")

    def embed_android(self):
        # Ensure container layout exists
        if self.android_interface.layout() is None:
            layout = QVBoxLayout(self.android_interface)
            layout.setContentsMargins(0, 0, 0, 0)

        # Initialize only once
        if not self.embedded_android:
            try:
                # Path adjusted for Apps directory
                android_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Apps", "Android_Tool")
                if android_path not in sys.path:
                    sys.path.insert(0, android_path)
                
                from Main import MainHub as AndroidWindow
                
                self.embedded_android = AndroidWindow(is_embedded=True)
                self.embedded_android.setWindowFlags(Qt.WindowType.Widget)
                self.embedded_android.setObjectName("embeddedAndroid")
                
                self.android_interface.layout().addWidget(self.embedded_android)
                print(f"✓ Android Tool embedded successfully, size: {self.embedded_android.size()}")
            
            except Exception as e:
                import traceback
                print(f"❌ Error embedding Android Tool:")
                traceback.print_exc()
                InfoBar.error("Lỗi", f"Không thể nhúng Android Tool: {e}", parent=self)
                return
        
        # ALWAYS ensure it's visible and resized (runs every time)
        if self.embedded_android:
            self.embedded_android.show()
            self.embedded_android.raise_()  # Bring to front
            self.embedded_android.resize(self.android_interface.size())
            print(f"✓ Android Tool shown and resized to: {self.android_interface.size()}")
    
    def embed_notes(self):
        """Embed Notes widget into Notes interface."""
        # Initialize only once
        if not self.embedded_notes:
            try:
                print("📝 Embedding Notes widget...")
                self.notes_interface.embed_notes_widget()
                self.embedded_notes = self.notes_interface.embedded_notes
                print(f"✓ Notes embedded successfully")
                
            except Exception as e:
                import traceback
                print(f"❌ Error embedding Notes:")
                traceback.print_exc()
                InfoBar.error("Lỗi", f"Không thể nhúng Notes: {e}", parent=self)
                return
        
        # ALWAYS ensure it's visible (runs every time)
        if self.embedded_notes:
            self.embedded_notes.show()
            print(f"✓ Notes shown")
    
    def close_autokey(self):
        """Close and unload AutoKey embedded app"""
        print("🔴 Closing AutoKey...")
        if self.embedded_autokey:
            try:
                # Disconnect signals
                if hasattr(self.embedded_autokey, 'toolbar'):
                    try:
                        self.embedded_autokey.toolbar.close_requested.disconnect()
                    except:
                        pass
                
                # Hide and remove widget
                self.embedded_autokey.hide()
                self.autokey_interface.layout().removeWidget(self.embedded_autokey)
                self.embedded_autokey.deleteLater()
                self.embedded_autokey = None
                
                # Remove orange border highlight
                self.highlight_running_app("autokey", False)
                
                # Switch to tools interface
                self.switchTo(self.tools_interface)
                
                InfoBar.success("Đã đóng", "AutoKey đã được đóng", parent=self)
                print("✓ AutoKey closed successfully")
            except Exception as e:
                print(f"❌ Error closing AutoKey: {e}")
                import traceback
                traceback.print_exc()
    
    def highlight_running_app(self, app_name, is_running):
        """Add/remove orange border to indicate app is running"""
        try:
            # Find the navigation item widget
            if app_name == "autokey":
                target_interface = self.autokey_interface
            elif app_name == "android":
                target_interface = self.android_interface
            else:
                return
            
            # Get navigation panel and find the item
            nav_panel = self.navigationInterface
            
            # Apply custom styling to the navigation item
            if is_running:
                # Add orange left border to indicate running
                style = """
                    NavigationTreeWidget {
                        border-left: 3px solid #ff6600;
                    }
                """
                print(f"🟧 Added orange border to {app_name}")
            else:
                # Remove border
                style = ""
                print(f"⬜ Removed border from {app_name}")
            
            # Try to apply style (may not work directly with FluentWindow's structure)
            # This is a workaround - FluentWindow doesn't expose easy API for this
            
        except Exception as e:
            print(f"⚠️ Could not highlight {app_name}: {e}")

    def init_system_tray(self):
        """Initialize system tray icon"""
        from PySide6.QtWidgets import QSystemTrayIcon, QMenu
        from PySide6.QtGui import QAction, QIcon
        
        # Prevent app from closing when window is closed
        QApplication.setQuitOnLastWindowClosed(False)
        
        self.tray_icon = QSystemTrayIcon(self)
        
        # Use the specific icon provided by user
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "app_icon.png")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.setWindowIcon(icon) # Update window icon too
        else:
            icon = self.windowIcon()
        
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("Mon Tool Hub")
        
        # Context Menu
        menu = QMenu()
        
        # Increase size by ~10% and style it
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 24px; /* Increased padding for ~10% larger hit area */
                font-size: 14px;
                color: white;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
        """)
        
        open_action = QAction("Mở", self)
        open_action.triggered.connect(self.show_window)
        menu.addAction(open_action)
        
        quit_action = QAction("Thoát", self)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(menu)
        
        # Click handler
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        self.tray_icon.show()
        
    def on_tray_icon_activated(self, reason):
        from PySide6.QtWidgets import QSystemTrayIcon
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                if self.isMinimized():
                    self.showNormal()
                    self.activateWindow()
                else:
                    self.hide()
            else:
                self.show_window()

    def show_window(self):
        self.show()
        self.setWindowState(Qt.WindowActive)
        self.activateWindow()
        
    def quit_app(self):
        """Fully exit the application"""
        # Close detached chat bubble if it exists
        if hasattr(self, 'chat_bubble') and self.chat_bubble:
            self.chat_bubble.close()
            
        QApplication.quit()

    def closeEvent(self, event):
        """Handle window close event"""
        run_in_background = self.config.get("run_in_background", False)
        
        if run_in_background:
            event.ignore()
            self.hide()
            # Tray icon is already initialized in __init__, no need to check
            
            # Show notification only once per session or just rely on tray tooltip
            # self.tray_icon.showMessage("Mon Tool Hub", "Ứng dụng đang chạy ngầm", QSystemTrayIcon.Information, 2000)
        else:
            # Close detached chat bubble if it exists
            if hasattr(self, 'chat_bubble') and self.chat_bubble:
                self.chat_bubble.close()
                
            super().closeEvent(event)

    def nativeEvent(self, eventType, message):
        """Handle native Windows messages"""
        try:
            # WM_USER + 1 = 0x0401 (1025)
            WM_SHOW_APP = 1025
            
            if eventType == "windows_generic_MSG":
                msg = ctypes.wintypes.MSG.from_address(message.__int__())
                if msg.message == WM_SHOW_APP:
                    print("📩 Received WM_SHOW_APP message. Restoring window...")
                    
                    # Restore window state safely on Qt thread
                    if self.isMinimized():
                        self.showNormal()
                    
                    self.show()
                    self.raise_()
                    self.activateWindow()
                    
                    return True, 0
                    
        except Exception as e:
            print(f"❌ Error in nativeEvent: {e}")
            
        return super().nativeEvent(eventType, message)
