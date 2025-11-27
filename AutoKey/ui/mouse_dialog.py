from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QSpinBox, QRadioButton, QCheckBox, 
                             QGroupBox, QPushButton, QDialogButtonBox, QWidget)
from PyQt6.QtCore import Qt

class MouseActionDialog(QDialog):
    def __init__(self, parent=None, event_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit selected command")
        self.setFixedSize(500, 450)
        
        self.event_data = event_data or {}
        
        layout = QVBoxLayout(self)
        
        # Description
        layout.addWidget(QLabel("Mouse Command moves the mouse cursor to the specified coordinates"))
        
        # Event Type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Event type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Click", "Right Click", "Double Click", "Move", "Wheel"])
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # Coordinates Group
        coord_group = QGroupBox("Coordinates")
        coord_layout = QVBoxLayout(coord_group)
        
        # X/Y Inputs
        xy_layout = QHBoxLayout()
        self.x_spin = QSpinBox()
        self.x_spin.setRange(-10000, 10000)
        self.y_spin = QSpinBox()
        self.y_spin.setRange(-10000, 10000)
        
        xy_layout.addWidget(self.x_spin)
        xy_layout.addWidget(self.y_spin)
        
        # Helper Text
        helper_text = QLabel("Press F2 to capture current position\nPress F3 to hide main recorder window")
        helper_text.setStyleSheet("color: gray;")
        xy_layout.addWidget(helper_text)
        
        coord_layout.addLayout(xy_layout)
        
        # Radio Buttons
        self.radio_absolute = QRadioButton("The above coordinates are absolute (screen-based)")
        self.radio_relative = QRadioButton("The above coordinates are relative to the active (foreground) window")
        self.radio_offset = QRadioButton("The above coordinates are offset to the previous mouse position")
        
        coord_layout.addWidget(self.radio_absolute)
        coord_layout.addWidget(self.radio_relative)
        coord_layout.addWidget(self.radio_offset)
        
        # Ignore Checkbox
        self.ignore_check = QCheckBox("Ignore the above coordinates - execute at the current position.")
        coord_layout.addWidget(self.ignore_check)
        
        # Randomize
        rand_layout = QHBoxLayout()
        rand_layout.addWidget(QLabel("Randomize coordinates by"))
        self.rand_spin = QSpinBox()
        self.rand_spin.setRange(0, 100)
        rand_layout.addWidget(self.rand_spin)
        rand_layout.addWidget(QLabel("pixels"))
        rand_layout.addStretch()
        coord_layout.addLayout(rand_layout)
        
        layout.addWidget(coord_group)
        
        # Wheel
        wheel_layout = QHBoxLayout()
        wheel_layout.addWidget(QLabel("Wheel:"))
        self.wheel_spin = QSpinBox()
        self.wheel_spin.setRange(-1000, 1000)
        wheel_layout.addWidget(self.wheel_spin)
        wheel_layout.addStretch()
        layout.addLayout(wheel_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Set Data
        self.load_data()
        
    def load_data(self):
        # Map event type
        etype = self.event_data.get('type', 'mouse_click')
        button = self.event_data.get('button', 'Button.left')
        
        if etype == 'mouse_move':
            self.type_combo.setCurrentText("Move")
        elif etype == 'mouse_scroll':
            self.type_combo.setCurrentText("Wheel")
        elif etype == 'mouse_click':
            if button == 'Button.right':
                self.type_combo.setCurrentText("Right Click")
            # TODO: Double click logic needs support in recorder/player
            else:
                self.type_combo.setCurrentText("Click")
                
        self.x_spin.setValue(self.event_data.get('x', 0))
        self.y_spin.setValue(self.event_data.get('y', 0))
        
        # Defaults
        self.radio_absolute.setChecked(True)
        
    def get_data(self):
        etype_text = self.type_combo.currentText()
        data = {
            'x': self.x_spin.value(),
            'y': self.y_spin.value(),
            'time': self.event_data.get('time', 0.5) # Preserve time
        }
        
        if etype_text == "Move":
            data['type'] = 'mouse_move'
        elif etype_text == "Wheel":
            data['type'] = 'mouse_scroll'
            data['dy'] = self.wheel_spin.value()
        else:
            data['type'] = 'mouse_click'
            data['pressed'] = True # Assume click is press+release or just press? 
            # Jitbit "Click" usually means full click. Our player handles press/release separately or as one?
            # Our current player handles separate events. 
            # For simplicity, let's assume this dialog creates a "Click" which the player interprets as Down+Up.
            # Or we stick to our event model.
            if etype_text == "Right Click":
                data['button'] = 'Button.right'
            else:
                data['button'] = 'Button.left'
                
        return data
