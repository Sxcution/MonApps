from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QSpinBox, QRadioButton, QCheckBox, 
                             QGroupBox, QPushButton, QDialogButtonBox, QWidget,
                             QAbstractSpinBox, QButtonGroup)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCursor

class MouseActionDialog(QDialog):
    def __init__(self, parent=None, event_data=None):
        super().__init__(parent)
        self.setWindowTitle("Chỉnh sửa lệnh chuột")
        self.setFixedSize(550, 400)
        
        self.event_data = event_data or {}
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Description
        desc_label = QLabel("Lệnh chuột di chuyển con trỏ đến tọa độ đã chỉ định")
        desc_label.setStyleSheet("color: #333;")
        layout.addWidget(desc_label)
        
        # Event Type
        type_layout = QHBoxLayout()
        type_layout.setSpacing(10)
        type_layout.addWidget(QLabel("Loại sự kiện:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Click", "Click Phải", "Double Click", "Di chuyển", "Cuộn chuột", "Giữ Chuột trái"])
        self.type_combo.setFixedWidth(150)
        self.type_combo.currentTextChanged.connect(self._on_event_type_changed)
        type_layout.addWidget(self.type_combo)
        
        # Duration field for Hold Mouse - only shown when "Giữ Chuột trái" is selected
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0, 999999)
        self.duration_spin.setFixedWidth(80)
        self.duration_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.duration_spin.setSuffix(" ms")
        self.duration_spin.setVisible(False)  # Hidden by default
        type_layout.addWidget(self.duration_spin)
        
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # Coordinates Section
        coords_layout = QHBoxLayout()
        coords_layout.setSpacing(10)
        
        # X Column (Input + Label)
        x_col = QVBoxLayout()
        x_col.setSpacing(2) # Tight spacing
        
        self.x_spin = QSpinBox()
        self.x_spin.setRange(-10000, 10000)
        self.x_spin.setFixedWidth(80)
        self.x_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        
        self.x_label = QLabel("0")
        self.x_label.setFixedWidth(80)
        self.x_label.setStyleSheet("color: gray; font-size: 12px;") # Increased font size
        
        x_col.addWidget(self.x_spin)
        x_col.addWidget(self.x_label)
        
        # Y Column (Input + Label)
        y_col = QVBoxLayout()
        y_col.setSpacing(2) # Tight spacing
        
        self.y_spin = QSpinBox()
        self.y_spin.setRange(-10000, 10000)
        self.y_spin.setFixedWidth(80)
        self.y_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        
        self.y_label = QLabel("0")
        self.y_label.setFixedWidth(80)
        self.y_label.setStyleSheet("color: gray; font-size: 12px;") # Increased font size
        
        y_col.addWidget(self.y_spin)
        y_col.addWidget(self.y_label)
        
        coords_layout.addLayout(x_col)
        coords_layout.addLayout(y_col)
        
        # Helper Text
        helper_text = QLabel("Nhấn F2 để lấy vị trí hiện tại\nNhấn F3 để ẩn cửa sổ chính")
        helper_text.setStyleSheet("color: gray; font-size: 11px;")
        # Align top to match inputs
        coords_layout.addWidget(helper_text, alignment=Qt.AlignmentFlag.AlignTop) 
        coords_layout.addStretch()
        
        layout.addLayout(coords_layout)
        
        # Checkboxes for Relative/Offset (Mutually Exclusive)
        self.check_relative = QCheckBox("Tọa độ tương đối (theo cửa sổ đang mở)")
        self.check_offset = QCheckBox("Tọa độ offset (so với vị trí chuột trước đó)")
        
        # Connect signals for mutual exclusivity
        self.check_relative.clicked.connect(self.on_relative_clicked)
        self.check_offset.clicked.connect(self.on_offset_clicked)
        
        layout.addWidget(self.check_relative)
        layout.addWidget(self.check_offset)
        
        # Ignore Checkbox
        self.ignore_check = QCheckBox("Bỏ qua tọa độ trên - thực hiện tại vị trí hiện tại")
        layout.addWidget(self.ignore_check)
        
        # Randomize
        rand_layout = QHBoxLayout()
        rand_layout.setSpacing(5)
        rand_layout.addWidget(QLabel("Ngẫu nhiên tọa độ trong khoảng"))
        self.rand_spin = QSpinBox()
        self.rand_spin.setRange(0, 100)
        self.rand_spin.setFixedWidth(50)
        self.rand_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        rand_layout.addWidget(self.rand_spin)
        rand_layout.addWidget(QLabel("pixels"))
        rand_layout.addStretch()
        layout.addLayout(rand_layout)
        
        # Wheel
        wheel_layout = QHBoxLayout()
        wheel_layout.setSpacing(10)
        wheel_layout.addWidget(QLabel("Cuộn chuột:"))
        self.wheel_spin = QSpinBox()
        self.wheel_spin.setRange(-1000, 1000)
        self.wheel_spin.setFixedWidth(80)
        self.wheel_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        wheel_layout.addWidget(self.wheel_spin)
        wheel_layout.addStretch()
        layout.addLayout(wheel_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Timer for Mouse Polling
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_mouse_pos)
        self.timer.start(50) # Update every 50ms
        
        # Set Data
        self.load_data()
        
    def on_relative_clicked(self, checked):
        if checked:
            self.check_offset.setChecked(False)
            
    def on_offset_clicked(self, checked):
        if checked:
            self.check_relative.setChecked(False)
    
    def _on_event_type_changed(self, text):
        """Show/hide duration field based on event type"""
        if text == "Giữ Chuột trái":
            self.duration_spin.setVisible(True)
        else:
            self.duration_spin.setVisible(False)
        
    def update_mouse_pos(self):
        pos = QCursor.pos()
        self.x_label.setText(str(pos.x()))
        self.y_label.setText(str(pos.y()))
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F2:
            # Capture current position
            pos = QCursor.pos()
            self.x_spin.setValue(pos.x())
            self.y_spin.setValue(pos.y())
        elif event.key() == Qt.Key.Key_F3:
            if self.parent():
                if self.parent().isVisible():
                    self.parent().hide()
                else:
                    self.parent().show()
        else:
            super().keyPressEvent(event)
        
    def load_data(self):
        # Map event type
        etype = self.event_data.get('type', 'mouse_click')
        button = self.event_data.get('button', 'Button.left')
        
        if etype == 'mouse_move':
            self.type_combo.setCurrentText("Di chuyển")
        elif etype == 'mouse_scroll':
            self.type_combo.setCurrentText("Cuộn chuột")
        elif etype == 'mouse_hold':
            self.type_combo.setCurrentText("Giữ Chuột trái")
            # Load duration for hold
            self.duration_spin.setValue(self.event_data.get('duration', 500))
        elif etype == 'mouse_click':
            if button == 'Button.right':
                self.type_combo.setCurrentText("Click Phải")
            else:
                self.type_combo.setCurrentText("Click")
                
        self.x_spin.setValue(self.event_data.get('x', 0))
        self.y_spin.setValue(self.event_data.get('y', 0))
        
        # Coordinate Mode
        mode = self.event_data.get('coordinate_mode', 'absolute')
        if mode == 'relative':
            self.check_relative.setChecked(True)
        elif mode == 'offset':
            self.check_offset.setChecked(True)
        else:
            # Absolute: both unchecked
            self.check_relative.setChecked(False)
            self.check_offset.setChecked(False)
            
        # Ignore Coords
        self.ignore_check.setChecked(self.event_data.get('ignore_coordinates', False))
        
        # Randomize
        self.rand_spin.setValue(self.event_data.get('randomize_pixels', 0))
        
        # Wheel
        self.wheel_spin.setValue(self.event_data.get('dy', 0))
        
    def get_data(self):
        etype_text = self.type_combo.currentText()
        data = {
            'x': self.x_spin.value(),
            'y': self.y_spin.value(),
            'time': self.event_data.get('time', 0.5), # Preserve time
            'ignore_coordinates': self.ignore_check.isChecked(),
            'randomize_pixels': self.rand_spin.value()
        }
        
        # Coordinate Mode
        if self.check_relative.isChecked():
            data['coordinate_mode'] = 'relative'
        elif self.check_offset.isChecked():
            data['coordinate_mode'] = 'offset'
        else:
            data['coordinate_mode'] = 'absolute'
        
        if etype_text == "Di chuyển":
            data['type'] = 'mouse_move'
        elif etype_text == "Cuộn chuột":
            data['type'] = 'mouse_scroll'
            data['dy'] = self.wheel_spin.value()
        elif etype_text == "Giữ Chuột trái":
            data['type'] = 'mouse_hold'
            data['button'] = 'Button.left'
            data['duration'] = self.duration_spin.value()
            data['pressed'] = True
        else:
            data['type'] = 'mouse_click'
            data['pressed'] = True 
            if etype_text == "Click Phải":
                data['button'] = 'Button.right'
            else:
                data['button'] = 'Button.left'
                
        return data
