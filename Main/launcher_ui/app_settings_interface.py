from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import SubtitleLabel, PrimaryPushSettingCard, FluentIcon as FIF, InfoBar

class AppSettingsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("appSettingsInterface")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = SubtitleLabel("Cài đặt ứng dụng", self)
        layout.addWidget(title)
        
        # AutoKey Settings
        self.autokey_card = PrimaryPushSettingCard(
            "Mở",
            FIF.GAME,
            "AutoKey",
            "Cấu hình macro, phím tắt và tự động hóa",
            self
        )
        self.autokey_card.clicked.connect(lambda: InfoBar.info("Thông báo", "Tính năng đang phát triển", parent=self.window()))
        layout.addWidget(self.autokey_card)

        # Android Tool Settings
        self.android_card = PrimaryPushSettingCard(
            "Mở",
            FIF.FOLDER,
            "Android Tool",
            "Quản lý thiết bị Android, ADB và kịch bản",
            self
        )
        self.android_card.clicked.connect(lambda: InfoBar.info("Thông báo", "Tính năng đang phát triển", parent=self.window()))
        layout.addWidget(self.android_card)
        
        layout.addStretch(1)
