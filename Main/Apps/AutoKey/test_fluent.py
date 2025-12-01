import sys
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from qfluentwidgets import (FluentWindow, PushButton, LineEdit, 
                            StrongBodyLabel, SubtitleLabel, InfoBar, InfoBarPosition)
from qfluentwidgets import FluentIcon as FIF

class DemoWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fluent Widgets Demo")
        self.resize(800, 600)

        # 1. Create a central widget and layout
        self.central_widget = QWidget()
        self.central_widget.setObjectName("homeInterface") # REQUIRED for FluentWindow
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)
        
        # We need to add the central widget to the FluentWindow's stacked widget or use it as a sub-interface
        # But for a simple demo, let's just add a "Home" interface
        self.addSubInterface(self.central_widget, FIF.HOME, "Trang chủ")

        # 2. Add some Fluent Widgets
        
        # Title
        self.title_label = SubtitleLabel("Xin chào Fluent Widgets!", self.central_widget)
        self.layout.addWidget(self.title_label)

        # Input
        self.input_box = LineEdit(self.central_widget)
        self.input_box.setPlaceholderText("Nhập tên của bạn...")
        self.layout.addWidget(self.input_box)

        # Button
        self.btn_hello = PushButton("Gửi lời chào", self.central_widget, FIF.SEND)
        self.btn_hello.clicked.connect(self.show_greeting)
        self.layout.addWidget(self.btn_hello)
        
        # Spacer
        self.layout.addStretch(1)

    def show_greeting(self):
        name = self.input_box.text() or "Bạn"
        
        # Show a Fluent InfoBar (Notification)
        InfoBar.success(
            title='Thành công',
            content=f"Xin chào, {name}! Giao diện này thật đẹp đúng không?",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000,
            parent=self
        )

if __name__ == '__main__':
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    
    # Create and show window
    w = DemoWindow()
    w.show()
    
    sys.exit(app.exec())
