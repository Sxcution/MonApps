from PySide6.QtWidgets import QToolBar, QWidget, QHBoxLayout, QToolButton, QSizePolicy
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QIcon

class MainToolbar(QToolBar):
    close_requested = Signal()  # Signal to request closing the app
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setFloatable(False)
        self.setOrientation(Qt.Orientation.Horizontal)
        self.setIconSize(QSize(24, 24))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)  # Disable right-click menu
        
        # Setup Actions
        # File Menu Actions
        self.new_action = QAction("New", self)
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.setStatusTip("Create new macro")
        
        self.open_action = QAction("Open...", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.setStatusTip("Open recorded file")
        
        self.save_action = QAction("Save", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.setStatusTip("Save current macro")
        
        self.save_as_action = QAction("Save as...", self)
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.save_as_action.setStatusTip("Save current macro as new file")
        
        self.exit_action = QAction("Exit", self)
        self.exit_action.setShortcut("Alt+F4")
        self.exit_action.setStatusTip("Exit application")

        # File Menu Button
        self.file_button = QToolButton(self)
        self.file_button.setText("File")
        self.file_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        from PySide6.QtWidgets import QMenu
        self.file_menu = QMenu(self.file_button)
        self.file_menu.addAction(self.new_action)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.save_action)
        self.file_menu.addAction(self.save_as_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)
        
        self.file_button.setMenu(self.file_menu)
        
        self.add_action = QAction("Add", self)
        self.add_action.setStatusTip("Add new step")
        
        self.play_action = QAction("Play", self)
        self.play_action.setCheckable(True)
        self.play_action.setStatusTip("Play/Stop recording")
        
        self.record_action = QAction("Record", self)
        self.record_action.setCheckable(True)
        self.record_action.setStatusTip("Start/Stop recording")
        
        self.settings_action = QAction("Settings", self)
        self.settings_action.setStatusTip("Configure application settings")
        
        # Close button for embedded mode
        self.close_action = QAction("✖", self)
        self.close_action.setStatusTip("Đóng ứng dụng nhúng")
        self.close_action.triggered.connect(self.close_requested.emit)
        
        # Add actions to toolbar
        self.addWidget(self.file_button)
        self.addSeparator()
        self.addAction(self.add_action)
        self.addSeparator()
        self.addAction(self.play_action)
        self.addSeparator()
        self.addAction(self.record_action)
        self.addSeparator()
        self.addAction(self.settings_action)
        
        # Add spacer to push close button to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)
        
        # Add close button at the far right (only visible when embedded)
        self.close_action_item = self.addAction(self.close_action)
        # Hide by removing it initially
        self.close_visible = False
        
        # Style close button text to red
        self.setStyleSheet("""
            QToolBar QToolButton:hover:!checked {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        
        # Connect signals
        self.play_action.toggled.connect(self.on_play_toggled)
        self.record_action.toggled.connect(self.on_record_toggled)
    
    def set_embedded_mode(self, embedded):
        """Show/hide close button based on embedded mode"""
        if embedded and not self.close_visible:
            # Make action visible by re-adding if needed
            self.close_visible = True
            widget = self.widgetForAction(self.close_action_item)
            if widget:
                widget.setVisible(True)
        elif not embedded and self.close_visible:
            self.close_visible = False
            widget = self.widgetForAction(self.close_action_item)
            if widget:
                widget.setVisible(False)

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
