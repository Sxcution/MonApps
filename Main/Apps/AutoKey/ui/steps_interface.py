from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableView, 
                              QHeaderView, QFileDialog, QMenu, QAbstractItemView)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QMimeData, QModelIndex, QPoint
from PySide6.QtGui import (QStandardItemModel, QStandardItem, QColor, QIcon, QPixmap, 
                          QDragEnterEvent, QDropEvent, QDragMoveEvent, QPolygon)
from qfluentwidgets import (PushButton, ToolButton, FluentIcon as FIF, 
                            InfoBar, CardWidget, SubtitleLabel)
import uuid
import os
import glob


class MacroStepsModel(QStandardItemModel):
    """Custom model cho table chính để xử lý drag & drop đúng cách, tránh mất dòng"""
    
    STEP_COL = 0  # cột Step
    
    def data(self, index, role=Qt.DisplayRole):
        """Override data để cột Step luôn hiển thị row + 1 (auto index)"""
        # Cột Step: luôn hiển thị row + 1
        if index.isValid() and index.column() == self.STEP_COL:
            if role in (Qt.DisplayRole, Qt.EditRole):
                return str(index.row() + 1)
        return super().data(index, role)
    
    def dropMimeData(self, data, action, row, column, parent):
        """Override dropMimeData để ngăn default behavior, để QTableView.dropEvent xử lý"""
        print(f"🔍 DEBUG [MAIN TABLE]: dropMimeData called - action: {action}, row: {row}, column: {column}")
        print(f"🔍 DEBUG [MAIN TABLE]: dropMimeData - Returning False to prevent default behavior")
        # Return False để ngăn default behavior, để QTableView.dropEvent xử lý
        return False
    
    def moveRow(self, sourceParent, sourceRow, destinationParent, destinationChild):
        """Move 1 row trong cùng model, không làm mất dữ liệu"""
        print(f"🔍 DEBUG [MAIN TABLE]: moveRow called - sourceRow={sourceRow}, destChild={destinationChild}")
        row_count = self.rowCount()

        # Validate
        if sourceRow < 0 or sourceRow >= row_count:
            print(f"❌ moveRow: invalid sourceRow {sourceRow}")
            return False

        # Khi drop dưới cùng, dest có thể > row_count
        if destinationChild < 0:
            destinationChild = 0
        if destinationChild > row_count:
            destinationChild = row_count

        # Trường hợp không đổi vị trí (kéo lên chính nó / ngay dưới nó)
        if destinationChild == sourceRow or destinationChild == sourceRow + 1:
            print(f"ℹ️ moveRow: no move needed (source={sourceRow}, dest={destinationChild})")
            return False

        # Lấy nguyên cả row ra (remove khỏi model)
        items = self.takeRow(sourceRow)
        if not items:
            print(f"❌ moveRow: takeRow({sourceRow}) returned empty")
            return False

        # Sau khi takeRow, số row đã giảm 1 → clamp lại dest
        row_count_after = self.rowCount()
        if destinationChild > row_count_after:
            destinationChild = row_count_after

        print(f"🔁 moveRow: inserting row at dest={destinationChild}, row_count_after_remove={row_count_after}")

        # Insert lại row vào vị trí mới
        self.insertRow(destinationChild, items)

        print(f"✅ moveRow done: total rows={self.rowCount()}")
        return True


class SavedMacrosModel(QStandardItemModel):
    """Custom model để xử lý drag & drop đúng cách, tránh mất dòng"""
    
    def moveRow(self, sourceParent, sourceRow, destinationParent, destinationChild):
        """Override moveRow để xử lý move rows đúng cách, tránh mất dòng"""
        print(f"🔍 DEBUG: moveRow called - sourceRow: {sourceRow}, destinationChild: {destinationChild}")
        print(f"🔍 DEBUG: moveRow - total rows before: {self.rowCount()}")
        
        # Validate source row
        if sourceRow < 0 or sourceRow >= self.rowCount():
            print(f"🔍 DEBUG: moveRow - Invalid sourceRow {sourceRow}, aborting")
            return False
        
        # Lưu item trước khi move
        source_item = self.item(sourceRow, 0)
        if not source_item:
            print(f"🔍 DEBUG: moveRow - No item at sourceRow {sourceRow}, aborting")
            return False
        
        item_text = source_item.text()
        item_data = source_item.data(Qt.ItemDataRole.UserRole)
        item_flags = source_item.flags()
        
        print(f"🔍 DEBUG: moveRow - Moving item '{item_text}' from row {sourceRow} to row {destinationChild}")
        
        # Adjust destination if moving down
        if sourceRow < destinationChild:
            destinationChild += 1
        
        # Gọi parent để move
        result = super().moveRow(sourceParent, sourceRow, destinationParent, destinationChild)
        
        print(f"🔍 DEBUG: moveRow - total rows after: {self.rowCount()}")
        print(f"🔍 DEBUG: moveRow - result: {result}")
        
        # Verify item was moved correctly
        if result:
            # Calculate actual destination after move
            actual_dest = destinationChild if sourceRow > destinationChild else destinationChild - 1
            if actual_dest >= 0 and actual_dest < self.rowCount():
                new_item = self.item(actual_dest, 0)
                if new_item:
                    print(f"🔍 DEBUG: moveRow - Verification: item at position {actual_dest} is '{new_item.text()}'")
                else:
                    print(f"🔍 DEBUG: moveRow - ERROR: Item missing at position {actual_dest}!")
            else:
                print(f"🔍 DEBUG: moveRow - WARNING: Calculated destination {actual_dest} is out of range")
        
        return result


class MacroStepsTableView(QTableView):
    """Custom QTableView cho main table để xử lý drag & drop đúng cách, tránh mất dòng"""
    
    def __init__(self, parent=None, steps_interface=None):
        super().__init__(parent)
        self.steps_interface = steps_interface  # Reference để reconnect signals
        
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # ⛔ ĐỪNG dùng InternalMove nữa - nó tự xử lý move row, conflict với custom dropEvent
        # self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
    
    def dropEvent(self, event: QDropEvent):
        """Override dropEvent để xử lý move rows thủ công, tránh mất dòng"""
        print(f"🔍 DEBUG [MAIN TABLE]: dropEvent called - source: {event.source()}, self: {self}")
        
        model = self.model()
        if model is None:
            event.ignore()
            return
        
        print(f"🔍 DEBUG [MAIN TABLE]: Before drop - total rows: {model.rowCount()}")
        
        # Nếu drag từ chỗ khác tới (không phải chính table này) → để Qt xử lý bình thường
        if event.source() is not self:
            print("🔍 DEBUG [MAIN TABLE]: External drop -> use default handler")
            super().dropEvent(event)
            return
        
        # Tính row đích
        drop_index = self.indexAt(event.position().toPoint())
        drop_row = drop_index.row()
        if drop_row < 0:
            drop_row = model.rowCount()
        
        print(f"🔍 DEBUG [MAIN TABLE]: Drop position - row: {drop_row}")
        
        # Row source (đang chọn)
        selected_rows = sorted(set(index.row() for index in self.selectedIndexes()))
        print(f"🔍 DEBUG [MAIN TABLE]: Selected rows to move: {selected_rows}")
        
        if not selected_rows:
            event.ignore()
            return
        
        source_row = selected_rows[0]
        
        # Không move nếu không đổi vị trí thực sự
        if drop_row == source_row or drop_row == source_row + 1:
            print(f"🔍 DEBUG [MAIN TABLE]: No move needed (source={source_row}, drop={drop_row})")
            event.setDropAction(Qt.DropAction.IgnoreAction)
            event.ignore()
            return
        
        print(f"🔍 DEBUG [MAIN TABLE]: Moving row {source_row} -> {drop_row}")
        
        # Tạm ngắt signals nếu có on_rows_removed / inserted rebuild
        try:
            model.rowsAboutToBeRemoved.disconnect()
            model.rowsRemoved.disconnect()
            model.rowsAboutToBeInserted.disconnect()
            model.rowsInserted.disconnect()
        except TypeError:
            pass
        
        # Gọi moveRow custom (dùng takeRow/insertRow)
        ok = model.moveRow(QModelIndex(), source_row, QModelIndex(), drop_row)
        
        # Kết nối lại signals
        if hasattr(self, "steps_interface") and self.steps_interface:
            self.steps_interface._connect_main_table_signals()
        
        print(f"🔍 DEBUG [MAIN TABLE]: moveRow result={ok}, total rows={model.rowCount()}")
        
        # CRITICAL: Rebuild recorded_events manually sau khi drag-drop
        # Tìm main_window và gọi rebuild
        parent = self.parent()
        while parent and not hasattr(parent, 'recorded_events'):
            parent = parent.parent()
        
        if parent and hasattr(parent, 'recorded_events'):
            print(f"🔍 DEBUG [MAIN TABLE]: Rebuilding recorded_events after drag-drop")
            # Rebuild recorded_events từ model
            event_map = {e.get('id'): e for e in parent.recorded_events if 'id' in e}
            new_events = []
            for row in range(model.rowCount()):
                item = model.item(row, 1)
                if item:
                    event_id = item.data(Qt.ItemDataRole.UserRole)
                    if event_id and event_id in event_map:
                        new_events.append(event_map[event_id])
            parent.recorded_events = new_events
            print(f"🔍 DEBUG [MAIN TABLE]: Rebuilt recorded_events - count: {len(new_events)}")
        
        # Quan trọng: TỰ accept event, KHÔNG gọi super().dropEvent
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()
        
        print(f"🔍 DEBUG [MAIN TABLE]: After drop - total rows: {model.rowCount()}")


class SavedMacrosTableView(QTableView):
    """Custom QTableView để xử lý drag & drop đúng cách, tránh mất dòng"""
    
    def startDrag(self, supportedActions):
        """Override startDrag để debug"""
        print(f"🔍 DEBUG: startDrag called - supportedActions: {supportedActions}")
        print(f"🔍 DEBUG: startDrag - selected rows: {[idx.row() for idx in self.selectedIndexes()]}")
        print(f"🔍 DEBUG: startDrag - total rows before: {self.model().rowCount()}")
        # Call parent để vẫn có drag behavior
        super().startDrag(supportedActions)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter - debug"""
        print(f"🔍 DEBUG: dragEnterEvent - source: {event.source()}, self: {self}")
        print(f"🔍 DEBUG: dragEnterEvent - mimeData formats: {event.mimeData().formats()}")
        if event.source() == self:
            print(f"🔍 DEBUG: dragEnterEvent - ACCEPTING (source matches)")
            event.acceptProposedAction()
        else:
            print(f"🔍 DEBUG: dragEnterEvent - IGNORING (source mismatch)")
            event.ignore()
    
    def dragMoveEvent(self, event: QDragMoveEvent):
        """Handle drag move - debug"""
        drop_index = self.indexAt(event.position().toPoint())
        drop_row = drop_index.row() if drop_index.isValid() else -1
        print(f"🔍 DEBUG: dragMoveEvent - drop_row: {drop_row}, total_rows: {self.model().rowCount()}")
        if event.source() == self:
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def mousePressEvent(self, event):
        """Debug mouse press"""
        index = self.indexAt(event.position().toPoint())
        if index.isValid():
            print(f"🔍 DEBUG: mousePressEvent at {event.position().toPoint()}, row: {index.row()}")
        else:
            print(f"🔍 DEBUG: mousePressEvent at {event.position().toPoint()}, no valid index")
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Debug mouse move (for drag start detection)"""
        if event.buttons() & Qt.MouseButton.LeftButton:
            index = self.indexAt(event.position().toPoint())
            print(f"🔍 DEBUG: mouseMoveEvent with left button - potential drag start, row: {index.row() if index.isValid() else -1}")
        super().mouseMoveEvent(event)
    
    def event(self, event):
        """Override event để catch tất cả events"""
        if event.type() == event.Type.DragEnter:
            print(f"🔍 DEBUG: event() - DragEnter detected")
        elif event.type() == event.Type.DragMove:
            print(f"🔍 DEBUG: event() - DragMove detected")
        elif event.type() == event.Type.Drop:
            print(f"🔍 DEBUG: event() - Drop detected")
        return super().event(event)
    
    def dropEvent(self, event: QDropEvent):
        """Override dropEvent - để model xử lý nhưng có debug"""
        print(f"🔍 DEBUG: dropEvent called - source: {event.source()}, self: {self}")
        
        if event.source() != self:
            print(f"🔍 DEBUG: Ignoring drop - source mismatch")
            super().dropEvent(event)
            return
        
        model = self.model()
        print(f"🔍 DEBUG: Before drop - total rows: {model.rowCount()}")
        
        # Get drop position
        drop_index = self.indexAt(event.position().toPoint())
        drop_row = drop_index.row()
        if drop_row < 0:
            drop_row = model.rowCount()
        
        print(f"🔍 DEBUG: Drop position - row: {drop_row}")
        
        # Get selected rows
        selected_rows = sorted(set(index.row() for index in self.selectedIndexes()))
        print(f"🔍 DEBUG: Selected rows to move: {selected_rows}")
        
        # Let model handle it - our moveRow override will ensure no data loss
        print(f"🔍 DEBUG: Calling super().dropEvent() to let model handle")
        super().dropEvent(event)
        
        print(f"🔍 DEBUG: After drop - total rows: {model.rowCount()}")


class StepsInterface(QWidget):
    """Steps/Macro interface page - contains the macro table and action buttons"""
    
    # btn_new : Nút tạo macro mới
    new_requested = Signal()
    # btn_open : Nút mở macro
    open_requested = Signal()
    # btn_save : Nút lưu macro  
    save_requested = Signal()
    # btn_add_step : Nút thêm bước mới
    add_step_requested = Signal()
    # btn_record : Nút ghi/dừng ghi
    record_toggled = Signal(bool)
    # btn_play : Nút phát/dừng phát
    play_toggled = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("stepsInterface")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Action Buttons Row - Hàng nút hành động
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # File operations - Thao tác file
        # btn_new : Nút tạo macro mới
        self.new_btn = PushButton(FIF.ADD, "Mới", self)
        self.new_btn.setToolTip("Tạo macro mới (Ctrl+N)")
        self.new_btn.clicked.connect(self.new_requested.emit)
        # Xóa stylesheet - để dùng style mặc định, đảm bảo chữ không bị che
        button_layout.addWidget(self.new_btn)
        
        # btn_open : Nút mở macro
        self.open_btn = PushButton(FIF.FOLDER, "Mở", self)
        self.open_btn.setToolTip("Mở macro (Ctrl+O)")
        self.open_btn.clicked.connect(self.open_requested.emit)
        # Xóa stylesheet - để dùng style mặc định, đảm bảo chữ không bị che
        button_layout.addWidget(self.open_btn)
        
        # btn_save : Nút lưu macro
        self.save_btn = PushButton(FIF.SAVE, "Lưu", self)
        self.save_btn.setToolTip("Lưu macro (Ctrl+S)")
        self.save_btn.clicked.connect(self.save_requested.emit)
        # Xóa stylesheet - để dùng style mặc định, đảm bảo chữ không bị che
        button_layout.addWidget(self.save_btn)
        
        button_layout.addSpacing(20)
        
        # Edit operations - Thao tác chỉnh sửa
        # btn_add_step : Nút thêm bước mới
        self.add_btn = PushButton(FIF.ADD_TO, "Thêm bước", self)
        self.add_btn.setToolTip("Thêm bước mới vào macro")
        self.add_btn.clicked.connect(self.add_step_requested.emit)
        button_layout.addWidget(self.add_btn)
        
        button_layout.addSpacing(20)
        
        # Recording/Playback - Ghi/phát
        # btn_record : Nút ghi/dừng ghi
        self.record_btn = PushButton(FIF.VIDEO, "Ghi", self)
        self.record_btn.setToolTip("Bắt đầu/dừng ghi")  # Will be updated with actual hotkeys
        self.record_btn.setCheckable(True)
        self.record_btn.toggled.connect(self._on_record_toggled)
        # Xóa stylesheet - để dùng style mặc định, đảm bảo chữ không bị che
        button_layout.addWidget(self.record_btn)
        
        # btn_play : Nút phát/dừng phát
        self.play_btn = PushButton(FIF.PLAY, "Phát", self)
        self.play_btn.setToolTip("Phát/dừng macro")  # Will be updated with actual hotkeys
        self.play_btn.setCheckable(True)
        self.play_btn.toggled.connect(self._on_play_toggled)
        # Chỉ đổi màu icon Play thành xanh dương, giữ nền button trắng
        # Tạo icon màu xanh dương với nền tròn xanh dương và tam giác Play trắng (icon lớn hơn)
        from PySide6.QtGui import QPainter
        icon_size = 22  # Tăng từ 16 lên 22 để icon to hơn
        blue_icon_pixmap = QPixmap(icon_size, icon_size)
        blue_icon_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(blue_icon_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Vẽ nền tròn xanh dương
        painter.setBrush(QColor("#0078D4"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, icon_size - 4, icon_size - 4)
        # Vẽ tam giác Play (3 điểm) màu trắng - điều chỉnh theo icon_size mới
        painter.setBrush(QColor("#FFFFFF"))
        points = [
            QPoint(8, 6),
            QPoint(8, 16),
            QPoint(16, 11)
        ]
        painter.drawPolygon(QPolygon(points))
        painter.end()
        blue_play_icon = QIcon(blue_icon_pixmap)
        self.play_btn.setIcon(blue_play_icon)
        # Set icon size cho button để hiển thị đúng
        self.play_btn.setIconSize(QSize(icon_size, icon_size))
        # Xóa stylesheet - để dùng style mặc định, đảm bảo chữ không bị che
        # Lưu icon xanh dương và size để dùng lại khi toggle
        self.blue_play_icon = blue_play_icon
        self.blue_play_icon_size = icon_size
        button_layout.addWidget(self.play_btn)
        
        button_layout.addStretch(1)
        
        # btn_log : Nút xem log playback
        self.log_btn = PushButton(FIF.INFO, "!", self)
        self.log_btn.setToolTip("Xem log playback")
        self.log_btn.clicked.connect(self._on_log_clicked)
        self.log_btn.setFixedWidth(50)  # Narrow button for "!" symbol
        button_layout.addWidget(self.log_btn)
        
        # btn_settings : Nút cài đặt
        self.settings_btn = PushButton(FIF.SETTING, "Settings", self)
        self.settings_btn.setToolTip("Mở cài đặt AutoKey")
        self.settings_btn.clicked.connect(self._on_settings_clicked)
        button_layout.addWidget(self.settings_btn)
        
        layout.addLayout(button_layout)
        
        # Update tooltips with actual hotkeys from settings
        self.update_tooltips()
        
        # Main content: Table (left) + Saved Macros List (right)
        content_layout = QHBoxLayout()
        
        # tbl_macro_list : Bảng danh sách macro steps
        self.table_view = MacroStepsTableView(self, steps_interface=self)  # Dùng custom QTableView với reference
        self.model = MacroStepsModel(0, 5)  # Dùng custom model với debug
        self.model.setHorizontalHeaderLabels(["Step", "Action", "Delay (ms)", "Details", "Note"])
        self.table_view.setModel(self.model)
        
        # Configure Column Resizing
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table_view.setColumnWidth(0, 50)  # Step
        
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table_view.setColumnWidth(1, 250)  # Action
        
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_view.setColumnWidth(2, 80)  # Delay
        
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table_view.setColumnWidth(3, 200)  # Details
        
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Note
        
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setShowGrid(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setIconSize(QSize(300, 40))
        
        # Drag and Drop đã được setup trong MacroStepsTableView.__init__
        # Không cần setup lại ở đây nữa
        print(f"🔍 DEBUG [MAIN TABLE]: Drag drop mode: {self.table_view.dragDropMode()}")
        
        # Connect model signals để debug (sẽ được reconnect sau khi disconnect trong dropEvent)
        self._connect_main_table_signals()
        
        # Styling will come from global stylesheet in styles.py
        # Removed hardcoded light theme to allow dark theme
        
        content_layout.addWidget(self.table_view, stretch=3)
        
        # Right Panel: Saved Macros Table (clone from main table)
        # tbl_saved_macros : Bảng danh sách file macro đã lưu - clone từ table gốc
        self.saved_table = SavedMacrosTableView(self)
        self.saved_table.setObjectName("tbl_saved_macros")
        self.saved_model = SavedMacrosModel(0, 1)  # Dùng custom model
        self.saved_model.setHorizontalHeaderLabels(["File Macro"])
        self.saved_table.setModel(self.saved_model)
        
        # Configure Column Resizing - giống table gốc
        saved_header = self.saved_table.horizontalHeader()
        saved_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.saved_table.setFixedWidth(125)
        
        # Configure table - giống table gốc
        self.saved_table.setAlternatingRowColors(True)
        self.saved_table.setShowGrid(True)
        self.saved_table.verticalHeader().setVisible(False)
        
        # Selection behavior - giống table gốc
        self.saved_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.saved_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Enable Drag and Drop - giống table gốc
        print(f"🔍 DEBUG: Setting up drag & drop for saved_table")
        self.saved_table.setDragEnabled(True)
        self.saved_table.setAcceptDrops(True)
        self.saved_table.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.saved_table.setDragDropOverwriteMode(False)  # Prevent overwrite, use move instead
        print(f"🔍 DEBUG: Drag enabled: {self.saved_table.dragEnabled()}")
        print(f"🔍 DEBUG: Accept drops: {self.saved_table.acceptDrops()}")
        print(f"🔍 DEBUG: Drag drop mode: {self.saved_table.dragDropMode()}")
        
        # Connect click signal
        self.saved_table.clicked.connect(self._on_saved_macro_clicked)
        
        # Connect model signals to handle drag & drop properly - với debug chi tiết
        self.saved_model.rowsMoved.connect(self._on_saved_rows_moved)
        self.saved_model.rowsRemoved.connect(self._on_saved_rows_removed)
        self.saved_model.rowsInserted.connect(self._on_saved_rows_inserted)
        self.saved_model.rowsAboutToBeRemoved.connect(self._on_saved_rows_about_to_be_removed)
        self.saved_model.rowsAboutToBeInserted.connect(self._on_saved_rows_about_to_be_inserted)
        
        # Track currently loaded file to prevent unload on second click
        self.current_loaded_filepath = None
        
        content_layout.addWidget(self.saved_table)
        content_layout.setSpacing(0)

        
        layout.addLayout(content_layout)
        
        # Load saved macros
        self.refresh_saved_macros()
    
    def refresh_saved_macros(self):
        """Scan for saved macro files in AutoKey/Save folder only"""
        self.saved_model.removeRows(0, self.saved_model.rowCount())
        
        # Get AutoKey root directory (2 levels up from this file)
        # This file is at: AutoKey/ui/steps_interface.py
        # We need: AutoKey/Save/
        script_dir = os.path.dirname(os.path.abspath(__file__))  # AutoKey/ui/
        autokey_root = os.path.dirname(script_dir)  # AutoKey/
        save_dir = os.path.join(autokey_root, "Save")
        
        # Create Save directory if it doesn't exist
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            print(f"📁 Created Save directory: {save_dir}")
        
        # Scan for .json files in Save folder
        search_pattern = os.path.join(save_dir, "*.json")
        macro_files = glob.glob(search_pattern)
        
        for filepath in macro_files:
            filename = os.path.basename(filepath)
            item_text = filename.replace(".json", "")
            
            # Create item giống table gốc
            item = QStandardItem(item_text)
            item.setData(filepath, Qt.ItemDataRole.UserRole)  # Store full path
            item.setEditable(False)
            # Set flags để hỗ trợ drag & drop - giống table gốc
            item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | 
                         Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled)
            self.saved_model.appendRow(item)
    
    def _on_saved_macro_clicked(self, index):
        """Handle click on saved macro - load it automatically (prevent unload on second click)"""
        if not index.isValid():
            return
        
        row = index.row()
        item = self.saved_model.item(row)
        if item:
            filepath = item.data(Qt.ItemDataRole.UserRole)
            if filepath:
                # Prevent unload: nếu click lại file đã load thì không làm gì
                if self.current_loaded_filepath == filepath:
                    return
                
                # Call parent's load method (MainWindow)
                parent = self.parent()
                # Navigate up to MainWindow if needed
                while parent and not hasattr(parent, 'load_macro_from_path'):
                    parent = parent.parent()
                
                if parent and hasattr(parent, 'load_macro_from_path'):
                    parent.load_macro_from_path(filepath)
                    # Lưu filepath hiện tại để tránh unload khi click lại
                    self.current_loaded_filepath = filepath
    
    def reset_loaded_filepath(self):
        """Reset current loaded filepath (called when new/load from dialog)"""
        self.current_loaded_filepath = None
    
    def _on_saved_rows_moved(self, parent, start, end, destination, row):
        """Handle rows moved in saved macros table (drag & drop)"""
        print(f"🔍 DEBUG: Rows moved from {start}-{end} to {row}, total rows: {self.saved_model.rowCount()}")
        # Ensure model is properly updated
        self.saved_model.layoutChanged.emit()
    
    def _on_saved_rows_removed(self, parent, start, end):
        """Handle rows removed in saved macros table"""
        print(f"🔍 DEBUG: Rows removed {start}-{end}, remaining rows: {self.saved_model.rowCount()}")
    
    def _on_saved_rows_inserted(self, parent, start, end):
        """Handle rows inserted in saved macros table"""
        print(f"🔍 DEBUG: Rows inserted {start}-{end}, total rows: {self.saved_model.rowCount()}")
    
    def _on_saved_rows_about_to_be_removed(self, parent, start, end):
        """Handle rows about to be removed - debug"""
        print(f"🔍 DEBUG: Rows ABOUT TO BE removed {start}-{end}, current total: {self.saved_model.rowCount()}")
        for row in range(start, end + 1):
            item = self.saved_model.item(row, 0)
            if item:
                print(f"🔍 DEBUG:   - Row {row}: '{item.text()}'")
    
    def _on_saved_rows_about_to_be_inserted(self, parent, start, end):
        """Handle rows about to be inserted - debug"""
        print(f"🔍 DEBUG: Rows ABOUT TO BE inserted at {start}-{end}, current total: {self.saved_model.rowCount()}")
    
    def _on_main_rows_moved(self, parent, start, end, destination, row):
        """Handle rows moved in main table (drag & drop)"""
        print(f"🔍 DEBUG [MAIN TABLE]: Rows moved from {start}-{end} to {row}, total rows: {self.model.rowCount()}")
    
    def _on_main_rows_removed(self, parent, start, end):
        """Handle rows removed in main table"""
        print(f"🔍 DEBUG [MAIN TABLE]: Rows removed {start}-{end}, remaining rows: {self.model.rowCount()}")
    
    def _on_main_rows_inserted(self, parent, start, end):
        """Handle rows inserted in main table"""
        print(f"🔍 DEBUG [MAIN TABLE]: Rows inserted {start}-{end}, total rows: {self.model.rowCount()}")
    
    def _on_main_rows_about_to_be_removed(self, parent, start, end):
        """Handle rows about to be removed in main table - debug"""
        print(f"🔍 DEBUG [MAIN TABLE]: Rows ABOUT TO BE removed {start}-{end}, current total: {self.model.rowCount()}")
        for row in range(start, end + 1):
            item = self.model.item(row, 1)
            if item:
                print(f"🔍 DEBUG [MAIN TABLE]:   - Row {row}: '{item.text()}'")
    
    def _on_main_rows_about_to_be_inserted(self, parent, start, end):
        """Handle rows about to be inserted in main table - debug"""
        print(f"🔍 DEBUG [MAIN TABLE]: Rows ABOUT TO BE inserted at {start}-{end}, current total: {self.model.rowCount()}")
    
    def _connect_main_table_signals(self):
        """Connect model signals for main table"""
        try:
            self.model.rowsMoved.connect(self._on_main_rows_moved)
            self.model.rowsRemoved.connect(self._on_main_rows_removed)
            self.model.rowsInserted.connect(self._on_main_rows_inserted)
            self.model.rowsAboutToBeRemoved.connect(self._on_main_rows_about_to_be_removed)
            self.model.rowsAboutToBeInserted.connect(self._on_main_rows_about_to_be_inserted)
        except:
            pass  # Signals might already be connected
    
    def _on_record_toggled(self, checked):
        """Handle record button toggle"""
        if checked:
            self.record_btn.setText("Dừng ghi")
            self.record_btn.setIcon(FIF.PAUSE_BOLD)
            # Stop play if active
            if self.play_btn.isChecked():
                self.play_btn.setChecked(False)
        else:
            self.record_btn.setText("Ghi")
            self.record_btn.setIcon(FIF.VIDEO)
        
        self.record_toggled.emit(checked)
    
    def _on_play_toggled(self, checked):
        """Handle play button toggle"""
        from PySide6.QtGui import QPainter
        icon_size = self.blue_play_icon_size  # Dùng size đã lưu
        
        if checked:
            self.play_btn.setText("Dừng")
            # Tạo icon Pause màu xanh dương với nền tròn xanh dương
            blue_pause_pixmap = QPixmap(icon_size, icon_size)
            blue_pause_pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(blue_pause_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            # Vẽ nền tròn xanh dương
            painter.setBrush(QColor("#0078D4"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(2, 2, icon_size - 4, icon_size - 4)
            # Vẽ 2 thanh Pause màu trắng - điều chỉnh theo icon_size
            painter.setBrush(QColor("#FFFFFF"))
            bar_width = 2
            bar_height = icon_size - 8
            bar_y = 6
            bar_spacing = 3
            painter.drawRect(7, bar_y, bar_width, bar_height)  # Thanh trái
            painter.drawRect(7 + bar_width + bar_spacing, bar_y, bar_width, bar_height)  # Thanh phải
            painter.end()
            blue_pause_icon = QIcon(blue_pause_pixmap)
            self.play_btn.setIcon(blue_pause_icon)
            self.play_btn.setIconSize(QSize(icon_size, icon_size))
            # Stop record if active
            if self.record_btn.isChecked():
                self.record_btn.setChecked(False)
        else:
            self.play_btn.setText("Phát")
            # Dùng lại icon Play xanh dương đã tạo
            self.play_btn.setIcon(self.blue_play_icon)
        
        self.play_toggled.emit(checked)
    
    def set_record_state(self, recording):
        """Externally set record button state without triggering signal"""
        self.record_btn.blockSignals(True)
        self.record_btn.setChecked(recording)
        self.record_btn.blockSignals(False)
        self._on_record_toggled(recording)
    
    def set_play_state(self, playing):
        """Externally set play button state without triggering signal"""
        self.play_btn.blockSignals(True)
        self.play_btn.setChecked(playing)
        self.play_btn.blockSignals(False)
        self._on_play_toggled(playing)
    
    def _on_log_clicked(self):
        """Handle log button click - show playback log dialog"""
        if not hasattr(self, 'log_dialog'):
            from ui.playback_log_dialog import PlaybackLogDialog
            self.log_dialog = PlaybackLogDialog(self)
        
        self.log_dialog.show()
        self.log_dialog.raise_()
        self.log_dialog.activateWindow()
    
    def _on_settings_clicked(self):
        """Handle settings button click - open Settings dialog"""
        # Get main window
        parent = self.parent()
        while parent and not isinstance(parent, QWidget) or not hasattr(parent, 'open_settings'):
            parent = parent.parent()
        
        if parent and hasattr(parent, 'open_settings'):
            # Call main window's open_settings method
            parent.open_settings()
            # Update tooltips after settings dialog closes
            self.update_tooltips()
        else:
            # Fallback: open dialog directly
            from ui.settings_dialog import SettingsDialog
            dialog = SettingsDialog(self)
            if dialog.exec():
                dialog.save_settings()
                self.update_tooltips()
    
    def update_tooltips(self):
        """Update button tooltips with current hotkey settings"""
        from PySide6.QtCore import QSettings
        settings = QSettings("MonSoft", "MacroRecorder")
        
        # Get hotkeys from settings
        record_key = settings.value("hotkey_record", "F9")
        stop_key = settings.value("hotkey_stop_record", "F10")
        play_key = settings.value("hotkey_play", "F11")
        
        # Update tooltips
        self.record_btn.setToolTip(f"Bắt đầu/dừng ghi ({record_key}/{stop_key})")
        self.play_btn.setToolTip(f"Phát/dừng macro ({play_key})")
