from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import SubtitleLabel, BodyLabel, InfoBar
import os
import sys
import subprocess
from core.config_manager import ConfigManager

class HomeInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("homeInterface")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title
        title = SubtitleLabel("Trung tâm điều khiển", self)
        layout.addWidget(title)
        
        # Description
        desc = BodyLabel("Chào mừng bạn đến với Mon Tool Hub.\nChọn công cụ từ menu bên trái để bắt đầu.", self)
        layout.addWidget(desc)
        
        layout.addStretch(1)

    def launch_autokey(self):
        config = ConfigManager.load()
        if config.get("external_autokey", True):
            try:
                # Path adjusted for Apps directory
                script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Apps", "AutoKey", "main.py")
                subprocess.Popen([sys.executable, script_path], cwd=os.path.dirname(script_path))
                InfoBar.success("Đã mở AutoKey", "Ứng dụng đang khởi động (Cửa sổ ngoài)...", parent=self.window())
            except Exception as e:
                InfoBar.error("Lỗi", f"Không thể mở AutoKey: {e}", parent=self.window())
        else:
            self.window().embed_autokey()

    def launch_android(self):
        config = ConfigManager.load()
        if config.get("external_android", True):
            try:
                # Path adjusted for Apps directory
                script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Apps", "Android_Tool", "Main.py")
                subprocess.Popen([sys.executable, script_path], cwd=os.path.dirname(script_path))
                InfoBar.success("Đã mở Android Tool", "Ứng dụng đang khởi động (Cửa sổ ngoài)...", parent=self.window())
            except Exception as e:
                InfoBar.error("Lỗi", f"Không thể mở Android Tool: {e}", parent=self.window())
        else:
            self.window().embed_android()
