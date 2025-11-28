from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTableView, QHeaderView, 
                             QToolButton, QMenu, QFileDialog, QInputDialog, QAbstractItemView)
from PyQt6.QtCore import QSettings, QSize, QPoint, Qt, pyqtSlot, QTimer
import ctypes
from ctypes import c_int, byref
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QAction, QPalette, QColor, QIcon, QPixmap

import time
import threading
import uuid

from ui.toolbar import MainToolbar
from ui.styles import MAIN_STYLESHEET
from ui.playback_overlay import PlaybackOverlay
from core.recorder import Recorder
from core.player import Player

from ui.delegates import ActionDelegate, NumberDelegate
from ui.mouse_dialog import MouseActionDialog
from ui.keyboard_dialog import KeyboardActionDialog
from ui.image_search_dialog import ImageSearchDialog


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
        
        # Auto-load previous state
        self.load_autosave()

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
        self.model = QStandardItemModel(0, 5)
        # Reordered Columns: Step | Action | Delay (ms) | Details | Note
        self.model.setHorizontalHeaderLabels(["Step", "Action", "Delay (ms)", "Details", "Note"])
        self.table_view.setModel(self.model)
        
        # Configure Column Resizing
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table_view.setColumnWidth(0, 50) # Step
        
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table_view.setColumnWidth(1, 250) # Action
        
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_view.setColumnWidth(2, 80) # Delay (approx 6 digits)
        
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive) # Details
        self.table_view.setColumnWidth(3, 200)
        
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) # Note
        
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setShowGrid(True)
        self.table_view.verticalHeader().setVisible(False) # Hide default vertical header
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)
        
        # Enable larger icons for thumbnails
        self.table_view.setIconSize(QSize(300, 40))
        
        # Connect Click for "Click to setup"
        self.table_view.clicked.connect(self.on_table_clicked)
        # Connect Double Click to Edit
        self.table_view.doubleClicked.connect(self.on_table_double_clicked)
        
        # Enable Drag and Drop
        self.table_view.setDragEnabled(True)
        self.table_view.setAcceptDrops(True)
        self.table_view.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Set Delegates
        self.table_view.setItemDelegateForColumn(1, ActionDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(2, NumberDelegate(self.table_view))
        
        # Connect Item Changed
        self.model.itemChanged.connect(self.on_item_changed)
        self.model.rowsRemoved.connect(self.on_rows_removed)
        self.model.rowsInserted.connect(self.on_rows_inserted)
        
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
        hotkey_action.triggered.connect(lambda: self.open_settings(0))
        
        play_settings_action = settings_menu.addAction("Play Settings")
        play_settings_action.triggered.connect(lambda: self.open_settings(1))
        
        mini_mode_action = settings_menu.addAction("Mini Mode")
        mini_mode_action.triggered.connect(lambda: self.open_settings(2))
        
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
        self.pause_playback_event = threading.Event()  # For pause/resume
        self.recorded_events = []
        self.current_filename = None # Track current file
        
        # Playback Overlay
        self.overlay = PlaybackOverlay(self)
        self.overlay.stop_btn.clicked.connect(self.stop_playback_from_overlay)
        self.overlay.pause_btn.toggled.connect(self.pause_playback)
        
        # Timer for updating overlay time
        self.overlay_timer = QTimer(self)
        self.overlay_timer.timeout.connect(self.update_overlay_time)
        self.overlay_start_time = 0
        
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
            
            # Hide main window and show overlay
            self.hide()
            self.overlay.show()
            self.overlay.position_overlay()
            
            # Reset overlay
            play_count = int(self.settings.value("play_count", 1))
            self.overlay.update_loop(0, play_count)
            self.overlay.update_time(0)
            self.overlay.progress_bar.setValue(0)
            
            # Start timer for time updates
            self.overlay_start_time = time.time()
            self.overlay_timer.start(1000)  # Update every second
            
            self.statusBar().showMessage("Playing...")
            self.stop_playback_event.clear()
            self.pause_playback_event.clear()  # Start unpaused
            self.player = Player(self.recorded_events, self.stop_playback_event, self.pause_playback_event)
            
            # Connect signals
            self.player.progress_updated.connect(self.overlay.update_loop)
            self.player.time_updated.connect(self.overlay.update_time)
            self.player.playback_finished.connect(self.on_playback_finished)
            self.player.step_progress_updated.connect(self.overlay.update_step_progress)
            
            self.player.start()
        else:
            # Stop playback - hide overlay immediately and show main window
            self.statusBar().showMessage("Stopping playback...")
            self.stop_playback_event.set()
            self.overlay_timer.stop()
            self.overlay.hide()
            self.show()
    
    def stop_playback_from_overlay(self):
        """Stop playback when stop button is clicked in overlay"""
        # Immediately hide overlay and show main window
        self.overlay.hide()
        self.show()
        self.toolbar.play_action.setChecked(False)
    
    def pause_playback(self, paused):
        """Pause/resume playback - keeps overlay visible"""
        if paused:
            self.pause_playback_event.set()  # Set event to pause
            self.overlay_timer.stop()  # Stop time updates when paused
            self.overlay.pause_btn.setText("▶️ Resume")
        else:
            self.pause_playback_event.clear()  # Clear event to resume
            self.overlay_timer.start(1000)  # Resume time updates
            self.overlay.pause_btn.setText("⏸️ Pause")
    
    def update_overlay_time(self):
        """Update overlay time display"""
        if self.overlay.isVisible():
            elapsed = time.time() - self.overlay_start_time
            self.overlay.update_time(elapsed)
    
    def on_playback_finished(self):
        """Called when playback finishes"""
        self.overlay_timer.stop()
        self.overlay.hide()
        self.show()
        self.toolbar.play_action.setChecked(False)
        self.statusBar().showMessage("Playback finished.")

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
             action_text = f"Key Press {event['key']}"
        elif event['type'] == 'key_release':
             action_text = f"Key Release {event['key']}"
        elif event['type'] == 'key_click':
             action_text = f"Key Click {event['key']}"
        elif event['type'] == 'mouse_click':
             action_text = "Mouse Click"
        elif event['type'] == 'mouse_move':
             action_text = "Mouse Move"
        elif event['type'] == 'mouse_scroll':
             action_text = "Mouse Wheel"
        elif event['type'] == 'detect_image':
             action_text = "Detect Image"

        action_item = QStandardItem(action_text)
        action_item.setEditable(False) # Disable inline edit, use Dialog instead
        
        # Ensure event has an ID for drag-and-drop tracking
        if 'id' not in event:
            event['id'] = str(uuid.uuid4())
            
        action_item.setData(event['id'], Qt.ItemDataRole.UserRole) # Store ID only (safe for drag-drop)
        action_item.setData(event['id'], Qt.ItemDataRole.ToolTipRole) # Fallback/Debug ID
        
        # Explicitly set flags to ensure copy works
        action_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled)
        
        if event['type'] == 'undefined':
             action_item.setForeground(QColor("gray"))
        
        # Delay Column (2) - Display in Milliseconds
        ms_delay = int(event.get('time', 0.5) * 1000)
        delay_item = QStandardItem(str(ms_delay))
        delay_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        delay_item.setEditable(True)
        
        # Details Column (3)
        details_item = QStandardItem()
        self.update_details_item(details_item, event)
        details_item.setEditable(False) # Disable inline edit
        
        # Note Column (4) - Editable for user notes
        note_item = QStandardItem(event.get('note', ''))
        note_item.setEditable(True)
        
        self.model.setItem(row, 0, step_item)
        self.model.setItem(row, 1, action_item)
        self.model.setItem(row, 2, delay_item)
        self.model.setItem(row, 3, details_item)
        self.model.setItem(row, 4, note_item)
        self.table_view.scrollToBottom()

    def on_item_changed(self, item):
        # Handle edits
        row = item.row()
        col = item.column()
        
        if row >= len(self.recorded_events):
            return
            
        event = self.recorded_events[row]
        
        if col == 4: # Note column
            event['note'] = item.text()
        elif col == 1: # Action
            text = item.text()
            # Smart Action Logic
            if text.startswith("Key ") and " Down" not in text and " Up" not in text:
                # Likely just "Key X"
                pass
            elif len(text) == 1: # Single char typed (e.g. "W")
                event['type'] = 'key_press'
                event['key'] = text.lower()
                self.model.blockSignals(True)
                item.setText(f"Key {text}")
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

    def on_table_double_clicked(self, index):
        if not index.isValid():
            return
        # Allow inline edit for Delay column (2) and Note column (4)
        if index.column() == 2 or index.column() == 4:
            return
        self.edit_event(index.row())

    def on_rows_inserted(self, parent, start, end):
        print(f"🔍 DEBUG: Rows inserted {start} to {end}")
        for row in range(start, end + 1):
            item = self.model.item(row, 1)
            if item:
                event_id = item.data(Qt.ItemDataRole.UserRole)
                print(f"  Row {row} ID: {event_id}")

    def on_rows_removed(self, parent, start, end):
        """Rebuild recorded_events list after rows are moved/removed using IDs"""
        print(f"🔍 DEBUG: Rows removed {start} to {end}")
        # Create a map of current events by ID for quick lookup
        event_map = {e.get('id'): e for e in self.recorded_events if 'id' in e}
        
        new_events = []
        for row in range(self.model.rowCount()):
            item = self.model.item(row, 1)
            if item:
                event_id = item.data(Qt.ItemDataRole.UserRole)
                if not event_id:
                    event_id = item.data(Qt.ItemDataRole.ToolTipRole) # Fallback
                
                if event_id and event_id in event_map:
                    new_events.append(event_map[event_id])
                elif event_id:
                    print(f"Warning: Event ID {event_id} not found in map")
                else:
                    print(f"Warning: Row {row} has NO ID")
        
        print(f"🔍 DEBUG: Rebuilt list has {len(new_events)} events (Model has {self.model.rowCount()} rows)")
        self.recorded_events = new_events
        
        # Renumber steps
        for row in range(self.model.rowCount()):
             self.model.item(row, 0).setText(str(row + 1))

    def show_context_menu(self, pos):
        index = self.table_view.indexAt(pos)
        if not index.isValid():
            return
            
        menu = QMenu(self)
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")
        
        action = menu.exec(self.table_view.viewport().mapToGlobal(pos))
        
        if action == edit_action:
            self.edit_event(index.row())
        elif action == delete_action:
            self.delete_event(index.row())
            

            self.edit_event(index.row())
        elif action == delete_action:
            self.delete_event(index.row())

    def edit_event(self, row):
        if row >= len(self.recorded_events):
            # For undefined/new rows, show setup menu
            index = self.model.index(row, 1)
            self.show_setup_menu(index)
            return

        event = self.recorded_events[row]
        
        # Determine which dialog to open based on event type
        if event['type'] in ['mouse_move', 'mouse_click', 'mouse_scroll']:
            self.open_mouse_dialog(row)
        elif event['type'] in ['key_press', 'key_release', 'key_click']:
            self.open_keyboard_dialog(row)
        elif event['type'] == 'detect_image':
            self.open_image_search_dialog(row)
        elif event['type'] == 'undefined':
            index = self.model.index(row, 1)
            self.show_setup_menu(index)

    def delete_event(self, row):
        if row >= len(self.recorded_events):
            return
            
        # Remove from data
        self.recorded_events.pop(row)
        
        # Remove from model
        self.model.removeRow(row)
        
        # Renumber steps
        for r in range(self.model.rowCount()):
            self.model.item(r, 0).setText(str(r + 1))
            
        self.statusBar().showMessage(f"Deleted step {row + 1}.")

    def keyPressEvent(self, event):
        # Handle Delete key for table
        if event.key() == Qt.Key.Key_Delete:
            if self.table_view.hasFocus():
                selection = self.table_view.selectionModel().selectedRows()
                if selection:
                    # Delete in reverse order to avoid index shifting issues
                    rows = sorted([index.row() for index in selection], reverse=True)
                    for row in rows:
                        self.delete_event(row)
                    return
                    
        super().keyPressEvent(event)

    def show_setup_menu(self, index):
        menu = QMenu(self)
        mouse_action = menu.addAction("Mouse Action")
        keyboard_action = menu.addAction("Keyboard Action")
        
        # Add Image submenu
        image_menu = QMenu("Image", self)
        detect_image_action = image_menu.addAction("Detect image [I]")
        menu.addMenu(image_menu)
        
        action = menu.exec(self.table_view.viewport().mapToGlobal(self.table_view.visualRect(index).bottomLeft()))
        
        if action == mouse_action:
            self.open_mouse_dialog(index.row())
        elif action == keyboard_action:
            self.open_keyboard_dialog(index.row())
        elif action == detect_image_action:
            self.open_image_search_dialog(index.row())


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

    def open_image_search_dialog(self, row):
        event = self.recorded_events[row]
        dialog = ImageSearchDialog(self, event)
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
             action_text = f"Key Press {event['key']}"
        elif event['type'] == 'key_release':
             action_text = f"Key Release {event['key']}"
        elif event['type'] == 'key_click':
             action_text = f"Key Click {event['key']}"
        elif event['type'] == 'mouse_click':
             action_text = "Mouse Click"
        elif event['type'] == 'mouse_move':
             action_text = "Mouse Move"
        elif event['type'] == 'mouse_scroll':
             action_text = "Mouse Wheel"
        elif event['type'] == 'detect_image':
             action_text = "Detect Image"

             
        self.model.item(row, 1).setText(action_text)
        self.model.item(row, 1).setForeground(QColor("black")) # Reset color
        self.model.item(row, 1).setEditable(False)
        
        # Delay
        ms_delay = int(event.get('time', 0.5) * 1000)
        self.model.item(row, 2).setText(str(ms_delay))
        self.model.item(row, 2).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Details
        self.update_details_item(self.model.item(row, 3), event)

    def update_details_item(self, item, event):
        import os
        details = ""
        
        # Reset icon first
        item.setIcon(QIcon())
        
        if event['type'] == 'mouse_move':
            details = f"x={event.get('x',0)}, y={event.get('y',0)}"
        elif event['type'] == 'mouse_click':
            button = event.get('button', 'Button.left')
            x = event.get('x', 0)
            y = event.get('y', 0)
            if button == 'Button.left':
                details = f"Click: {x},{y}"
            elif button == 'Button.right':
                details = f"Right Click: {x},{y}"
            elif button == 'Button.middle':
                details = f"Middle Click: {x},{y}"
            else:
                details = f"{button}: {x},{y}"
        elif event['type'] == 'key_press':
            details = f"Press: {event.get('key','')}"
        elif event['type'] == 'key_release':
            details = f"Release: {event.get('key','')}"
        elif event['type'] == 'key_click':
            details = f"Click: {event.get('key','')}"
        elif event['type'] == 'mouse_scroll':
            details = f"Delta: {event.get('dy', 0)}"
        elif event['type'] == 'detect_image':
            image_path = event.get('image_path', '')
            if image_path:
                # No text, just thumbnail
                if os.path.exists(image_path):
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        # Create thumbnail - larger size
                        scaled = pixmap.scaledToHeight(40, Qt.TransformationMode.SmoothTransformation)
                        item.setIcon(QIcon(scaled))
                        # Set size hint to ensure row is tall enough
                        item.setSizeHint(QSize(0, 40))
            else:
                details = "No image set"

        item.setText(details)


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

    def open_settings(self, tab_index=0):
        if hasattr(self, 'hotkey_listener') and self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None
            
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self, initial_tab=tab_index)
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

        # Only add non-empty hotkeys to the map
        self.hotkey_map = {}
        
        if rec_key and rec_key.strip():
            self.hotkey_map[to_pynput(rec_key)] = self.on_hotkey_record
        
        if stop_rec_key and stop_rec_key.strip():
            self.hotkey_map[to_pynput(stop_rec_key)] = self.on_hotkey_stop_record
        
        if play_key and play_key.strip():
            self.hotkey_map[to_pynput(play_key)] = self.on_hotkey_play
        
        # Only register if we have at least one hotkey
        if not self.hotkey_map:
            print("⚠️ No hotkeys configured")
            self.hotkey_listener = None
            return
        
        try:
            from pynput import keyboard
            self.hotkey_listener = keyboard.GlobalHotKeys(self.hotkey_map)
            self.hotkey_listener.start()
            print(f"✓ Hotkeys registered: {list(self.hotkey_map.keys())}")
        except Exception as e:
            print(f"⚠️ Failed to register hotkeys: {e}")
            self.hotkey_listener = None

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
        self.save_autosave()
        self.settings.setValue("window_size", self.size())
        self.settings.setValue("window_pos", self.pos())
        super().closeEvent(event)
        # Explicitly quit the app since we disabled auto-quit on last window closed
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def save_autosave(self):
        """Save current state to a hidden autosave file"""
        import json
        import os
        try:
            autosave_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".autosave.json")
            data = {
                'events': self.recorded_events,
                'current_filename': self.current_filename
            }
            with open(autosave_file, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"State autosaved to {autosave_file}")
        except Exception as e:
            print(f"Error autosaving state: {e}")

    def load_autosave(self):
        """Load state from hidden autosave file"""
        import json
        import os
        try:
            autosave_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".autosave.json")
            if os.path.exists(autosave_file):
                with open(autosave_file, 'r') as f:
                    data = json.load(f)
                
                self.recorded_events = data.get('events', [])
                self.current_filename = data.get('current_filename')
                
                self.model.removeRows(0, self.model.rowCount())
                for event in self.recorded_events:
                    self.add_event_to_table(event)
                    
                print(f"State restored from {autosave_file}")
        except Exception as e:
            print(f"Error loading autosave: {e}")
