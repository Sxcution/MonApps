from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar
from PyQt6.QtCore import Qt, QTimer, QPoint, QSettings
from PyQt6.QtGui import QFont

class PlaybackOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Macro Playback")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        
        # Make window frameless but keep close button
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        
        # Variables for dragging
        self.dragging = False
        self.drag_position = QPoint()
        
        # Settings for position
        self.settings = QSettings("MonSoft", "MacroRecorder")
        
        self.setup_ui()
        self.resize(280, 60)  # Ultra-compact height
        
        # Set transparent background to allow rounded corners
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # Minimal outer margins
        layout.setSpacing(0)  # No spacing between rows
        
        # Progress bar with loop info and time on same line (no spacing)
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(0)  # No spacing between elements
        progress_layout.setContentsMargins(0, 0, 0, 0)  # No margins
        
        # Progress Bar (left side, reduced width by 50%)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximumHeight(18)
        self.progress_bar.setMaximumWidth(140)  # 50% of original width
        progress_layout.addWidget(self.progress_bar)
        
        # Loop counter (middle, compact, no gap)
        self.loop_label = QLabel("⏳ 0/0")
        self.loop_label.setFont(QFont("Segoe UI", 9))
        self.loop_label.setMinimumWidth(50)
        self.loop_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        progress_layout.addWidget(self.loop_label)
        
        # Time display (right side, same row)
        self.time_label = QLabel("⏱️ 00:00:00")
        self.time_label.setFont(QFont("Segoe UI", 9))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.time_label.setContentsMargins(0, 0, 0, 0)
        progress_layout.addWidget(self.time_label)
        
        layout.addLayout(progress_layout)
        
        # Control Buttons (no spacing, touching progress bar)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)
        btn_layout.setContentsMargins(0, 0, 0, 0)  # No margins - touching
        
        self.pause_btn = QPushButton("⏸️ Pause")
        self.pause_btn.setCheckable(True)
        self.pause_btn.setMinimumHeight(25)
        self.pause_btn.setMaximumHeight(25)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setMinimumHeight(25)
        self.stop_btn.setMaximumHeight(25)
        
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.stop_btn)
        
        layout.addLayout(btn_layout)
        
        # Apply Styling with rounded corners
        self.setStyleSheet("""
            PlaybackOverlay {
                background-color: #2b2b2b;
                color: #ffffff;
                border-radius: 10px;
            }
            QLabel {
                color: #ffffff;
                background-color: transparent;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 9pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:checked {
                background-color: #ff8c00;
            }
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                background-color: #1e1e1e;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 3px;
            }
        """)
        
    def update_loop(self, current, total):
        """Update loop counter (text only)"""
        if total == 0:
            self.loop_label.setText(f"⏳ {current} (∞)")
        else:
            self.loop_label.setText(f"⏳ {current}/{total}")
    
    def update_step_progress(self, current_step, total_steps):
        """Update progress bar based on step execution"""
        if total_steps > 0:
            progress = int((current_step / total_steps) * 100)
            self.progress_bar.setValue(min(progress, 100))
            self.progress_bar.setFormat(f"{current_step}/{total_steps} steps - {progress}%")
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("0%")

    
    def update_time(self, elapsed_seconds):
        """Update elapsed time"""
        hours = int(elapsed_seconds // 3600)
        minutes = int((elapsed_seconds % 3600) // 60)
        seconds = int(elapsed_seconds % 60)
        self.time_label.setText(f"⏱️ {hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()
    
    def position_overlay(self):
        """Position overlay based on settings"""
        position = self.settings.value("overlay_position", "top_left")
        screen = self.screen().availableGeometry()
        margin = 20
        
        if position == "top_left":
            self.move(screen.left() + margin, screen.top() + margin)
        elif position == "top_center":
            self.move(screen.center().x() - self.width() // 2, screen.top() + margin)
        elif position == "top_right":
            self.move(screen.right() - self.width() - margin, screen.top() + margin)
        elif position == "center":
            frame_gm = self.frameGeometry()
            frame_gm.moveCenter(screen.center())
            self.move(frame_gm.topLeft())
        elif position == "bottom_left":
            self.move(screen.left() + margin, screen.bottom() - self.height() - margin)
        elif position == "bottom_center":
            self.move(screen.center().x() - self.width() // 2, screen.bottom() - self.height() - margin)
        elif position == "bottom_right":
            self.move(screen.right() - self.width() - margin, screen.bottom() - self.height() - margin)
        else:
            # Default to top left
            self.move(screen.left() + margin, screen.top() + margin)
    
    def center_on_screen(self):
        """Deprecated: Use position_overlay instead"""
        self.position_overlay()
