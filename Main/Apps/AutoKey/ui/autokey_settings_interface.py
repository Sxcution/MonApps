# Simplified AutoKey Settings Interface
# Using only PushSettingCard to avoid API complexities

from PySide6.QtWidgets import QWidget, QVBoxLayout, QInputDialog
from PySide6.QtCore import QSettings
from qfluentwidgets import (SubtitleLabel, SettingCardGroup, PushSettingCard, 
                            FluentIcon as FIF, InfoBar)

class AutoKeySettingsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("settingsInterface")
        self.settings = QSettings("MonSoft", "MacroRecorder")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = SubtitleLabel("Cài đặt AutoKey", self)
        layout.addWidget(title)
        
        # Hotkeys Group
        hotkey_group = SettingCardGroup("Phím tắt", self)
        
        self.record_hotkey_card = PushSettingCard(
            "Thiết lập",
            FIF.EDIT,
            "Phím bắt đầu ghi",
            self.settings.value("hotkey_record", "F9"),
            hotkey_group
        )
        self.record_hotkey_card.clicked.connect(lambda: self.setup_hotkey("hotkey_record", "Phím bắt đầu ghi"))
        hotkey_group.addSettingCard(self.record_hotkey_card)
        
        self.stop_record_hotkey_card = PushSettingCard(
            "Thiết lập",
            FIF.EDIT,
            "Phím dừng ghi",
            self.settings.value("hotkey_stop_record", "F10"),
            hotkey_group
        )
        self.stop_record_hotkey_card.clicked.connect(lambda: self.setup_hotkey("hotkey_stop_record", "Phím dừng ghi"))
        hotkey_group.addSettingCard(self.stop_record_hotkey_card)
        
        self.play_hotkey_card = PushSettingCard(
            "Thiết lập",
            FIF.PLAY,
            "Phím phát/dừng macro",
            self.settings.value("hotkey_play", "F11"),
            hotkey_group
        )
        self.play_hotkey_card.clicked.connect(lambda: self.setup_hotkey("hotkey_play", "Phím phát/dừng"))
        hotkey_group.addSettingCard(self.play_hotkey_card)
        
        layout.addWidget(hotkey_group)
        
        # Playback Settings
        playback_group = SettingCardGroup("Cài đặt phát macro", self)
        
        self.play_count_card = PushSettingCard(
            "Chỉnh",
            FIF.SYNC,
            "Số lần lặp",
            f"{self.settings.value('play_count', 1)} lần",
            playback_group
        )
        self.play_count_card.clicked.connect(lambda: self.set_number("play_count", "Số lần lặp", 0, 999999, "lần"))
        playback_group.addSettingCard(self.play_count_card)
        
        layout.addWidget(playback_group)
        layout.addStretch(1)
    
    def setup_hotkey(self, key, title):
        current_value = self.settings.value(key, "")
        new_value, ok = QInputDialog.getText(
            self, title,
            f"Nhập phím tắt mới (VD: F9, Ctrl+A, Num+1):\\nHiện tại: {current_value}",
            text=current_value
        )
        if ok and new_value:
            self.settings.setValue(key, new_value)
            if key == "hotkey_record":
                self.record_hotkey_card.setContent(new_value)
            elif key == "hotkey_stop_record":
                self.stop_record_hotkey_card.setContent(new_value)
            elif key == "hotkey_play":
               self.play_hotkey_card.setContent(new_value)
            
            InfoBar.success("Đã lưu", f"Phím tắt: {new_value}", parent=self.window())
            if hasattr(self.window(), 'setup_global_hotkeys'):
                self.window().setup_global_hotkeys()
    
    def set_number(self, key, title, min_val, max_val, suffix):
        current = int(self.settings.value(key, 0))
        value, ok = QInputDialog.getInt(self, title, f"Nhập giá trị ({min_val}-{max_val}):", current, min_val, max_val)
        if ok:
            self.settings.setValue(key, value)
            self.play_count_card.setContent(f"{value} {suffix}")
            InfoBar.success("Đã lưu", f"Giá trị: {value}", parent=self.window())
