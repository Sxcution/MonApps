"""
Text Search Overlay - Live test visualization with bounding boxes
Shows OCR results and match scores in real-time
"""
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPixmap
from utils.text_search import TextSearchEngine
from utils.roi_manager import ROIManager
import time

class TextSearchOverlay(QWidget):
    """Overlay window for visualizing text search results"""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        
        # Make window transparent and always on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Get screen geometry
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        # Initialize OCR engine
        self.engine = TextSearchEngine(
            languages=config['languages'],
            gpu=False
        )
        
        # Initialize ROI manager
        self.roi_manager = ROIManager(rate_limit_fps=10)
        
        # Test state
        self.ocr_results = []
        self.best_match = None
        self.timer = None
    
    def start_test(self):
        """Start continuous OCR testing"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ocr)
        self.timer.start(100)  # 10 fps
    
    def stop_test(self):
        """Stop testing"""
        if self.timer:
            self.timer.stop()
    
    def update_ocr(self):
        """Perform OCR and update display"""
        # Capture screen
        img = self.roi_manager.capture()
        if img is None:
            return
        
        # Search for text
        try:
            self.best_match = self.engine.search(
                img,
                self.config['query'],
                match_mode=self.config['match'],
                min_score=self.config['min_score'],
                preproc=self.config['preproc']
            )
            
            # Also get all OCR results for visualization
            self.ocr_results = self.engine.ocr(img, preproc=self.config['preproc'])
        except Exception as e:
            print(f"⚠️ OCR error: {e}")
        
        self.update()
    
    def paintEvent(self, event):
        """Draw overlay with bounding boxes"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw all OCR results (gray)
        pen = QPen(QColor(128, 128, 128, 180))
        pen.setWidth(2)
        painter.setPen(pen)
        font = QFont("Arial", 10)
        painter.setFont(font)
        
        for result in self.ocr_results:
            x1, y1, x2, y2 = result.bbox
            rect = QRect(x1, y1, x2 - x1, y2 - y1)
            painter.drawRect(rect)
            
            # Draw text and confidence
            label = f"{result.text} ({result.confidence:.2f})"
            painter.drawText(x1, y1 - 5, label)
        
        # Draw best match (green)
        if self.best_match:
            pen = QPen(QColor(0, 255, 0, 255))
            pen.setWidth(3)
            painter.setPen(pen)
            
            x1, y1, x2, y2 = self.best_match.bbox
            rect = QRect(x1, y1, x2 - x1, y2 - y1)
            painter.drawRect(rect)
            
            # Draw match score
            label = f"✅ {self.best_match.text} (score: {self.best_match.match_score})"
            font_large = QFont("Arial", 12, QFont.Weight.Bold)
            painter.setFont(font_large)
            painter.drawText(x1, y1 - 10, label)
            
            # Draw center point
            cx, cy = self.best_match.center
            painter.drawEllipse(cx - 3, cy - 3, 6, 6)
