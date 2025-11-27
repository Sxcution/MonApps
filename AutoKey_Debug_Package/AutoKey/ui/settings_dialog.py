from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QKeySequenceEdit)
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QKeySequence

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = QSettings("MonSoft", "MacroRecorder")
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Hotkey Fields
        self.record_hotkey = QKeySequenceEdit()
        self.record_hotkey.setMaximumSequenceLength(1)
        
        self.stop_record_hotkey = QKeySequenceEdit()
        self.stop_record_hotkey.setMaximumSequenceLength(1)
        
        self.play_hotkey = QKeySequenceEdit()
        self.play_hotkey.setMaximumSequenceLength(1)
        
        form_layout.addRow("Start Record Hotkey:", self.record_hotkey)
        form_layout.addRow("Stop Record Hotkey:", self.stop_record_hotkey)
        form_layout.addRow("Play/Stop Hotkey:", self.play_hotkey)
        
        layout.addLayout(form_layout)
        
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
        
        # Connect signals for validation
        self.record_hotkey.keySequenceChanged.connect(self.validate_hotkeys)
        self.stop_record_hotkey.keySequenceChanged.connect(self.validate_hotkeys)
        self.play_hotkey.keySequenceChanged.connect(self.validate_hotkeys)
        
        # Apply Styles
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; color: #333333; }
            QLabel { color: #333333; font-weight: bold; }
            QKeySequenceEdit { 
                padding: 5px; 
                border: 1px solid #cccccc; 
                border-radius: 3px;
                color: #333333;
                background-color: #ffffff;
                selection-background-color: #0078d4;
            }
            QKeySequenceEdit:focus {
                border: 2px solid #0078d4;
                background-color: #ffffff;
            }
            QLineEdit {
                padding: 5px; 
                border: 1px solid #cccccc; 
                border-radius: 4px;
                color: #333333;
                background-color: #f9f9f9;
            }
            QPushButton {
                padding: 6px 12px;
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #106ebe; }
            QPushButton:disabled { background-color: #cccccc; }
        """)

    def validate_hotkeys(self):
        hotkeys = {}
        duplicates = []
        
        # Helper to check
        def check(name, widget):
            seq = widget.keySequence().toString()
            if not seq: return
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

    def save_settings(self):
        # Save hotkeys
        self.settings.setValue("hotkey_record", self.record_hotkey.keySequence().toString())
        self.settings.setValue("hotkey_stop_record", self.stop_record_hotkey.keySequence().toString())
        self.settings.setValue("hotkey_play", self.play_hotkey.keySequence().toString())
