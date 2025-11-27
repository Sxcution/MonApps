"""
Image Search Dialog - for configuring image detection actions
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QCheckBox, QComboBox, QSpinBox,
                            QGroupBox, QFormLayout, QFileDialog, QWidget, QApplication)
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QPixmap, QPainter, QColor
import os
import time

class ImagePreviewLabel(QLabel):
    """Custom label to display image with icon overlay if no image"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(160, 160)
        self.setMaximumSize(160, 160)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("QLabel { border: 1px solid #ccc; background: white; }")
        self.pixmap_data = None
        self.show_placeholder()
        
    def show_placeholder(self):
        placeholder = QPixmap(160, 160)
        placeholder.fill(Qt.GlobalColor.white)
        painter = QPainter(placeholder)
        painter.setPen(QColor(180, 180, 180))
        painter.drawRect(40, 40, 80, 80)
        painter.drawLine(50, 90, 70, 70)
        painter.drawLine(70, 70, 90, 100)
        painter.drawLine(90, 100, 110, 60)
        painter.end()
        self.setPixmap(placeholder)
        
    def set_image(self, pixmap):
        if pixmap and not pixmap.isNull():
            self.pixmap_data = pixmap
            scaled = pixmap.scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatio, 
                                 Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(scaled)
        else:
            self.show_placeholder()

class ImageSearchDialog(QDialog):
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
        
        desc_label = QLabel("Finds position of the defined image in the selected screen area.")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        img_group = QGroupBox("Image specifications:")
        img_layout = QHBoxLayout()
        preview_container = QVBoxLayout()
        preview_container.addWidget(QLabel("Image:"))
        self.image_preview = ImagePreviewLabel()
        preview_container.addWidget(self.image_preview)
        
        btn_container = QHBoxLayout()
        self.btn_load = QPushButton("Nhập Ảnh")
        self.btn_load.clicked.connect(self.load_from_file)
        self.btn_capture = QPushButton("Cắt Ảnh")
        self.btn_capture.clicked.connect(self.capture_from_screen)
        
        btn_container.addWidget(self.btn_load)
        btn_container.addWidget(self.btn_capture)
        btn_container.addStretch()
        preview_container.addLayout(btn_container)
        img_layout.addLayout(preview_container)
        
        options_layout = QFormLayout()
        self.cb_restrict = QCheckBox("Restrict search area to")
        self.combo_window = QComboBox()
        self.combo_window.addItems(["focused window", "entire screen", "custom region"])
        self.combo_window.setEnabled(False)
        self.cb_restrict.toggled.connect(self.combo_window.setEnabled)
        options_layout.addRow(self.cb_restrict, self.combo_window)
        
        tolerance_layout = QHBoxLayout()
        self.spin_tolerance = QSpinBox()
        self.spin_tolerance.setRange(0, 255)
        options_layout.addRow(QLabel("Color tolerance:"), self.spin_tolerance)
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
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setDefault(True)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        layout.addLayout(button_layout)

    def load_event_data(self):
        if not self.event: return
        if self.image_path and os.path.exists(self.image_path):
            self.image_preview.set_image(QPixmap(self.image_path))
        self.cb_restrict.setChecked(self.event.get('restrict_area', False))
        self.spin_tolerance.setValue(self.event.get('tolerance', 0))
        self.combo_window.setCurrentText(self.event.get('search_area', 'focused window'))
        self.cb_mouse_action.setChecked(self.event.get('mouse_action_enabled', False))
        self.combo_mouse_action.setCurrentText(self.event.get('mouse_action', 'Move'))
        self.combo_position.setCurrentText(self.event.get('mouse_position', 'Centered'))
        self.spin_wait_time.setValue(self.event.get('wait_timeout', 65535))
        self.combo_goto_found.setCurrentText(self.event.get('goto_found', 'Start'))
        self.combo_goto_not_found.setCurrentText(self.event.get('goto_not_found', 'End'))

    def capture_from_screen(self):
        """Hides dialog -> Shows Snipper -> Restores Dialog"""
        try:
            # 1. Hide the modal dialog explicitly
            self.hide()
            
            # 2. Minimize the main window if it exists
            if self.parent():
                self.parent().showMinimized()
                
            # 3. Allow UI to update (essential for hide to take effect)
            QApplication.processEvents()
            import time
            time.sleep(0.2) # Small buffer for OS animations
            
            # 4. Initialize Snipper
            from utils.snipping_tool import SnippingWidget
            self.snipper = SnippingWidget()
            
            # 5. Connect signals using a closure or helper to restore windows
            self.snipper.snippet_taken.connect(self.on_snipper_success)
            self.snipper.closed.connect(self.restore_ui)
            
            # 6. Show the snipper (It is now ApplicationModal, so it takes over)
            self.snipper.show()
            
        except Exception as e:
            print(f"Error launching snipper: {e}")
            self.restore_ui()

    def restore_ui(self):
        """Restores the main UI state"""
        if self.parent():
            self.parent().showNormal()
            self.parent().activateWindow()
        
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def on_snipper_success(self, path):
        """Handle success"""
        self.image_path = path
        self.image_preview.set_image(QPixmap(path))
        self.restore_ui()

    def load_from_file(self):
        dialog = QFileDialog(self, "Select Image")
        dialog.setNameFilter("Images (*.png *.jpg *.bmp)")
        if dialog.exec():
            f = dialog.selectedFiles()[0]
            self.image_path = f
            self.image_preview.set_image(QPixmap(f))

    def get_data(self):
        # Trả về data như cũ
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
