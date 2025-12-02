from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                               QListWidgetItem, QLabel, QDialog, QFrame, QScrollArea, QSizeGrip, QPushButton, QApplication)
from PySide6.QtGui import QColor, QPainter, QPainterPath, QBrush, QPen, QMouseEvent, QPixmap, QClipboard, QKeySequence, QShortcut
from PySide6.QtCore import Qt, QPoint, Signal, QSize, QRect, QBuffer, QByteArray, QEvent

from qfluentwidgets import (CardWidget, PrimaryPushButton, PushButton, LineEdit, 
                            FluentIcon as FIF, TextEdit, InfoBar, StrongBodyLabel,
                            BodyLabel, Theme, isDarkTheme, TransparentToolButton,
                            ComboBox, ToolButton)
from core.ai_handler import AIHandler

import json
import os



class ChatSettings:
    """Data class to hold chatbot settings with persistence."""
    # Use absolute path relative to this file to ensure persistence works
    SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_settings.json")

    def __init__(self, api_keys: list = None, active_key_index: int = 0, bot_name: str = "Mon Assistant", system_rule: str = ""):
        self.api_keys = api_keys
        self.active_key_index = active_key_index
        self.bot_name = bot_name
        self.system_rule = system_rule
        
        if self.api_keys is None:
            self.api_keys = [{"name": "Default", "key": ""}]
            self.load() # Only load if no keys provided (default init)

    @property
    def current_key(self):
        if 0 <= self.active_key_index < len(self.api_keys):
            return self.api_keys[self.active_key_index]["key"]
        return ""

    def save(self):
        """Save settings to JSON file."""
        data = {
            "api_keys": self.api_keys,
            "active_key_index": self.active_key_index,
            "bot_name": self.bot_name,
            "system_rule": self.system_rule
        }
        try:
            with open(self.SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("✅ ChatSettings saved.")
        except Exception as e:
            print(f"❌ Error saving ChatSettings: {e}")

    def load(self):
        """Load settings from JSON file."""
        if not os.path.exists(self.SETTINGS_FILE):
            return
        
        try:
            with open(self.SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.api_keys = data.get("api_keys", [{"name": "Default", "key": ""}])
                self.active_key_index = data.get("active_key_index", 0)
                self.bot_name = data.get("bot_name", "Mon Assistant")
                self.system_rule = data.get("system_rule", "")
            print("✅ ChatSettings loaded.")
        except Exception as e:
            print(f"❌ Error loading ChatSettings: {e}")

class ApiKeyRow(QWidget):
    """Row widget for a single API key entry."""
    removed = Signal(QWidget)
    
    def __init__(self, name="", key="", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        
        self.name_input = LineEdit(self)
        self.name_input.setPlaceholderText("Tên (vd: Gemini)")
        self.name_input.setText(name)
        self.name_input.setFixedWidth(100)
        
        self.key_input = LineEdit(self)
        self.key_input.setPlaceholderText("API Key")
        self.key_input.setText(key)
        self.key_input.setEchoMode(LineEdit.Password)
        
        self.btn_remove = TransparentToolButton(FIF.DELETE, self)
        self.btn_remove.clicked.connect(lambda: self.removed.emit(self))
        
        layout.addWidget(self.name_input)
        layout.addWidget(self.key_input)
        layout.addWidget(self.btn_remove)

class DraggableHeader(QWidget):
    """Header widget that allows dragging the parent window."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dragging = False
        self._drag_start_pos = QPoint()
        self._window_start_pos = QPoint()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_start_pos = event.globalPosition().toPoint()
            self._window_start_pos = self.window().pos()
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            self.window().move(self._window_start_pos + delta)
            # Update _userMoved flag in ChatBubble if it exists
            if hasattr(self.window(), '_userMoved'):
                self.window()._userMoved = True
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging = False
        super().mouseReleaseEvent(event)

class SnippingOverlay(QWidget):
    """Fullscreen overlay for capturing a screenshot area."""
    captured = Signal(QPixmap)
    closed = Signal() # Signal emitted when overlay is closed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowState(Qt.WindowFullScreen)
        self.setCursor(Qt.CrossCursor)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.start_pos = None
        self.end_pos = None
        self.is_drawing = False
        
        # Capture full screen
        screen = QApplication.primaryScreen()
        self.original_pixmap = screen.grabWindow(0)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        # 1. Draw the original screenshot (background)
        painter.drawPixmap(0, 0, self.original_pixmap)
        
        # 2. Draw the dimming layer (semi-transparent black)
        painter.setBrush(QColor(0, 0, 0, 100))
        painter.setPen(Qt.NoPen)
        
        if self.start_pos and self.end_pos:
            # Draw 4 rectangles around the selection to create the "hole"
            # This avoids CompositionMode issues and ensures the selection is clear
            rect = QRect(self.start_pos, self.end_pos).normalized()
            
            # Top
            painter.drawRect(0, 0, self.width(), rect.top())
            # Bottom
            painter.drawRect(0, rect.bottom() + 1, self.width(), self.height() - rect.bottom() - 1)
            # Left
            painter.drawRect(0, rect.top(), rect.left(), rect.height())
            # Right
            painter.drawRect(rect.right() + 1, rect.top(), self.width() - rect.right() - 1, rect.height())
            
            # Draw border around selection
            painter.setPen(QPen(QColor("#0078d4"), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)
        else:
            # No selection, dim everything
            painter.drawRect(self.rect())
            
    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()
        self.setFocus()
        self.grabKeyboard() # Ensure we catch Esc key

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            self.is_drawing = True
            self.update()
        elif event.button() == Qt.RightButton:
            # Right click to cancel immediately
            self.close()
            self.closed.emit()
            
    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.end_pos = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event):
        if self.is_drawing:
            self.is_drawing = False
            self.close()
            
            # Capture the selected area
            rect = QRect(self.start_pos, self.end_pos).normalized()
            if rect.width() > 10 and rect.height() > 10:
                captured_pixmap = self.original_pixmap.copy(rect)
                self.captured.emit(captured_pixmap)
            else:
                self.closed.emit() # Emit closed if no valid capture
                
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            self.closed.emit()

class ResizeGrip(QWidget):
    """Custom grip to resize the top-level window."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.setCursor(Qt.SizeFDiagCursor)
        self.setStyleSheet("background: transparent;")
        self._dragging = False
        self._drag_start_pos = QPoint()
        self._window_start_size = QSize()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_start_pos = event.globalPosition().toPoint()
            self._window_start_size = self.window().size()

    def mouseMoveEvent(self, event):
        if self._dragging:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            new_width = max(300, self._window_start_size.width() + delta.x())
            new_height = max(400, self._window_start_size.height() + delta.y())
            self.window().resize(new_width, new_height)
            
    def mouseReleaseEvent(self, event):
        self._dragging = False

class ResizableCardWidget(CardWidget):
    """CardWidget with a built-in resize grip that resizes the top-level window."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.size_grip = ResizeGrip(self)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        rect = self.rect()
        # Position in bottom-right corner
        self.size_grip.move(rect.right() - self.size_grip.width(), rect.bottom() - self.size_grip.height())
        self.size_grip.raise_()


class ChatSettingsDialog(QDialog):
    """Dialog to configure chatbot settings."""
    def __init__(self, settings: ChatSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Cài đặt Chatbot")
        self.resize(500, 600)
        
        # Fix black background by setting a theme-aware background
        bg_color = "#2b2b2b" if isDarkTheme() else "#f9f9f9"
        self.setStyleSheet(f"QDialog {{ background-color: {bg_color}; }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = StrongBodyLabel("Cấu hình Trợ lý AI", self)
        layout.addWidget(title)
        
        # Bot Name
        layout.addWidget(BodyLabel("Tên Bot:", self))
        self.bot_name_input = LineEdit(self)
        self.bot_name_input.setPlaceholderText("Tên Bot")
        self.bot_name_input.setText(self.settings.bot_name)
        layout.addWidget(self.bot_name_input)
        
        # API Keys Section
        layout.addWidget(BodyLabel("Danh sách API Key:", self))
        
        self.keys_list = QListWidget(self)
        self.keys_list.setSelectionMode(QListWidget.NoSelection)
        self.keys_list.setStyleSheet("QListWidget { background: transparent; border: 1px solid #ddd; border-radius: 5px; }")
        if isDarkTheme():
             self.keys_list.setStyleSheet("QListWidget { background: transparent; border: 1px solid #444; border-radius: 5px; }")
             
        layout.addWidget(self.keys_list)
        
        # Active Key Selection (Initialize BEFORE adding keys)
        layout.addWidget(BodyLabel("Key đang dùng:", self))
        self.combo_active = ComboBox(self)
        layout.addWidget(self.combo_active)

        # Add existing keys
        for item in self.settings.api_keys:
            self.add_key_row(item["name"], item["key"])
            
        # Add Button
        self.btn_add_key = PushButton("Thêm API Key", self)
        self.btn_add_key.setIcon(FIF.ADD)
        self.btn_add_key.clicked.connect(lambda: self.add_key_row("", ""))
        layout.addWidget(self.btn_add_key)
        
        # Set initial selection
        if 0 <= self.settings.active_key_index < self.combo_active.count():
            self.combo_active.setCurrentIndex(self.settings.active_key_index)
        
        # System Rule
        layout.addWidget(BodyLabel("Luật hệ thống:", self))
        self.rule_input = TextEdit(self)
        self.rule_input.setPlaceholderText("Luật / System Prompt...")
        self.rule_input.setText(self.settings.system_rule)
        layout.addWidget(self.rule_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = PrimaryPushButton("Lưu", self)
        self.btn_cancel = PushButton("Hủy", self)
        
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def add_key_row(self, name, key):
        item = QListWidgetItem(self.keys_list)
        row = ApiKeyRow(name, key)
        item.setSizeHint(row.sizeHint())
        
        row.removed.connect(lambda w: self.remove_key_row(item))
        row.name_input.textChanged.connect(self.update_combo_items)
        
        self.keys_list.addItem(item)
        self.keys_list.setItemWidget(item, row)
        self.update_combo_items()

    def remove_key_row(self, item):
        row = self.keys_list.row(item)
        self.keys_list.takeItem(row)
        self.update_combo_items()

    def update_combo_items(self):
        current_idx = self.combo_active.currentIndex()
        self.combo_active.clear()
        for i in range(self.keys_list.count()):
            item = self.keys_list.item(i)
            widget = self.keys_list.itemWidget(item)
            name = widget.name_input.text() or f"Key {i+1}"
            self.combo_active.addItem(name)
        
        if current_idx < self.combo_active.count():
            self.combo_active.setCurrentIndex(current_idx)

    def get_settings(self) -> ChatSettings:
        keys = []
        for i in range(self.keys_list.count()):
            item = self.keys_list.item(i)
            widget = self.keys_list.itemWidget(item)
            keys.append({
                "name": widget.name_input.text().strip(),
                "key": widget.key_input.text().strip()
            })
            
        if not keys:
            keys.append({"name": "Default", "key": ""})
            
        return ChatSettings(
            api_keys=keys,
            active_key_index=self.combo_active.currentIndex(),
            bot_name=self.bot_name_input.text().strip() or "Mon Assistant",
            system_rule=self.rule_input.toPlainText().strip()
        )

class DraggableButton(QPushButton):
    """A PushButton that can be dragged to move its parent ChatBubble."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dragging = False
        self._drag_start_pos = QPoint()
        self._widget_start_pos = QPoint()
        self._chat_bubble = None
        
    def _find_chat_bubble(self):
        """Find the ChatBubble parent widget."""
        parent = self.parent()
        while parent:
            if isinstance(parent, ChatBubble):
                return parent
            parent = parent.parent()
        return None
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.globalPosition().toPoint()
            
            # Find ChatBubble widget to move
            if not self._chat_bubble:
                self._chat_bubble = self._find_chat_bubble()
            
            if self._chat_bubble:
                self._widget_start_pos = self._chat_bubble.pos()
                self._dragging = True
            
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton and self._dragging and self._chat_bubble:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            if delta.manhattanLength() > 5: # Threshold to distinguish click vs drag
                self._chat_bubble.move(self._widget_start_pos + delta)
                self._chat_bubble._userMoved = True
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging = False
        super().mouseReleaseEvent(event)

class ChatBubble(QWidget):
    """
    Modern floating chat bubble (Circular, Elevated, Beautiful)
    Has two states: Collapsed (Bubble) and Expanded (Chat Window).
    """
    messageSent = Signal(str)

    def __init__(self, parent=None):
        # Pass None to super() to make it a top-level window, 
        # but keep 'parent' reference for logical connection if needed
        super().__init__(None) 
        self.main_window = parent # Store reference to main window
        self.settings = ChatSettings()
        self._userMoved = False
        self._isExpanded = False
        self._userMoved = False
        self._isExpanded = False
        self._dragPos = QPoint()
        
        # Resize state
        self._resizing = False
        self._resize_edge = None
        self._resize_start_pos = QPoint()
        self._resize_start_geo = None
        self.setMouseTracking(True) # Enable mouse tracking for cursor update
        
        # Initialize AI Handler
        self.ai_handler = AIHandler(self.settings.current_key)
        
        # Setup UI
        # Qt.Tool makes it float nicely without a taskbar entry (optional)
        # Qt.WindowStaysOnTopHint keeps it above other windows
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        self.layout.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        
        # 1. Chat Card (Expanded State) - Initially Hidden
        self.chat_card = ResizableCardWidget(self)
        self.chat_card.setMinimumSize(300, 400)
        self.chat_card.resize(350, 500) # Initial size
        # Set gray background to match Main window
        self.chat_card.setStyleSheet("""
            CardWidget {
                background-color: #2b2b2b;
                border-radius: 10px;
            }
        """)
        self.chat_card.hide()
        
        self._setup_chat_card()
        self.layout.addWidget(self.chat_card)
        
        # 2. Bubble Button (Collapsed State) - Modern Circular Design
        self.bubble_btn = DraggableButton(self)
        self.bubble_btn.setObjectName("ChatBubbleBtn") # ID for specific styling
        self.bubble_btn.setIcon(FIF.CHAT.icon())
        self.bubble_btn.setIconSize(QSize(20, 20)) # Reduced icon size
        self.bubble_btn.setFixedSize(42, 42) # Reduced size by ~30% (60 -> 42)
        
        # ✅ Modern circular style with gradient and glow
        # Using ID selector #ChatBubbleBtn to prevent theme overrides
        self.bubble_btn.setStyleSheet("""
            #ChatBubbleBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0078d4, stop:1 #00bcf2);
                border: 2px solid rgba(255, 255, 255, 0.8);
                border-radius: 21px;
                padding: 0px;
            }
            #ChatBubbleBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1084d9, stop:1 #2ce0f5);
                border: 2px solid #ffffff;
            }
            #ChatBubbleBtn:pressed {
                background: #005a9e;
            }
        """)
        
        # ✅ Add drop shadow for elevated/floating effect
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 120, 212, 100)) # Blueish shadow
        shadow.setOffset(0, 4)
        self.bubble_btn.setGraphicsEffect(shadow)
        
        # Connect click to toggle
        self.bubble_btn.clicked.connect(self.toggle_chat)
        
        # Container for bubble to align it right
        bubble_container = QWidget(self)
        bubble_layout = QHBoxLayout(bubble_container)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.addStretch()
        bubble_layout.addWidget(self.bubble_btn, 0, Qt.AlignCenter)
        
        self.layout.addWidget(bubble_container)
        
        # Initial sizing
        self.adjustSize()

    def _setup_chat_card(self):
        """Build the internal layout of the chat card."""
        layout = QVBoxLayout(self.chat_card)
        layout.setContentsMargins(10, 10, 10, 5)
        layout.setSpacing(5)
        
        # --- Header ---
        # --- Header ---
        self.header = DraggableHeader(self.chat_card)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = StrongBodyLabel(self.settings.bot_name, self.header)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        self.btn_settings = TransparentToolButton(FIF.SETTING, self.header)
        self.btn_settings.setFixedSize(30, 30)
        self.btn_settings.clicked.connect(self.open_settings)
        header_layout.addWidget(self.btn_settings)
        
        self.btn_close = TransparentToolButton(FIF.CLOSE, self.header)
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.clicked.connect(self.toggle_chat)
        header_layout.addWidget(self.btn_close)
        
        layout.addWidget(self.header)
        
        # --- Chat History ---
        self.chat_list = QListWidget(self.chat_card)
        self.chat_list.setFrameShape(QFrame.NoFrame)
        self.chat_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        # ✅ Dark theme background for chat area
        self.chat_list.setStyleSheet("QListWidget { background: #2b2b2b; border-radius: 5px; }")
        layout.addWidget(self.chat_list, 1)  # Give it stretch factor to fill space
        
        # --- Image Preview Area ---
        self.image_preview_container = QWidget(self.chat_card)
        self.image_preview_container.hide()
        preview_layout = QHBoxLayout(self.image_preview_container)
        preview_layout.setContentsMargins(10, 5, 10, 5)
        
        self.image_preview_label = QLabel(self.image_preview_container)
        self.image_preview_label.setFixedSize(100, 100)
        self.image_preview_label.setScaledContents(True)
        self.image_preview_label.setStyleSheet("border: 1px solid #555; border-radius: 5px;")
        
        self.btn_clear_image = TransparentToolButton(FIF.CLOSE, self.image_preview_container)
        self.btn_clear_image.setFixedSize(24, 24)
        self.btn_clear_image.clicked.connect(self.clear_image_preview)
        
        preview_layout.addWidget(self.image_preview_label)
        preview_layout.addWidget(self.btn_clear_image, 0, Qt.AlignTop)
        preview_layout.addStretch()
        
        layout.addWidget(self.image_preview_container)
        
        # --- Input Area (moved to bottom) ---
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 5, 0, 0)
        
        # Camera Button (Snipping Tool)
        self.btn_camera = TransparentToolButton(FIF.CAMERA, self.chat_card)
        self.btn_camera.setFixedSize(36, 36)
        self.btn_camera.setIconSize(QSize(18, 18))
        self.btn_camera.setToolTip("Chụp màn hình")
        self.btn_camera.clicked.connect(self.start_snipping)
        input_layout.addWidget(self.btn_camera)
        
        self.input_box = LineEdit(self.chat_card)
        self.input_box.setPlaceholderText("Nhập tin nhắn... (Ctrl+V để dán ảnh)")
        self.input_box.setFixedHeight(40)  # Fixed height for better appearance
        self.input_box.returnPressed.connect(self.send_message)
        
        # Install event filter for Ctrl+V
        self.input_box.installEventFilter(self)
        
        # ✅ Rounded input field styling
        self.input_box.setStyleSheet("""
            LineEdit {
                border-radius: 20px;
                padding-left: 15px;
                padding-right: 15px;
                border: 1px solid #454545;
                border-bottom: 1px solid #454545;
                background-color: #1e1e1e;
            }
            LineEdit:focus {
                border: 1px solid #0078d4;
                border-bottom: 1px solid #0078d4;
                background-color: #1e1e1e;
            }
        """)
        input_layout.addWidget(self.input_box, 1)
        
        # ✅ Modern Send Button (Circular, Icon-only)
        self.btn_send = TransparentToolButton(FIF.SEND, self.chat_card)
        self.btn_send.setFixedSize(40, 40)
        self.btn_send.setIconSize(QSize(18, 18))
        self.btn_send.setToolTip("Gửi")
        self.btn_send.clicked.connect(self.send_message)
        
        # Circular send button styling
        self.btn_send.setStyleSheet("""
            TransparentToolButton {
                border-radius: 20px;
                background-color: #0078d4;
                border: none;
            }
            TransparentToolButton:hover {
                background-color: #1084d9;
                border: none;
            }
            TransparentToolButton:pressed {
                background-color: #005a9e;
            }
        """)
        input_layout.addWidget(self.btn_send, 0)
        
        layout.addLayout(input_layout, 0)  # No stretch, stays at bottom
        
        self.current_image = None # Store current image data

    def eventFilter(self, obj, event):
        if obj == self.input_box and event.type() == QEvent.KeyPress:
            if event.matches(QKeySequence.Paste):
                clipboard = QApplication.clipboard()
                mime_data = clipboard.mimeData()
                if mime_data.hasImage():
                    self.set_image_preview(clipboard.pixmap())
                    return True
        return super().eventFilter(obj, event)

    def start_snipping(self):
        """Start the snipping tool overlay."""
        self.hide() # Hide chat window
        self.snipper = SnippingOverlay()
        self.snipper.captured.connect(self.on_snip_captured)
        self.snipper.closed.connect(self.show) # Show chat window if cancelled
        self.snipper.show()
        
    def on_snip_captured(self, pixmap):
        """Handle captured screenshot."""
        self.show() # Show chat window again
        self.set_image_preview(pixmap)
        self.send_message() # Auto-send immediately
        
    def set_image_preview(self, pixmap):
        """Show image in preview area."""
        self.current_image = pixmap
        self.image_preview_label.setPixmap(pixmap)
        self.image_preview_container.show()
        self.input_box.setFocus()
        
    def clear_image_preview(self):
        """Clear the current image."""
        self.current_image = None
        self.image_preview_container.hide()

    def toggle_chat(self):
        """Toggle between expanded and collapsed states."""
        print(f"🔄 Toggle Chat: Currently Expanded={self._isExpanded}")
        
        # Capture current bottom-right position BEFORE resizing
        current_geo = self.geometry()
        bottom_right = current_geo.bottomRight()
        
        if self.chat_card.isVisible():
            self.chat_card.hide()
            self.bubble_btn.show() # Show bubble when collapsed
            self._isExpanded = False
            print("  → Hiding chat card")
        else:
            self.chat_card.show()
            self.bubble_btn.hide() # Hide bubble when expanded
            self._isExpanded = True
            self.input_box.setFocus()
            print("  → Showing chat card")
        
        self.adjustSize()
        
        # Restore position based on bottom-right anchor
        new_geo = self.geometry()
        new_top_left = QPoint(bottom_right.x() - new_geo.width() + 1, bottom_right.y() - new_geo.height() + 1)
        self.move(new_top_left)
        
        self._ensure_within_bounds()

    def _ensure_within_bounds(self):
        """Ensure the bubble stays within the screen bounds."""
        # Use screen geometry since we are now a top-level window
        screen = self.screen()
        if not screen:
            return
            
        screen_rect = screen.availableGeometry()
        my_rect = self.geometry()
        
        new_x = my_rect.x()
        new_y = my_rect.y()
        
        # Debug current pos
        print(f"📍 Checking bounds: Pos=({new_x}, {new_y}), Size={my_rect.width()}x{my_rect.height()}, Screen={screen_rect.width()}x{screen_rect.height()}")
        
        # Clamp X
        if new_x < screen_rect.left(): new_x = screen_rect.left()
        if new_x + my_rect.width() > screen_rect.right():
            new_x = screen_rect.right() - my_rect.width()
            
        # Clamp Y
        if new_y < screen_rect.top(): new_y = screen_rect.top()
        if new_y + my_rect.height() > screen_rect.bottom():
            new_y = screen_rect.bottom() - my_rect.height()
            
        if new_x != my_rect.x() or new_y != my_rect.y():
            print(f"  ⚠️ Clamping to: ({new_x}, {new_y})")
            self.move(new_x, new_y)

    def open_settings(self):
        try:
            dialog = ChatSettingsDialog(self.settings, self.window())
            if dialog.exec():
                self.settings = dialog.get_settings()
                self.settings.save() # ✅ Save to file
                self.title_label.setText(self.settings.bot_name)
                # Update API Key in AI Handler
                self.ai_handler.update_api_key(self.settings.current_key)
                InfoBar.success("Thành công", "Đã lưu cài đặt Chatbot", parent=self.window())
        except Exception as e:
            print(f"❌ Error opening settings: {e}")
            import traceback
            traceback.print_exc()
            InfoBar.error("Lỗi", f"Không thể mở cài đặt: {e}", parent=self.window())

    def send_message(self):
        text = self.input_box.text().strip()
        image = self.current_image
        
        if not text and not image:
            return
            
        # Clear input immediately
        self.input_box.clear()
        if image:
            self.clear_image_preview()
            
        # Display user message
        self.appendUserMessage(text, image)
        self.messageSent.emit(text)
        
        # Process reply
        self.request_ai_reply(text, image)

    def appendUserMessage(self, text: str, image: QPixmap = None):
        item = QListWidgetItem()
        item.setTextAlignment(Qt.AlignRight)
        
        # Create a widget for the bubble
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.addStretch()
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(5)
        
        # Add Image if present
        if image:
            img_label = QLabel()
            # Scale image for chat display
            scaled_pixmap = image.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label.setPixmap(scaled_pixmap)
            img_label.setStyleSheet("border-radius: 10px;")
            content_layout.addWidget(img_label, 0, Qt.AlignRight)
        
        # Add Text if present
        if text:
            label = BodyLabel(text, widget)
            label.setStyleSheet("""
                QLabel {
                    background-color: #2986ff;
                    color: white;
                    border-radius: 10px;
                    padding: 8px 12px;
                }
            """)
            label.setWordWrap(True)
            label.setMaximumWidth(250)
            content_layout.addWidget(label, 0, Qt.AlignRight)
            
        layout.addLayout(content_layout)
        
        item.setSizeHint(widget.sizeHint())
        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, widget)
        self.chat_list.scrollToBottom()

    def appendBotMessage(self, text: str):
        item = QListWidgetItem()
        item.setTextAlignment(Qt.AlignLeft)
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 5)
        
        label = BodyLabel(text, widget)
        
        # Theme-aware styling
        bg_color = "#3e3e3e" if isDarkTheme() else "#f0f0f0"
        text_color = "white" if isDarkTheme() else "black"
        
        label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 10px;
                padding: 8px 12px;
            }}
        """)
        label.setWordWrap(True)
        label.setMaximumWidth(250)
        
        layout.addWidget(label)
        layout.addStretch()
        
        item.setSizeHint(widget.sizeHint())
        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, widget)
        self.chat_list.scrollToBottom()

    def clearChat(self):
        self.chat_list.clear()

    def request_ai_reply(self, user_text: str, image: QPixmap = None):
        """
        Call Gemini API via AIHandler.
        """
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents() # Keep UI responsive
        
        # Convert QPixmap to bytes if present
        image_data = None
        if image:
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QBuffer.WriteOnly)
            image.save(buffer, "PNG")
            image_data = byte_array.data()
        
        reply = self.ai_handler.process_message(user_text, image_data)
        self.appendBotMessage(reply)

    # --- Edge Resizing Logic ---
    def mousePressEvent(self, event: QMouseEvent):
        if not self._isExpanded:
            super().mousePressEvent(event)
            return

        edge = self._check_edge(event.pos())
        if edge:
            self._resizing = True
            self._resize_edge = edge
            self._resize_start_pos = event.globalPosition().toPoint()
            self._resize_start_geo = self.geometry()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self._isExpanded:
            super().mouseMoveEvent(event)
            return

        if self._resizing:
            self._handle_resize(event.globalPosition().toPoint())
            event.accept()
        else:
            # Update cursor shape
            edge = self._check_edge(event.pos())
            if edge:
                if edge in ['left', 'right']:
                    self.setCursor(Qt.SizeHorCursor)
                elif edge in ['top', 'bottom']:
                    self.setCursor(Qt.SizeVerCursor)
                elif edge in ['top_left', 'bottom_right']:
                    self.setCursor(Qt.SizeFDiagCursor)
                elif edge in ['top_right', 'bottom_left']:
                    self.setCursor(Qt.SizeBDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._resizing:
            self._resizing = False
            self._resize_edge = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def _check_edge(self, pos: QPoint):
        """Check if cursor is near an edge."""
        margin = 10
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        
        edge = ""
        if y < margin: edge += "top"
        elif y > h - margin: edge += "bottom"
        
        if x < margin: 
            edge += "_" if edge else ""
            edge += "left"
        elif x > w - margin:
            edge += "_" if edge else ""
            edge += "right"
            
        return edge if edge else None

    def _handle_resize(self, global_pos: QPoint):
        """Resize window based on drag."""
        delta = global_pos - self._resize_start_pos
        geo = self._resize_start_geo
        new_geo = list(geo.getRect()) # x, y, w, h
        
        # Minimum size constraints
        min_w, min_h = 300, 400
        
        if 'right' in self._resize_edge:
            new_geo[2] = max(min_w, geo.width() + delta.x())
            
        if 'left' in self._resize_edge:
            diff = delta.x()
            if geo.width() - diff >= min_w:
                new_geo[0] = geo.x() + diff
                new_geo[2] = geo.width() - diff
                
        if 'bottom' in self._resize_edge:
            new_geo[3] = max(min_h, geo.height() + delta.y())
            
        if 'top' in self._resize_edge:
            diff = delta.y()
            if geo.height() - diff >= min_h:
                new_geo[1] = geo.y() + diff
                new_geo[3] = geo.height() - diff
                
        self.setGeometry(*new_geo)
        # Resize internal card to match
        self.chat_card.resize(new_geo[2], new_geo[3])
