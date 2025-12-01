from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from qfluentwidgets import SubtitleLabel, PrimaryPushButton, FluentIcon as FIF, InfoBar, TextEdit
from core.log_manager import LogManager
import pyperclip

class LogInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("logInterface")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        title = SubtitleLabel("Nhật ký ứng dụng", self)
        header_layout.addWidget(title)
        header_layout.addStretch(1)
        
        # Copy Button
        self.copy_btn = PrimaryPushButton(FIF.COPY, "Sao chép toàn bộ", self)
        self.copy_btn.clicked.connect(self.copy_logs)
        header_layout.addWidget(self.copy_btn)
        
        layout.addLayout(header_layout)
        
        # Log View
        self.log_view = TextEdit(self)
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 10))
        # Remove all borders and focus indicators
        self.log_view.setStyleSheet("""
            TextEdit {
                border: none;
                color: black;
                selection-background-color: #009faa;
            }
            TextEdit:focus {
                border: none;
                outline: none;
            }
        """)
        self.log_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Disable focus completely
        layout.addWidget(self.log_view)
        
        # Connect Logger
        self.logger = LogManager.get_instance()
        self.logger.log_signal.connect(self.append_log)

    def append_log(self, text):
        self.log_view.moveCursor(self.log_view.textCursor().MoveOperation.End)
        self.log_view.insertPlainText(text)
        self.log_view.moveCursor(self.log_view.textCursor().MoveOperation.End)

    def copy_logs(self):
        logs = self.log_view.toPlainText()
        pyperclip.copy(logs)
        InfoBar.success("Thành công", "Đã sao chép nhật ký vào clipboard", parent=self.window())

