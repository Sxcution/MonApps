"""
Auto Detect Dialog - for configuring complex conditional detection with images and text
<!-- auto_detect_dialog : Dialog cấu hình phát hiện tự động với nhiều điều kiện ảnh/text -->
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QCheckBox, QComboBox, QSpinBox,
                            QGroupBox, QFormLayout, QFileDialog, QWidget, QApplication,
                            QStyleOptionButton, QStyle, QAbstractItemView, QStyleOptionComboBox,
                            QGridLayout, QTabWidget, QScrollArea, QTextEdit, QLineEdit)
from PySide6.QtCore import Qt, QTimer, QRect, Signal, QPointF, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QPalette
import os
import time
from utils.image_finder import find_image_on_screen

# Reuse styled components from ImageSearchDialog
from ui.image_search_dialog import StyledComboBox, StyledCheckBox, ImagePreviewLabel


class ImageDetectItem(QWidget):
    """Widget representing one image detection item with thumbnail and controls"""
    # btn_remove_image : Nút xóa ảnh detect này
    remove_requested = Signal(object)  # Signal when remove button is clicked
    
    def __init__(self, parent=None, item_index=0):
        super().__init__(parent)
        self.item_index = item_index
        self.image_path = ''
        self.custom_region = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        
        # Container with border
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                background-color: #F9F9F9;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(8)
        
        # Header with index and remove button
        header_layout = QHBoxLayout()
        # lbl_image_detect_index : Label hiển thị số thứ tự ảnh
        self.lbl_index = QLabel(f"Ảnh #{self.item_index + 1}")
        self.lbl_index.setStyleSheet("font-weight: bold; font-size: 13px; color: #0078D4;")
        header_layout.addWidget(self.lbl_index)
        header_layout.addStretch()
        
        # btn_remove_image : Nút xóa ảnh detect này
        self.btn_remove = QPushButton("✖ Xóa")
        self.btn_remove.setFixedSize(60, 24)
        self.btn_remove.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #B71C1C;
            }
        """)
        self.btn_remove.clicked.connect(lambda: self.remove_requested.emit(self))
        header_layout.addWidget(self.btn_remove)
        container_layout.addLayout(header_layout)
        
        # Image preview and controls
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left: Image preview
        preview_container = QVBoxLayout()
        preview_container.setSpacing(8)
        # img_preview : Preview ảnh
        self.image_preview = ImagePreviewLabel()
        self.image_preview.setMinimumSize(150, 150)
        self.image_preview.setMaximumSize(150, 150)
        preview_container.addWidget(self.image_preview)
        
        # Buttons below preview
        btn_container = QHBoxLayout()
        btn_container.setSpacing(6)
        # btn_load_image : Nút nhập ảnh từ file
        self.btn_load = QPushButton("Nhập Ảnh")
        self.btn_load.setMinimumHeight(26)
        self.btn_load.clicked.connect(self.load_from_file)
        # btn_capture_image : Nút cắt ảnh từ màn hình
        self.btn_capture = QPushButton("Cắt Ảnh")
        self.btn_capture.setMinimumHeight(26)
        self.btn_capture.clicked.connect(self.capture_from_screen)
        
        btn_container.addWidget(self.btn_load)
        btn_container.addWidget(self.btn_capture)
        preview_container.addLayout(btn_container)
        
        content_layout.addLayout(preview_container)
        
        # Right: Options
        options_container = QVBoxLayout()
        options_container.setSpacing(10)
        
        # Grid for options
        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)
        
        # Row 0: Search Area
        search_area_label = QLabel("Vùng Tìm:")
        search_area_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(search_area_label, 0, 0)
        
        # combo_search_area : ComboBox chọn vùng tìm kiếm
        self.combo_window = StyledComboBox()
        self.combo_window.addItems(["toàn màn hình", "cửa sổ đang focus", "vùng tùy chỉnh"])
        self.combo_window.setCurrentText("toàn màn hình")
        self.combo_window.setMinimumWidth(130)
        self.combo_window.currentTextChanged.connect(self.on_search_area_changed)
        grid_layout.addWidget(self.combo_window, 0, 1)
        
        # btn_define_region : Nút định nghĩa vùng tìm kiếm
        self.btn_define = QPushButton("Define")
        self.btn_define.setMinimumHeight(26)
        self.btn_define.setMinimumWidth(60)
        self.btn_define.clicked.connect(self.define_search_area)
        self.btn_define.setVisible(False)
        grid_layout.addWidget(self.btn_define, 0, 2)
        
        # Row 1: Tolerance
        tolerance_label = QLabel("Độ dung sai:")
        tolerance_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(tolerance_label, 1, 0)
        
        # spin_tolerance : Độ dung sai màu (0-255)
        self.spin_tolerance = QSpinBox()
        self.spin_tolerance.setRange(0, 255)
        self.spin_tolerance.setSuffix(" / 255")
        self.spin_tolerance.setMinimumWidth(90)
        grid_layout.addWidget(self.spin_tolerance, 1, 1)
        
        # btn_test_image : Nút test tìm ảnh
        self.btn_test = QPushButton("Test")
        self.btn_test.setMinimumHeight(26)
        self.btn_test.clicked.connect(self.test_image_search)
        grid_layout.addWidget(self.btn_test, 1, 2)
        
        # Row 2: Action on found
        action_label = QLabel("Hành động:")
        action_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(action_label, 2, 0)
        
        # combo_action : ComboBox chọn hành động khi tìm thấy
        self.combo_action = StyledComboBox()
        self.combo_action.addItems(["Không làm gì", "Press Key", "Key Down", "Click chuột trái", "Click chuột phải", "Hold chuột trái"])
        self.combo_action.setMinimumWidth(130)
        self.combo_action.currentTextChanged.connect(self.on_action_changed)
        grid_layout.addWidget(self.combo_action, 2, 1)
        
        # Bước Kế (Goto) - cùng hàng với Hành động
        goto_label = QLabel("Bước Kế:")
        goto_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(goto_label, 2, 2)
        
        # combo_goto : ComboBox chọn bước kế tiếp
        self.combo_goto = StyledComboBox()
        self.combo_goto.addItems(["Không làm gì", "Tiếp theo", "Bắt đầu", "Kết thúc", "Chuyển Đến"])
        self.combo_goto.setMinimumWidth(120)
        self.combo_goto.currentTextChanged.connect(self.on_goto_changed)
        grid_layout.addWidget(self.combo_goto, 2, 3)
        
        # Row 3: Action parameter (hidden by default)
        param_label = QLabel("Tham số:")
        param_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(param_label, 3, 0)
        
        # input_action_param : Input cho tham số hành động (key hoặc duration)
        self.input_action_param = QLineEdit()
        self.input_action_param.setPlaceholderText("Ví dụ: A, D, F...")
        self.input_action_param.setVisible(False)
        grid_layout.addWidget(self.input_action_param, 3, 1)
        
        # lbl_param_label : Label tham số động
        self.lbl_param_label = param_label
        self.lbl_param_label.setVisible(False)
        
        # Goto step number (hidden by default)
        goto_step_label = QLabel("Step:")
        goto_step_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(goto_step_label, 3, 2)
        self.lbl_goto_step_label = goto_step_label
        self.lbl_goto_step_label.setVisible(False)
        
        # spin_goto_step : Step number cho Chuyển Đến
        self.spin_goto_step = QSpinBox()
        self.spin_goto_step.setRange(1, 999)
        self.spin_goto_step.setValue(1)
        self.spin_goto_step.setMinimumWidth(80)
        self.spin_goto_step.setVisible(False)
        grid_layout.addWidget(self.spin_goto_step, 3, 3)
        
        grid_layout.setColumnStretch(4, 1)
        options_container.addLayout(grid_layout)
        
        # Advanced options
        adv_layout = QHBoxLayout()
        adv_layout.setSpacing(12)
        # cb_grayscale : Checkbox chế độ grayscale
        self.cb_grayscale = StyledCheckBox("Grayscale")
        # cb_multiscale : Checkbox chế độ multi-scale
        self.cb_multiscale = StyledCheckBox("Multi-scale")
        adv_layout.addWidget(self.cb_grayscale)
        adv_layout.addWidget(self.cb_multiscale)
        adv_layout.addStretch()
        options_container.addLayout(adv_layout)
        
        # Test result label
        # lbl_test_result : Label hiển thị kết quả test
        self.lbl_test_result = QLabel("")
        self.lbl_test_result.setStyleSheet("font-weight: bold; font-size: 11px;")
        options_container.addWidget(self.lbl_test_result)
        
        options_container.addStretch()
        content_layout.addLayout(options_container, 1)
        
        container_layout.addLayout(content_layout)
        layout.addWidget(container)
        
        self.is_snipping = False
    
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
            self.spin_goto_step.setVisible(True)
        else:
            self.lbl_goto_step_label.setVisible(False)
            self.spin_goto_step.setVisible(False)
    
    def load_from_file(self):
        """Load image from file"""
        dialog = QFileDialog(self, "Chọn ảnh")
        dialog.setNameFilter("Ảnh (*.png *.jpg *.bmp)")
        if dialog.exec():
            f = dialog.selectedFiles()[0]
            self.image_path = f
            self.image_preview.set_image(QPixmap(f))
    
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
        self.image_preview.set_image(QPixmap(path))
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
        
        tolerance = self.spin_tolerance.value()
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
        
        result = find_image_on_screen(
            self.image_path,
            confidence=confidence,
            region=region,
            grayscale=self.cb_grayscale.isChecked(),
            multi_scale=self.cb_multiscale.isChecked()
        )
        
        if result:
            x, y, w, h = result
            self.lbl_test_result.setText(f"✅ Tìm thấy: {x}, {y}")
            self.lbl_test_result.setStyleSheet("color: green; font-weight: bold; font-size: 11px;")
        else:
            self.lbl_test_result.setText("❌ Không tìm thấy!")
            self.lbl_test_result.setStyleSheet("color: red; font-weight: bold; font-size: 11px;")
    
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
            'Chuyển Đến': f"Step {self.spin_goto_step.value()}"
        }
        
        goto_text = self.combo_goto.currentText()
        goto_value = goto_map.get(goto_text, 'none')
        if goto_text == 'Chuyển Đến':
            goto_value = f"Step {self.spin_goto_step.value()}"
        
        return {
            'image_path': self.image_path,
            'search_area': search_area_map.get(self.combo_window.currentText(), 'entire screen'),
            'custom_region': self.custom_region,
            'tolerance': self.spin_tolerance.value(),
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
                self.image_preview.set_image(QPixmap(self.image_path))
        
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
            self.spin_tolerance.setValue(data['tolerance'])
        
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
                    step_num = int(goto_str.replace('Step ', ''))
                    self.spin_goto_step.setValue(step_num)
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
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Tab Widget (đưa lên đầu tiên)
        # tab_widget : Tab widget chứa tab Hình Ảnh và Text
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background: white;
            }
            QTabBar::tab {
                background: #F5F5F5;
                color: #333333;
                padding: 8px 20px;
                margin-right: 2px;
                border: 1px solid #E0E0E0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #0078D4;
                font-weight: bold;
                border-bottom: 2px solid #0078D4;
            }
            QTabBar::tab:hover {
                background: #E8E8E8;
            }
        """)
        
        # Tab 1: Image Detection
        # tab_image_detect : Tab Hình Ảnh
        self.tab_image = QWidget()
        self.setup_image_tab()
        self.tab_widget.addTab(self.tab_image, "Hình Ảnh")
        
        # Tab 2: Text Detection
        # tab_text_detect : Tab Text
        self.tab_text = QWidget()
        self.setup_text_tab()
        self.tab_widget.addTab(self.tab_text, "Text")
        
        layout.addWidget(self.tab_widget)
        
        # Global settings group - GỘP THÀNH 1 HÀNG
        global_group = QGroupBox("Cài đặt chung:")
        global_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        global_layout = QHBoxLayout()
        global_layout.setSpacing(15)
        
        # Scan interval
        global_layout.addWidget(QLabel("Quét lại mỗi:"))
        # spin_scan_interval : Khoảng thời gian quét lại (ms)
        self.spin_scan_interval = QSpinBox()
        self.spin_scan_interval.setRange(50, 10000)
        self.spin_scan_interval.setValue(200)
        self.spin_scan_interval.setSuffix(" ms")
        self.spin_scan_interval.setMaximumWidth(120)
        global_layout.addWidget(self.spin_scan_interval)
        
        # Max duration
        global_layout.addWidget(QLabel("Thời gian chờ tối đa:"))
        # spin_max_duration : Thời gian chờ tối đa (s)
        self.spin_max_duration = QSpinBox()
        self.spin_max_duration.setRange(1, 999999)
        self.spin_max_duration.setValue(65535)
        self.spin_max_duration.setSuffix(" giây")
        self.spin_max_duration.setMaximumWidth(120)
        global_layout.addWidget(self.spin_max_duration)
        
        # Goto on timeout
        global_layout.addWidget(QLabel("Nếu hết thời gian chờ:"))
        # combo_goto_timeout : Hành động khi hết thời gian chờ
        self.combo_goto_timeout = StyledComboBox()
        self.combo_goto_timeout.addItems(["Tiếp theo", "Bắt đầu", "Kết thúc"])
        self.combo_goto_timeout.setMinimumWidth(120)
        global_layout.addWidget(self.combo_goto_timeout)
        
        global_layout.addStretch()
        
        global_group.setLayout(global_layout)
        layout.addWidget(global_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        # btn_ok : Nút OK
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setDefault(True)
        self.btn_ok.setMinimumWidth(80)
        self.btn_ok.setMinimumHeight(28)
        self.btn_ok.clicked.connect(self.accept)
        # btn_cancel : Nút Hủy
        self.btn_cancel = QPushButton("Hủy")
        self.btn_cancel.setMinimumWidth(80)
        self.btn_cancel.setMinimumHeight(28)
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        layout.addLayout(button_layout)
    
    def setup_image_tab(self):
        """Setup Image Detection tab"""
        layout = QVBoxLayout(self.tab_image)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Instruction label
        instruction = QLabel("Thêm nhiều ảnh để quét. Khi tìm thấy ảnh nào, hệ thống sẽ thực hiện hành động tương ứng.")
        instruction.setWordWrap(True)
        instruction.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(instruction)
        
        # Add image button
        # btn_add_image : Nút thêm ảnh mới
        self.btn_add_image = QPushButton("+ Thêm Ảnh")
        self.btn_add_image.setMinimumHeight(32)
        self.btn_add_image.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
        """)
        self.btn_add_image.clicked.connect(self.add_image_item)
        layout.addWidget(self.btn_add_image)
        
        # Scroll area for image items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        # Container for image items
        # container_image_items : Container chứa các ImageDetectItem
        self.image_items_container = QWidget()
        self.image_items_layout = QVBoxLayout(self.image_items_container)
        self.image_items_layout.setContentsMargins(0, 0, 0, 0)
        self.image_items_layout.setSpacing(10)
        self.image_items_layout.addStretch()
        
        scroll.setWidget(self.image_items_container)
        layout.addWidget(scroll)
        
        # Add first item by default
        self.add_image_item()
    
    def setup_text_tab(self):
        """Setup Text Detection tab"""
        layout = QVBoxLayout(self.tab_text)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Placeholder for future text detection implementation
        placeholder = QLabel("Text Detection sẽ được phát triển trong phiên bản sau.\n\nChức năng này cho phép quét text trên màn hình bằng OCR và thực hiện hành động tương ứng.")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #999999; font-size: 13px; padding: 40px;")
        layout.addWidget(placeholder)
    
    def add_image_item(self):
        """Add a new image detection item"""
        item_index = len(self.image_items)
        item = ImageDetectItem(self, item_index)
        item.remove_requested.connect(self.remove_image_item)
        
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
            item.lbl_index.setText(f"Ảnh #{idx + 1}")
    
    def load_event_data(self):
        """Load event data into dialog"""
        if not self.event:
            return
        
        # Load global settings
        if 'scan_interval' in self.event:
            self.spin_scan_interval.setValue(self.event['scan_interval'])
        
        if 'max_duration' in self.event:
            self.spin_max_duration.setValue(self.event['max_duration'])
        
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
        
        return {
            'type': 'auto_detect',
            'scan_interval': self.spin_scan_interval.value(),
            'max_duration': self.spin_max_duration.value(),
            'goto_timeout': goto_map.get(self.combo_goto_timeout.currentText(), 'Next'),
            'image_detects': image_detects,
            'time': self.event.get('time', 0.5)
        }

