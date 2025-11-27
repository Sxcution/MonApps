import sys
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QCursor, QGuiApplication

class SnippingWidget(QWidget):
    snippet_taken = pyqtSignal(str)
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        print("🔍 DEBUG: SnippingWidget __init__")
        # Fix 1: Use Window flag (not Tool) and Frameless
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  # Add Tool flag to ensure it stays on top
        )
        # Fix 2: ApplicationModal ensures this window takes priority over the hidden dialog
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # CRITICAL: Disable translucent background for solid overlay
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        
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
        print("🔍 DEBUG: capture_screen_state called")
        screen = QApplication.primaryScreen()
        
        # Fix 3: Calculate the Virtual Geometry (can include negative coordinates)
        virtual_geometry = QRect()
        for s in QApplication.screens():
            virtual_geometry = virtual_geometry.united(s.geometry())
            
        print(f"🔍 DEBUG: Virtual Desktop Geometry: {virtual_geometry}")

        # Capture the full virtual desktop
        self.original_pixmap = screen.grabWindow(
            0, 
            virtual_geometry.x(), 
            virtual_geometry.y(), 
            virtual_geometry.width(), 
            virtual_geometry.height()
        )
        
        print(f"🔍 DEBUG: Captured pixmap size: {self.original_pixmap.width()}x{self.original_pixmap.height()}")
        
        # Create dark overlay with stronger opacity
        self.dark_pixmap = self.original_pixmap.copy()
        painter = QPainter(self.dark_pixmap)
        # Use compositing mode for proper overlay
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.setBrush(QColor(0, 0, 0, 150)) # Increased opacity: Black 150 alpha (was 100)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.dark_pixmap.rect())
        painter.end()
        
        print(f"🔍 DEBUG: Created dark overlay pixmap")
        
        # Set geometry to cover the full virtual area
        self.setGeometry(virtual_geometry)
        print(f"🔍 DEBUG: Set widget geometry: {virtual_geometry}")
        
        # CRITICAL: Show fullscreen to ensure it covers everything
        self.showFullScreen()
        
        # Force update to ensure paintEvent is called
        self.update()
        QApplication.processEvents()
        
        # Ensure widget is on top and active - multiple attempts
        self.raise_()
        self.activateWindow()
        self.setFocus()
        QApplication.processEvents()
        
        # Additional activation after a short delay
        QTimer.singleShot(50, lambda: (
            self.raise_(),
            self.activateWindow(),
            self.setFocus(),
            QApplication.processEvents()
        ))
        
        print(f"🔍 DEBUG: Widget shown fullscreen, size: {self.width()}x{self.height()}, visible: {self.isVisible()}")

    def paintEvent(self, event):
        print(f"🔍 DEBUG: paintEvent called, dark_pixmap exists: {self.dark_pixmap is not None}")
        if not self.dark_pixmap:
            print("🔍 DEBUG: WARNING - dark_pixmap is None, cannot paint!")
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw the dark overlay first
        painter.drawPixmap(0, 0, self.dark_pixmap)
        
        if self.is_snipping:
            # Map selection rect to global, then to local if needed, 
            # but since widget == virtual desktop, local coords match pixmap coords
            rect = QRect(self.begin, self.end).normalized()
            if not rect.isEmpty():
                # Draw the original image in the selection area (bright area)
                painter.drawPixmap(rect, self.original_pixmap, rect)
                
                # Draw selection border
                painter.setPen(QPen(QColor('#0078D4'), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(rect)
                
                # Draw text dimensions
                w, h = rect.width(), rect.height()
                painter.setPen(Qt.GlobalColor.white)
                painter.setFont(painter.font())
                painter.drawText(rect.topLeft() - QPoint(0, 5), f"{w} x {h}")
        
        painter.end()

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
        print(f"🔍 DEBUG: mouseReleaseEvent - is_snipping: {self.is_snipping}")
        self.is_snipping = False
        rect = QRect(self.begin, self.end).normalized()
        
        if rect.width() < 10 or rect.height() < 10:
            print("🔍 DEBUG: Selection too small, closing")
            self.close()
            self.closed.emit()
            return

        print(f"🔍 DEBUG: Saving snippet: {rect.width()}x{rect.height()}")
        # Save logic
        import os, time
        if not os.path.exists("captures"): os.makedirs("captures")
        filename = f"captures/snip_{int(time.time())}.png"
        full_path = os.path.abspath(filename)
        
        # Crop from original
        self.original_pixmap.copy(rect).save(full_path)
        print(f"🔍 DEBUG: Saved to {full_path}")
        
        self.close()
        self.snippet_taken.emit(full_path)

    def keyPressEvent(self, event):
        print(f"🔍 DEBUG: keyPressEvent - key: {event.key()}")
        if event.key() == Qt.Key.Key_Escape:
            print("🔍 DEBUG: ESC pressed, closing")
            self.close()
            self.closed.emit()
    
    def closeEvent(self, event):
        """Override to add debug"""
        print(f"🔍 DEBUG: SnippingWidget closeEvent called, visible: {self.isVisible()}")
        super().closeEvent(event)
