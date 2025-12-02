from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QKeySequenceEdit,
                             QTabWidget, QWidget, QSpinBox, QComboBox, QDoubleSpinBox)
from PySide6.QtCore import QSettings
from PySide6.QtGui import QKeySequence

class SettingsDialog(QDialog):
    def __init__(self, parent=None, initial_tab=0):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = QSettings("MonSoft", "MacroRecorder")
        self.setup_ui()
        self.load_settings()
        self.tabs.setCurrentIndex(initial_tab)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab Widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: Hotkeys
        self.hotkey_tab = QWidget()
        self.setup_hotkey_tab()
        self.tabs.addTab(self.hotkey_tab, "Hotkeys")
        
        # Tab 2: Play
        self.play_tab = QWidget()
        self.setup_play_tab()
        self.tabs.addTab(self.play_tab, "Play")
        
        # Tab 3: Mini Mode
        self.mini_mode_tab = QWidget()
        self.setup_mini_mode_tab()
        self.tabs.addTab(self.mini_mode_tab, "Mini Mode")
        
        # Tab 4: Mouse (New)
        self.mouse_tab = QWidget()
        self.setup_mouse_tab()
        self.tabs.addTab(self.mouse_tab, "Mouse")
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        self.save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        # Validation Label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        layout.addWidget(self.error_label)

    def setup_hotkey_tab(self):
        layout = QVBoxLayout(self.hotkey_tab)
        form_layout = QFormLayout()
        
        # Custom QKeySequenceEdit that allows Backspace to clear and handles Numpad
        class ClearableKeySequenceEdit(QKeySequenceEdit):
            def keyPressEvent(self, event):
                from PySide6.QtCore import Qt
                from PySide6.QtGui import QKeySequence
                
                if event.key() == Qt.Key.Key_Backspace:
                    # Clear the sequence
                    self.clear()
                    event.accept()
                elif event.modifiers() & Qt.KeyboardModifier.KeypadModifier:
                    # Explicitly handle Numpad keys to ensure "Num+X" format
                    # QKeySequenceEdit sometimes drops the KeypadModifier for digits
                    key = event.key()
                    modifiers = event.modifiers()
                    
                    # Create sequence with KeypadModifier explicitly
                    # We combine the key code with the KeypadModifier
                    # Fix: Use .value for bitwise OR with int key
                    seq = QKeySequence(key | Qt.KeyboardModifier.KeypadModifier.value)
                    self.setKeySequence(seq)
                    event.accept()
                else:
                    super().keyPressEvent(event)
        
        # Hotkey Fields
        self.record_hotkey = ClearableKeySequenceEdit()
        self.record_hotkey.setMaximumSequenceLength(1)
        
        self.stop_record_hotkey = ClearableKeySequenceEdit()
        self.stop_record_hotkey.setMaximumSequenceLength(1)
        
        self.play_hotkey = ClearableKeySequenceEdit()
        self.play_hotkey.setMaximumSequenceLength(1)
        
        form_layout.addRow("Start Record Hotkey:", self.record_hotkey)
        form_layout.addRow("Stop Record Hotkey:", self.stop_record_hotkey)
        form_layout.addRow("Play/Stop Hotkey:", self.play_hotkey)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Connect signals for validation
        self.record_hotkey.keySequenceChanged.connect(self.validate_hotkeys)
        self.stop_record_hotkey.keySequenceChanged.connect(self.validate_hotkeys)
        self.play_hotkey.keySequenceChanged.connect(self.validate_hotkeys)

    def setup_play_tab(self):
        layout = QVBoxLayout(self.play_tab)
        form_layout = QFormLayout()
        
        # 1. Run Count
        self.spin_count = QSpinBox()
        self.spin_count.setRange(0, 99999)
        self.spin_count.setValue(1)
        self.spin_count.setSpecialValueText("Vô hạn (Infinite)")  # 0 displays as this
        form_layout.addRow("Số lần chạy (0=Vô hạn):", self.spin_count)
        
        # 2. Duration (Hours : Minutes)
        duration_layout = QHBoxLayout()
        self.spin_hours = QSpinBox()
        self.spin_hours.setRange(0, 999)
        self.spin_hours.setSuffix(" giờ")
        
        self.spin_minutes = QSpinBox()
        self.spin_minutes.setRange(0, 59)
        self.spin_minutes.setSuffix(" phút")
        
        duration_layout.addWidget(self.spin_hours)
        duration_layout.addWidget(self.spin_minutes)
        duration_layout.addStretch()
        
        form_layout.addRow("Thời gian chạy:", duration_layout)
        
        # 3. Playback Speed and Loop Delay in same row
        speed_delay_layout = QHBoxLayout()
        
        self.spin_speed = QDoubleSpinBox()
        self.spin_speed.setRange(0.1, 50.0)
        self.spin_speed.setSingleStep(0.1)
        self.spin_speed.setDecimals(1)
        self.spin_speed.setValue(1.0)
        self.spin_speed.setFixedWidth(100)
        self.spin_speed.editingFinished.connect(self._clamp_speed)
        speed_delay_layout.addWidget(self.spin_speed)
        
        speed_delay_layout.addWidget(QLabel("   Delay:"))
        
        self.spin_loop_delay = QSpinBox()
        self.spin_loop_delay.setRange(0, 999999)
        self.spin_loop_delay.setSuffix(" ms")
        self.spin_loop_delay.setValue(0)
        self.spin_loop_delay.setFixedWidth(120)
        self.spin_loop_delay.setToolTip("Thời gian chờ sau mỗi vòng lặp (0 = không chờ)")
        speed_delay_layout.addWidget(self.spin_loop_delay)
        
        speed_delay_layout.addStretch()
        
        form_layout.addRow("Tốc độ Phát:", speed_delay_layout)
        
        # 4. After Completion
        self.combo_after = QComboBox()
        self.combo_after.addItems(["None", "Tắt Máy", "Sleep"])
        form_layout.addRow("Khi chạy xong:", self.combo_after)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        
        # ✅ Apply Dark Theme Styles
        self.setStyleSheet("""
            QDialog { 
                background-color: #2b2b2b; 
                color: #ffffff; 
            }
            QTabWidget::pane {
                background-color: #2b2b2b;
                border: 1px solid #454545;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #1e1e1e;
                color: #ffffff;
                padding: 8px 16px;
                border: 1px solid #454545;
                border-bottom: none;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #2b2b2b;
                border-bottom: 2px solid #0078d4;
            }
            QLabel { 
                color: #ffffff; 
                font-weight: bold; 
            }
            QKeySequenceEdit { 
                padding: 5px; 
                border: 1px solid #454545; 
                border-radius: 3px;
                color: #ffffff;
                background-color: #1e1e1e;
                selection-background-color: #0078d4;
            }
            QKeySequenceEdit:focus {
                border: 2px solid #0078d4;
                background-color: #2b2b2b;
            }
            QLineEdit {
                padding: 5px; 
                border: 1px solid #454545; 
                border-radius: 4px;
                color: #ffffff;
                background-color: #1e1e1e;
            }
            QSpinBox, QDoubleSpinBox, QComboBox {
                padding: 5px;
                border: 1px solid #454545;
                border-radius: 4px;
                color: #ffffff;
                background-color: #1e1e1e;
            }
            QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border: 2px solid #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #ffffff;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: #ffffff;
                selection-background-color: #0078d4;
                border: 1px solid #454545;
            }
            QPushButton {
                padding: 6px 12px;
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { 
                background-color: #1084d9; 
            }
            QPushButton:disabled { 
                background-color: #454545;
                color: #808080;
            }
        """)
    
    def _clamp_speed(self):
        """Clamp playback speed to max 50 when user finishes editing"""
        if self.spin_speed.value() > 50.0:
            self.spin_speed.setValue(50.0)
    
    def setup_mini_mode_tab(self):
        layout = QVBoxLayout(self.mini_mode_tab)
        form_layout = QFormLayout()
        
        # Overlay Position
        self.combo_position = QComboBox()
        self.combo_position.addItems([
            "Top Left",
            "Top Center",
            "Top Right",
            "Center",
            "Bottom Left",
            "Bottom Center",
            "Bottom Right"
        ])
        form_layout.addRow("Vị trí xuất hiện Overlay:", self.combo_position)
        
        # Add info label
        info_label = QLabel("Chọn vị trí mà bảng Playback sẽ xuất hiện khi bắt đầu phát macro.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 9pt; margin-top: 10px;")
        
        layout.addLayout(form_layout)
        layout.addWidget(info_label)
        layout.addStretch()

    def setup_mouse_tab(self):
        layout = QVBoxLayout(self.mouse_tab)
        form_layout = QFormLayout()
        
        # Mouse Mode
        self.combo_mouse_mode = QComboBox()
        self.combo_mouse_mode.addItems([
            "Auto (Detect 2D/3D)",
            "Force UI (Absolute)",
            "Force 3D (Relative Delta)"
        ])
        form_layout.addRow("Mouse Mode:", self.combo_mouse_mode)
        
        # Tick Hz
        self.spin_tick_hz = QSpinBox()
        self.spin_tick_hz.setRange(60, 1000)
        self.spin_tick_hz.setSingleStep(10)
        self.spin_tick_hz.setSuffix(" Hz")
        self.spin_tick_hz.setSuffix(" Hz")
        form_layout.addRow("Playback Tick Rate:", self.spin_tick_hz)
        
        # Mouse Gain
        self.spin_gain = QDoubleSpinBox()
        self.spin_gain.setRange(0.1, 5.0)
        self.spin_gain.setSingleStep(0.1)
        self.spin_gain.setValue(1.0)
        form_layout.addRow("Mouse Gain (Sensitivity):", self.spin_gain)
        
        # Info
        info_label = QLabel(
            "• Auto: Tự động chuyển đổi giữa chuột tuyệt đối (UI) và tương đối (Game 3D).\n"
            "• Force UI: Luôn dùng toạ độ tuyệt đối (cho ứng dụng văn phòng/web).\n"
            "• Force 3D: Luôn dùng delta (cho game FPS/TPS xoay camera).\n"
            "• Tick Rate: Tần số gửi sự kiện chuột (cao hơn = mượt hơn nhưng tốn CPU).\n"
            "• Mouse Gain: Hệ số nhân quãng đường chuột (1.0 = chuẩn). Tăng lên nếu thấy chuột di chuyển thiếu."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 9pt; margin-top: 10px;")
        
        layout.addLayout(form_layout)
        layout.addWidget(info_label)
        layout.addStretch()

    def validate_hotkeys(self):
        hotkeys = {}
        duplicates = []
        
        # Helper to check
        def check(name, widget):
            seq = widget.keySequence().toString()
            if not seq:
                return  # Empty is OK (None/disabled)
            
            if seq in hotkeys:
                duplicates.append(f"{name} conflicts with {hotkeys[seq]}")
            else:
                hotkeys[seq] = name

        check("Record", self.record_hotkey)
        check("Stop Record", self.stop_record_hotkey)
        check("Play/Stop", self.play_hotkey)
        
        if duplicates:
            self.error_label.setText("\n".join(duplicates))
            self.save_btn.setEnabled(False)
        else:
            self.error_label.setText("")
            self.save_btn.setEnabled(True)

    def load_settings(self):
        # Load saved hotkeys or defaults
        rec_seq = self.settings.value("hotkey_record", "F9")
        stop_rec_seq = self.settings.value("hotkey_stop_record", "F10")
        play_seq = self.settings.value("hotkey_play", "F11")
        
        self.record_hotkey.setKeySequence(QKeySequence(rec_seq))
        self.stop_record_hotkey.setKeySequence(QKeySequence(stop_rec_seq))
        self.play_hotkey.setKeySequence(QKeySequence(play_seq))
        
        # Load Play Settings
        self.spin_count.setValue(int(self.settings.value("play_count", 1)))
        self.spin_hours.setValue(int(self.settings.value("play_hours", 0)))
        self.spin_minutes.setValue(int(self.settings.value("play_minutes", 0)))
        self.spin_speed.setValue(float(self.settings.value("playback_speed", 1.0)))
        self.spin_loop_delay.setValue(int(self.settings.value("loop_delay", 0)))
        
        after_action = self.settings.value("play_after_action", "None")
        index = self.combo_after.findText(after_action)
        if index >= 0:
            self.combo_after.setCurrentIndex(index)
        
        # Load Mini Mode Settings
        overlay_position = self.settings.value("overlay_position", "top_left")
        # Map internal values to display values
        position_map = {
            "top_left": "Top Left",
            "top_center": "Top Center",
            "top_right": "Top Right",
            "center": "Center",
            "bottom_left": "Bottom Left",
            "bottom_center": "Bottom Center",
            "bottom_right": "Bottom Right"
        }
        display_position = position_map.get(overlay_position, "Top Left")
        index = self.combo_position.findText(display_position)
        if index >= 0:
            self.combo_position.setCurrentIndex(index)
            
        # Load Mouse Settings
        mouse_mode = self.settings.value("mouse_mode", "auto")
        mode_map = {
            "auto": "Auto (Detect 2D/3D)",
            "force_ui": "Force UI (Absolute)",
            "force_3d": "Force 3D (Relative Delta)"
        }
        display_mode = mode_map.get(mouse_mode, "Auto (Detect 2D/3D)")
        index = self.combo_mouse_mode.findText(display_mode)
        if index >= 0:
            self.combo_mouse_mode.setCurrentIndex(index)
            
        tick_hz = int(self.settings.value("mouse_tick_hz", 240))
        tick_hz = int(self.settings.value("mouse_tick_hz", 240))
        self.spin_tick_hz.setValue(tick_hz)
        
        gain = float(self.settings.value("mouse_gain", 1.0))
        self.spin_gain.setValue(gain)

    def save_settings(self):
        # Save hotkeys
        self.settings.setValue("hotkey_record", self.record_hotkey.keySequence().toString())
        self.settings.setValue("hotkey_stop_record", self.stop_record_hotkey.keySequence().toString())
        self.settings.setValue("hotkey_play", self.play_hotkey.keySequence().toString())
        
        # Save Play Settings
        self.settings.setValue("play_count", self.spin_count.value())
        self.settings.setValue("play_hours", self.spin_hours.value())
        self.settings.setValue("play_minutes", self.spin_minutes.value())
        self.settings.setValue("playback_speed", self.spin_speed.value())
        self.settings.setValue("loop_delay", self.spin_loop_delay.value())
        self.settings.setValue("play_after_action", self.combo_after.currentText())
        
        # Save Mini Mode Settings
        # Map display values to internal values
        position_map = {
            "Top Left": "top_left",
            "Top Center": "top_center",
            "Top Right": "top_right",
            "Center": "center",
            "Bottom Left": "bottom_left",
            "Bottom Center": "bottom_center",
            "Bottom Right": "bottom_right"
        }
        display_position = self.combo_position.currentText()
        internal_position = position_map.get(display_position, "top_left")
        self.settings.setValue("overlay_position", internal_position)
        
        # Save Mouse Settings
        mode_map_inv = {
            "Auto (Detect 2D/3D)": "auto",
            "Force UI (Absolute)": "force_ui",
            "Force 3D (Relative Delta)": "force_3d"
        }
        display_mode = self.combo_mouse_mode.currentText()
        internal_mode = mode_map_inv.get(display_mode, "auto")
        self.settings.setValue("mouse_mode", internal_mode)
        
        self.settings.setValue("mouse_tick_hz", self.spin_tick_hz.value())
        self.settings.setValue("mouse_gain", self.spin_gain.value())
        
        # Force immediate write to registry/config
        self.settings.sync()

