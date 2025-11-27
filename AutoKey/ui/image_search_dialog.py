"""
Image Search Dialog - for configuring image detection actions
Fixed version with working capture functionality
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QCheckBox, QComboBox, QSpinBox,
                            QGroupBox, QFormLayout, QFileDialog, QWidget)
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QPixmap, QPainter, QColor
import os


class ImagePreviewLabel(QLabel):
    """Custom label to display image with icon overlay if no image"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(160, 160)
        self.setMaximumSize(160, 160)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                background: white;
            }
        """)
        self.pixmap_data = None
        self.show_placeholder()
        
    def show_placeholder(self):
        """Show placeholder icon"""
        placeholder = QPixmap(160, 160)
        placeholder.fill(Qt.GlobalColor.white)
        painter = QPainter(placeholder)
        painter.setPen(QColor(180, 180, 180))
        # Draw a simple image icon representation
        painter.drawRect(40, 40, 80, 80)
        painter.drawLine(50, 90, 70, 70)
        painter.drawLine(70, 70, 90, 100)
        painter.drawLine(90, 100, 110, 60)
        painter.end()
        self.setPixmap(placeholder)
        
    def set_image(self, pixmap):
        """Set image, scaled to fit"""
        if pixmap and not pixmap.isNull():
            self.pixmap_data = pixmap
            scaled = pixmap.scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatio, 
                                 Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(scaled)
        else:
            self.show_placeholder()


class ImageSearchDialog(QDialog):
    """Dialog for configuring image detection/search action"""
    
    def __init__(self, parent=None, event=None):
        super().__init__(parent)
        self.setWindowTitle("Search image")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(520, 480)
        
        self.event = event if event else {}
        self.captured_pixmap = None
        self.image_path = self.event.get('image_path', '')
        
        self.setup_ui()
        self.load_event_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Description label
        desc_label = QLabel("Finds position of the defined image in the selected screen area.")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Image specifications group
        img_group = QGroupBox("Image specifications:")
        img_layout = QHBoxLayout()
        
        # Left: Image preview
        preview_container = QVBoxLayout()
        preview_label = QLabel("Image:")
        preview_container.addWidget(preview_label)
        
        self.image_preview = ImagePreviewLabel()
        preview_container.addWidget(self.image_preview)
        
        # Buttons under image
        btn_container = QHBoxLayout()
        
        self.btn_load = QPushButton("Nhập Ảnh")
        self.btn_load.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon))
        self.btn_load.setToolTip("Load from file")
        self.btn_load.clicked.connect(self.load_from_file)
        
        self.btn_capture = QPushButton("Cắt Ảnh")
        self.btn_capture.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogYesButton))
        self.btn_capture.setToolTip("Capture from screen")
        self.btn_capture.clicked.connect(self.capture_from_screen)
        
        btn_container.addWidget(self.btn_load)
        btn_container.addWidget(self.btn_capture)
        btn_container.addStretch()
        preview_container.addLayout(btn_container)
        
        img_layout.addLayout(preview_container)
        
        # Right: Options
        options_layout = QFormLayout()
        
        # Restrict search area
        self.cb_restrict = QCheckBox("Restrict search area to")
        self.combo_window = QComboBox()
        self.combo_window.addItems(["focused window", "entire screen", "custom region"])
        self.combo_window.setEnabled(False)
        self.cb_restrict.toggled.connect(self.combo_window.setEnabled)
        
        options_layout.addRow(self.cb_restrict, self.combo_window)
        
        # Color tolerance
        tolerance_layout = QHBoxLayout()
        tolerance_label = QLabel("Color tolerance:")
        self.spin_tolerance = QSpinBox()
        self.spin_tolerance.setRange(0, 255)
        self.spin_tolerance.setValue(0)
        self.spin_tolerance.setMaximumWidth(60)
        tolerance_layout.addWidget(tolerance_label)
        tolerance_layout.addWidget(self.spin_tolerance)
        tolerance_layout.addStretch()
        
        options_layout.addRow(tolerance_layout)
        
        img_layout.addLayout(options_layout, 1)
        img_group.setLayout(img_layout)
        layout.addWidget(img_group)
        
        # If image is found section
        found_group = QGroupBox("If image is found:")
        found_layout = QFormLayout()
        
        # Mouse action
        self.cb_mouse_action = QCheckBox("Mouse action:")
        self.combo_mouse_action = QComboBox()
        self.combo_mouse_action.addItems(["Move", "Click", "Double Click", "Right Click"])
        self.combo_mouse_action.setEnabled(False)
        self.cb_mouse_action.toggled.connect(self.combo_mouse_action.setEnabled)
        
        mouse_layout = QHBoxLayout()
        mouse_layout.addWidget(self.combo_mouse_action)
        
        self.combo_position = QComboBox()
        self.combo_position.addItems(["Centered", "Top-Left", "Top-Right", "Bottom-Left", "Bottom-Right"])
        self.combo_position.setEnabled(False)
        self.cb_mouse_action.toggled.connect(self.combo_position.setEnabled)
        mouse_layout.addWidget(self.combo_position)
        
        found_layout.addRow(self.cb_mouse_action, mouse_layout)
        
        # Save X to
        self.cb_save_x = QCheckBox("Save X to:")
        self.combo_save_x = QComboBox()
        self.combo_save_x.addItems(["Variable1", "Variable2", "Variable3"])
        self.combo_save_x.setEnabled(False)
        self.cb_save_x.toggled.connect(self.combo_save_x.setEnabled)
        
        save_x_layout = QHBoxLayout()
        save_x_layout.addWidget(self.combo_save_x)
        save_x_layout.addWidget(QLabel("and Y to:"))
        
        self.combo_save_y = QComboBox()
        self.combo_save_y.addItems(["Variable1", "Variable2", "Variable3"])
        self.combo_save_y.setEnabled(False)
        self.cb_save_x.toggled.connect(self.combo_save_y.setEnabled)
        save_x_layout.addWidget(self.combo_save_y)
        
        found_layout.addRow(self.cb_save_x, save_x_layout)
        
        # Go to
        goto_layout = QHBoxLayout()
        goto_label = QLabel("Go to")
        self.combo_goto_found = QComboBox()
        self.combo_goto_found.addItems(["Start", "End", "Step 1", "Step 2"])
        goto_layout.addWidget(goto_label)
        goto_layout.addWidget(self.combo_goto_found)
        goto_layout.addStretch()
        
        found_layout.addRow(goto_layout)
        
        found_group.setLayout(found_layout)
        layout.addWidget(found_group)
        
        # If image is not found section
        not_found_group = QGroupBox("If image is not found")
        not_found_layout = QFormLayout()
        
        # Continue waiting
        wait_layout = QHBoxLayout()
        wait_label = QLabel("Continue waiting")
        self.spin_wait_time = QSpinBox()
        self.spin_wait_time.setRange(0, 999999)
        self.spin_wait_time.setValue(65535)
        self.spin_wait_time.setMaximumWidth(80)
        wait_layout.addWidget(wait_label)
        wait_layout.addWidget(self.spin_wait_time)
        wait_layout.addWidget(QLabel("seconds and then"))
        wait_layout.addStretch()
        
        not_found_layout.addRow(wait_layout)
        
        # Go to
        goto_not_found_layout = QHBoxLayout()
        goto_not_found_label = QLabel("Go to")
        self.combo_goto_not_found = QComboBox()
        self.combo_goto_not_found.addItems(["End", "Start", "Step 1", "Step 2"])
        goto_not_found_layout.addWidget(goto_not_found_label)
        goto_not_found_layout.addWidget(self.combo_goto_not_found)
        goto_not_found_layout.addStretch()
        
        not_found_layout.addRow(goto_not_found_layout)
        
        not_found_group.setLayout(not_found_layout)
        layout.addWidget(not_found_group)
        
        layout.addStretch()
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setDefault(True)
        self.btn_ok.clicked.connect(self.accept)
        button_layout.addWidget(self.btn_ok)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        self.btn_help = QPushButton("Help")
        button_layout.addWidget(self.btn_help)
        
        layout.addLayout(button_layout)
        
    def load_event_data(self):
        """Load existing event data into UI"""
        if not self.event:
            return
            
        # Load image if path exists
        if self.image_path and os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            self.image_preview.set_image(pixmap)
            
        # Load other settings
        self.cb_restrict.setChecked(self.event.get('restrict_area', False))
        self.combo_window.setCurrentText(self.event.get('search_area', 'focused window'))
        self.spin_tolerance.setValue(self.event.get('tolerance', 0))
        
        self.cb_mouse_action.setChecked(self.event.get('mouse_action_enabled', False))
        self.combo_mouse_action.setCurrentText(self.event.get('mouse_action', 'Move'))
        self.combo_position.setCurrentText(self.event.get('mouse_position', 'Centered'))
        
        self.spin_wait_time.setValue(self.event.get('wait_timeout', 65535))
        
    def capture_from_screen(self):
        """Capture image from screen using snipping tool"""
        # ✅ FIX: Import đúng và gọi hàm đúng
        try:
            from utils.snipping_tool import capture_screen_region
            
            # Ẩn dialog tạm thời
            self.hide()
            
            # Gọi capture_screen_region() và đợi kết quả
            pixmap, rect = capture_screen_region()
            
            if pixmap and not pixmap.isNull():
                self.captured_pixmap = pixmap
                self.image_preview.set_image(pixmap)
                
                # Lưu ảnh vào thư mục
                images_dir = os.path.join(os.getcwd(), "captured_images")
                os.makedirs(images_dir, exist_ok=True)
                
                import time
                filename = f"capture_{int(time.time())}.png"
                self.image_path = os.path.join(images_dir, filename)
                pixmap.save(self.image_path, "PNG")
                
                print(f"✅ Ảnh cắt lưu tại: {self.image_path}")
            else:
                print("❌ Không cắt được ảnh")
            
            # Hiện dialog lại
            self.show()
            self.activateWindow()
            
        except ImportError as e:
            print(f"❌ Lỗi import: {e}")
            self.show()
            self.activateWindow()
        except Exception as e:
            print(f"❌ Lỗi khi cắt ảnh: {e}")
            self.show()
            self.activateWindow()
        
    def load_from_file(self):
        """Load image from file"""
        try:
            dialog = QFileDialog(self, "Select Image")
            dialog.setNameFilter("Image Files (*.png *.jpg *.bmp)")
            dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            
            if dialog.exec():
                filenames = dialog.selectedFiles()
                if filenames:
                    filename = filenames[0]
                    pixmap = QPixmap(filename)
                    if not pixmap.isNull():
                        self.image_path = filename
                        self.image_preview.set_image(pixmap)
                        print(f"✅ Ảnh tải: {filename}")
                    else:
                        print(f"❌ Không thể tải: {filename}")
        except Exception as e:
            print(f"❌ Lỗi: {e}")
                
    def get_data(self):
        """Return dialog data as dict"""
        return {
            'type': 'detect_image',
            'image_path': self.image_path,
            'restrict_area': self.cb_restrict.isChecked(),
            'search_area': self.combo_window.currentText(),
            'tolerance': self.spin_tolerance.value(),
            'mouse_action_enabled': self.cb_mouse_action.isChecked(),
            'mouse_action': self.combo_mouse_action.currentText(),
            'mouse_position': self.combo_position.currentText(),
            'save_x': self.cb_save_x.isChecked(),
            'save_y': self.cb_save_x.isChecked(),
            'wait_timeout': self.spin_wait_time.value(),
            'goto_found': self.combo_goto_found.currentText(),
            'goto_not_found': self.combo_goto_not_found.currentText(),
            'time': self.event.get('time', 0.5)
        }
