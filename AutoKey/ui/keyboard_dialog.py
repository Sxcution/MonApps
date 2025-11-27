from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QSpinBox, QDialogButtonBox)

class KeyboardActionDialog(QDialog):
    def __init__(self, parent=None, event_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit selected command")
        self.setFixedSize(400, 200)
        
        self.event_data = event_data or {}
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("This command send keystrokes to the currently active window"))
        
        # Event Type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Keyboard event type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["KeyPress", "KeyDown", "KeyUp"])
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # Key
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Key:"))
        self.key_combo = QComboBox()
        # Populate with common keys
        keys = [chr(i) for i in range(65, 91)] + [str(i) for i in range(10)] # A-Z, 0-9
        keys.extend(["Enter", "Space", "Tab", "Esc", "Backspace", "Shift", "Ctrl", "Alt"])
        self.key_combo.addItems(keys)
        self.key_combo.setEditable(True) # Allow typing
        
        key_layout.addWidget(self.key_combo)
        
        # ASCII/Scan code (placeholder)
        self.code_spin = QSpinBox()
        self.code_spin.setEnabled(False)
        key_layout.addWidget(self.code_spin)
        
        layout.addLayout(key_layout)
        
        layout.addStretch()
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.load_data()
        
    def load_data(self):
        etype = self.event_data.get('type', 'key_press')
        if etype == 'key_press':
            self.type_combo.setCurrentText("KeyPress")
        elif etype == 'key_release':
            self.type_combo.setCurrentText("KeyUp")
        # KeyDown isn't strictly in our model yet (we have press/release), but 'key_press' usually implies down.
        
        key = self.event_data.get('key', '')
        if key:
            self.key_combo.setCurrentText(key.upper())
            
    def get_data(self):
        etype_text = self.type_combo.currentText()
        data = {
            'key': self.key_combo.currentText().lower(),
            'time': self.event_data.get('time', 0.5)
        }
        
        if etype_text == "KeyUp":
            data['type'] = 'key_release'
        else:
            data['type'] = 'key_press'
            
        return data
