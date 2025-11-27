import sys
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QCursor

class SnippingWidget(QWidget):
    # Signals
    snippet_taken = pyqtSignal(str)  # Returns path
    closed = pyqtSignal()            # Returns nothing (cancel)

    def __init__(self):
        super().__init__()
        print("DEBUG: SnippingWidget initializing...")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.setMouseTracking(True)
        
        # State
        self.begin = QPoint()
        self.end = QPoint()
        self.is_snipping = False
        
        # Screen Capture Data
        self.original_pixmap = None  # Clean screenshot
        self.dark_pixmap = None      # Dimmed screenshot
        
        # Init Geometry & Capture
        self.capture_screen_state()
        print("DEBUG: SnippingWidget initialized.")

    def showEvent(self, event):
        """
        Show event override. 
        CRITICAL: Do NOT grab mouse here immediately. Qt requires the window to be 
        physically visible on screen before grabbing input.
        """
        super().showEvent(event)
        self.setFocus()
        self.activateWindow()
        
        # Wait 100ms for the window to be fully mapped by Windows OS
        QTimer.singleShot(100, self._start_grabbing)

    def _start_grabbing(self):
        """Safe place to grab inputs"""
        try:
            self.grabMouse()
            self.grabKeyboard()
            print("DEBUG: Mouse and Keyboard grabbed successfully")
        except Exception as e:
            print(f"ERROR: Failed to grab input: {e}")

    def capture_screen_state(self):
        """Captures the entire virtual desktop immediately."""
        print("DEBUG: Capturing screen state...")
        screen = QApplication.primaryScreen()
        
        # Calculate total geometry of all screens
        total_geometry = QRect()
        for s in QApplication.screens():
            total_geometry = total_geometry.united(s.geometry())
            
        print(f"DEBUG: Total geometry: {total_geometry}")

        # Grab Window (0 means desktop)
        self.original_pixmap = screen.grabWindow(0, 
                                                 total_geometry.x(), 
                                                 total_geometry.y(), 
                                                 total_geometry.width(), 
                                                 total_geometry.height())
        
        if self.original_pixmap.isNull():
            print("ERROR: Failed to grab screen!")
        else:
            print(f"DEBUG: Screen grabbed. Size: {self.original_pixmap.size()}")

        # Create a darkened version for the background
        self.dark_pixmap = self.original_pixmap.copy()
        painter = QPainter(self.dark_pixmap)
        painter.setBrush(QColor(0, 0, 0, 100)) # Black with 100 alpha
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.dark_pixmap.rect())
        painter.end()
        
        # Set widget geometry to cover everything
        self.setGeometry(total_geometry)

    def paintEvent(self, event):
        if not self.dark_pixmap:
            return

        painter = QPainter(self)
        
        # 1. Draw the darkened background everywhere
        painter.drawPixmap(0, 0, self.dark_pixmap)
        
        # 2. If selecting, draw the original (bright) pixmap in the selection rect
        if self.is_snipping:
            rect = QRect(self.begin, self.end).normalized()
            if not rect.isEmpty():
                # Draw the clear part (reveal original)
                painter.drawPixmap(rect, self.original_pixmap, rect)
                
                # Draw Border
                pen = QPen(QColor('#0078D4'), 2)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(rect)
                
                # Draw Coordinates Text (Optional - Jibit style)
                text = f"{rect.width()} x {rect.height()}"
                painter.setPen(QColor('white'))
                painter.drawText(rect.topLeft() - QPoint(0, 5), text)

    def mousePressEvent(self, event):
        print(f"DEBUG: Mouse press at {event.pos()}")
        self.begin = event.pos()
        self.end = event.pos()
        self.is_snipping = True
        self.update()

    def mouseMoveEvent(self, event):
        if self.is_snipping:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        print(f"DEBUG: Mouse release at {event.pos()}")
        # Release input capture before closing
        self.releaseMouse()
        self.releaseKeyboard()
        
        self.is_snipping = False
        rect = QRect(self.begin, self.end).normalized()
        
        # If selection is too small, treat as cancel or mistake
        if rect.width() < 10 or rect.height() < 10:
            print("DEBUG: Selection too small, cancelling.")
            self.close()
            self.closed.emit()
            return

        # Crop the image from the ORIGINAL (Clean) pixmap
        cropped = self.original_pixmap.copy(rect)
        
        # Save to temp file
        import os, time
        if not os.path.exists("captures"):
            os.makedirs("captures")
        
        filename = f"captures/snip_{int(time.time())}.png"
        full_path = os.path.abspath(filename)
        cropped.save(full_path)
        
        print(f"📸 Saved snippet: {full_path}")
        self.close()
        self.snippet_taken.emit(full_path)

    def keyPressEvent(self, event):
        # Allow cancelling with ESC
        if event.key() == Qt.Key.Key_Escape:
            self.releaseMouse()
            self.releaseKeyboard()
            self.close()
            self.closed.emit()
