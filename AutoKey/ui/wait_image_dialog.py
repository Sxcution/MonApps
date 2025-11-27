from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox, 
                             QDialogButtonBox, QFileDialog, QWidget, QApplication, QFormLayout)
from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap
from utils.snipping_tool import SnippingWidget
import mss
import mss.tools
import os
import datetime
import time  # For busy-wait loop

class RegionSelectionOverlay(QWidget):
    region_selected = pyqtSignal(tuple) # (x1, y1, x2, y2)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        
        self.start_pos = None
        self.current_pos = None
        self.is_selecting = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dim the screen
        painter.setBrush(QColor(0, 0, 0, 100))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        
        if self.start_pos and self.current_pos:
            rect = QRect(self.start_pos, self.current_pos).normalized()
            
            # Clear the selection area (make it transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.setBrush(Qt.BrushStyle.SolidPattern)
            painter.drawRect(rect)
            
            # Draw border
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.pos()
            self.current_pos = event.pos()
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.current_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False
            rect = QRect(self.start_pos, self.current_pos).normalized()
            self.region_selected.emit((rect.left(), rect.top(), rect.right(), rect.bottom()))
            self.close()
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

class WaitImageDialog(QDialog):
    def __init__(self, parent=None, event_data=None):
        super().__init__(parent)
        self.setWindowTitle("Đợi hình ảnh")
        self.setFixedSize(500, 350)
        
        self.event_data = event_data or {}
        
        layout = QVBoxLayout(self)
        
        # Image Path
        img_layout = QHBoxLayout()
        img_layout.addWidget(QLabel("Đường dẫn ảnh:"))
        self.img_path_edit = QLineEdit()
        self.img_path_edit.setText(self.event_data.get('path', ''))
        img_layout.addWidget(self.img_path_edit)
        self.img_path_edit.setText(self.event_data.get('path', ''))
        img_layout.addWidget(self.img_path_edit)
        
        self.browse_btn = QPushButton("Chọn ảnh...")
        self.browse_btn.clicked.connect(self.browse_image)
        img_layout.addWidget(self.browse_btn)
        
        self.capture_img_btn = QPushButton("Chụp ảnh...")
        self.capture_img_btn.clicked.connect(self.capture_image_template)
        img_layout.addWidget(self.capture_img_btn)
        
        layout.addLayout(img_layout)
        
        # Content Layout (Preview + Params)
        content_layout = QHBoxLayout()
        
        # Left: Image Preview
        self.preview_label = QLabel("Chưa chọn ảnh")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFixedSize(200, 150)
        self.preview_label.setStyleSheet("border: 1px solid #CCCCCC; background-color: #F0F0F0;")
        content_layout.addWidget(self.preview_label)
        
        # Connect text change to preview update
        self.img_path_edit.textChanged.connect(self.update_preview)
        
        # Right: Parameters
        params_layout = QFormLayout()
        
        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(0, 3600000) # Up to 1 hour
        self.timeout_spin.setValue(self.event_data.get('timeout_ms', 60000))
        params_layout.addRow("Thời gian quét (ms):", self.timeout_spin)
        
        # Threshold
        self.thresh_spin = QDoubleSpinBox()
        self.thresh_spin.setRange(0.5, 0.99)
        self.thresh_spin.setSingleStep(0.01)
        self.thresh_spin.setValue(self.event_data.get('threshold', 0.85))
        params_layout.addRow("Độ chính xác (0.5 - 0.99):", self.thresh_spin)
        
        # Poll Interval
        self.poll_spin = QSpinBox()
        self.poll_spin.setRange(10, 5000)
        self.poll_spin.setValue(self.event_data.get('poll_interval_ms', 150))
        params_layout.addRow("Tần suất quét (ms):", self.poll_spin)
        
        content_layout.addLayout(params_layout)
        layout.addLayout(content_layout)
        
        # Region
        region_group = QVBoxLayout()
        region_group.addWidget(QLabel("Vùng tìm kiếm (Tùy chọn):"))
        
        coord_layout = QHBoxLayout()
        self.x1_spin = QSpinBox()
        self.y1_spin = QSpinBox()
        self.x2_spin = QSpinBox()
        self.y2_spin = QSpinBox()
        
        for spin in [self.x1_spin, self.y1_spin, self.x2_spin, self.y2_spin]:
            spin.setRange(0, 10000)
            spin.setValue(0)
            
        coord_layout.addWidget(QLabel("x1:"))
        coord_layout.addWidget(self.x1_spin)
        coord_layout.addWidget(QLabel("y1:"))
        coord_layout.addWidget(self.y1_spin)
        coord_layout.addWidget(QLabel("x2:"))
        coord_layout.addWidget(self.x2_spin)
        coord_layout.addWidget(QLabel("y2:"))
        coord_layout.addWidget(self.y2_spin)
        
        region_group.addLayout(coord_layout)
        
        self.capture_btn = QPushButton("Chọn vùng...")
        self.capture_btn.clicked.connect(self.capture_region)
        region_group.addWidget(self.capture_btn)
        
        layout.addLayout(region_group)
        
        # Load existing region if any
        region = self.event_data.get('region')
        if region:
            self.x1_spin.setValue(region[0])
            self.y1_spin.setValue(region[1])
            self.x2_spin.setValue(region[2])
            self.y2_spin.setValue(region[3])
            
        layout.addStretch()
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Initial preview
        self.update_preview(self.img_path_edit.text())
        
    def browse_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.bmp)")
        if path:
            self.img_path_edit.setText(path)
            
    def update_preview(self, path):
        if not path:
            self.preview_label.setText("Chưa chọn ảnh")
            self.preview_label.setPixmap(QPixmap())
            return
            
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            # Scale to fit
            scaled = pixmap.scaled(self.preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_label.setPixmap(scaled)
            self.preview_label.setText("")
        else:
            self.preview_label.setText("Ảnh không hợp lệ")
            self.preview_label.setPixmap(QPixmap())

    def capture_region(self):
        self.hide()
        # Small delay to let window hide
        QApplication.processEvents()
        
        self.overlay = RegionSelectionOverlay()
        self.overlay.region_selected.connect(self.on_region_selected)
        self.overlay.show()
        
    def capture_image_template(self):
        """Chụp ảnh với vòng lặp xử lý sự kiện (An toàn nhất)"""
        print("DEBUG: capture_image_template called (BUSY WAIT MODE)")
        
        try:
            # 1. Ẩn các cửa sổ
            if self.parent():
                self.parent().hide()
            self.hide()
            
            # 2. Vòng lặp đợi 0.3 giây để UI kịp ẩn hoàn toàn
            # Thay vì dùng QTimer (dễ bị kill), ta dùng vòng lặp processEvents
            print("DEBUG: Waiting for windows to hide...")
            deadline = time.time() + 0.3
            while time.time() < deadline:
                QApplication.processEvents()
                time.sleep(0.01)
                
            # 3. Sau khi đợi xong, gọi Snipper NGAY LẬP TỨC
            print("DEBUG: Launching snipper now...")
            
            from utils.snipping_tool import SnippingWidget
            # Tạo Snipper (lúc này màn hình đã sạch)
            self.snipper = SnippingWidget()
            
            # Kết nối tín hiệu
            self.snipper.snippet_taken.connect(self.on_image_captured)
            self.snipper.closed.connect(self.on_snipper_closed)
            
            # 4. Hiển thị Snipper
            self.snipper.show()
            self.snipper.raise_()
            self.snipper.activateWindow()
            self.snipper.setFocus()
            print("DEBUG: Snipper launched successfully!")
            
        except Exception as e:
            print(f"ERROR launching snipper: {e}")
            import traceback
            traceback.print_exc()
            self.restore_windows()
    
    def _show_snipper(self):
        """Show the already-created snipper"""
        try:
            print("DEBUG: _show_snipper called - showing snipper now")
            if hasattr(self, 'snipper') and self.snipper:
                self.snipper.show()
                self.snipper.raise_()
                self.snipper.activateWindow()
                self.snipper.setFocus()
                print("DEBUG: Snipper shown, raised, activated, and focused")
            else:
                print("ERROR: No snipper object found!")
                self.restore_windows()
        except Exception as e:
            print(f"ERROR in _show_snipper: {e}")
            import traceback
            traceback.print_exc()
            self.restore_windows()
        
    def _launch_snipper_safe(self):
        """Launch snipper after windows are hidden"""
        try:
            print("DEBUG: _launch_snipper_safe called")
            self.snipper = SnippingWidget()
            print("DEBUG: SnippingWidget created")
            self.snipper.snippet_taken.connect(self.on_image_captured)
            self.snipper.closed.connect(self.on_snipper_closed)
            print("DEBUG: Signals connected")
            self.snipper.show()
            print("DEBUG: Snipper shown")
            
            # CRITICAL: Force the snipper to be on top and have focus
            self.snipper.raise_()
            self.snipper.activateWindow()
            self.snipper.setFocus()
            print("DEBUG: Snipper raised, activated, and focused")
        except Exception as e:
            print(f"ERROR in _launch_snipper_safe: {e}")
            import traceback
            traceback.print_exc()
            # Restore windows on error
            self.restore_windows()
        
    def restore_windows(self):
        """Restore dialog and parent window visibility"""
        if self.parent():
            self.parent().showNormal()
        self.showNormal()
        self.activateWindow()
    
    
    def on_snipper_closed(self):
        """Restore windows"""
        print("DEBUG: Restoring windows")
        if self.parent():
            self.parent().showNormal()
            self.parent().activateWindow()
        self.showNormal()
        self.activateWindow()
        
        # Clean up
        if hasattr(self, 'snipper'):
            self.snipper.deleteLater()
            self.snipper = None

        
    def on_image_captured(self, file_path):
        try:
            print(f"DEBUG: on_image_captured in dialog: {file_path}")
            # Restore windows first
            self.restore_windows()
            # Then load image
            self.img_path_edit.setText(file_path)
        except Exception as e:
            print(f"ERROR in on_image_captured: {e}")
            import traceback
            traceback.print_exc()
        
    def on_region_selected(self, rect):
        self.x1_spin.setValue(rect[0])
        self.y1_spin.setValue(rect[1])
        self.x2_spin.setValue(rect[2])
        self.y2_spin.setValue(rect[3])
        self.show()
        
    def get_data(self):
        region = None
        x1 = self.x1_spin.value()
        y1 = self.y1_spin.value()
        x2 = self.x2_spin.value()
        y2 = self.y2_spin.value()
        
        if x2 > x1 and y2 > y1:
            region = [x1, y1, x2, y2]
            
        return {
            'type': 'wait_image',
            'path': self.img_path_edit.text(),
            'timeout_ms': self.timeout_spin.value(),
            'threshold': self.thresh_spin.value(),
            'poll_interval_ms': self.poll_spin.value(),
            'region': region,
            'time': 0.5 # Default delay after finding
        }
