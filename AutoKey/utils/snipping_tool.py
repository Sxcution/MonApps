import sys
import time
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QCursor, QScreen

class SnippingWidget(QWidget):
    """Lớp phủ toàn màn hình để cắt ảnh"""
    snippet_taken = pyqtSignal(object)  # Trả về QPixmap
    closed = pyqtSignal()

    def __init__(self, parent=None, original_pixmap=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool  # Dùng Tool để không hiện icon dưới taskbar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        
        # Ảnh gốc chụp màn hình (sạch)
        self.original_pixmap = original_pixmap
        
        # Tính toán hình học của toàn bộ các màn hình (Virtual Desktop)
        self.total_geometry = QRect()
        for screen in QApplication.screens():
            self.total_geometry = self.total_geometry.united(screen.geometry())
            
        self.setGeometry(self.total_geometry)
        
        # Biến điều khiển chuột
        self.begin = QPoint()
        self.end = QPoint()
        self.is_snipping = False

    def paintEvent(self, event):
        if not self.original_pixmap:
            return

        painter = QPainter(self)
        
        # 1. Vẽ ảnh gốc nhưng làm tối đi (Overlay effect)
        painter.drawPixmap(self.rect(), self.original_pixmap)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100)) # Phủ lớp đen mờ 100/255
        
        # 2. Nếu đang kéo chuột, vẽ vùng chọn SÁNG lên (đục lỗ lớp đen)
        if self.is_snipping:
            rect = QRect(self.begin, self.end).normalized()
            if not rect.isEmpty():
                # Vẽ lại phần ảnh gốc (sáng) vào đúng vị trí ô vuông
                # Lưu ý: rect ở đây là toạ độ trên widget, cần map sang toạ độ pixmap nếu cần
                # Nhưng vì widget phủ kín pixmap nên tỉ lệ là 1:1
                painter.drawPixmap(rect, self.original_pixmap, rect)
                
                # Vẽ viền đỏ cho dễ nhìn
                pen = QPen(QColor(255, 0, 0), 2)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(rect)
                
                # Vẽ kích thước (Optional)
                w, h = rect.width(), rect.height()
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(rect.topLeft() - QPoint(0, 5), f"{w}x{h}")

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = event.pos()
        self.is_snipping = True
        self.update()

    def mouseMoveEvent(self, event):
        if self.is_snipping:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self.is_snipping = False
        self.close()
        
        rect = QRect(self.begin, self.end).normalized()
        
        # Xử lý cắt ảnh từ Pixmap gốc
        if rect.width() > 10 and rect.height() > 10 and self.original_pixmap:
            cropped = self.original_pixmap.copy(rect)
            self.snippet_taken.emit(cropped)
        else:
            self.closed.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            self.closed.emit()

def capture_screen_region():
    """
    Hàm helper xử lý quy trình: Ẩn App -> Chụp -> Hiện Tool -> Trả về kết quả
    """
    app = QApplication.instance()
    
    # 1. Tìm tất cả cửa sổ chính để ẩn đi
    top_levels = app.topLevelWidgets()
    visible_windows = [w for w in top_levels if w.isVisible()]
    
    for w in visible_windows:
        if w.objectName() != "SnippingWidget": # Đừng ẩn chính nó nếu lỡ có
            w.showMinimized() # Minimize cho mượt (giống Windows) hoặc w.hide()
            
    # 2. Đợi hiệu ứng ẩn cửa sổ hoàn tất
    # Dùng processEvents liên tục trong 300ms để UI cập nhật
    deadline = time.time() + 0.3
    while time.time() < deadline:
        app.processEvents()
        
    # 3. CHỤP MÀN HÌNH (Lúc này màn hình đã sạch)
    screen = app.primaryScreen()
    # Lấy toàn bộ kích thước màn hình ảo (nếu dùng nhiều màn hình)
    virtual_geometry = screen.virtualGeometry()
    
    # Grab toàn bộ màn hình
    full_screenshot = screen.grabWindow(
        0, 
        virtual_geometry.x(), virtual_geometry.y(), 
        virtual_geometry.width(), virtual_geometry.height()
    )
    
    # 4. Khởi tạo Snipping Tool với ảnh vừa chụp
    snipper = SnippingWidget(original_pixmap=full_screenshot)
    
    # Biến lưu kết quả dùng closure
    result_container = {"pixmap": None}
    
    def on_done(pixmap):
        result_container["pixmap"] = pixmap
        
    snipper.snippet_taken.connect(on_done)
    
    # Hiện overlay full màn hình
    snipper.showFullScreen()
    snipper.activateWindow()
    snipper.raise_()
    
    # 5. Chặn luồng (Block loop) cho đến khi cắt xong
    while snipper.isVisible():
        app.processEvents()
        
    # 6. Khôi phục cửa sổ cũ
    for w in visible_windows:
        w.showNormal() # Hoặc w.show()
        w.activateWindow()
        
    if result_container["pixmap"]:
        return result_container["pixmap"], result_container["pixmap"].rect()
        
    return None, None
