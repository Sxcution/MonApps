from PySide6.QtCore import Qt, QPoint, Signal, QSize
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                               QListWidgetItem, QLabel, QDialog, QFrame, QScrollArea)
from PySide6.QtGui import QColor, QPainter, QPainterPath, QBrush, QPen, QMouseEvent

from qfluentwidgets import (CardWidget, PrimaryPushButton, PushButton, LineEdit, 
                            FluentIcon as FIF, TextEdit, InfoBar, StrongBodyLabel,
                            BodyLabel, Theme, isDarkTheme, TransparentToolButton,
                            ComboBox)

class ChatSettings:
    """Data class to hold chatbot settings."""
    def __init__(self, api_keys: list = None, active_key_index: int = 0, bot_name: str = "Mon Assistant", system_rule: str = ""):
        self.api_keys = api_keys or [{"name": "Default", "key": ""}]  # List of dicts: {"name": "...", "key": "..."}
        self.active_key_index = active_key_index
        self.bot_name = bot_name
        self.system_rule = system_rule

    @property
    def current_key(self):
        if 0 <= self.active_key_index < len(self.api_keys):
            return self.api_keys[self.active_key_index]["key"]
        return ""

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
        
        # Add existing keys
        for item in self.settings.api_keys:
            self.add_key_row(item["name"], item["key"])
            
        # Add Button
        self.btn_add_key = PushButton("Thêm API Key", self)
        self.btn_add_key.setIcon(FIF.ADD)
        self.btn_add_key.clicked.connect(lambda: self.add_key_row("", ""))
        layout.addWidget(self.btn_add_key)
        
        # Active Key Selection
        layout.addWidget(BodyLabel("Key đang dùng:", self))
        self.combo_active = ComboBox(self)
        self.update_combo_items()
        if 0 <= self.settings.active_key_index < self.combo_active.count():
            self.combo_active.setCurrentIndex(self.settings.active_key_index)
        layout.addWidget(self.combo_active)
        
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

class ChatBubble(QWidget):
    """
    Floating chat bubble widget that sits on top of the MainWindow.
    Has two states: Collapsed (Bubble) and Expanded (Chat Window).
    """
    messageSent = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = ChatSettings()
        self._userMoved = False
        self._isExpanded = False
        self._dragPos = QPoint()
        
        # Setup UI
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        self.layout.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        
        # 1. Chat Card (Expanded State) - Initially Hidden
        self.chat_card = CardWidget(self)
        self.chat_card.setFixedSize(350, 500)
        self.chat_card.hide()
        
        self._setup_chat_card()
        self.layout.addWidget(self.chat_card)
        
        # 2. Bubble Button (Collapsed State)
        self.bubble_btn = PrimaryPushButton(self)
        self.bubble_btn.setIcon(FIF.CHAT)
        self.bubble_btn.setFixedSize(60, 60)
        self.bubble_btn.setIconSize(QSize(24, 24))
        
        # Make it circular and add shadow
        self.bubble_btn.setStyleSheet("""
            PrimaryPushButton {
                border-radius: 30px;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        # Force mask for perfect circle if stylesheet fails
        # self.bubble_btn.setMask(QRegion(self.bubble_btn.rect(), QRegion.Ellipse))
        
        # Connect click to toggle
        self.bubble_btn.clicked.connect(self.toggle_chat)
        
        # Container for bubble to align it right
        bubble_container = QWidget(self)
        bubble_layout = QHBoxLayout(bubble_container)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.addStretch()
        bubble_layout.addWidget(self.bubble_btn)
        
        self.layout.addWidget(bubble_container)
        
        # Initial sizing
        self.adjustSize()

    def _setup_chat_card(self):
        """Build the internal layout of the chat card."""
        layout = QVBoxLayout(self.chat_card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # --- Header ---
        header_layout = QHBoxLayout()
        
        self.title_label = StrongBodyLabel(self.settings.bot_name, self.chat_card)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        self.btn_settings = TransparentToolButton(FIF.SETTING, self.chat_card)
        self.btn_settings.setFixedSize(30, 30)
        self.btn_settings.clicked.connect(self.open_settings)
        header_layout.addWidget(self.btn_settings)
        
        self.btn_close = TransparentToolButton(FIF.CLOSE, self.chat_card)
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.clicked.connect(self.toggle_chat)
        header_layout.addWidget(self.btn_close)
        
        layout.addLayout(header_layout)
        
        # --- Chat History ---
        self.chat_list = QListWidget(self.chat_card)
        self.chat_list.setFrameShape(QFrame.NoFrame)
        self.chat_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.chat_list.setStyleSheet("QListWidget { background: transparent; }")
        layout.addWidget(self.chat_list)
        
        # --- Input Area ---
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 5, 0, 5)
        
        self.input_box = LineEdit(self.chat_card)
        self.input_box.setPlaceholderText("Nhập tin nhắn...")
        self.input_box.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_box, 1) # Give it stretch factor 1
        
        self.btn_send = PrimaryPushButton(self.chat_card)
        self.btn_send.setIcon(FIF.SEND)
        self.btn_send.setFixedSize(40, 40) # Square and larger
        self.btn_send.clicked.connect(self.send_message)
        input_layout.addWidget(self.btn_send, 0)
        
        layout.addLayout(input_layout)

    def toggle_chat(self):
        """Toggle between expanded and collapsed states."""
        print(f"🔄 Toggle Chat: Currently Expanded={self._isExpanded}")
        if self.chat_card.isVisible():
            self.chat_card.hide()
            self._isExpanded = False
            print("  → Hiding chat card")
        else:
            self.chat_card.show()
            self._isExpanded = True
            self.input_box.setFocus()
            print("  → Showing chat card")
        
        self.adjustSize()
        self._ensure_within_bounds()

    def _ensure_within_bounds(self):
        """Ensure the bubble stays within the parent window bounds."""
        if not self.parent():
            return
            
        parent_rect = self.parent().rect()
        my_rect = self.geometry()
        
        new_x = my_rect.x()
        new_y = my_rect.y()
        
        # Debug current pos
        print(f"📍 Checking bounds: Pos=({new_x}, {new_y}), Size={my_rect.width()}x{my_rect.height()}, Parent={parent_rect.width()}x{parent_rect.height()}")
        
        # Clamp X
        if new_x < 0: new_x = 0
        if new_x + my_rect.width() > parent_rect.width():
            new_x = parent_rect.width() - my_rect.width()
            
        # Clamp Y
        if new_y < 0: new_y = 0
        if new_y + my_rect.height() > parent_rect.height():
            new_y = parent_rect.height() - my_rect.height()
            
        if new_x != my_rect.x() or new_y != my_rect.y():
            print(f"  ⚠️ Clamping to: ({new_x}, {new_y})")
            self.move(new_x, new_y)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            # Store position relative to widget
            self._dragPos = event.pos()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            # Calculate new position in parent coordinates
            # mapToParent(event.pos()) gives the cursor position in parent coords
            # Subtracting _dragPos (which is the offset of cursor within widget) gives the new widget top-left
            new_pos = self.mapToParent(event.pos()) - self._dragPos
            self.move(new_pos)
            self._userMoved = True
            event.accept()
            
    def open_settings(self):
        try:
            dialog = ChatSettingsDialog(self.settings, self.window())
            if dialog.exec():
                self.settings = dialog.get_settings()
                self.title_label.setText(self.settings.bot_name)
                InfoBar.success("Thành công", "Đã lưu cài đặt Chatbot", parent=self.window())
        except Exception as e:
            print(f"❌ Error opening settings: {e}")
            import traceback
            traceback.print_exc()
            InfoBar.error("Lỗi", f"Không thể mở cài đặt: {e}", parent=self.window())

    def send_message(self):
        text = self.input_box.text().strip()
        if not text:
            return
            
        self.appendUserMessage(text)
        self.input_box.clear()
        self.messageSent.emit(text)
        
        # Process reply
        self.request_ai_reply(text)

    def appendUserMessage(self, text: str):
        item = QListWidgetItem()
        item.setTextAlignment(Qt.AlignRight)
        
        # Create a widget for the bubble
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.addStretch()
        
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
        
        layout.addWidget(label)
        
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

    def process_command(self, text: str) -> str:
        """
        Basic mock logic.
        Later this will be replaced or extended to call Gemini API.
        """
        text_lower = text.lower()
        
        if text_lower.startswith("/note"):
            return "Note saved (mock)."
        elif "autokey" in text_lower:
            return "Opening AutoKey... (mock)"
        else:
            return f"This is a mock reply from {self.settings.bot_name}.\nYou said: {text}"

    def request_ai_reply(self, user_text: str):
        """
        Placeholder for future Gemini API integration.

        In the future this method will:
        - Use self.settings.current_key for authorization.
        - Build a message history including:
            - system: self.settings.system_rule
            - user: user_text
        - Call Gemini API and return the AI reply text.
        For now, just delegate to process_command(user_text).
        """
        # Simulate delay or async call here if needed
        reply = self.process_command(user_text)
        self.appendBotMessage(reply)
