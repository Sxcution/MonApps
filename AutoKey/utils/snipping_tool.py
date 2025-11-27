from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QCursor

class SnippingWidget(QWidget):
    # Signal returns the path of the saved image
    snippet_taken = pyqtSignal(str) 
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.setMouseTracking(True)
        
        # Geometry setup (cover all screens)
        full_screen = QApplication.primaryScreen().geometry()
        for screen in QApplication.screens():
            full_screen = full_screen.united(screen.geometry())
        self.setGeometry(full_screen)
        
        self.begin = QPoint()
        self.end = QPoint()
        self.is_snipping = False
        self.opacity_color = QColor(0, 0, 0, 100) # Dim background

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(self.opacity_color)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Fill whole screen with dim color
        painter.drawRect(self.rect())
        
        if self.is_snipping:
            # Clear the selected rectangle (make it transparent) to "see through"
            selection_rect = QRect(self.begin, self.end).normalized()
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.drawRect(selection_rect)
            
            # Reset mode to draw border
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            pen = QPen(QColor('#0078D4'), 2) # Blue border like Windows/Jibit
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(selection_rect)

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
        
        # Capture logic
        rect = QRect(self.begin, self.end).normalized()
        if rect.width() > 10 and rect.height() > 10:
            self.capture_image(rect)
        else:
            self.closed.emit()

    def capture_image(self, rect):
        # Hide self to grab the screen behind
        self.hide()
        screen = QApplication.primaryScreen()
        if screen:
            pixmap = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())
            
            # Save to temp file
            import os, time
            if not os.path.exists("captures"):
                os.makedirs("captures")
            
            filename = f"captures/snip_{int(time.time())}.png"
            # Ensure absolute path
            abs_path = os.path.abspath(filename)
            pixmap.save(abs_path)
            print(f"📸 Image captured: {abs_path}")
            self.snippet_taken.emit(abs_path)
        else:
            self.closed.emit()
