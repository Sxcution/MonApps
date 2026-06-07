from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QSpinBox, QDialogButtonBox, QKeySequenceEdit)
from PySide6.QtGui import QKeySequence
from utils.preset_shortcuts import get_preset_names

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
        
        # Row 1: Key Input and Type
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(10)
        
        # Key (First)
        self.key_label = QLabel("Key:")
        row1_layout.addWidget(self.key_label)
        self.key_edit = QKeySequenceEdit()
        self.key_edit.setMaximumSequenceLength(1)
        self.key_edit.setFixedWidth(100)
        row1_layout.addWidget(self.key_edit)
        
        # Type (Second)
        row1_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["KeyPress", "KeyDown", "KeyUp"])
        self.type_combo.setFixedWidth(90)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        row1_layout.addWidget(self.type_combo)
        
        row1_layout.addStretch()
        layout.addLayout(row1_layout)
        
        # Row 2: Preset Shortcuts (only shown when not Custom)
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(10)
        
        row2_layout.addWidget(QLabel("Shortcut:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(get_preset_names())
        self.preset_combo.setFixedWidth(150)
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        row2_layout.addWidget(self.preset_combo)
        
        row2_layout.addStretch()
        layout.addLayout(row2_layout)
        
        # Duration Row (for KeyDown only)
        self.duration_row = QHBoxLayout()
        self.duration_row.setSpacing(10)
        self.duration_label = QLabel("Hold Duration:")
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0, 60000)  # 0 to 60 seconds
        self.duration_spin.setSuffix(" ms")
        self.duration_spin.setValue(1000)  # Default 1 second
        self.duration_spin.setFixedWidth(120)
        self.duration_row.addWidget(self.duration_label)
        self.duration_row.addWidget(self.duration_spin)
        self.duration_row.addStretch()
        layout.addLayout(self.duration_row)
        
        # Hide duration by default
        self.duration_label.hide()
        self.duration_spin.hide()
        
        # Removed layout.addStretch() to bring buttons closer
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.load_data()
        
        # Auto-focus the key input
        self.key_edit.setFocus()
    
    def _on_preset_changed(self, preset_text):
        """Show/hide key input field based on preset selection"""
        if preset_text == "Custom":
            self.key_label.show()
            self.key_edit.show()
        else:
            self.key_label.hide()
            self.key_edit.hide()
    
    def _on_type_changed(self, type_text):
        """Show/hide duration field based on type"""
        if type_text == "KeyDown":
            self.duration_label.show()
            self.duration_spin.show()
        else:
            self.duration_label.hide()
            self.duration_spin.hide()
        
    def load_data(self):
        etype = self.event_data.get('type', 'key_click')
        
        # Check if this is a preset shortcut
        if etype == 'key_preset':
            preset_name = self.event_data.get('preset', 'Alt+Tab')
            self.preset_combo.setCurrentText(preset_name)
            # Key input will be hidden by _on_preset_changed signal
            self.type_combo.setCurrentText("KeyPress")  # Presets always use KeyPress
        else:
            # Custom key - set preset to "Custom"
            self.preset_combo.setCurrentText("Custom")
            
            # Set type
            if etype == 'key_click':
                self.type_combo.setCurrentText("KeyPress")
            elif etype == 'key_press':
                self.type_combo.setCurrentText("KeyDown")
            elif etype == 'key_release':
                self.type_combo.setCurrentText("KeyUp")
            
            # Set key
            key = self.event_data.get('key', '')
            if key:
                self.key_edit.setKeySequence(QKeySequence(key))
            
            # Load hold duration if exists
            hold_duration = self.event_data.get('hold_duration', 1000)
            self.duration_spin.setValue(hold_duration)
            
            # Show duration field if KeyDown
            if self.type_combo.currentText() == "KeyDown":
                self.duration_label.show()
                self.duration_spin.show()
            
    def get_data(self):
        preset_name = self.preset_combo.currentText()
        
        # If a preset is selected, return preset format
        if preset_name != "Custom":
            return {
                'type': 'key_preset',
                'preset': preset_name,
                'time': self.event_data.get('time', 0.5)
            }
        
        # Otherwise, return custom key format
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
            data['hold_duration'] = self.duration_spin.value()
        else:
            # KeyPress = Click
            data['type'] = 'key_click'
            
        return data
