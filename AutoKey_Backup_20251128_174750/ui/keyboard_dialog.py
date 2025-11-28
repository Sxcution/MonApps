from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QSpinBox, QDialogButtonBox, QKeySequenceEdit)
from PyQt6.QtGui import QKeySequence

class KeyboardActionDialog(QDialog):
    def __init__(self, parent=None, event_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit selected command")
        self.setWindowTitle("Edit selected command")
        # Removed setFixedSize to allow auto-sizing
        
        self.event_data = event_data or {}
        
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize) # Auto-fit content
        layout.setSpacing(10)
        
        # Combined Row for Key and Type (Swapped)
        row_layout = QHBoxLayout()
        row_layout.setSpacing(10) # Minimal spacing
        
        # Key (First now)
        row_layout.addWidget(QLabel("Key:"))
        self.key_edit = QKeySequenceEdit()
        self.key_edit.setMaximumSequenceLength(1)
        self.key_edit.setFixedWidth(100) # Reduced width
        row_layout.addWidget(self.key_edit)
        
        # Type (Second now)
        row_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["KeyPress", "KeyDown", "KeyUp"])
        self.type_combo.setFixedWidth(90) # Reduced width
        row_layout.addWidget(self.type_combo)
        
        row_layout.addStretch()
        layout.addLayout(row_layout)
        
        # Removed layout.addStretch() to bring buttons closer
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.load_data()
        
        # Auto-focus the key input
        self.key_edit.setFocus()
        
    def load_data(self):
        etype = self.event_data.get('type', 'key_click') # Default to click for new/unknown
        if etype == 'key_click':
            self.type_combo.setCurrentText("KeyPress")
        elif etype == 'key_press':
            self.type_combo.setCurrentText("KeyDown")
        elif etype == 'key_release':
            self.type_combo.setCurrentText("KeyUp")
        
        key = self.event_data.get('key', '')
        if key:
            self.key_edit.setKeySequence(QKeySequence(key))
            
    def get_data(self):
        etype_text = self.type_combo.currentText()
        
        # Get key string from sequence
        key_seq = self.key_edit.keySequence().toString()
        
        data = {
            'key': key_seq,
            'time': self.event_data.get('time', 0.5)
        }
        
        if etype_text == "KeyUp":
            data['type'] = 'key_release'
        elif etype_text == "KeyDown":
            data['type'] = 'key_press'
        else:
            # KeyPress = Click
            data['type'] = 'key_click'
            
        return data
