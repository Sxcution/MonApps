import sys
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QCursor, QGuiApplication

class SnippingWidget(QWidget):
    snippet_taken = pyqtSignal(str)
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # Fix 1: Use Window flag (not Tool) and Frameless
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        # Fix 2: ApplicationModal ensures this window takes priority over the hidden dialog
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.setMouseTracking(True)
        
        self.begin = QPoint()
        self.end = QPoint()
        self.is_snipping = False
        self.original_pixmap = None
        self.dark_pixmap = None
        
        # Initialize
        self.capture_screen_state()

    def capture_screen_state(self):
        """Captures the entire Virtual Desktop (all monitors)"""
        screen = QApplication.primaryScreen()
        
        # Fix 3: Calculate the Virtual Geometry (can include negative coordinates)
        virtual_geometry = QRect()
        for s in QApplication.screens():
            virtual_geometry = virtual_geometry.united(s.geometry())
            
        print(f"DEBUG: Virtual Desktop Geometry: {virtual_geometry}")

        # Capture the full virtual desktop
        self.original_pixmap = screen.grabWindow(
            0, 
            virtual_geometry.x(), 
            virtual_geometry.y(), 
            virtual_geometry.width(), 
            virtual_geometry.height()
        )
        
        # Create dark overlay
        self.dark_pixmap = self.original_pixmap.copy()
        painter = QPainter(self.dark_pixmap)
        painter.setBrush(QColor(0, 0, 0, 100)) # Black 100 alpha
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.dark_pixmap.rect())
        painter.end()
        
        # Set geometry to cover the full virtual area
        self.setGeometry(virtual_geometry)
        self.show()

    def paintEvent(self, event):
        if not self.dark_pixmap: return
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.dark_pixmap)
        
        if self.is_snipping:
            # Map selection rect to global, then to local if needed, 
            # but since widget == virtual desktop, local coords match pixmap coords
            rect = QRect(self.begin, self.end).normalized()
            if not rect.isEmpty():
                painter.drawPixmap(rect, self.original_pixmap, rect)
                painter.setPen(QPen(QColor('#0078D4'), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(rect)
                
                # Draw text dimensions
                w, h = rect.width(), rect.height()
                painter.setPen(Qt.GlobalColor.white)
                painter.drawText(rect.topLeft() - QPoint(0, 5), f"{w} x {h}")

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
        rect = QRect(self.begin, self.end).normalized()
        
        if rect.width() < 10 or rect.height() < 10:
            self.close()
            self.closed.emit()
            return

        # Save logic
        import os, time
        if not os.path.exists("captures"): os.makedirs("captures")
        filename = f"captures/snip_{int(time.time())}.png"
        full_path = os.path.abspath(filename)
        
        # Crop from original
        self.original_pixmap.copy(rect).save(full_path)
        
        self.close()
        self.snippet_taken.emit(full_path)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            self.closed.emit()
