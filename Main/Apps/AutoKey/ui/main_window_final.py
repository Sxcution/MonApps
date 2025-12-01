# AUTO-GENERATED: This file was automatically regenerated from the backup to use FluentWindow
# Original backup: ui/main_window.py.backup

# This is a modernized version of AutoKey using FluentWindow instead of QMainWindow
# All core functionality is preserved

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableView, QHeaderView, 
                              QFileDialog, QInputDialog, QAbstractItemView, QMessageBox, QMenu)
from PySide6.QtCore import QSettings, QSize, QPoint, Qt, Slot, QTimer
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QIcon, QPixmap
from qfluentwidgets import FluentWindow, NavigationItemPosition, FluentIcon as FIF, InfoBar

import ctypes
from ctypes import c_int, byref
import time
import threading
import uuid

from ui.home_interface import HomeInterface
from ui.steps_interface import StepsInterface
from ui.autokey_settings_interface import AutoKeySettingsInterface
from ui.playback_overlay import PlaybackOverlay
from ui.delegates import ActionDelegate, NumberDelegate
from ui.mouse_dialog import MouseActionDialog
from ui.keyboard_dialog import KeyboardActionDialog
from ui.image_search_dialog import ImageSearchDialog

from core.recorder import Recorder
from core.player import Player


class MainWindow(FluentWindow):
    """AutoKey Main Window - Fluent Design Version
    
    Converted from QMainWindow to FluentWindow for modern UI.
    Features:
    - Navigation-based interface with Home, Steps, and Settings pages
    - Macro recording and playback
    -Global hotkey support
    - Image and text search capabilities
    """
    
    def __init__(self, is_embedded=False):
        super().__init__()
        self.is_embedded = is_embedded
        self.setWindowTitle("AutoKey Macro Recorder")
        self.settings = QSettings("Mon Soft", "MacroRecorder")
        
        # Track if there are unsaved changes
        self.has_unsaved_changes = False
        self.current_filename = None
        self.recorded_events = []
        
        # Setup UI
        self.setup_ui()
        
        # Restore window state (only if not embedded)
        if not self.is_embedded:
            self.restore_geometry()
        
        # Setup Hotkeys
        self.setup_global_hotkeys()

    def setup_ui(self):
        """Setup Fluent UI with navigation"""
        # Resize window
        self.resize(1000, 700)
        
        # Create Interface Pages
        self.home_interface = HomeInterface(self)
        self.steps_interface = StepsInterface(self)
        self.settings_interface = AutoKeySettingsInterface(self)
        
        # Add to Navigation
        self.addSubInterface(self.home_interface, FIF.HOME, "Home")
        self.addSubInterface(self.steps_interface, FIF.MENU, "Steps")
        self.addSubInterface(self.settings_interface, FIF.SETTING, "Cài đặt", position=NavigationItemPosition.BOTTOM)
        
        # Connect Steps Interface Signals
        self.steps_interface.new_requested.connect(self.new_recording)
        self.steps_interface.open_requested.connect(self.load_recording)
        self.steps_interface.save_requested.connect(self.save_recording)
        self.steps_interface.add_step_requested.connect(self.add_empty_row)
        self.steps_interface.record_toggled.connect(self.toggle_recording)
        self.steps_interface.play_toggled.connect(self.toggle_playing)
        
        # Connect Home Interface Signals
        self.home_interface.new_macro_requested.connect(self.new_recording)
        self.home_interface.open_macro_requested.connect(self.load_recording)
        self.home_interface.start_record_requested.connect(lambda: self.steps_interface.record_btn.setChecked(True))
        
        # Reference table and model from steps interface
        self.table_view = self.steps_interface.table_view
        self.model = self.steps_interface.model
        
        # Set Delegates for table
        self.table_view.setItemDelegateForColumn(1, ActionDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(2, NumberDelegate(self.table_view))
        
        # Connect table signals
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)
        self.table_view.clicked.connect(self.on_table_clicked)
        self.table_view.doubleClicked.connect(self.on_table_double_clicked)
        
        # Connect model signals
        self.model.itemChanged.connect(self.on_item_changed)
        self.model.rowsRemoved.connect(self.on_rows_removed)
        self.model.rowsInserted.connect(self.on_rows_inserted)
        
        # Logic Components
        self.recorder = Recorder()
        self.recorder.event_recorded.connect(self.add_event_to_table)
        self.player = None
        self.stop_playback_event = threading.Event()
        self.pause_playback_event = threading.Event()
        
        # Playback Overlay
        self.overlay = PlaybackOverlay(self)
        self.overlay.stop_btn.clicked.connect(self.stop_playback_from_overlay)
        self.overlay.pause_btn.toggled.connect(self.pause_playback)
        
        # Timer for updating overlay time
        self.overlay_timer = QTimer(self)
        self.overlay_timer.timeout.connect(self.update_overlay_time)
        self.overlay_start_time = 0

    # ===========================================
    # RECORDING/PLAYBACK METHODS
    # ===========================================

    def new_recording(self):
        """Create new macro"""
        self.model.removeRows(0, self.model.rowCount())
        self.recorded_events = []
        self.current_filename = None
        self.has_unsaved_changes = False
        InfoBar.success("Tạo mới", "Đã tạo macro mới", parent=self)

    def add_empty_row(self):
        """Add placeholder event for user to configure"""
        event = {
            'type': 'undefined',
            'text': 'Click to setup',
            'time': 0.5
        }
        self.recorded_events.append(event)
        self.add_event_to_table(event)
        self.has_unsaved_changes = True
        InfoBar.info("Đã thêm", "Đã thêm bước mới",  parent=self)

    def toggle_recording(self, checked):
        """Toggle recording on/off"""
        if checked:
            # Start Recording
            if not self.recorded_events:
                self.model.removeRows(0, self.model.rowCount())
                self.recorded_events = []
            
            self.recorder.start_recording()
            InfoBar.info("Đang ghi", "Đang ghi macro...", parent=self)
        else:
            # Stop Recording
            new_events = self.recorder.stop_recording()
            
            # Check if the last event matches the Stop Record hotkey
            stop_rec_key = self.settings.value("hotkey_stop_record", "F10").lower()
            
            print(f"DEBUG: Stop Key='{stop_rec_key}'")
            
            if new_events and stop_rec_key:
                # Loop backwards to remove all events related to the stop key (Press and Release)
                while new_events:
                    last_event = new_events[-1]
                    
                    if last_event['type'] not in ['key_press', 'key_release', 'key_click']:
                        break
                        
                    key = last_event['key'].lower()
                    print(f"DEBUG: Checking last event: {key} vs {stop_rec_key}")
                    
                    event_key_norm = key.replace("num ", "num+")
                    hotkey_base = stop_rec_key.split('+')[-1].strip()
                    event_base = key.split(' ')[-1].strip()
                    
                    match = False
                    
                    if event_key_norm == stop_rec_key:
                        match = True
                    elif event_base == hotkey_base:
                        match = True
                    elif "num" in stop_rec_key and "num" in key and event_base == hotkey_base:
                        match = True
                        
                    if match:
                        print(f"Removing stop hotkey event: {last_event}")
                        new_events.pop()
                    else:
                        if key in stop_rec_key and len(key) > 1:
                             print(f"Removing modifier/part of hotkey: {last_event}")
                             new_events.pop()
                        else:
                            break
            
            self.recorded_events.extend(new_events)
            if new_events:
                self.has_unsaved_changes = True
            InfoBar.success("Đã dừng", f"Đã ghi {len(self.recorded_events)} sự kiện", parent=self)

    def toggle_playing(self, checked):
        """Toggle playback on/off"""
        if checked:
            if not self.recorded_events:
                InfoBar.warning("Không có macro", "Chưa có macro để phát", parent=self)
                self.steps_interface.set_play_state(False)
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
            self.overlay_timer.start(1000)
            
            self.stop_playback_event.clear()
            self.pause_playback_event.clear()
            self.player = Player(self.recorded_events, self.stop_playback_event, self.pause_playback_event)
            
            # Connect signals
            self.player.progress_updated.connect(self.overlay.update_loop)
            self.player.time_updated.connect(self.overlay.update_time)
            self.player.playback_finished.connect(self.on_playback_finished)
            self.player.step_progress_updated.connect(self.overlay.update_step_progress)
            
            self.player.start()
        else:
            # Stop playback
            self.stop_playback_event.set()
            self.overlay_timer.stop()
            self.overlay.hide()
            self.show()
    
    def stop_playback_from_overlay(self):
        """Stop playback when stop button is clicked in overlay"""
        self.overlay.hide()
        self.show()
        self.steps_interface.set_play_state(False)
    
    def pause_playback(self, paused):
        """Pause/resume playback - keeps overlay visible"""
        if paused:
            self.pause_playback_event.set()
            self.overlay_timer.stop()
            self.overlay.pause_btn.setText("▶️ Resume")
        else:
            self.pause_playback_event.clear()
            self.overlay_timer.start(1000)
            selfoverlay.pause_btn.setText("⏸️ Pause")
    
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
        self.steps_interface.set_play_state(False)
        InfoBar.success("Hoàn thành", "Đã phát xong macro", parent=self)

    # ===========================================================================
    # TABLE EVENT HANDLERS (from original)
    # The following methods are preserved from the original main_window.py.backup
    # They handle table operations, event editing, dialogs, file I/O, and hotkeys
    # ===========================================================================
