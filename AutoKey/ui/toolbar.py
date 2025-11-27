from PyQt6.QtWidgets import QToolBar, QWidget, QHBoxLayout, QToolButton, QSizePolicy
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QIcon

class MainToolbar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setFloatable(False)
        self.setOrientation(Qt.Orientation.Horizontal)
        self.setIconSize(QSize(24, 24))
        
        # Setup Actions
        self.open_action = QAction("Open", self)
        self.open_action.setStatusTip("Open recorded file")
        
        self.play_action = QAction("Play", self)
        self.play_action.setCheckable(True)
        self.play_action.setStatusTip("Play/Stop recording")
        
        self.record_action = QAction("Record", self)
        self.record_action.setCheckable(True)
        self.record_action.setStatusTip("Start/Stop recording")
        
        self.settings_action = QAction("Settings", self)
        self.settings_action.setStatusTip("Configure application settings")
        
        # Add actions to toolbar
        self.addAction(self.open_action)
        self.addSeparator()
        self.addAction(self.play_action)
        self.addSeparator()
        self.addAction(self.record_action)
        self.addSeparator()
        self.addAction(self.settings_action)
        
        # Connect signals
        self.play_action.toggled.connect(self.on_play_toggled)
        self.record_action.toggled.connect(self.on_record_toggled)

    def on_play_toggled(self, checked):
        if checked:
            self.play_action.setText("Stop")
            # If recording is active, stop it
            if self.record_action.isChecked():
                self.record_action.setChecked(False)
        else:
            self.play_action.setText("Play")

    def on_record_toggled(self, checked):
        if checked:
            self.record_action.setText("Stop Rec")
            # If playing is active, stop it
            if self.play_action.isChecked():
                self.play_action.setChecked(False)
        else:
            self.record_action.setText("Record")
