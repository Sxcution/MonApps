from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QBrush

class RecordingOverlay(QWidget):
    """
    Mini overlay to indicate recording status.
    Shows a blinking red dot and 'Recording...' text.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.layout.setSpacing(8)
        
        # Red Dot Indicator
        self.dot_label = QLabel()
        self.dot_label.setFixedSize(12, 12)
        self.dot_label.setStyleSheet("""
            background-color: #ff3b30;
            border-radius: 6px;
        """)
        self.layout.addWidget(self.dot_label)
        
        # Text Label
        self.text_label = QLabel("Recording...")
        self.text_label.setStyleSheet("""
            color: white;
            font-family: 'Segoe UI';
            font-weight: bold;
            font-size: 12px;
        """)
        self.layout.addWidget(self.text_label)
        
        # Blink Timer
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_dot)
        self.blink_timer.start(800)
        self.dot_visible = True
        
    def toggle_dot(self):
        self.dot_visible = not self.dot_visible
        if self.dot_visible:
            self.dot_label.setStyleSheet("""
                background-color: #ff3b30;
                border-radius: 6px;
            """)
        else:
            self.dot_label.setStyleSheet("""
                background-color: transparent;
                border-radius: 6px;
            """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Semi-transparent black background with rounded corners
        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)

    def position_overlay(self):
        """Position overlay at the top-center of the screen or parent window"""
        if self.parent():
            parent_geo = self.parent().geometry()
            # Position at top center of parent window
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + 20
            self.move(x, y)
        else:
            # Fallback to screen top center
            screen = self.screen().geometry()
            x = (screen.width() - self.width()) // 2
            y = 50
            self.move(x, y)
