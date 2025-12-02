from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (SubtitleLabel, SwitchSettingCard, PrimaryPushSettingCard, 
                            ExpandGroupSettingCard, FluentIcon as FIF, InfoBar, Theme, setTheme, PushButton)
from core.config_manager import ConfigManager
import os
import sys
import subprocess

class SettingsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("settingsInterface")
        self.parent_window = parent
        self.config = ConfigManager.load()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header with title and button
        header_layout = QHBoxLayout()
        title = SubtitleLabel("Cài đặt chung", self)
        header_layout.addWidget(title)
        
        # Mẫu button - simple button next to title
        samples_btn = PushButton(FIF.CODE, "Mẫu button", self)
        samples_btn.clicked.connect(self.switch_to_widget_samples)
        header_layout.addWidget(samples_btn)
        
        header_layout.addStretch(1)
        layout.addLayout(header_layout)
        
        # Dark Mode Card
        self.dark_mode_card = SwitchSettingCard(
            FIF.BRUSH,
            "Giao diện tối",
            "Bật để chuyển sang chế độ nền tối (Dark Theme)",
            configItem=None,
            parent=self
        )
        self.dark_mode_card.setChecked(self.config.get("dark_mode", True))
        self.dark_mode_card.checkedChanged.connect(self.on_dark_mode_changed)
        layout.addWidget(self.dark_mode_card)
        
        # Startup Card
        self.startup_card = SwitchSettingCard(
            FIF.POWER_BUTTON,
            "Khởi động cùng Windows",
            "Tự động chạy ứng dụng này khi bật máy",
            configItem=None,
            parent=self
        )
        self.startup_card.setChecked(self.config.get("startup", False))
        self.startup_card.checkedChanged.connect(self.on_startup_changed)
        layout.addWidget(self.startup_card)
        
        # Run in Background Card
        self.background_card = SwitchSettingCard(
            FIF.REMOVE,
            "Chạy ngầm hệ thống",
            "Khi đóng cửa sổ, ứng dụng sẽ chạy ngầm dưới khay hệ thống",
            configItem=None,
            parent=self
        )
        self.background_card.setChecked(self.config.get("run_in_background", False))
        self.background_card.checkedChanged.connect(self.on_run_in_background_changed)
        layout.addWidget(self.background_card)

        # App Settings Link
        self.app_settings_card = PrimaryPushSettingCard(
            "Mở",
            FIF.SETTING,
            "Cài đặt ứng dụng",
            "Cấu hình riêng cho từng ứng dụng",
            self
        )
        self.app_settings_card.clicked.connect(self.switch_to_app_settings)
        layout.addWidget(self.app_settings_card)

        # External Window Mode Group
        self.external_group = ExpandGroupSettingCard(
            FIF.APPLICATION,
            "Ứng dụng chạy cửa sổ ngoài",
            "Bật để chạy ứng dụng trong cửa sổ riêng biệt thay vì tích hợp vào đây",
            self
        )
        
        # AutoKey Toggle
        self.autokey_external = SwitchSettingCard(
            FIF.GAME,
            "AutoKey",
            "Chạy AutoKey dưới dạng cửa sổ độc lập",
            configItem=None,
            parent=self.external_group
        )
        self.autokey_external.setChecked(self.config.get("external_autokey", True))
        self.autokey_external.checkedChanged.connect(lambda c: self.on_external_changed("external_autokey", c))
        self.external_group.addGroupWidget(self.autokey_external)
        
        # Android Tool Toggle
        self.android_external = SwitchSettingCard(
            FIF.FOLDER,
            "Android Tool",
            "Chạy Android Tool dưới dạng cửa sổ độc lập",
            configItem=None,
            parent=self.external_group
        )
        self.android_external.setChecked(self.config.get("external_android", True))
        self.android_external.checkedChanged.connect(lambda c: self.on_external_changed("external_android", c))
        self.external_group.addGroupWidget(self.android_external)
        
        layout.addWidget(self.external_group)
        layout.addStretch(1)

    def switch_to_app_settings(self):
        main_window = self.window()
        if hasattr(main_window, 'app_settings_interface'):
            main_window.switchTo(main_window.app_settings_interface)
    
    def switch_to_widget_samples(self):
        main_window = self.window()
        if hasattr(main_window, 'widget_samples_interface'):
            main_window.switchTo(main_window.widget_samples_interface)

    def on_dark_mode_changed(self, checked):
        self.config["dark_mode"] = checked
        ConfigManager.save(self.config)
        new_theme = Theme.DARK if checked else Theme.LIGHT
        setTheme(new_theme)
        
        # Update main window's current_theme property
        main_window = self.window()
        if hasattr(main_window, 'current_theme'):
            main_window.current_theme = new_theme
            print(f"🎨 DEBUG: Main theme updated to: {new_theme}")

    def on_startup_changed(self, checked):
        self.config["startup"] = checked
        ConfigManager.save(self.config)
        startup_folder = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
        shortcut_path = os.path.join(startup_folder, "MonToolHub.lnk")
        if checked:
            target = os.path.abspath(sys.argv[0])
            working_dir = os.path.dirname(target)
            script = f'$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut("{shortcut_path}"); $s.TargetPath = "{sys.executable}"; $s.Arguments = "{target}"; $s.WorkingDirectory = "{working_dir}"; $s.Save()'
            subprocess.run(["powershell", "-Command", script], shell=True)
            InfoBar.success("Thành công", "Đã thêm vào khởi động cùng Windows", parent=self.window())
        else:
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
                InfoBar.success("Thành công", "Đã gỡ khỏi khởi động cùng Windows", parent=self.window())

    def on_run_in_background_changed(self, checked):
        self.config["run_in_background"] = checked
        ConfigManager.save(self.config)
        InfoBar.success("Đã lưu", "Cài đặt chạy ngầm đã được cập nhật", parent=self.window())

    def on_external_changed(self, key, checked):
        self.config[key] = checked
        ConfigManager.save(self.config)
