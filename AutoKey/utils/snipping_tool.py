from PyQt6.QtWidgets import QSplashScreen, QApplication
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPixmap, QGuiApplication
import sys


class CaptureScreen(QSplashScreen):
    """Cửa sổ để cắt ảnh từ màn hình"""
    
    capture_done = pyqtSignal(object)  # Signal trả về pixmap
    
    def __init__(self):
        super().__init__()
        self.origin = QPoint(0, 0)
        self.end = QPoint(0, 0)
        
        # Thiết lập màn hình toàn bộ với tối đen 70%
        primary_screen = QGuiApplication.primaryScreen()
        screen_geometry = primary_screen.geometry()
        
        # Tạo pixmap màu đen
        self.setGeometry(screen_geometry)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 180);")
        
        self.captured_pixmap = None
        
    def mousePressEvent(self, event):
        """Bắt đầu vẽ vùng cắt"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.pos()
    
    def mouseMoveEvent(self, event):
        """Hiển thị vùng được chọn"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.update()  # Vẽ lại
    
    def mouseReleaseEvent(self, event):
        """Hoàn thành cắt ảnh"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.end = event.pos()
            
            # Cắt ảnh từ vùng được chọn
            primary_screen = QGuiApplication.primaryScreen()
            
            # Tính toán tọa độ
            x = min(self.origin.x(), self.end.x())
            y = min(self.origin.y(), self.end.y())
            w = abs(self.end.x() - self.origin.x())
            h = abs(self.end.y() - self.origin.y())
            
            # Chụp màn hình
            if w > 0 and h > 0:
                self.captured_pixmap = primary_screen.grabWindow(0, x, y, w, h)
            
            self.hide()
            self.capture_done.emit(self.captured_pixmap)
    
    def paintEvent(self, event):
        """Vẽ hình chữ nhật vùng cắt"""
        super().paintEvent(event)
        
        # Chỉ vẽ khi đang kéo
        if self.origin != self.end:
            painter = QPainter(self)
            
            # Vẽ hình chữ nhật
            x = min(self.origin.x(), self.end.x())
            y = min(self.origin.y(), self.end.y())
            w = abs(self.end.x() - self.origin.x())
            h = abs(self.end.y() - self.origin.y())
            
            # Đường viền màu xanh
            painter.setPen(QColor(0, 123, 255))
            painter.drawRect(x, y, w, h)
            
            # Tô sáng vùng được chọn
            painter.fillRect(x, y, w, h, QColor(0, 123, 255, 30))
            painter.end()


def capture_screen_region():
    """
    Mở cửa sổ cắt ảnh toàn màn hình
    Return: (QPixmap, QRect) hoặc (None, None) nếu hủy
    """
    app = QApplication.instance()
    
    capture_widget = CaptureScreen()
    pixmap = None
    
    def on_capture_done(result_pixmap):
        nonlocal pixmap
        pixmap = result_pixmap
        capture_widget.close()
    
    capture_widget.capture_done.connect(on_capture_done)
    capture_widget.show()
    
    # Chạy event loop cho đến khi người dùng xong
    while capture_widget.isVisible():
        QApplication.processEvents()
    
    if pixmap:
        return pixmap, pixmap.rect()
    return None, None
