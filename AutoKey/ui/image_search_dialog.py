"""
Image Search Dialog - for configuring image detection actions
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QCheckBox, QComboBox, QSpinBox,
                            QGroupBox, QFormLayout, QFileDialog, QWidget, QApplication,
                            QStyleOptionButton, QStyle, QAbstractItemView, QStyleOptionComboBox,
                            QGridLayout)
from PyQt6.QtCore import Qt, QTimer, QRect, pyqtSignal, QPointF
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QPalette
import os
import time
from utils.image_finder import find_image_on_screen

class StyledComboBox(QComboBox):
    """QComboBox with styled dropdown menu border"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Đảm bảo text không bị cắt
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.setMinimumContentsLength(0)  # Không giới hạn độ dài tối thiểu
    
    def paintEvent(self, event):
        """Override paintEvent để hiển thị đầy đủ text không bị cắt"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Vẽ background
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        style = self.style()
        style.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option, painter, self)
        
        # Vẽ text đầy đủ
        text_rect = style.subControlRect(
            QStyle.ComplexControl.CC_ComboBox, 
            option, 
            QStyle.SubControl.SC_ComboBoxEditField, 
            self
        )
        text_rect.adjust(4, 0, -4, 0)  # Thêm padding nhẹ, không trừ quá nhiều
        
        current_text = self.currentText()
        if current_text:
            painter.setPen(self.palette().color(QPalette.ColorRole.Text))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, current_text)
    
    def showPopup(self):
        """Override to style popup menu when shown"""
        super().showPopup()
        # Get the popup menu (QAbstractItemView)
        popup = self.view()
        if popup:
            # Đảm bảo dropdown menu đủ rộng để hiển thị đầy đủ text
            # Tính toán width dựa trên text dài nhất
            max_width = self.width()
            for i in range(self.count()):
                text_width = self.fontMetrics().boundingRect(self.itemText(i)).width()
                max_width = max(max_width, text_width + 40)  # +40 cho padding và border
            popup.setMinimumWidth(max_width)
            popup.setStyleSheet("""
                QAbstractItemView {
                    background-color: #FFFFFF;
                    border: 2px solid #000000;
                    border-radius: 4px;
                    selection-background-color: #E5F3FF;
                    selection-color: #000000;
                    outline: none;
                    padding: 0px;
                }
                QAbstractItemView::item {
                    padding: 4px 8px;
                    border: none;
                    background-color: transparent;
                }
                QAbstractItemView::item:hover {
                    background-color: #E5F3FF;
                    border: none;
                }
                QAbstractItemView::item:selected {
                    background-color: #0078D4;
                    color: #FFFFFF;
                    border: 1px solid #000000;
                }
            """)

class StyledCheckBox(QCheckBox):
    """QCheckBox with modern styled appearance - like "Enable notifications" example"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QCheckBox {
                spacing: 8px;
                color: #1A1A1A;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #0078D4;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                background-color: #FFFFFF;
                border: 2px solid #0078D4;
            }
            QCheckBox::indicator:unchecked {
                background-color: #FFFFFF;
                border: 2px solid #CCCCCC;
            }
            QCheckBox::indicator:unchecked:hover {
                border: 2px solid #0078D4;
                background-color: #F5F5F5;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #F5F5F5;
                border: 2px solid #005A9E;
            }
        """)
    
    def paintEvent(self, event):
        """Override to draw white checkmark when checked"""
        super().paintEvent(event)
        
        if self.isChecked():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Create style option to get indicator rect
            opt = QStyleOptionButton()
            self.initStyleOption(opt)
            
            # Get indicator rectangle using style
            indicator_rect = self.style().subElementRect(
                QStyle.SubElement.SE_CheckBoxIndicator,
                opt,
                self
            )
            
            if not indicator_rect.isEmpty():
                # Draw black checkmark
                painter.setPen(QPen(QColor(0, 0, 0), 2.5, 
                                  Qt.PenStyle.SolidLine, 
                                  Qt.PenCapStyle.RoundCap, 
                                  Qt.PenJoinStyle.RoundJoin))
                
                # Calculate checkmark points (centered in indicator)
                center_x = indicator_rect.x() + indicator_rect.width() / 2
                center_y = indicator_rect.y() + indicator_rect.height() / 2
                
                # Draw checkmark: left point -> middle point -> right point
                checkmark_points = [
                    QPointF(center_x - 4, center_y),
                    QPointF(center_x - 1, center_y + 3),
                    QPointF(center_x + 4, center_y - 2)
                ]
                
                painter.drawPolyline(checkmark_points)
            
            painter.end()

class ImagePreviewLabel(QLabel):
    """Custom label to display image with icon overlay if no image"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.setMaximumSize(200, 200)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel { 
                border: 1px solid #CCCCCC; 
                background: #FFFFFF;
                border-radius: 4px;
            }
        """)
        self.pixmap_data = None
        self.show_placeholder()
        
    def show_placeholder(self):
        placeholder = QPixmap(200, 200)
        placeholder.fill(Qt.GlobalColor.white)
        painter = QPainter(placeholder)
        painter.setPen(QColor(200, 200, 200))
        painter.setBrush(QColor(245, 245, 245))
        # Draw frame
        painter.drawRect(50, 50, 100, 100)
        # Draw question mark
        painter.setPen(QColor(180, 180, 180))
        painter.setFont(painter.font())
        painter.drawText(75, 75, 50, 50, Qt.AlignmentFlag.AlignCenter, "?")
        painter.end()
        self.setPixmap(placeholder)
        
    def set_image(self, pixmap):
        if pixmap and not pixmap.isNull():
            self.pixmap_data = pixmap
            scaled = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, 
                                 Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(scaled)
        else:
            self.show_placeholder()

class ImageSearchDialog(QDialog):
    def __init__(self, parent=None, event=None):
        super().__init__(parent)
        self.setWindowTitle("Tìm kiếm ảnh")
        # CRITICAL: Do NOT use WA_DeleteOnClose - we need to keep dialog alive during snipping
        # self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(560, 600)
        
        self.event = event if event else {}
        self.captured_pixmap = None
        self.image_path = self.event.get('image_path', '')
        self.image_path = self.event.get('image_path', '')
        self.is_snipping = False  # Track snipping state
        self.custom_region = self.event.get('custom_region', None) # Store custom region rect
        
        self.setup_ui()
        self.load_event_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Description
        desc_label = QLabel("Tìm vị trí của ảnh đã định nghĩa trong vùng màn hình đã chọn.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("QLabel { color: #333333; margin-bottom: 8px; }")
        layout.addWidget(desc_label)
        
        # Image specifications group
        img_group = QGroupBox("Thông số ảnh:")
        img_group.setStyleSheet("""
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
        img_layout = QHBoxLayout()
        img_layout.setSpacing(15)
        
        # Left side: Image preview
        preview_container = QVBoxLayout()
        preview_container.setSpacing(8)
        # Xóa label "Image:" và đưa preview lên sát trên
        self.image_preview = ImagePreviewLabel()
        preview_container.addWidget(self.image_preview)
        preview_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Buttons below preview
        btn_container = QHBoxLayout()
        btn_container.setSpacing(8)
        self.btn_load = QPushButton("Nhập Ảnh")
        self.btn_load.setMinimumHeight(28)
        self.btn_load.clicked.connect(self.load_from_file)
        self.btn_capture = QPushButton("Cắt Ảnh")
        self.btn_capture.setMinimumHeight(28)
        self.btn_capture.clicked.connect(self.capture_from_screen)
        
        btn_container.addWidget(self.btn_load)
        btn_container.addWidget(self.btn_capture)
        preview_container.addLayout(btn_container)
        
        img_layout.addLayout(preview_container)
        
        # Right side: Options
        options_container = QVBoxLayout()
        options_container.setSpacing(12)
        
        # Search area (bỏ checkbox, mặc định toàn màn hình)
        # Use Grid Layout for better alignment
        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Row 0: Search Area
        search_area_label = QLabel("Vùng Tìm Kiếm:")
        search_area_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(search_area_label, 0, 0)
        
        self.combo_window = StyledComboBox()
        self.combo_window.addItems(["toàn màn hình", "cửa sổ đang focus", "vùng tùy chỉnh"])
        self.combo_window.setCurrentText("toàn màn hình")
        # Calc width logic...
        fm = self.combo_window.fontMetrics()
        max_text = "cửa sổ đang focus"
        text_width = fm.boundingRect(max_text).width()
        self.combo_window.setMinimumWidth(max(140, text_width + 30))
        self.combo_window.currentTextChanged.connect(self.on_search_area_changed)
        grid_layout.addWidget(self.combo_window, 0, 1)
        
        self.btn_define = QPushButton("Define")
        self.btn_define.setMinimumHeight(28)
        self.btn_define.setMinimumWidth(60)
        self.btn_define.clicked.connect(self.define_search_area)
        self.btn_define.setVisible(False)
        grid_layout.addWidget(self.btn_define, 0, 2)
        
        # Row 1: Tolerance
        tolerance_label = QLabel("Độ dung sai màu:")
        tolerance_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addWidget(tolerance_label, 1, 0)
        
        self.spin_tolerance = QSpinBox()
        self.spin_tolerance.setRange(0, 255)
        self.spin_tolerance.setSuffix(" / 255")
        self.spin_tolerance.setMinimumWidth(100)
        grid_layout.addWidget(self.spin_tolerance, 1, 1)
        
        self.btn_test = QPushButton("Test Ảnh")
        self.btn_test.setMinimumHeight(28)
        self.btn_test.clicked.connect(self.test_image_search)
        grid_layout.addWidget(self.btn_test, 1, 2)
        
        # Push everything to the left
        grid_layout.setColumnStretch(3, 1)
        
        options_container.addLayout(grid_layout)
        
        # Advanced Options
        adv_layout = QHBoxLayout()
        adv_layout.setSpacing(15)
        self.cb_grayscale = StyledCheckBox("Grayscale (Đen trắng)")
        self.cb_multiscale = StyledCheckBox("Multi-scale (Đa tỉ lệ)")
        adv_layout.addWidget(self.cb_grayscale)
        adv_layout.addWidget(self.cb_multiscale)
        adv_layout.addStretch()
        options_container.addLayout(adv_layout)
        
        # Test Result Label
        self.lbl_test_result = QLabel("")
        self.lbl_test_result.setStyleSheet("font-weight: bold; margin-left: 60px;")
        options_container.addWidget(self.lbl_test_result)
        
        options_container.addStretch()
        img_layout.addLayout(options_container, 1)
        
        img_group.setLayout(img_layout)
        layout.addWidget(img_group)
        
        # If image is found section
        found_group = QGroupBox("Nếu tìm thấy ảnh:")
        found_group.setStyleSheet("""
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
        found_layout = QVBoxLayout()
        found_layout.setSpacing(10)
        
        # Mouse action
        mouse_action_layout = QHBoxLayout()
        mouse_action_layout.setSpacing(8)
        self.cb_mouse_action = StyledCheckBox("Hành động chuột:")
        self.combo_mouse_action = StyledComboBox()
        self.combo_mouse_action.addItems(["Di chuyển", "Nhấp", "Nhấp đôi", "Nhấp phải"])
        self.combo_mouse_action.setEnabled(False)
        self.combo_mouse_action.setMinimumWidth(120)
        self.cb_mouse_action.toggled.connect(self.combo_mouse_action.setEnabled)
        
        self.combo_position = StyledComboBox()
        self.combo_position.addItems(["Giữa", "Trên-Trái", "Trên-Phải", "Dưới-Trái", "Dưới-Phải"])
        self.combo_position.setEnabled(False)
        self.combo_position.setMinimumWidth(120)
        self.cb_mouse_action.toggled.connect(self.combo_position.setEnabled)
        
        mouse_action_layout.addWidget(self.cb_mouse_action)
        mouse_action_layout.addWidget(self.combo_mouse_action)
        mouse_action_layout.addWidget(self.combo_position)
        mouse_action_layout.addStretch()
        found_layout.addLayout(mouse_action_layout)
        
        # Save X to
        save_x_layout = QHBoxLayout()
        save_x_layout.setSpacing(8)
        self.cb_save_x = StyledCheckBox("Lưu X vào:")
        self.combo_save_x = StyledComboBox()
        self.combo_save_x.addItems(["Biến1", "Biến2", "Biến3"])
        self.combo_save_x.setEnabled(False)
        self.combo_save_x.setMinimumWidth(100)
        self.cb_save_x.toggled.connect(self.combo_save_x.setEnabled)
        
        self.combo_save_y = StyledComboBox()
        self.combo_save_y.addItems(["Biến1", "Biến2", "Biến3"])
        self.combo_save_y.setEnabled(False)
        self.combo_save_y.setMinimumWidth(100)
        self.cb_save_x.toggled.connect(self.combo_save_y.setEnabled)
        
        save_x_layout.addWidget(self.cb_save_x)
        save_x_layout.addWidget(self.combo_save_x)
        save_x_layout.addWidget(QLabel("và Y vào:"))
        save_x_layout.addWidget(self.combo_save_y)
        save_x_layout.addStretch()
        found_layout.addLayout(save_x_layout)
        
        # Go to
        goto_layout = QHBoxLayout()
        goto_layout.setSpacing(8)
        goto_label = QLabel("Chuyển đến")
        goto_label.setMinimumWidth(120)
        self.combo_goto_found = StyledComboBox()
        self.combo_goto_found.addItems(["Tiếp theo", "Bắt đầu", "Kết thúc"])
        self.combo_goto_found.setMinimumWidth(120)
        goto_layout.addWidget(goto_label)
        goto_layout.addWidget(self.combo_goto_found)
        goto_layout.addStretch()
        found_layout.addLayout(goto_layout)
        
        found_group.setLayout(found_layout)
        layout.addWidget(found_group)
        
        # If image is not found section
        not_found_group = QGroupBox("Nếu không tìm thấy ảnh")
        not_found_group.setStyleSheet("""
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
        not_found_layout = QVBoxLayout()
        not_found_layout.setSpacing(10)
        
        # Continue waiting
        wait_layout = QHBoxLayout()
        wait_layout.setSpacing(8)
        wait_label = QLabel("Tiếp tục chờ")
        wait_label.setMinimumWidth(120)
        self.spin_wait_time = QSpinBox()
        self.spin_wait_time.setRange(0, 999999)
        self.spin_wait_time.setValue(65535)
        self.spin_wait_time.setMaximumWidth(100)
        wait_layout.addWidget(wait_label)
        wait_layout.addWidget(self.spin_wait_time)
        wait_layout.addWidget(QLabel("giây và sau đó"))
        wait_layout.addStretch()
        not_found_layout.addLayout(wait_layout)
        
        # Go to
        goto_not_found_layout = QHBoxLayout()
        goto_not_found_layout.setSpacing(8)
        goto_not_found_label = QLabel("Chuyển đến")
        goto_not_found_label.setMinimumWidth(120)
        self.combo_goto_not_found = StyledComboBox()
        self.combo_goto_not_found.addItems(["Bắt đầu", "Kết thúc", "Tiếp theo"])
        self.combo_goto_not_found.setMinimumWidth(120)
        goto_not_found_layout.addWidget(goto_not_found_label)
        goto_not_found_layout.addWidget(self.combo_goto_not_found)
        goto_not_found_layout.addStretch()
        not_found_layout.addLayout(goto_not_found_layout)
        
        not_found_group.setLayout(not_found_layout)
        layout.addWidget(not_found_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setDefault(True)
        self.btn_ok.setMinimumWidth(80)
        self.btn_ok.setMinimumHeight(28)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Hủy")
        self.btn_cancel.setMinimumWidth(80)
        self.btn_cancel.setMinimumHeight(28)
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        layout.addLayout(button_layout)

    def load_event_data(self):
        if not self.event: return
        if self.image_path and os.path.exists(self.image_path):
            self.image_preview.set_image(QPixmap(self.image_path))
        if self.image_path and os.path.exists(self.image_path):
            self.image_preview.set_image(QPixmap(self.image_path))
        self.spin_tolerance.setValue(self.event.get('tolerance', 0))
        self.cb_grayscale.setChecked(self.event.get('grayscale', False))
        self.cb_multiscale.setChecked(self.event.get('multi_scale', False))
        
        # Map old English values to Vietnamese
        search_area_map = {
            'focused window': 'cửa sổ đang focus',
            'entire screen': 'toàn màn hình',
            'custom region': 'vùng tùy chỉnh'
        }
        search_area = self.event.get('search_area', 'entire screen')  # Mặc định toàn màn hình
        self.combo_window.setCurrentText(search_area_map.get(search_area, search_area))
        self.on_search_area_changed(self.combo_window.currentText())  # Update button visibility
        
        self.cb_mouse_action.setChecked(self.event.get('mouse_action_enabled', False))
        mouse_action_map = {
            'Move': 'Di chuyển',
            'Click': 'Nhấp',
            'Double Click': 'Nhấp đôi',
            'Right Click': 'Nhấp phải'
        }
        mouse_action = self.event.get('mouse_action', 'Move')
        self.combo_mouse_action.setCurrentText(mouse_action_map.get(mouse_action, mouse_action))
        
        position_map = {
            'Centered': 'Giữa',
            'Top-Left': 'Trên-Trái',
            'Top-Right': 'Trên-Phải',
            'Bottom-Left': 'Dưới-Trái',
            'Bottom-Right': 'Dưới-Phải'
        }
        position = self.event.get('mouse_position', 'Centered')
        self.combo_position.setCurrentText(position_map.get(position, position))
        
        self.spin_wait_time.setValue(self.event.get('wait_timeout', 65535))
        
        goto_map = {
            'Next': 'Tiếp theo',
            'Start': 'Bắt đầu',
            'End': 'Kết thúc',
            'Step 1': 'Bước 1',
            'Step 2': 'Bước 2'
        }
        goto_found = self.event.get('goto_found', 'Next')
        self.combo_goto_found.setCurrentText(goto_map.get(goto_found, goto_found))
        
        goto_not_found = self.event.get('goto_not_found', 'Start')
        self.combo_goto_not_found.setCurrentText(goto_map.get(goto_not_found, goto_not_found))
        
        if self.event.get('save_x', False):
            self.cb_save_x.setChecked(True)

    def capture_from_screen(self):
        """Shows Snipper on top of dialog -> Restores Dialog"""
        try:
            print("🔍 DEBUG: Starting capture_from_screen")
            self.is_snipping = True
            
            # CRITICAL: Block signals to prevent any accidental accept/reject
            self.blockSignals(True)
            
            # 1. Set dialog to non-modal FIRST (critical to prevent blocking)
            self.setWindowModality(Qt.WindowModality.NonModal)
            
            # 2. Disable all buttons to prevent clicks during snipping
            self.btn_ok.setEnabled(False)
            self.btn_cancel.setEnabled(False)
            self.btn_load.setEnabled(False)
            self.btn_capture.setEnabled(False)
            
            # 3. Lower dialog to background (don't hide it - that causes exec() to return!)
            self.lower()
            QApplication.processEvents()
            
            # 4. Minimize the main window if it exists
            if self.parent():
                self.parent().showMinimized()
                
            # 5. Allow UI to update
            QApplication.processEvents()
            import time
            time.sleep(0.3) # Small buffer for OS animations
            
            print("🔍 DEBUG: Creating SnippingWidget")
            # 6. Initialize Snipper
            from utils.snipping_tool import SnippingWidget
            self.snipper = SnippingWidget()
            
            # 7. Connect signals using a closure or helper to restore windows
            self.snipper.snippet_taken.connect(self.on_snipper_success)
            self.snipper.closed.connect(self.restore_ui)
            
            print("🔍 DEBUG: SnippingWidget already shown in capture_screen_state")
            # SnippingWidget is already shown in capture_screen_state()
            # Just ensure it's on top
            self.snipper.raise_()
            self.snipper.activateWindow()
            QApplication.processEvents()
            
            # Force focus to snipper multiple times
            QTimer.singleShot(50, lambda: (
                self.snipper.raise_(),
                self.snipper.activateWindow(),
                self.snipper.setFocus(),
                QApplication.processEvents()
            ))
            QTimer.singleShot(150, lambda: (
                self.snipper.raise_(),
                self.snipper.activateWindow(),
                QApplication.processEvents()
            ))
            
            print("🔍 DEBUG: SnippingWidget should be visible now")
            
        except Exception as e:
            print(f"🔍 DEBUG: Error launching snipper: {e}")
            import traceback
            traceback.print_exc()
            self.is_snipping = False
            self.blockSignals(False)
            self.restore_ui()

    def restore_ui(self):
        """Restores the main UI state"""
        print("🔍 DEBUG: Restoring UI")
        self.is_snipping = False
        
        # Re-enable signals
        self.blockSignals(False)
        
        # Re-enable buttons
        self.btn_ok.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        self.btn_load.setEnabled(True)
        self.btn_capture.setEnabled(True)
        
        # Restore main window first
        if self.parent():
            self.parent().showNormal()
            self.parent().activateWindow()
        
        # Restore dialog and set back to modal
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.raise_()  # Bring dialog back to front
        self.activateWindow()
        QApplication.processEvents()

    def on_snipper_success(self, path):
        """Handle success"""
        self.image_path = path
        self.image_preview.set_image(QPixmap(path))
        self.restore_ui()

    def on_search_area_changed(self, text):
        """Show/hide Define button based on selected search area"""
        # Hiển thị button Define khi chọn "cửa sổ đang focus" hoặc "vùng tùy chỉnh"
        self.btn_define.setVisible(text in ["cửa sổ đang focus", "vùng tùy chỉnh"])
    
    def define_search_area(self):
        """Define custom search area using Snipping Tool"""
        try:
            print("🔍 DEBUG: Starting define_search_area")
            self.is_snipping = True
            self.blockSignals(True)
            self.setWindowModality(Qt.WindowModality.NonModal)
            self.lower()
            QApplication.processEvents()
            
            if self.parent():
                self.parent().showMinimized()
            
            QApplication.processEvents()
            import time
            time.sleep(0.3)
            
            from utils.snipping_tool import SnippingWidget
            self.snipper = SnippingWidget()
            
            # Connect signals
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
        
        # Update button text to show defined status
        self.btn_define.setText(f"Defined ({rect.width()}x{rect.height()})")
        self.btn_define.setStyleSheet("color: green; font-weight: bold;")
        
        self.restore_ui()
    
    def load_from_file(self):
        dialog = QFileDialog(self, "Chọn ảnh")
        dialog.setNameFilter("Ảnh (*.png *.jpg *.bmp)")
        if dialog.exec():
            f = dialog.selectedFiles()[0]
            self.image_path = f
            self.image_path = f
            self.image_preview.set_image(QPixmap(f))

    def test_image_search(self):
        """Test if image can be found on screen now"""
        if not self.image_path or not os.path.exists(self.image_path):
            self.lbl_test_result.setText("❌ Chưa chọn ảnh hoặc ảnh không tồn tại!")
            self.lbl_test_result.setStyleSheet("color: red; font-weight: bold; margin-left: 60px;")
            return
            
        # Calculate confidence same as Player
        # Adjusted: 0 tolerance now maps to ~0.9975 to allow tiny rendering differences
        tolerance = self.spin_tolerance.value()
        confidence = 1.0 - ((tolerance + 1) / 400.0)
        if confidence < 0.1: confidence = 0.1
        
        self.lbl_test_result.setText("⏳ Đang tìm kiếm...")
        self.lbl_test_result.setStyleSheet("color: blue; font-weight: bold; margin-left: 60px;")
        QApplication.processEvents()
        
        # Determine Search Region for Test
        region = None
        search_area_text = self.combo_window.currentText()
        
        if search_area_text == "cửa sổ đang focus":
            from utils.window_utils import get_foreground_window_rect
            region = get_foreground_window_rect()
            if region:
                print(f"🔍 DEBUG: Testing in focused window: {region}")
            else:
                self.lbl_test_result.setText("⚠️ Không tìm thấy cửa sổ focus!")
                self.lbl_test_result.setStyleSheet("color: orange; font-weight: bold; margin-left: 60px;")
                return
        elif search_area_text == "vùng tùy chỉnh":
            if self.custom_region:
                region = self.custom_region
                print(f"🔍 DEBUG: Testing in custom region: {region}")
            else:
                self.lbl_test_result.setText("⚠️ Chưa định nghĩa vùng tìm kiếm!")
                self.lbl_test_result.setStyleSheet("color: orange; font-weight: bold; margin-left: 60px;")
                return

        # Perform search
        result = find_image_on_screen(
            self.image_path, 
            confidence=confidence,
            region=region,
            grayscale=self.cb_grayscale.isChecked(),
            multi_scale=self.cb_multiscale.isChecked()
        )
        
        if result:
            x, y, w, h = result
            self.lbl_test_result.setText(f"✅ Đã tìm thấy ảnh tại vị trí: {x}, {y}")
            self.lbl_test_result.setStyleSheet("color: green; font-weight: bold; margin-left: 60px;")
        else:
            self.lbl_test_result.setText("❌ Không tìm thấy ảnh trên màn hình!")
            self.lbl_test_result.setStyleSheet("color: red; font-weight: bold; margin-left: 60px;")

    def closeEvent(self, event):
        """Override to prevent closing during snipping"""
        if self.is_snipping:
            print("🔍 DEBUG: closeEvent blocked - currently snipping")
            event.ignore()
            return
        super().closeEvent(event)
    
    def reject(self):
        """Override to prevent reject during snipping"""
        if self.is_snipping:
            print("🔍 DEBUG: reject() blocked - currently snipping")
            return
        super().reject()
    
    def accept(self):
        """Override to prevent accept during snipping"""
        if self.is_snipping:
            print("🔍 DEBUG: accept() blocked - currently snipping")
            return
        super().accept()
    
    def get_data(self):
        # Map Vietnamese values back to English for compatibility
        search_area_map = {
            'cửa sổ đang focus': 'focused window',
            'toàn màn hình': 'entire screen',
            'vùng tùy chỉnh': 'custom region'
        }
        mouse_action_map = {
            'Di chuyển': 'Move',
            'Nhấp': 'Click',
            'Nhấp đôi': 'Double Click',
            'Nhấp phải': 'Right Click'
        }
        position_map = {
            'Giữa': 'Centered',
            'Trên-Trái': 'Top-Left',
            'Trên-Phải': 'Top-Right',
            'Dưới-Trái': 'Bottom-Left',
            'Dưới-Phải': 'Bottom-Right'
        }
        goto_map = {
            'Tiếp theo': 'Next',
            'Bắt đầu': 'Start',
            'Kết thúc': 'End',
            'Bước 1': 'Step 1',
            'Bước 2': 'Step 2'
        }
        
        return {
            'type': 'detect_image',
            'image_path': self.image_path,
            'restrict_area': True,  # Luôn True vì đã bỏ checkbox
            'search_area': search_area_map.get(self.combo_window.currentText(), self.combo_window.currentText()),
            'custom_region': self.custom_region,
            'tolerance': self.spin_tolerance.value(),
            'grayscale': self.cb_grayscale.isChecked(),
            'multi_scale': self.cb_multiscale.isChecked(),
            'mouse_action_enabled': self.cb_mouse_action.isChecked(),
            'mouse_action': mouse_action_map.get(self.combo_mouse_action.currentText(), self.combo_mouse_action.currentText()),
            'mouse_position': position_map.get(self.combo_position.currentText(), self.combo_position.currentText()),
            'save_x': self.cb_save_x.isChecked(),
            'save_y': self.cb_save_x.isChecked(),
            'wait_timeout': self.spin_wait_time.value(),
            'goto_found': goto_map.get(self.combo_goto_found.currentText(), self.combo_goto_found.currentText()),
            'goto_not_found': goto_map.get(self.combo_goto_not_found.currentText(), self.combo_goto_not_found.currentText()),
            'time': self.event.get('time', 0.5)
        }
