from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTableView, QHeaderView, QToolButton
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTableView, QHeaderView
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTableView, QHeaderView
from PyQt6.QtCore import QSettings, QSize, QPoint, Qt, pyqtSlot
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QAction
import threading

from ui.toolbar import MainToolbar
from ui.styles import MAIN_STYLESHEET
from core.recorder import Recorder
from core.player import Player

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Macro Recorder")
        self.settings = QSettings("MonSoft", "MacroRecorder")
        
        # Setup UI
        self.setup_ui()
        
        # Restore window state
        self.restore_geometry()

    def setup_ui(self):
        # Central Widget
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.central_widget.setAutoFillBackground(True)
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        self.toolbar = MainToolbar(self)
        self.addToolBar(self.toolbar)
        
        # Table View (Placeholder for steps)
        self.table_view = QTableView()
        self.model = QStandardItemModel(0, 3)
        self.model.setHorizontalHeaderLabels(["Action", "Details", "Delay (ms)"])
        self.table_view.setModel(self.model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setShowGrid(False)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)
        
        self.layout.addWidget(self.table_view)
        
        # Apply Theme
        print("🔍 Applying MAIN_STYLESHEET for solid white theme")
        self.setStyleSheet(MAIN_STYLESHEET)
        
        # Connect Toolbar Actions
        self.toolbar.open_action.triggered.connect(self.load_recording)
        self.toolbar.record_action.toggled.connect(self.toggle_recording)
        self.toolbar.play_action.toggled.connect(self.toggle_playing)
        
        # Settings Menu
        from PyQt6.QtWidgets import QMenu
        settings_menu = QMenu(self)
        hotkey_action = settings_menu.addAction("Hotkeys")
        hotkey_action.triggered.connect(self.open_hotkey_settings)
        self.toolbar.settings_action.setMenu(settings_menu)
        
        # Make the button show the menu immediately (optional, depends on Qt style)
        # For QToolButton with menu, we usually want InstantPopup or MenuButtonPopup
        widget = self.toolbar.widgetForAction(self.toolbar.settings_action)
        if widget:
            widget.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        # Add Save Action (not in original spec but essential)
        self.save_action = QAction("Save", self)
        self.save_action.triggered.connect(self.save_recording)
        self.toolbar.insertAction(self.toolbar.play_action, self.save_action) # Insert before Play
        self.toolbar.insertSeparator(self.toolbar.play_action)
        
        # Logic Components
        self.recorder = Recorder()
        self.recorder.event_recorded.connect(self.add_event_to_table)
        self.player = None
        self.stop_playback_event = threading.Event()
        self.recorded_events = []
        
        # Setup Hotkeys
        self.setup_global_hotkeys()

    def toggle_recording(self, checked):
        if checked:
            # Start Recording
            self.model.removeRows(0, self.model.rowCount()) # Clear table
            self.recorded_events = []
            self.recorder.start_recording()
            self.statusBar().showMessage("Recording...")
        else:
            # Stop Recording
            self.recorded_events = self.recorder.stop_recording()
            self.statusBar().showMessage(f"Recording stopped. {len(self.recorded_events)} events captured.")

    def toggle_playing(self, checked):
        if checked:
            if not self.recorded_events:
                self.statusBar().showMessage("No events to play.")
                self.toolbar.play_action.setChecked(False)
                return
            
            self.statusBar().showMessage("Playing...")
            self.stop_playback_event.clear()
            self.player = Player(self.recorded_events, self.stop_playback_event)
            self.player.start()
            
            # Watch for playback finish (simplified)
            # In a real app, we'd use a signal from the player thread
        else:
            self.statusBar().showMessage("Stopping playback...")
            self.stop_playback_event.set()

    def add_event_to_table(self, event):
        # Add row to table
        row = self.model.rowCount()
        self.model.insertRow(row)
        
        action_item = QStandardItem(event['type'])
        
        details = ""
        if event['type'] == 'mouse_move':
            details = f"x={event['x']}, y={event['y']}"
        elif event['type'] == 'mouse_click':
            details = f"{event['button']} {'Down' if event['pressed'] else 'Up'} at {event['x']},{event['y']}"
        elif event['type'] == 'key_press':
            details = f"Key {event['key']} Down"
        elif event['type'] == 'key_release':
            details = f"Key {event['key']} Up"
        elif event['type'] == 'wait_image':
            details = f"Wait Image: {event['path']}"
            
        details_item = QStandardItem(details)
        delay_item = QStandardItem(f"{event['time']:.3f}s")
        
        self.model.setItem(row, 0, action_item)
        self.model.setItem(row, 1, details_item)
        self.model.setItem(row, 2, delay_item)
        self.table_view.scrollToBottom()

    def save_recording(self):
        if not self.recorded_events:
            return
            
        from PyQt6.QtWidgets import QFileDialog
        import json
        
        filename, _ = QFileDialog.getSaveFileName(self, "Save Macro", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.recorded_events, f, indent=4)
                self.statusBar().showMessage(f"Saved to {filename}")
            except Exception as e:
                self.statusBar().showMessage(f"Error saving: {e}")

    def load_recording(self):
        from PyQt6.QtWidgets import QFileDialog
        import json
        
        filename, _ = QFileDialog.getOpenFileName(self, "Open Macro", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'r') as f:
                    self.recorded_events = json.load(f)
                
                self.model.removeRows(0, self.model.rowCount())
                for event in self.recorded_events:
                    self.add_event_to_table(event)
                    
                self.statusBar().showMessage(f"Loaded {len(self.recorded_events)} events from {filename}")
            except Exception as e:
                self.statusBar().showMessage(f"Error loading: {e}")

    def show_context_menu(self, pos):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        insert_action = menu.addAction("Insert 'Wait for Image' Step")
        action = menu.exec(self.table_view.viewport().mapToGlobal(pos))
        
        if action == insert_action:
            self.insert_wait_image()

    def insert_wait_image(self):
        from PyQt6.QtWidgets import QFileDialog, QInputDialog
        
        path, _ = QFileDialog.getOpenFileName(self, "Select Image Template", "", "Images (*.png *.jpg *.bmp)")
        if not path:
            return
            
        timeout, ok = QInputDialog.getInt(self, "Timeout", "Wait timeout (seconds):", 30, 1, 3600)
        if not ok:
            return
            
        event = {
            'type': 'wait_image',
            'path': path,
            'timeout': timeout,
            'time': 0.5 # Default small delay
        }
        
        self.recorded_events.append(event)
        self.add_event_to_table(event)

    def open_hotkey_settings(self):
        # Disable global hotkeys while in settings to prevent accidental triggering
        if hasattr(self, 'hotkey_listener') and self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None
            
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        if dialog.exec():
            dialog.save_settings()
            self.setup_global_hotkeys() # Reload hotkeys
            self.statusBar().showMessage("Settings saved.")
        else:
            # Re-enable hotkeys if cancelled
            self.setup_global_hotkeys()

    def setup_global_hotkeys(self):
        # Stop existing listener if any
        if hasattr(self, 'hotkey_listener') and self.hotkey_listener:
            self.hotkey_listener.stop()
            
        # Load hotkeys
        rec_key = self.settings.value("hotkey_record", "F9")
        stop_rec_key = self.settings.value("hotkey_stop_record", "F10")
        play_key = self.settings.value("hotkey_play", "F11")
        
        # Convert QKeySequence string to pynput format (simplified)
        # Note: pynput expects specific format (e.g. '<ctrl>+<alt>+h')
        # QKeySequence might return 'Ctrl+Alt+H'. We need a mapper or use a library that handles this better.
        # For now, let's assume simple function keys or single keys for stability, 
        # or do a basic replacement.
        
        def to_pynput(k):
            k = k.lower()
            k = k.replace("ctrl+", "<ctrl>+")
            k = k.replace("alt+", "<alt>+")
            k = k.replace("shift+", "<shift>+")
            # Handle F-keys
            if len(k) > 1 and k.startswith('f') and k[1:].isdigit():
                k = k.replace("f", "<f") + ">"
                k = k.replace("<<f", "<f") # fix double < if any
            return k

        # Mapping for pynput GlobalHotKeys
        self.hotkey_map = {
            to_pynput(rec_key): self.on_hotkey_record,
            to_pynput(stop_rec_key): self.on_hotkey_stop_record,
            to_pynput(play_key): self.on_hotkey_play
        }
        
        try:
            from pynput import keyboard
            self.hotkey_listener = keyboard.GlobalHotKeys(self.hotkey_map)
            self.hotkey_listener.start()
            print(f"Hotkeys registered: {self.hotkey_map.keys()}")
        except Exception as e:
            print(f"Failed to register hotkeys: {e}")

    def on_hotkey_record(self):
        # Use QMetaObject.invokeMethod to ensure thread safety with GUI
        from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
        QMetaObject.invokeMethod(self, "toggle_recording_safe", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, True))

    def on_hotkey_stop_record(self):
        from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
        QMetaObject.invokeMethod(self, "toggle_recording_safe", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, False))

    def on_hotkey_play(self):
        from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
        # Toggle play state
        is_playing = self.toolbar.play_action.isChecked()
        QMetaObject.invokeMethod(self, "toggle_playing_safe", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, not is_playing))

    # Thread-safe slots
    @pyqtSlot(bool)
    def toggle_recording_safe(self, start):
        if start:
            if not self.toolbar.record_action.isChecked():
                self.toolbar.record_action.setChecked(True)
        else:
            if self.toolbar.record_action.isChecked():
                self.toolbar.record_action.setChecked(False)

    @pyqtSlot(bool)
    def toggle_playing_safe(self, start):
        self.toolbar.play_action.setChecked(start)

    def restore_geometry(self):
        # Restore size and position
        size = self.settings.value("window_size", QSize(800, 600))
        pos = self.settings.value("window_pos", QPoint())
        
        self.resize(size)
        
        if pos.isNull():
            # Center on screen if no saved position
            self.center_on_screen()
        else:
            self.move(pos)

    def center_on_screen(self):
        frame_gm = self.frameGeometry()
        screen = self.screen().availableGeometry().center()
        frame_gm.moveCenter(screen)
        self.move(frame_gm.topLeft())

    def closeEvent(self, event):
        # Save window state
        self.settings.setValue("window_size", self.size())
        self.settings.setValue("window_pos", self.pos())
        super().closeEvent(event)
