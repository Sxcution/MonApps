# AUTO-GENERATED: This file was automatically regenerated from the backup to use FluentWindow
# Original backup: ui/main_window.py.backup

# This is a modernized version of AutoKey using FluentWindow instead of QMainWindow
# All core functionality is preserved

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableView, QHeaderView, 
                              QFileDialog, QInputDialog, QAbstractItemView, QMessageBox, QMenu)
from PySide6.QtCore import QSettings, QSize, QPoint, Qt, Slot, QTimer
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QIcon, QPixmap
from PySide6.QtWidgets import QMainWindow
from qfluentwidgets import FluentIcon as FIF, InfoBar, Theme, setTheme

import ctypes
from ctypes import c_int, byref
import time
import threading
import uuid
import os

from ui.steps_interface import StepsInterface

from ui.steps_interface import StepsInterface
from ui.playback_overlay import PlaybackOverlay
from ui.delegates import ActionDelegate, NumberDelegate
from ui.mouse_dialog import MouseActionDialog
from ui.keyboard_dialog import KeyboardActionDialog
from ui.image_search_dialog import ImageSearchDialog

from core.recorder import Recorder
from core.player import Player


class MainWindow(QMainWindow):
    """AutoKey Main Window - Fluent Design Version
    
    Converted from QMainWindow to FluentWindow for modern UI.
    Features:
    - Navigation-based interface with Home, Steps, and Settings pages
    - Macro recording and playback
    -Global hotkey support
    - Image and text search capabilities
    """
    
    def __init__(self, is_embedded=False, parent_theme=None):
        super().__init__()
        self.is_embedded = is_embedded
        self.setWindowTitle("AutoKey Macro Recorder")
        self.settings = QSettings("MonSoft", "MacroRecorder")  # Must match settings_dialog.py!
        
        # Store current theme
        if self.is_embedded and parent_theme is not None:
            self.current_theme = parent_theme
            print(f"🎨 DEBUG: AutoKey embedded - using parent theme: {parent_theme}")
        else:
            self.current_theme = Theme.LIGHT
            print(f"🎨 DEBUG: AutoKey standalone - using default Light theme")
        
        # Apply theme and stylesheet
        setTheme(self.current_theme)
        self.apply_stylesheet()
        
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
    
    def apply_stylesheet(self):
        """Apply appropriate stylesheet based on current theme"""
        from ui.styles import LIGHT_STYLESHEET, DARK_STYLESHEET
        
        if self.current_theme == Theme.DARK:
            stylesheet = DARK_STYLESHEET
            print("🎨 Applying DARK stylesheet to AutoKey")
        else:
            stylesheet = LIGHT_STYLESHEET
            print("🎨 Applying LIGHT stylesheet to AutoKey")
        
        # Apply to this window
        self.setStyleSheet(stylesheet)
        
        # Also apply to QApplication to affect dialogs
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet)
            print("✓ Stylesheet applied to QApplication")


    def setup_ui(self):
        """Setup UI - Single window with steps interface, no sidebar"""
        # Resize window
        self.resize(1000, 700)
        
        # Create Steps Interface (main view)
        self.steps_interface = StepsInterface(self)
        
        # Set as central widget (no navigation/sidebar)
        from PySide6.QtWidgets import QVBoxLayout, QWidget
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.steps_interface)
        self.setCentralWidget(central)
        
        # Connect Steps Interface Signals
        self.steps_interface.new_requested.connect(self.new_recording)
        self.steps_interface.open_requested.connect(self.load_recording)
        self.steps_interface.save_requested.connect(self.save_recording)
        self.steps_interface.add_step_requested.connect(self.add_empty_row)
        self.steps_interface.record_toggled.connect(self.toggle_recording)
        self.steps_interface.play_toggled.connect(self.toggle_playing)
        
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
        # Reset loaded filepath in saved macros panel
        if hasattr(self, 'steps_interface'):
            self.steps_interface.reset_loaded_filepath()
        InfoBar.success("Tạo mới", "Đã tạo macro mới", parent=self)

    def add_empty_row(self):
        """Add placeholder event for user to configure - thêm ngay dưới hàng được chọn nếu có"""
        event = {
            'type': 'undefined',
            'text': 'Click to setup',
            'time': 0.5
        }
        
        # Kiểm tra xem có hàng nào đang được chọn không
        selection = self.table_view.selectionModel().selectedRows()
        if selection and len(selection) > 0:
            # Có hàng được chọn → thêm ngay dưới hàng đó
            selected_row = selection[0].row()
            insert_position = selected_row + 1
            
            # Insert vào recorded_events tại vị trí insert_position
            self.recorded_events.insert(insert_position, event)
            # Insert vào model tại vị trí insert_position
            self.add_event_to_table(event, insert_at_row=insert_position)
            
            # Select hàng vừa thêm
            self.table_view.selectRow(insert_position)
            self.table_view.setFocus()
        else:
            # Không có hàng được chọn → thêm vào cuối như cũ
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
            
            # Get hotkeys for filtering
            start_rec_key = self.settings.value("hotkey_record", "F9")
            stop_rec_key = self.settings.value("hotkey_stop_record", "F10")
            
            # Remove START hotkey from beginning (if exists)
            if new_events and start_rec_key:
                start_key_normalized = start_rec_key.lower().strip()
                start_key_base = start_key_normalized.split('+')[-1] if '+' in start_key_normalized else start_key_normalized
                
                print(f"🔍 Filtering start hotkey: '{start_rec_key}' (base: '{start_key_base}')")
                
                # Remove from beginning
                while new_events:
                    first_event = new_events[0]
                    
                    if first_event['type'] not in ['key_press', 'key_release']:
                        break
                    
                    event_key = first_event['key'].lower().strip()
                    event_key_normalized = event_key.replace(' ', '+')
                    
                    should_remove = self._check_hotkey_match(event_key, event_key_normalized, start_key_normalized, start_key_base)
                    
                    if should_remove:
                        print(f"  ✂️ Removing start hotkey event: {first_event['type']} '{first_event['key']}'")
                        new_events.pop(0)
                    else:
                        break
            
            # Remove STOP hotkey from end (if exists)
            if new_events and stop_rec_key:
                stop_key_normalized = stop_rec_key.lower().strip()
                stop_key_base = stop_key_normalized.split('+')[-1] if '+' in stop_key_normalized else stop_key_normalized
                
                print(f"🔍 Filtering stop hotkey: '{stop_rec_key}' (base: '{stop_key_base}')")
                
                # Remove from end
                while new_events:
                    last_event = new_events[-1]
                    
                    if last_event['type'] not in ['key_press', 'key_release']:
                        break
                    
                    event_key = last_event['key'].lower().strip()
                    event_key_normalized = event_key.replace(' ', '+')
                    
                    should_remove = self._check_hotkey_match(event_key, event_key_normalized, stop_key_normalized, stop_key_base)
                    
                    if should_remove:
                        print(f"  ✂️ Removing stop hotkey event: {last_event['type']} '{last_event['key']}'")
                        new_events.pop()
                    else:
                        break
            
            # Add cleaned events to recorded_events
            self.recorded_events.extend(new_events)
            
            # No need to scan and remove from table - we filter at add time now
            
            if new_events:
                self.has_unsaved_changes = True
            InfoBar.success("Đã dừng", f"Đã ghi {len(self.recorded_events)} sự kiện", parent=self)
    
    def _check_hotkey_match(self, event_key, event_key_normalized, hotkey_normalized, hotkey_base):
        """Check if event key matches the hotkey
        
        IMPORTANT: Must distinguish between Numpad and regular keys!
        - Num+2 should ONLY match "Num 2", NOT regular "2"
        - F10 should ONLY match "F10", NOT regular "f10" text
        """
        # Direct full match (most reliable)
        if event_key_normalized == hotkey_normalized:
            return True
        
        # Special case: If hotkey contains "num", ONLY match if event also contains "num"
        if 'num' in hotkey_normalized:
            # Hotkey is Numpad - event MUST also be Numpad
            if 'num' not in event_key_normalized and 'num' not in event_key:
                return False  # Event is NOT numpad, don't match
            
            # Both are numpad - extract and compare numbers
            event_num = event_key_normalized.split('+')[-1] if '+' in event_key_normalized else event_key_normalized.replace('num', '').strip()
            hotkey_num = hotkey_base.replace('num', '').strip()
            if event_num == hotkey_num:
                return True
        
        # F-key match (exact match required)
        elif event_key.startswith('f') and hotkey_base.startswith('f'):
            if event_key == hotkey_base:
                return True
        
        # Regular key match (NOT numpad, NOT F-key)
        else:
            # Only match if event is also NOT numpad
            if 'num' not in event_key and 'num' not in event_key_normalized:
                if event_key == hotkey_base or event_key_normalized == hotkey_base:
                    return True
        
        return False

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
            
            # Connect log signals and start new session
            if hasattr(self.steps_interface, 'log_dialog'):
                # Get filename for session
                filename = self.current_filename if self.current_filename else "Untitled"
                if filename.endswith('.json'):
                    filename = filename[:-5]  # Remove .json extension
                
                # Start new playback session
                self.steps_interface.log_dialog.start_new_session(filename)
                
                # Connect signals
                self.player.log_entry.connect(self.steps_interface.log_dialog.add_log)
                self.player.log_loop_marker.connect(self.steps_interface.log_dialog.add_loop_marker)
                self.player.log_status.connect(self.steps_interface.log_dialog.add_status_message)
            
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
            # Icon is handled by _on_pause_toggled in overlay, no text needed
        else:
            self.pause_playback_event.clear()
            self.overlay_timer.start(1000)
            # Icon is handled by _on_pause_toggled in overlay, no text needed
    
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

    def add_event_to_table(self, event, insert_at_row=None):
        """Add event to table at specified row, or at the end if insert_at_row is None
        
        Visual Filter: 
        - mouse_move and mouse_scroll events are NOT displayed in the table
        - mouse_click with pressed=False (release) is NOT displayed in the table
        - start/stop recording hotkey events are NOT displayed in the table
        All hidden events are still recorded in recorded_events for accurate playback.
        """
        # VISUAL FILTER: Skip displaying filtered events in table
        # They are still in recorded_events, just hidden from view
        if event['type'] in ['mouse_move', 'mouse_scroll']:
            # Still assign ID for consistency
            if 'id' not in event:
                event['id'] = str(uuid.uuid4())
            return  # Don't add to table, exit early
        
        # VISUAL FILTER: Hide mouse release events (pressed=False)
        # Only show mouse press events to avoid duplicate entries in table
        if event['type'] == 'mouse_click' and not event.get('pressed', True):
            # Still assign ID for consistency
            if 'id' not in event:
                event['id'] = str(uuid.uuid4())
            return  # Don't add to table, exit early
        
        # VISUAL FILTER: Hide start/stop recording hotkey events
        # Check if this is a keyboard event that matches start or stop hotkey
        if event['type'] in ['key_press', 'key_release']:
            event_key = event.get('key', '').lower().strip()
            event_key_normalized = event_key.replace(' ', '+')
            
            # Get current hotkeys
            start_hotkey = self.settings.value("hotkey_record", "F9")
            stop_hotkey = self.settings.value("hotkey_stop_record", "F10")
            
            for hotkey in [start_hotkey, stop_hotkey]:
                if not hotkey:
                    continue
                hotkey_normalized = hotkey.lower().strip()
                hotkey_base = hotkey_normalized.split('+')[-1] if '+' in hotkey_normalized else hotkey_normalized
                
                # Check if this event matches the hotkey
                if self._check_hotkey_match(event_key, event_key_normalized, hotkey_normalized, hotkey_base):
                    # This is a start/stop hotkey - don't display it
                    if 'id' not in event:
                        event['id'] = str(uuid.uuid4())
                    return  # Don't add to table, exit early
        # Add row to table
        if insert_at_row is not None:
            row = insert_at_row
            # Clamp to valid range
            if row < 0:
                row = 0
            if row > self.model.rowCount():
                row = self.model.rowCount()
        else:
            row = self.model.rowCount()
        
        self.model.insertRow(row)
        
        # Step Column (0) - Auto index, không lưu số trong model
        step_item = QStandardItem("")  # Placeholder, model sẽ tự trả về row + 1
        step_item.setEditable(False)  # Không cho sửa Step bằng tay
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
        elif event['type'] == 'mouse_hold':
             action_text = "Mouse Hold"
        elif event['type'] == 'detect_image':
             action_text = "Detect Image"
        elif event['type'] == 'text_search':
             query = event.get('query', '')
             action_text = f"Text Search: {query[:30]}..." if len(query) > 30 else f"Text Search: {query}"

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
        
        # Scroll to the newly added row
        if insert_at_row is not None:
            # Scroll to specific row
            index = self.model.index(row, 0)
            self.table_view.scrollTo(index)
        else:
            # Scroll to bottom if added at the end
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
            self.has_unsaved_changes = True
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
        # Không cần renumber nữa - cột Step tự động = row + 1 qua model.data()
        pass

    def on_rows_removed(self, parent, start, end):
        """Rebuild recorded_events list after rows are moved/removed using IDs"""
        print(f"🔍 DEBUG [MAIN TABLE on_rows_removed]: Called - start: {start}, end: {end}, current model rows: {self.model.rowCount()}, recorded_events: {len(self.recorded_events)}")
        
        # Create a map of current events by ID for quick lookup
        event_map = {e.get('id'): e for e in self.recorded_events if 'id' in e}
        print(f"🔍 DEBUG [MAIN TABLE on_rows_removed]: event_map has {len(event_map)} events")
        
        new_events = []
        for row in range(self.model.rowCount()):
            item = self.model.item(row, 1)
            if item:
                event_id = item.data(Qt.ItemDataRole.UserRole)
                if not event_id:
                    event_id = item.data(Qt.ItemDataRole.ToolTipRole) # Fallback
                
                if event_id and event_id in event_map:
                    new_events.append(event_map[event_id])
                    print(f"🔍 DEBUG [MAIN TABLE on_rows_removed]: Found event {event_id} at row {row}")
                else:
                    print(f"🔍 DEBUG [MAIN TABLE on_rows_removed]: WARNING - No event_id found for row {row}, item text: '{item.text()}'")
        
        print(f"🔍 DEBUG [MAIN TABLE on_rows_removed]: Rebuilding - old count: {len(self.recorded_events)}, new count: {len(new_events)}")
        self.recorded_events = new_events
        
        # Không cần renumber nữa - cột Step tự động = row + 1 qua model.data()

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
        if event['type'] in ['mouse_move', 'mouse_click', 'mouse_scroll', 'mouse_hold']:
            self.open_mouse_dialog(row)
        elif event['type'] in ['key_press', 'key_release', 'key_click']:
            self.open_keyboard_dialog(row)
        elif event['type'] == 'detect_image':
            self.open_image_search_dialog(row)
        elif event['type'] == 'text_search':
            self.open_text_search_dialog(row)
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
        
        # Không cần renumber nữa - cột Step tự động = row + 1 qua model.data()
        
        self.has_unsaved_changes = True
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
        
        # Add Text submenu
        text_menu = QMenu("Text", self)
        text_search_action = text_menu.addAction("Search Text [T]")
        menu.addMenu(text_menu)
        
        action = menu.exec(self.table_view.viewport().mapToGlobal(self.table_view.visualRect(index).bottomLeft()))
        
        if action == mouse_action:
            self.open_mouse_dialog(index.row())
        elif action == keyboard_action:
            self.open_keyboard_dialog(index.row())
        elif action == detect_image_action:
            self.open_image_search_dialog(index.row())
        elif action == text_search_action:
            self.open_text_search_dialog(index.row())


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

    def open_text_search_dialog(self, row):
        """Open text search configuration dialog"""
        from ui.text_search_dialog import TextSearchDialog
        event = self.recorded_events[row] if row < len(self.recorded_events) else None
        dialog = TextSearchDialog(self, event)
        if dialog.exec():
            if event is None:
                return
            
            # Update event with dialog config
            config = dialog.get_config()
            config['type'] = 'text_search'  # Ensure type is set
            event.update(config)
            
            # Update table display
            if row < self.model.rowCount():
                query = event.get('query', '')
                action_text = f"Text Search: {query[:30]}..." if len(query) > 30 else f"Text Search: {query}"
                self.model.item(row, 1).setText(action_text)
                self.model.item(row, 3).setText(f"Query: {query}")
            
            self.has_unsaved_changes = True
            self.statusBar().showMessage(f"Updated text_search at row {row + 1}")





    def update_event(self, row, new_data):
        # Merge new data into event
        self.recorded_events[row].update(new_data)
        # Refresh row
        self.refresh_row(row)



    def refresh_row(self, row):
        event = self.recorded_events[row]
        
        # Re-generate items
        # Step - Không cần setText nữa, model tự trả về row + 1 qua data()
        
        # Action
        action_text = ""
        if event['type'] == 'key_press':
            key = event['key']
            hold_duration = event.get('hold_duration', 0)
            if hold_duration > 0:
                action_text = f"Key Press {key} (Hold: {hold_duration}ms)"
            else:
                action_text = f"Key Press {key}"
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
        elif event['type'] == 'mouse_hold':
             action_text = "Mouse Hold"
        elif event['type'] == 'detect_image':
             action_text = "Detect Image"
        elif event['type'] == 'text_search':
             query = event.get('query', '')
             action_text = f"Text Search: {query[:30]}..." if len(query) > 30 else f"Text Search: {query}"

             
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
        elif event['type'] == 'mouse_hold':
            x = event.get('x', 0)
            y = event.get('y', 0)
            duration = event.get('duration', 0)
            details = f"Hold: {x},{y} for {duration}ms"
        elif event['type'] == 'key_press':
            # Show hold duration if exists
            hold_duration = event.get('hold_duration', 0)
            if hold_duration > 0:
                details = f"Press: {event.get('key', '')} (Hold: {hold_duration}ms)"
            else:
                details = f"Press: {event.get('key', '')}"
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
        elif event['type'] == 'text_search':
            query = event.get('query', '')
            details = f"Query: {query}"

        item.setText(details)


    def save_recording(self):
        """Save recording - Always ask for name if not set, or save to current"""
        if not self.recorded_events:
            return
            
        if self.current_filename:
            self._save_to_file(self.current_filename)
        else:
            self.save_recording_as()

    def save_recording_as(self):
        """Ask for filename and save to 'Save' folder in AutoKey directory"""
        if not self.recorded_events:
            return

        # Prompt for filename
        name, ok = QInputDialog.getText(self, "Lưu Macro", "Nhập tên file macro:")
        if ok and name:
            # Get AutoKey root directory (parent of ui folder)
            autokey_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            save_dir = os.path.join(autokey_root, "Save")
            
            # Create Save directory if it doesn't exist
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
                print(f"📁 Created Save directory: {save_dir}")
            
            # Add .json extension if missing
            if not name.endswith('.json'):
                name += '.json'
                
            filepath = os.path.join(save_dir, name)
            
            self.current_filename = filepath
            self._save_to_file(filepath)
            
            # Refresh saved macros list
            if hasattr(self, 'steps_interface'):
                self.steps_interface.refresh_saved_macros()

    def _save_to_file(self, filename):
        import json
        try:
            with open(filename, 'w') as f:
                json.dump(self.recorded_events, f, indent=4)
            self.has_unsaved_changes = False
            
            # Show success message
            name = os.path.basename(filename)
            InfoBar.success("Đã lưu", f"Đã lưu macro: {name}", parent=self)
            
        except Exception as e:
            InfoBar.error("Lỗi", f"Không thể lưu: {e}", parent=self)

    def load_recording(self):
        import json
        
        filename, _ = QFileDialog.getOpenFileName(self, "Open Macro", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'r') as f:
                    self.recorded_events = json.load(f)
                
                self.current_filename = filename
                
                # Temporarily disconnect itemChanged to prevent false "unsaved changes"
                self.model.itemChanged.disconnect(self.on_item_changed)
                
                self.model.removeRows(0, self.model.rowCount())
                for event in self.recorded_events:
                    self.add_event_to_table(event)
                
                # Reconnect signal
                self.model.itemChanged.connect(self.on_item_changed)
                
                # Set unsaved changes AFTER reconnecting
                self.has_unsaved_changes = False
                
                # Reset loaded filepath in saved macros panel
                if hasattr(self, 'steps_interface'):
                    self.steps_interface.reset_loaded_filepath()
                    
                self.statusBar().showMessage(f"Loaded {len(self.recorded_events)} events from {filename}")
            except Exception as e:
                # Make sure to reconnect signal even on error
                try:
                    self.model.itemChanged.connect(self.on_item_changed)
                except:
                    pass
                self.statusBar().showMessage(f"Error loading: {e}")
    
    def load_macro_from_path(self, filepath):
        """Load macro from specific file path (called from saved macros list)"""
        import json
        import os
        from qfluentwidgets import InfoBar
        
        try:
            with open(filepath, 'r') as f:
                self.recorded_events = json.load(f)
            
            self.current_filename = filepath
            
            # Temporarily disconnect itemChanged
            self.model.itemChanged.disconnect(self.on_item_changed)
            
            self.model.removeRows(0, self.model.rowCount())
            for event in self.recorded_events:
                self.add_event_to_table(event)
            
            # Reconnect signal
            self.model.itemChanged.connect(self.on_item_changed)
            
            self.has_unsaved_changes = False
            
            filename = os.path.basename(filepath)
            InfoBar.success("Đã tải", f"Đã load: {filename}", parent=self)
            
        except Exception as e:
            try:
                self.model.itemChanged.connect(self.on_item_changed)
            except:
                pass
            InfoBar.error("Lỗi", f"Không thể load: {e}", parent=self)


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
        
        self.hotkey_configs = []
        self.pressed_keys = set()
        
        def parse_hotkey(key_str, callback):
            if not key_str or not key_str.strip():
                return
                
            key_str = key_str.lower()
            
            # Re-parsing strategy:
            # QKeySequence.toString() format: "Ctrl+Alt+Num+1"
            
            required_keys = set()
            
            # Modifiers
            if "ctrl+" in key_str: required_keys.add('ctrl')
            if "alt+" in key_str: required_keys.add('alt')
            if "shift+" in key_str: required_keys.add('shift')
            if "meta+" in key_str: required_keys.add('cmd')
            
            # Main Key
            # Handle Numpad
            if "num+" in key_str:
                # Extract digit
                main_part = key_str.split("num+")[-1]
                if main_part.isdigit():
                    # Map to VK 96-105
                    vk = 96 + int(main_part)
                    required_keys.add(vk)
            elif "f" in key_str and key_str.split('+')[-1].startswith('f'):
                # F-keys
                f_part = key_str.split('+')[-1]
                if f_part[1:].isdigit():
                    # F1 is VK 112
                    f_num = int(f_part[1:])
                    vk = 111 + f_num
                    required_keys.add(vk)
            else:
                # Standard keys (letters, etc)
                last_part = key_str.split('+')[-1]
                if len(last_part) == 1:
                    # Char - Map to VK using VkKeyScanW
                    try:
                        res = ctypes.windll.user32.VkKeyScanW(ord(last_part))
                        vk = res & 0xFF
                        if vk != 0xFF and vk != 0:
                            required_keys.add(vk)
                        else:
                            # Fallback to char if VK lookup fails
                            required_keys.add(last_part)
                    except:
                        required_keys.add(last_part)
                else:
                    # Special keys?
                    pass
            
            self.hotkey_configs.append({
                'triggers': required_keys,
                'callback': callback,
                'original': key_str
            })

        # Parse all hotkeys
        parse_hotkey(rec_key, self.on_hotkey_record)
        parse_hotkey(stop_rec_key, self.on_hotkey_stop_record)
        parse_hotkey(play_key, self.on_hotkey_play)
        
        if not self.hotkey_configs:
            print("⚠️ No hotkeys configured")
            self.hotkey_listener = None
            return
            
        try:
            from pynput import keyboard
            self.hotkey_listener = keyboard.Listener(
                on_press=self.on_global_key_press,
                on_release=self.on_global_key_release)
            self.hotkey_listener.start()
            print(f"✓ Manual Hotkey Listener registered")
        except Exception as e:
            print(f"⚠️ Failed to register hotkeys: {e}")
            self.hotkey_listener = None

    def on_global_key_press(self, key):
        try:
            # Add to pressed set
            # Normalize key
            key_id = self._get_key_id(key)
            if key_id:
                self.pressed_keys.add(key_id)
            
            # Check for matches
            for config in self.hotkey_configs:
                triggers = config['triggers']
                if not triggers: continue
                
                # Check if all triggers are pressed
                match = True
                for trigger in triggers:
                    if trigger not in self.pressed_keys:
                        match = False
                        break
                
                if match:
                    # Execute callback
                    config['callback']()
                    
        except Exception as e:
            print(f"Error in hotkey press: {e}")

    def on_global_key_release(self, key):
        try:
            key_id = self._get_key_id(key)
            if key_id and key_id in self.pressed_keys:
                self.pressed_keys.remove(key_id)
        except Exception as e:
            print(f"Error in hotkey release: {e}")

    def _get_key_id(self, key):
        from pynput import keyboard
        # Return a canonical ID for the key (string 'ctrl', 'alt', or int VK, or char)
        
        # Check VK first - this works for F-keys and most special keys
        if hasattr(key, 'vk') and key.vk is not None:
            return key.vk
        
        # Check for modifier keys (these typically don't have vk directly)
        if isinstance(key, keyboard.Key):
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r: return 'ctrl'
            if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r: return 'alt'
            if key == keyboard.Key.shift_l or key == keyboard.Key.shift_r: return 'shift'
            if key == keyboard.Key.cmd_l or key == keyboard.Key.cmd_r: return 'cmd'
            
            # Try to get VK from key.value if it exists
            if hasattr(key, 'value') and hasattr(key.value, 'vk'):
                return key.value.vk
            
        # Fallback for character keys
        if hasattr(key, 'char') and key.char:
            # Try to get VK for char
            try:
                res = ctypes.windll.user32.VkKeyScanW(ord(key.char))
                vk = res & 0xFF
                if vk != 0xFF and vk != 0:
                    return vk
            except:
                pass
            return key.char.lower()
            
        return None

    def on_hotkey_record(self):
        """Hotkey callback to start recording"""
        from PySide6.QtCore import QMetaObject, Qt, Q_ARG
        QMetaObject.invokeMethod(self, "toggle_recording_safe", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, True))

    def on_hotkey_stop_record(self):
        """Hotkey callback to stop recording"""
        from PySide6.QtCore import QMetaObject, Qt, Q_ARG
        QMetaObject.invokeMethod(self, "toggle_recording_safe", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, False))

    def on_hotkey_play(self):
        """Hotkey callback to toggle playback"""
        from PySide6.QtCore import QMetaObject, Qt
        # Check current state and toggle
        is_playing = self.steps_interface.play_btn.isChecked() if hasattr(self, 'steps_interface') else False
        QMetaObject.invokeMethod(self, "toggle_playing_safe", Qt.ConnectionType.QueuedConnection)

    @Slot(bool)
    def toggle_recording_safe(self, start):
        """Thread-safe method to toggle recording state via hotkey"""
        if not hasattr(self, 'steps_interface'):
            return
        
        if start:
            # Start recording
            if not self.steps_interface.record_btn.isChecked():
                self.steps_interface.record_btn.setChecked(True)
        else:
            # Stop recording
            if self.steps_interface.record_btn.isChecked():
                self.steps_interface.record_btn.setChecked(False)

    @Slot()
    def toggle_playing_safe(self):
        """Thread-safe method to toggle playback state via hotkey"""
        if not hasattr(self, 'steps_interface'):
            return
        
        # Toggle play state
        is_playing = self.steps_interface.play_btn.isChecked()
        self.steps_interface.play_btn.setChecked(not is_playing)

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
        # Check for unsaved changes
        if self.has_unsaved_changes and self.recorded_events:
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                'Unsaved Changes',
                'You have unsaved changes. Do you want to save before closing?',
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.save_recording()
                if self.has_unsaved_changes:  # Save was cancelled
                    event.ignore()
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        
        self.settings.setValue("window_size", self.size())
        self.settings.setValue("window_pos", self.pos())
        super().closeEvent(event)
        
        # Explicitly quit the app since we disabled auto-quit on last window closed
        if not self.is_embedded:
            from PySide6.QtWidgets import QApplication
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
                print(f"📂 Loading autosave from {autosave_file}")
                with open(autosave_file, 'r') as f:
                    data = json.load(f)
                
                self.recorded_events = data.get('events', [])
                self.current_filename = data.get('current_filename')
                
                print(f"📂 Loaded {len(self.recorded_events)} events")
                
                self.model.removeRows(0, self.model.rowCount())
                
                # Add events with safety check
                for idx, event in enumerate(self.recorded_events):
                    try:
                        self.add_event_to_table(event)
                    except Exception as e:
                        print(f"⚠️ Error adding event {idx}: {e}")
                        continue
                    
                print(f"✓ State restored from autosave")
            else:
                print("📂 No autosave file found")
        except Exception as e:
            print(f"⚠️ Error loading autosave: {e}")
            import traceback
            traceback.print_exc()

