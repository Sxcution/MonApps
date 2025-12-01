"""
Auto Detect Dialog - for configuring complex conditional detection with images and text
<!-- auto_detect_dialog : Dialog cấu hình phát hiện tự động với nhiều điều kiện ảnh/text -->
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QGroupBox, QFileDialog, QWidget, QApplication,
                            QGridLayout, QScrollArea, QAbstractSpinBox)
from PySide6.QtCore import Qt, QTimer, QRect, Signal, QPointF, QSize, QThread
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QPalette, QIntValidator
from qfluentwidgets import (PushButton, PrimaryPushButton, ComboBox, SpinBox, 
                           CheckBox, LineEdit, CardWidget, BodyLabel, 
                           StrongBodyLabel, Pivot, qrouter, ScrollArea, SegmentedWidget,
                           MessageBox, FluentIcon, ToolButton)
import os
import time
from utils.image_finder import find_image_on_screen


class ImageSearchThread(QThread):
    """Worker thread for searching image on screen to prevent UI freeze"""
    result_ready = Signal(object)

    def __init__(self, image_path, confidence, region, grayscale, multi_scale):
        super().__init__()
        self.image_path = image_path
        self.confidence = confidence
        self.region = region
        self.grayscale = grayscale
        self.multi_scale = multi_scale

    def run(self):
        try:
            result = find_image_on_screen(
                self.image_path,
                confidence=self.confidence,
                region=self.region,
                grayscale=self.grayscale,
                multi_scale=self.multi_scale
            )
            self.result_ready.emit(result)
        except Exception as e:
            print(f"Search error: {e}")
            self.result_ready.emit(None)


class ImageDetectItem(QWidget):
    """Widget representing one image detection item with thumbnail and controls"""
    # btn_remove_image : Nút xóa ảnh detect này
    remove_requested = Signal(object)  # Signal when remove button is clicked
    add_requested = Signal()           # Signal when add button is clicked
    
    def __init__(self, parent=None, item_index=0):
        super().__init__(parent)
        self.item_index = item_index
        self.image_path = ''
        self.custom_region = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Container - Dùng CardWidget từ qfluentwidgets
        container = CardWidget(self)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(16, 16, 16, 16)
        container_layout.setSpacing(12)
        
        # MAIN LAYOUT: Horizontal (Left: Image, Right: Controls)
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)  # Yêu cầu: không khoảng cách giữa ảnh và controls
        
        # --- LEFT PANEL: Image Preview + Import/Cut Buttons ---
        left_panel = QVBoxLayout()
        left_panel.setSpacing(8)
        left_panel.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Image preview
        self.image_preview = QLabel()
        self.image_preview.setFixedSize(120, 120)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setStyleSheet("""
            QLabel {
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                background-color: #FFFFFF;
            }
        """)
        self.show_placeholder()
        left_panel.addWidget(self.image_preview)
        
        # Buttons below preview: [Delete] [File] [Cut]
        btn_img_layout = QHBoxLayout()
        btn_img_layout.setSpacing(6)
        
        # 1. Delete Button
        self.btn_remove = ToolButton(FluentIcon.DELETE, self)
        self.btn_remove.setFixedSize(30, 30)
        self.btn_remove.setToolTip("Xóa ảnh này")
        # Style for delete button (red hover effect)
        self.btn_remove.setStyleSheet("""
            ToolButton:hover {
                background-color: #D32F2F;
                border-radius: 4px;
            }
            ToolButton:pressed {
                background-color: #B71C1C;
            }
        """)
        self.btn_remove.clicked.connect(self.confirm_remove)
        
        # 2. Load File Button
        self.btn_load = ToolButton(FluentIcon.FOLDER, self)
        self.btn_load.setFixedSize(30, 30)
        self.btn_load.setToolTip("Nhập từ file")
        self.btn_load.clicked.connect(self.load_from_file)
        
        # 3. Capture Button
        self.btn_capture = ToolButton(FluentIcon.CUT, self)
        self.btn_capture.setFixedSize(30, 30)
        self.btn_capture.setToolTip("Cắt từ màn hình")
        self.btn_capture.clicked.connect(self.capture_from_screen)
        
        btn_img_layout.addWidget(self.btn_remove)
        btn_img_layout.addWidget(self.btn_load)
        btn_img_layout.addWidget(self.btn_capture)
        # Add stretch to prevent buttons from expanding
        btn_img_layout.addStretch() 
        
        left_panel.addLayout(btn_img_layout)
        
        main_layout.addLayout(left_panel)
        
        # --- RIGHT PANEL: Header + Inputs ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(8)
        right_panel.setContentsMargins(0, 0, 0, 0) # Sát lề theo yêu cầu "không khoảng cách"
        
        # ROW 1: Header - Label | Grayscale | Multi-scale (No Buttons here)
        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        
        # Label: Ảnh 1 (no #)
        self.lbl_index = StrongBodyLabel(f"Ảnh {self.item_index + 1}")
        self.lbl_index.setStyleSheet("color: #0078D4;")
        header_row.addWidget(self.lbl_index)
        
        # Grayscale + Multi-scale
        self.cb_grayscale = CheckBox("Grayscale")
        self.cb_multiscale = CheckBox("Multi-scale")
        header_row.addWidget(self.cb_grayscale)
        header_row.addWidget(self.cb_multiscale)
        
        header_row.addStretch()
        
        right_panel.addLayout(header_row)
        
        # GRID: Vùng, Độ lệch, Hành động
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        # Adjust column stretch to pack items to the left
        grid_layout.setColumnStretch(4, 1) 
        
        # Row 0: Vùng
        search_area_label = BodyLabel("Vùng:")
        grid_layout.addWidget(search_area_label, 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.combo_window = ComboBox()
        self.combo_window.addItems(["toàn màn hình", "cửa sổ đang focus", "vùng tùy chỉnh"])
        self.combo_window.setCurrentText("toàn màn hình")
        self.combo_window.setFixedWidth(130)
        self.combo_window.currentTextChanged.connect(self.on_search_area_changed)
        grid_layout.addWidget(self.combo_window, 0, 1, Qt.AlignmentFlag.AlignLeft)
        
        self.btn_define = PushButton("Define")
        self.btn_define.setFixedSize(60, 32)
        self.btn_define.clicked.connect(self.define_search_area)
        self.btn_define.setVisible(False)
        grid_layout.addWidget(self.btn_define, 0, 2, Qt.AlignmentFlag.AlignLeft)
        
        # Row 1: Độ lệch (Dung sai) + Test
        # "Dung sai" -> "Độ lệch"
        tolerance_label = BodyLabel("Độ lệch:")
        grid_layout.addWidget(tolerance_label, 1, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Use LineEdit instead of SpinBox to completely remove buttons
        self.input_tolerance = LineEdit()
        self.input_tolerance.setValidator(QIntValidator(0, 255, self))
        self.input_tolerance.setText("0")
        self.input_tolerance.setFixedWidth(90)
        grid_layout.addWidget(self.input_tolerance, 1, 1, Qt.AlignmentFlag.AlignLeft)
        
        self.btn_test = PushButton("Test")
        self.btn_test.setFixedSize(60, 32)
        self.btn_test.clicked.connect(self.test_image_search)
        grid_layout.addWidget(self.btn_test, 1, 2, Qt.AlignmentFlag.AlignLeft)
        
        # Row 2: Hành động
        action_label = BodyLabel("Hành động:")
        grid_layout.addWidget(action_label, 2, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.combo_action = ComboBox()
        self.combo_action.addItems(["Không làm gì", "Press Key", "Key Down", "Click chuột trái", "Click chuột phải", "Hold chuột trái"])
        self.combo_action.setFixedWidth(130)
        self.combo_action.currentTextChanged.connect(self.on_action_changed)
        grid_layout.addWidget(self.combo_action, 2, 1, Qt.AlignmentFlag.AlignLeft)
        
        # Row 3: Tham số
        param_label = BodyLabel("Tham số:")
        self.lbl_param_label = param_label
        self.lbl_param_label.setVisible(False)
        grid_layout.addWidget(param_label, 3, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.input_action_param = LineEdit()
        self.input_action_param.setPlaceholderText("A, D, F...")
        self.input_action_param.setFixedWidth(130)
        self.input_action_param.setVisible(False)
        grid_layout.addWidget(self.input_action_param, 3, 1, Qt.AlignmentFlag.AlignLeft)
        
        # Row 4: Sau đó (Moved from Row 2)
        goto_label = BodyLabel("Sau đó:")
        grid_layout.addWidget(goto_label, 4, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.combo_goto = ComboBox()
        self.combo_goto.addItems(["Không làm gì", "Tiếp theo", "Bắt đầu", "Kết thúc", "Chuyển Đến"])
        self.combo_goto.setFixedWidth(110)
        self.combo_goto.currentTextChanged.connect(self.on_goto_changed)
        grid_layout.addWidget(self.combo_goto, 4, 1, Qt.AlignmentFlag.AlignLeft)
        
        goto_step_label = BodyLabel("Step:")
        self.lbl_goto_step_label = goto_step_label
        self.lbl_goto_step_label.setVisible(False)
        grid_layout.addWidget(goto_step_label, 4, 2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Use LineEdit instead of SpinBox
        self.input_goto_step = LineEdit()
        self.input_goto_step.setValidator(QIntValidator(1, 999, self))
        self.input_goto_step.setText("1")
        self.input_goto_step.setFixedWidth(80)
        self.input_goto_step.setVisible(False)
        grid_layout.addWidget(self.input_goto_step, 4, 3, Qt.AlignmentFlag.AlignLeft)
        
        right_panel.addLayout(grid_layout)
        
        right_panel.addStretch()
        main_layout.addLayout(right_panel)
        
        container_layout.addLayout(main_layout)
        
        # Test result label (Bottom of card)
        self.lbl_test_result = BodyLabel("")
        self.lbl_test_result.setStyleSheet("color: #0078D4; font-weight: bold;")
        container_layout.addWidget(self.lbl_test_result)
        
        layout.addWidget(container)
        
        self.is_snipping = False
    
    def show_placeholder(self):
        """Show placeholder when no image loaded"""
        self.image_preview.setText("No Image")
        self.image_preview.setStyleSheet("""
            QLabel {
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                background-color: #FAFAFA;
                color: #999;
            }
        """)
    
    def on_search_area_changed(self, text):
        """Show/hide Define button"""
        self.btn_define.setVisible(text in ["cửa sổ đang focus", "vùng tùy chỉnh"])
    
    def on_action_changed(self, text):
        """Show/hide action parameter input"""
        if text == "Press Key":
            self.lbl_param_label.setVisible(True)
            self.input_action_param.setVisible(True)
            self.input_action_param.setPlaceholderText("Nhập key (A, D, F...)")
        elif text == "Key Down":
            self.lbl_param_label.setVisible(True)
            self.input_action_param.setVisible(True)
            self.input_action_param.setPlaceholderText("Key và ms (A:1000)")
        elif text == "Hold chuột trái":
            self.lbl_param_label.setVisible(True)
            self.input_action_param.setVisible(True)
            self.input_action_param.setPlaceholderText("Thời gian hold (ms)")
        else:
            self.lbl_param_label.setVisible(False)
            self.input_action_param.setVisible(False)
    
    def on_goto_changed(self, text):
        """Show/hide goto step number input"""
        if text == "Chuyển Đến":
            self.lbl_goto_step_label.setVisible(True)
            self.input_goto_step.setVisible(True)
        else:
            self.lbl_goto_step_label.setVisible(False)
            self.input_goto_step.setVisible(False)
    
    def load_from_file(self):
        """Load image from file"""
        dialog = QFileDialog(self, "Chọn ảnh")
        dialog.setNameFilter("Ảnh (*.png *.jpg *.bmp)")
        if dialog.exec():
            f = dialog.selectedFiles()[0]
            self.image_path = f
            pixmap = QPixmap(f)
            scaled_pixmap = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_preview.setPixmap(scaled_pixmap)
    
    def capture_from_screen(self):
        """Capture image from screen using Snipping Tool"""
        try:
            print(f"🔍 DEBUG: ImageDetectItem #{self.item_index} - Starting capture")
            self.is_snipping = True
            
            # Get parent dialog and minimize it
            parent_dialog = self.window()
            if parent_dialog:
                parent_dialog.lower()
                QApplication.processEvents()
            
            # Minimize main window
            main_window = parent_dialog.parent() if parent_dialog else None
            if main_window:
                main_window.showMinimized()
            
            QApplication.processEvents()
            time.sleep(0.3)
            
            from utils.snipping_tool import SnippingWidget
            self.snipper = SnippingWidget()
            self.snipper.snippet_taken.connect(self.on_snipper_success)
            self.snipper.closed.connect(self.restore_ui)
            
            self.snipper.raise_()
            self.snipper.activateWindow()
            QApplication.processEvents()
            
        except Exception as e:
            print(f"Error launching snipper: {e}")
            self.restore_ui()
    
    def restore_ui(self):
        """Restore UI after snipping"""
        self.is_snipping = False
        parent_dialog = self.window()
        if parent_dialog:
            parent_dialog.raise_()
            parent_dialog.activateWindow()
        
        main_window = parent_dialog.parent() if parent_dialog else None
        if main_window:
            main_window.showNormal()
            main_window.activateWindow()
    
    def on_snipper_success(self, path):
        """Handle successful snippet"""
        self.image_path = path
        pixmap = QPixmap(path)
        scaled_pixmap = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_preview.setPixmap(scaled_pixmap)
        self.restore_ui()
    
    def define_search_area(self):
        """Define custom search area"""
        try:
            print(f"🔍 DEBUG: ImageDetectItem #{self.item_index} - Defining search area")
            self.is_snipping = True
            
            parent_dialog = self.window()
            if parent_dialog:
                parent_dialog.lower()
                QApplication.processEvents()
            
            main_window = parent_dialog.parent() if parent_dialog else None
            if main_window:
                main_window.showMinimized()
            
            QApplication.processEvents()
            time.sleep(0.3)
            
            from utils.snipping_tool import SnippingWidget
            self.snipper = SnippingWidget()
            self.snipper.region_selected.connect(self.on_region_selected)
            self.snipper.closed.connect(self.restore_ui)
            
            self.snipper.showFullScreen()
            
        except Exception as e:
            print(f"Error defining area: {e}")
            self.restore_ui()
    
    def on_region_selected(self, rect):
        """Handle region selection"""
        self.custom_region = {
            'left': rect.x(),
            'top': rect.y(),
            'width': rect.width(),
            'height': rect.height()
        }
        print(f"🔍 DEBUG: Custom region selected: {self.custom_region}")
        self.btn_define.setText(f"Defined ({rect.width()}x{rect.height()})")
        self.btn_define.setStyleSheet("color: green; font-weight: bold;")
        self.restore_ui()
    
    def test_image_search(self):
        """Test image detection"""
        if not self.image_path or not os.path.exists(self.image_path):
            self.lbl_test_result.setText("❌ Chưa chọn ảnh!")
            self.lbl_test_result.setStyleSheet("color: red; font-weight: bold; font-size: 11px;")
            return
        
        tolerance = 0
        try:
            tolerance = int(self.input_tolerance.text())
        except ValueError:
            tolerance = 0
            
        confidence = 1.0 - ((tolerance + 1) / 400.0)
        if confidence < 0.1: confidence = 0.1
        
        self.lbl_test_result.setText("⏳ Tìm...")
        self.lbl_test_result.setStyleSheet("color: blue; font-weight: bold; font-size: 11px;")
        QApplication.processEvents()
        
        region = None
        search_area_text = self.combo_window.currentText()
        
        if search_area_text == "cửa sổ đang focus":
            from utils.window_utils import get_foreground_window_rect
            region = get_foreground_window_rect()
        elif search_area_text == "vùng tùy chỉnh":
            region = self.custom_region
        
        # Use Thread for searching to prevent UI freeze
        self.search_thread = ImageSearchThread(
            self.image_path,
            confidence,
            region,
            self.cb_grayscale.isChecked(),
            self.cb_multiscale.isChecked()
        )
        self.search_thread.result_ready.connect(self.on_search_result)
        
        # Disable button while searching
        self.btn_test.setEnabled(False)
        self.search_thread.start()
        
    def on_search_result(self, result):
        """Handle search result from thread"""
        self.btn_test.setEnabled(True)
        
        if result:
            x, y, w, h = result
            self.lbl_test_result.setText(f"✅ Tìm thấy: {x}, {y}")
            self.lbl_test_result.setStyleSheet("color: green; font-weight: bold; font-size: 11px;")
        else:
            self.lbl_test_result.setText("❌ Không tìm thấy!")
            self.lbl_test_result.setStyleSheet("color: red; font-weight: bold; font-size: 11px;")
            
    def confirm_remove(self):
        """Ask for confirmation before removing"""
        w = MessageBox(
            "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa Ảnh #{self.item_index + 1} không?",
            self.window()
        )
        if w.exec():
            self.remove_requested.emit(self)
    
    def get_data(self):
        """Get configuration data for this image item"""
        search_area_map = {
            'cửa sổ đang focus': 'focused window',
            'toàn màn hình': 'entire screen',
            'vùng tùy chỉnh': 'custom region'
        }
        
        action_map = {
            'Không làm gì': 'none',
            'Press Key': 'press_key',
            'Key Down': 'key_down',
            'Click chuột trái': 'left_click',
            'Click chuột phải': 'right_click',
            'Hold chuột trái': 'hold_left'
        }
        
        goto_map = {
            'Không làm gì': 'none',
            'Tiếp theo': 'Next',
            'Bắt đầu': 'Start',
            'Kết thúc': 'End',
            'Chuyển Đến': f"Step {self.input_goto_step.text()}"
        }
        
        goto_text = self.combo_goto.currentText()
        goto_value = goto_map.get(goto_text, 'none')
        if goto_text == 'Chuyển Đến':
            goto_value = f"Step {self.input_goto_step.text()}"
        
        tolerance = 0
        try:
            tolerance = int(self.input_tolerance.text())
        except ValueError:
            tolerance = 0
            
        return {
            'image_path': self.image_path,
            'search_area': search_area_map.get(self.combo_window.currentText(), 'entire screen'),
            'custom_region': self.custom_region,
            'tolerance': tolerance,
            'grayscale': self.cb_grayscale.isChecked(),
            'multi_scale': self.cb_multiscale.isChecked(),
            'action': action_map.get(self.combo_action.currentText(), 'none'),
            'action_param': self.input_action_param.text(),
            'goto': goto_value
        }
    
    def set_data(self, data):
        """Load data into this item"""
        if not data:
            return
        
        if 'image_path' in data and data['image_path']:
            self.image_path = data['image_path']
            if os.path.exists(self.image_path):
                pixmap = QPixmap(self.image_path)
                scaled_pixmap = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.image_preview.setPixmap(scaled_pixmap)
        
        search_area_map = {
            'focused window': 'cửa sổ đang focus',
            'entire screen': 'toàn màn hình',
            'custom region': 'vùng tùy chỉnh'
        }
        if 'search_area' in data:
            self.combo_window.setCurrentText(search_area_map.get(data['search_area'], 'toàn màn hình'))
        
        if 'custom_region' in data:
            self.custom_region = data['custom_region']
        
        if 'tolerance' in data:
            self.input_tolerance.setText(str(data['tolerance']))
        
        if 'grayscale' in data:
            self.cb_grayscale.setChecked(data['grayscale'])
        
        if 'multi_scale' in data:
            self.cb_multiscale.setChecked(data['multi_scale'])
        
        action_map = {
            'none': 'Không làm gì',
            'press_key': 'Press Key',
            'key_down': 'Key Down',
            'left_click': 'Click chuột trái',
            'right_click': 'Click chuột phải',
            'hold_left': 'Hold chuột trái'
        }
        if 'action' in data:
            self.combo_action.setCurrentText(action_map.get(data['action'], 'Không làm gì'))
        
        if 'action_param' in data:
            self.input_action_param.setText(data['action_param'])
        
        # Load goto
        if 'goto' in data:
            goto_str = data['goto']
            if goto_str == 'none':
                self.combo_goto.setCurrentText('Không làm gì')
            elif goto_str == 'Next':
                self.combo_goto.setCurrentText('Tiếp theo')
            elif goto_str == 'Start':
                self.combo_goto.setCurrentText('Bắt đầu')
            elif goto_str == 'End':
                self.combo_goto.setCurrentText('Kết thúc')
            elif goto_str.startswith('Step '):
                self.combo_goto.setCurrentText('Chuyển Đến')
                try:
                    step_num = goto_str.replace('Step ', '')
                    self.input_goto_step.setText(step_num)
                except:
                    pass


class AutoDetectDialog(QDialog):
    """
    Dialog for Auto Detect - complex conditional detection with multiple images/text
    <!-- dialog_auto_detect : Dialog cấu hình Auto Detect -->
    """
    def __init__(self, parent=None, event=None):
        super().__init__(parent)
        self.setWindowTitle("Auto Detect - Phát hiện tự động")
        self.resize(800, 750)  # Tăng chiều cao từ 700 lên 750
        
        self.event = event if event else {}
        self.image_items = []  # List of ImageDetectItem widgets
        
        self.setup_ui()
        self.load_event_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Top Bar: Tabs (SegmentedWidget) + Global Add Button
        top_layout = QHBoxLayout()
        
        # PIVOT (Tab)
        self.pivot = SegmentedWidget(self)
        self.pivot.addItem(routeKey='image', text='Hình Ảnh', onClick=lambda: self.stackedWidget.setCurrentIndex(0))
        self.pivot.addItem(routeKey='text', text='Text', onClick=lambda: self.stackedWidget.setCurrentIndex(1))
        top_layout.addWidget(self.pivot)
        
        top_layout.addStretch()
        
        # btn_add_global : Nút thêm item (cho tab hiện tại)
        self.btn_add_global = PrimaryPushButton("+ Thêm", self)
        self.btn_add_global.setFixedSize(80, 32)
        self.btn_add_global.clicked.connect(self.on_add_clicked)
        top_layout.addWidget(self.btn_add_global)
        
        layout.addLayout(top_layout)
        
        # Stacked widget cho các tab
        from PySide6.QtWidgets import QStackedWidget
        self.stackedWidget = QStackedWidget(self)
        
        # Tab 1: Image Detection
        self.tab_image = QWidget()
        self.setup_image_tab()
        self.stackedWidget.addWidget(self.tab_image)
        
        # Tab 2: Text Detection (placeholder)
        self.tab_text = QWidget()
        self.setup_text_tab()
        self.stackedWidget.addWidget(self.tab_text)
        
        layout.addWidget(self.stackedWidget)
        
        # Global settings - GỘP THÀNH 1 HÀNG (dùng CardWidget)
        global_card = CardWidget(self)
        global_layout = QHBoxLayout(global_card)
        global_layout.setContentsMargins(16, 12, 16, 12)
        global_layout.setSpacing(20)
        
        global_layout.addWidget(BodyLabel("Quét lại mỗi:"))
        # Use LineEdit + Label for Scan Interval
        interval_layout = QHBoxLayout()
        interval_layout.setSpacing(4)
        
        self.input_scan_interval = LineEdit()
        self.input_scan_interval.setValidator(QIntValidator(50, 10000, self))
        self.input_scan_interval.setText("200")
        self.input_scan_interval.setFixedWidth(60)
        interval_layout.addWidget(self.input_scan_interval)
        interval_layout.addWidget(BodyLabel("ms"))
        
        global_layout.addLayout(interval_layout)
        
        global_layout.addWidget(BodyLabel("Thời gian chờ tối đa:"))
        # Use LineEdit + Label for Max Duration
        duration_layout = QHBoxLayout()
        duration_layout.setSpacing(4)
        
        self.input_max_duration = LineEdit()
        self.input_max_duration.setValidator(QIntValidator(1, 999999, self))
        self.input_max_duration.setText("65535")
        self.input_max_duration.setFixedWidth(80)
        duration_layout.addWidget(self.input_max_duration)
        duration_layout.addWidget(BodyLabel("s"))
        
        global_layout.addLayout(duration_layout)
        
        global_layout.addWidget(BodyLabel("Nếu hết thời gian:"))
        # combo_goto_timeout : Hành động khi hết thời gian chờ
        self.combo_goto_timeout = ComboBox()
        self.combo_goto_timeout.addItems(["Tiếp theo", "Bắt đầu", "Kết thúc"])
        self.combo_goto_timeout.setFixedWidth(120)
        global_layout.addWidget(self.combo_goto_timeout)
        
        global_layout.addStretch()
        layout.addWidget(global_card)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        # btn_cancel : Nút Hủy
        self.btn_cancel = PushButton("Hủy")
        self.btn_cancel.setFixedSize(100, 36)
        self.btn_cancel.clicked.connect(self.reject)
        # btn_ok : Nút OK
        self.btn_ok = PrimaryPushButton("OK")
        self.btn_ok.setFixedSize(100, 36)
        self.btn_ok.clicked.connect(self.accept)
        button_layout.addWidget(self.btn_cancel)
        button_layout.addWidget(self.btn_ok)
        layout.addLayout(button_layout)
    
    def on_add_clicked(self):
        """Handle global add button click"""
        current_index = self.stackedWidget.currentIndex()
        if current_index == 0: # Image Tab
            self.add_image_item()
        elif current_index == 1: # Text Tab
            # Placeholder for text item addition
            pass

    def setup_image_tab(self):
        """Setup Image Detection tab"""
        layout = QVBoxLayout(self.tab_image)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(12)
        
        # ScrollArea với Fluent Widgets style
        self.scroll_area = ScrollArea(self.tab_image)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Container for image items
        # container_image_items : Container chứa các ImageDetectItem
        self.image_items_container = QWidget()
        self.image_items_layout = QVBoxLayout(self.image_items_container)
        self.image_items_layout.setContentsMargins(0, 0, 8, 0)
        self.image_items_layout.setSpacing(12)
        self.image_items_layout.addStretch()
        
        self.scroll_area.setWidget(self.image_items_container)
        layout.addWidget(self.scroll_area)
        
        # Add first item by default
        self.add_image_item()
    
    def setup_text_tab(self):
        """Setup Text Detection tab (placeholder)"""
        layout = QVBoxLayout(self.tab_text)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Placeholder với Fluent style
        placeholder = BodyLabel("Text Detection sẽ được phát triển trong phiên bản sau.\n\nChức năng này cho phép quét text trên màn hình bằng OCR và thực hiện hành động tương ứng.")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setWordWrap(True)
        placeholder.setStyleSheet("color: #999; padding: 40px;")
        layout.addWidget(placeholder)
    
    def add_image_item(self):
        """Add a new image detection item"""
        item_index = len(self.image_items)
        item = ImageDetectItem(self, item_index)
        item.remove_requested.connect(self.remove_image_item)
        item.add_requested.connect(self.add_image_item)
        
        self.image_items.append(item)
        # Insert before stretch
        self.image_items_layout.insertWidget(self.image_items_layout.count() - 1, item)
        
        # Update indices for all items
        self.update_image_indices()
    
    def remove_image_item(self, item):
        """Remove an image detection item"""
        if len(self.image_items) <= 1:
            # Don't allow removing the last item
            return
        
        if item in self.image_items:
            self.image_items.remove(item)
            self.image_items_layout.removeWidget(item)
            item.deleteLater()
            
            # Update indices
            self.update_image_indices()
    
    def update_image_indices(self):
        """Update index labels for all image items"""
        for idx, item in enumerate(self.image_items):
            item.item_index = idx
            item.lbl_index.setText(f"Ảnh {idx + 1}") # Bỏ dấu #
    
    def load_event_data(self):
        """Load event data into dialog"""
        if not self.event:
            return
        
        # Load global settings
        if 'scan_interval' in self.event:
            self.input_scan_interval.setText(str(self.event['scan_interval']))
        
        if 'max_duration' in self.event:
            self.input_max_duration.setText(str(self.event['max_duration']))
        
        goto_map = {'Next': 'Tiếp theo', 'Start': 'Bắt đầu', 'End': 'Kết thúc'}
        if 'goto_timeout' in self.event:
            self.combo_goto_timeout.setCurrentText(goto_map.get(self.event['goto_timeout'], 'Tiếp theo'))
        
        # Load image items
        if 'image_detects' in self.event and self.event['image_detects']:
            # Clear default item (force remove without min check)
            while self.image_items:
                item = self.image_items[0]
                self.image_items.remove(item)
                self.image_items_layout.removeWidget(item)
                item.deleteLater()
            
            # Add items from data
            for img_data in self.event['image_detects']:
                self.add_image_item()
                self.image_items[-1].set_data(img_data)
    
    def get_data(self):
        """Get configuration data from dialog"""
        goto_map = {
            'Tiếp theo': 'Next',
            'Bắt đầu': 'Start',
            'Kết thúc': 'End'
        }
        
        # Collect image items data
        image_detects = []
        for item in self.image_items:
            image_detects.append(item.get_data())
            
        scan_interval = 200
        try:
            scan_interval = int(self.input_scan_interval.text())
        except ValueError:
            pass
            
        max_duration = 65535
        try:
            max_duration = int(self.input_max_duration.text())
        except ValueError:
            pass
        
        return {
            'type': 'auto_detect',
            'scan_interval': scan_interval,
            'max_duration': max_duration,
            'goto_timeout': goto_map.get(self.combo_goto_timeout.currentText(), 'Next'),
            'image_detects': image_detects,
            'time': self.event.get('time', 0.5)
        }

