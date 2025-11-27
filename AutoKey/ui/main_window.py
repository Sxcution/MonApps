from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTableView, QHeaderView, 
                             QToolButton, QMenu, QFileDialog, QInputDialog)
from PyQt6.QtCore import QSettings, QSize, QPoint, Qt, pyqtSlot
import ctypes
from ctypes import c_int, byref
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QAction, QPalette, QColor
import threading

from ui.toolbar import MainToolbar
from ui.styles import MAIN_STYLESHEET
from core.recorder import Recorder
from core.player import Player

from ui.delegates import ActionDelegate, NumberDelegate
from ui.mouse_dialog import MouseActionDialog
from ui.keyboard_dialog import KeyboardActionDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Macro Recorder")
        self.settings = QSettings("MonSoft", "MacroRecorder")
        
        # --- FORCE PURE WHITE BACKGROUND (SYSTEM LEVEL) ---
        white_palette = QPalette()
        white_palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
        white_palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        self.setPalette(white_palette)
        self.setAutoFillBackground(True)
        # ------------------------------------------------
        
        # Setup UI
        self.setup_ui()
        
        # 3. CALL THE DWM FIX
        self.disable_system_backdrop()
        
        # Restore window state
        self.restore_geometry()

    def disable_system_backdrop(self):
        """
        HARD FIX: Calls Windows DWM API to:
        1. Disable Mica/Acrylic effects (Solid Window)
        2. Force Title Bar to White
        3. Force Title Text to Black
        """
        try:
            # Get the Window Handle (HWND)
            hwnd = int(self.winId())
            
            # Constants for Windows DWM
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            DWMWA_SYSTEMBACKDROP_TYPE = 38
            DWMWA_CAPTION_COLOR = 35
            DWMWA_TEXT_COLOR = 36
            DWMSBT_NONE = 1
            
            dwmapi = ctypes.windll.dwmapi
            
            # 1. Disable Backdrop (Solid Background)
            val_none = c_int(DWMSBT_NONE)
            dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, byref(val_none), 4)
            
            # 2. Force Light Mode (for Title Bar)
            val_light = c_int(0)
            dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, byref(val_light), 4)
            
            # 3. Force Title Bar Color -> White (0x00FFFFFF)
            val_white = c_int(0x00FFFFFF)
            dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR, byref(val_white), 4)
            
            # 4. Force Title Text Color -> Black (0x00000000)
            val_black = c_int(0x00000000)
            dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_TEXT_COLOR, byref(val_black), 4)
            
            print("🔧 Windows DWM: Backdrop Disabled, Title Bar set to White.")
        except Exception as e:
            print(f"⚠️ DWM API Error: {e}")

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
        
        # Table View
        self.table_view = QTableView()
        self.model = QStandardItemModel(0, 4)
        # Reordered Columns: Step | Action | Delay (ms) | Details
        self.model.setHorizontalHeaderLabels(["Step", "Action", "Delay (ms)", "Details"])
        self.table_view.setModel(self.model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table_view.setColumnWidth(0, 50) # Fixed width for Step
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setShowGrid(True)
        self.table_view.verticalHeader().setVisible(False) # Hide default vertical header
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)
        
        # Connect Click for "Click to setup"
        self.table_view.clicked.connect(self.on_table_clicked)
        
        # Set Delegates
        self.table_view.setItemDelegateForColumn(1, ActionDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(2, NumberDelegate(self.table_view))
        
        # Connect Item Changed
        self.model.itemChanged.connect(self.on_item_changed)
        
        self.layout.addWidget(self.table_view)
        
        # Apply Theme
        print("🔍 Applying MAIN_STYLESHEET for solid white theme")
        self.setStyleSheet(MAIN_STYLESHEET)
        
        # Connect Toolbar Actions
        self.toolbar.new_action.triggered.connect(self.new_recording)
        self.toolbar.open_action.triggered.connect(self.load_recording)
        self.toolbar.save_action.triggered.connect(self.save_recording)
        self.toolbar.save_as_action.triggered.connect(self.save_recording_as)
        self.toolbar.exit_action.triggered.connect(self.close)
        
        self.toolbar.add_action.triggered.connect(self.add_empty_row)
        self.toolbar.record_action.toggled.connect(self.toggle_recording)
        self.toolbar.play_action.toggled.connect(self.toggle_playing)
        
        # Settings Menu
        settings_menu = QMenu(self)
        hotkey_action = settings_menu.addAction("Hotkeys")
        hotkey_action.triggered.connect(self.open_hotkey_settings)
        self.toolbar.settings_action.setMenu(settings_menu)
        
        # Make the button show the menu immediately
        widget = self.toolbar.widgetForAction(self.toolbar.settings_action)
        if widget:
            widget.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        # Logic Components
        self.recorder = Recorder()
        self.recorder.event_recorded.connect(self.add_event_to_table)
        self.player = None
        self.stop_playback_event = threading.Event()
        self.recorded_events = []
        self.current_filename = None # Track current file
        
        # Setup Hotkeys
        self.setup_global_hotkeys()

    def new_recording(self):
        self.model.removeRows(0, self.model.rowCount())
        self.recorded_events = []
        self.current_filename = None
        self.statusBar().showMessage("New macro created.")

    def add_empty_row(self):
        # Add a placeholder event
        event = {
            'type': 'undefined',
            'text': 'Click to setup',
            'time': 0.5
        }
        self.recorded_events.append(event)
        self.add_event_to_table(event)
        self.statusBar().showMessage("Added new step.")

    def toggle_recording(self, checked):
        if checked:
            # Start Recording
            if not self.recorded_events: 
                self.model.removeRows(0, self.model.rowCount()) 
                self.recorded_events = []
            
            self.recorder.start_recording()
            self.statusBar().showMessage("Recording...")
        else:
            # Stop Recording
            new_events = self.recorder.stop_recording()
            self.recorded_events.extend(new_events) # Append new events
            self.statusBar().showMessage(f"Recording stopped. {len(self.recorded_events)} events total.")

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
        else:
            self.statusBar().showMessage("Stopping playback...")
            self.stop_playback_event.set()

    def add_event_to_table(self, event):
        # Add row to table
        row = self.model.rowCount()
        self.model.insertRow(row)
        
        # Step Column (0)
        step_item = QStandardItem(str(row + 1))
        step_item.setEditable(False)
        step_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Action Column (1)
        action_text = ""
        if event['type'] == 'undefined':
            action_text = event['text']
        elif event['type'] == 'key_press':
             action_text = f"Key {event['key']} Down"
        elif event['type'] == 'key_release':
             action_text = f"Key {event['key']} Up"
        elif event['type'] == 'mouse_click':
             action_text = "Mouse Click"
        elif event['type'] == 'mouse_move':
             action_text = "Mouse Move"
        elif event['type'] == 'mouse_scroll':
             action_text = "Mouse Wheel"
        elif event['type'] == 'wait_image':
             action_text = "Wait Image"
             
        action_item = QStandardItem(action_text)
        action_item.setEditable(True)
        if event['type'] == 'undefined':
             action_item.setForeground(QColor("gray"))
             action_item.setEditable(False) # Prevent direct edit until setup
        
        # Delay Column (2) - Display in Milliseconds
        ms_delay = int(event.get('time', 0.5) * 1000)
        delay_item = QStandardItem(str(ms_delay))
        delay_item.setEditable(True)
        
        # Details Column (3)
        details = ""
        if event['type'] == 'mouse_move':
            details = f"x={event.get('x',0)}, y={event.get('y',0)}"
        elif event['type'] == 'mouse_click':
            details = f"{event.get('button','Left')} {'Down' if event.get('pressed',True) else 'Up'} at {event.get('x',0)},{event.get('y',0)}"
        elif event['type'] == 'key_press':
            details = f"Key: {event.get('key','')}"
        elif event['type'] == 'key_release':
            details = f"Key: {event.get('key','')}"
        elif event['type'] == 'mouse_scroll':
            details = f"Delta: {event.get('dy', 0)}"
        elif event['type'] == 'wait_image':
            details = f"Path: {event.get('path','')}"
            
        details_item = QStandardItem(details)
        details_item.setEditable(True)
        
        self.model.setItem(row, 0, step_item)
        self.model.setItem(row, 1, action_item)
        self.model.setItem(row, 2, delay_item)
        self.model.setItem(row, 3, details_item)
        self.table_view.scrollToBottom()

    def on_item_changed(self, item):
        # Handle edits
        row = item.row()
        col = item.column()
        
        if row >= len(self.recorded_events):
            return
            
        event = self.recorded_events[row]
        
        if col == 1: # Action
            text = item.text()
            # Smart Action Logic
            if text.startswith("Key ") and " Down" in text:
                pass
            elif len(text) == 1: # Single char typed (e.g. "W")
                event['type'] = 'key_press'
                event['key'] = text.lower()
                self.model.blockSignals(True)
                item.setText(f"Key {text} Down")
                self.model.blockSignals(False)
                
                details_item = self.model.item(row, 3)
                if details_item:
                    details_item.setText(f"Key: {text.lower()}")
                    
            elif text.lower() == "click":
                event['type'] = 'mouse_click'
                event['button'] = 'Button.left'
                event['pressed'] = True
                event['x'] = 0 
                event['y'] = 0
                self.model.blockSignals(True)
                item.setText("Mouse Click")
                self.model.blockSignals(False)
            
        elif col == 2: # Delay (ms input)
            try:
                ms_value = int(item.text())
                event['time'] = ms_value / 1000.0 
            except ValueError:
                pass 
                
        elif col == 3: # Details
            pass

    def on_table_clicked(self, index):
        if not index.isValid():
            return
            
        row = index.row()
        col = index.column()
        
        if row >= len(self.recorded_events):
            return
            
        event = self.recorded_events[row]
        
        # If clicking Action column (1)
        if col == 1:
            if event['type'] == 'undefined':
                self.show_setup_menu(index)
            else:
                # Optional: Allow opening dialog for existing items too?
                # For now, let's stick to "Click to setup" logic
                pass

    def show_setup_menu(self, index):
        menu = QMenu(self)
        mouse_action = menu.addAction("Mouse Action")
        keyboard_action = menu.addAction("Keyboard Action")
        
        action = menu.exec(self.table_view.viewport().mapToGlobal(self.table_view.visualRect(index).bottomLeft()))
        
        if action == mouse_action:
            self.open_mouse_dialog(index.row())
        elif action == keyboard_action:
            self.open_keyboard_dialog(index.row())

    def open_mouse_dialog(self, row):
        event = self.recorded_events[row]
        dialog = MouseActionDialog(self, event)
        if dialog.exec():
            new_data = dialog.get_data()
            self.update_event(row, new_data)

    def open_keyboard_dialog(self, row):
        event = self.recorded_events[row]
        dialog = KeyboardActionDialog(self, event)
        if dialog.exec():
            new_data = dialog.get_data()
            self.update_event(row, new_data)

    def update_event(self, row, new_data):
        # Merge new data into event
        self.recorded_events[row].update(new_data)
        # Refresh row
        self.refresh_row(row)

    def refresh_row(self, row):
        event = self.recorded_events[row]
        
        # Re-generate items
        # Step
        self.model.item(row, 0).setText(str(row + 1))
        
        # Action
        action_text = ""
        if event['type'] == 'key_press':
             action_text = f"Key {event['key']} Down"
        elif event['type'] == 'key_release':
             action_text = f"Key {event['key']} Up"
        elif event['type'] == 'mouse_click':
             action_text = "Mouse Click"
        elif event['type'] == 'mouse_move':
             action_text = "Mouse Move"
        elif event['type'] == 'mouse_scroll':
             action_text = "Mouse Wheel"
             
        self.model.item(row, 1).setText(action_text)
        self.model.item(row, 1).setForeground(QColor("black")) # Reset color
        self.model.item(row, 1).setEditable(True)
        
        # Delay
        ms_delay = int(event.get('time', 0.5) * 1000)
        self.model.item(row, 2).setText(str(ms_delay))
        
        # Details
        details = ""
        if event['type'] == 'mouse_move':
            details = f"x={event.get('x',0)}, y={event.get('y',0)}"
        elif event['type'] == 'mouse_click':
            details = f"{event.get('button','Left')} {'Down' if event.get('pressed',True) else 'Up'} at {event.get('x',0)},{event.get('y',0)}"
        elif event['type'] == 'key_press':
            details = f"Key: {event.get('key','')}"
        elif event['type'] == 'key_release':
            details = f"Key: {event.get('key','')}"
        elif event['type'] == 'mouse_scroll':
            details = f"Delta: {event.get('dy', 0)}"
            
        self.model.item(row, 3).setText(details)

    def save_recording(self):
        if not self.recorded_events:
            return
            
        if self.current_filename:
            self._save_to_file(self.current_filename)
        else:
            self.save_recording_as()

    def save_recording_as(self):
        if not self.recorded_events:
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Save Macro", "", "JSON Files (*.json)")
        if filename:
            self.current_filename = filename
            self._save_to_file(filename)

    def _save_to_file(self, filename):
        import json
        try:
            with open(filename, 'w') as f:
                json.dump(self.recorded_events, f, indent=4)
            self.statusBar().showMessage(f"Saved to {filename}")
        except Exception as e:
            self.statusBar().showMessage(f"Error saving: {e}")

    def load_recording(self):
        import json
        
        filename, _ = QFileDialog.getOpenFileName(self, "Open Macro", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'r') as f:
                    self.recorded_events = json.load(f)
                
                self.current_filename = filename
                self.model.removeRows(0, self.model.rowCount())
                for event in self.recorded_events:
                    self.add_event_to_table(event)
                    
                self.statusBar().showMessage(f"Loaded {len(self.recorded_events)} events from {filename}")
            except Exception as e:
                self.statusBar().showMessage(f"Error loading: {e}")

    def show_context_menu(self, pos):
        menu = QMenu(self)
        insert_action = menu.addAction("Insert 'Wait for Image' Step")
        action = menu.exec(self.table_view.viewport().mapToGlobal(pos))
        
        if action == insert_action:
            self.insert_wait_image()

    def insert_wait_image(self):
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
        if hasattr(self, 'hotkey_listener') and self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None
            
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        if dialog.exec():
            dialog.save_settings()
            self.setup_global_hotkeys() 
            self.statusBar().showMessage("Settings saved.")
        else:
            self.setup_global_hotkeys()

    def setup_global_hotkeys(self):
        if hasattr(self, 'hotkey_listener') and self.hotkey_listener:
            self.hotkey_listener.stop()
            
        rec_key = self.settings.value("hotkey_record", "F9")
        stop_rec_key = self.settings.value("hotkey_stop_record", "F10")
        play_key = self.settings.value("hotkey_play", "F11")
        
        def to_pynput(k):
            k = k.lower()
            k = k.replace("ctrl+", "<ctrl>+")
            k = k.replace("alt+", "<alt>+")
            k = k.replace("shift+", "<shift>+")
            if len(k) > 1 and k.startswith('f') and k[1:].isdigit():
                k = k.replace("f", "<f") + ">"
                k = k.replace("<<f", "<f") 
            return k

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
        from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
        QMetaObject.invokeMethod(self, "toggle_recording_safe", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, True))

    def on_hotkey_stop_record(self):
        from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
        QMetaObject.invokeMethod(self, "toggle_recording_safe", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, False))

    def on_hotkey_play(self):
        from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
        is_playing = self.toolbar.play_action.isChecked()
        QMetaObject.invokeMethod(self, "toggle_playing_safe", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, not is_playing))

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
        size = self.settings.value("window_size", QSize(800, 600))
        pos = self.settings.value("window_pos", QPoint())
        
        self.resize(size)
        
        if pos.isNull():
            self.center_on_screen()
        else:
            self.move(pos)

    def center_on_screen(self):
        frame_gm = self.frameGeometry()
        screen = self.screen().availableGeometry().center()
        frame_gm.moveCenter(screen)
        self.move(frame_gm.topLeft())

    def closeEvent(self, event):
        self.settings.setValue("window_size", self.size())
        self.settings.setValue("window_pos", self.pos())
        super().closeEvent(event)
