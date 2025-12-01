from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton
from PySide6.QtCore import Qt, QTimer, QPoint, QSettings, QSize
from PySide6.QtGui import QFont, QIcon
from qfluentwidgets import CardWidget, FluentIcon as FIF, Theme, isDarkTheme

class PlaybackOverlay(QWidget):
    """Mini playback overlay with Fluent design - playback_overlay : Cửa sổ điều khiển phát macro"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Macro Playback")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Variables for dragging
        self.dragging = False
        self.drag_position = QPoint()
        
        # Settings for position
        self.settings = QSettings("MonSoft", "MacroRecorder")
        
        self.setup_ui()
        self.resize(280, 40)  # Wider for single row
        
    def setup_ui(self):
        """Setup UI with Fluent design components"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Use CardWidget as container for fluent look
        self.card = CardWidget(self)
        self.card.setStyleSheet("CardWidget { background-color: rgba(255, 255, 255, 0.85); }")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(6, 4, 6, 4)
        card_layout.setSpacing(0)
        
        # === SINGLE ROW: Progress + Loop + Time + Pause + Stop ===
        row = QHBoxLayout()
        row.setSpacing(0)  # No spacing - all elements sit next to each other
        
        # pbar_playback : Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("pbar_playback")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximumHeight(20)
        self.progress_bar.setMinimumWidth(70)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("0%")
        row.addWidget(self.progress_bar)
        
        # lbl_loop_count
        self.loop_label = QLabel("1/1")
        self.loop_label.setObjectName("lbl_loop_count")
        self.loop_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.loop_label.setMinimumWidth(30)
        self.loop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self.loop_label)
        
        # lbl_elapsed_time
        self.time_label = QLabel("00:00:00")
        self.time_label.setObjectName("lbl_elapsed_time")
        self.time_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.time_label.setMinimumWidth(60)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self.time_label)
        
        # btn_pause - minimal size, icon only (QPushButton for better control)
        self.pause_btn = QPushButton()
        self.pause_btn.setObjectName("btn_pause")
        self.pause_btn.setCheckable(True)  # Toggle behavior
        self.pause_btn.setIcon(FIF.PAUSE.icon())
        self.pause_btn.setText("")  # No text
        self.pause_btn.setFixedSize(14, 14)
        self.pause_btn.setIconSize(QSize(10, 10))
        self.pause_btn.setToolTip("⏸️")
        self.pause_btn.setStyleSheet("""
            QPushButton {
                padding: 0px;
                margin: 0px;
                border: 1px solid #0078D4;
                border-radius: 3px;
                background-color: #0078D4;
                min-width: 14px;
                max-width: 14px;
                min-height: 14px;
                max-height: 14px;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
            QPushButton:checked {
                background-color: #0078D4;
            }
        """)
        self.pause_btn.toggled.connect(self._on_pause_toggled)
        row.addWidget(self.pause_btn)
        
        # btn_stop - minimal size, red background (QPushButton for better control)
        self.stop_btn = QPushButton()
        self.stop_btn.setObjectName("btn_stop")
        self.stop_btn.setIcon(FIF.CLOSE.icon())
        self.stop_btn.setText("")  # No text
        self.stop_btn.setFixedSize(14, 14)
        self.stop_btn.setIconSize(QSize(10, 10))
        self.stop_btn.setToolTip("⏹️")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF0000;
                border: 1px solid #CC0000;
                border-radius: 3px;
                padding: 0px;
                margin: 0px;
                min-width: 14px;
                max-width: 14px;
                min-height: 14px;
                max-height: 14px;
            }
            QPushButton:hover {
                background-color: #FF3333;
            }
            QPushButton:pressed {
                background-color: #CC0000;
            }
        """)
        row.addWidget(self.stop_btn)
        
        card_layout.addLayout(row)
        main_layout.addWidget(self.card)
        
        # Apply custom styling
        self.apply_overlay_style()
        
    def apply_overlay_style(self):
        """Apply styling that adapts to theme"""
        is_dark = isDarkTheme()
        
        if is_dark:
            self.card.setStyleSheet("CardWidget { background-color: rgba(30, 30, 30, 0.85); }")
            progress_style = """
                QProgressBar {
                    border: 1px solid #3A3A3A;
                    border-radius: 4px;
                    text-align: center;
                    background-color: #252525;
                    color: #E0E0E0;
                    font-size: 9px;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background-color: #0078D4;
                    border-radius: 3px;
                }
                QLabel {
                    color: #E0E0E0;
                }
            """
        else:
            self.card.setStyleSheet("CardWidget { background-color: rgba(255, 255, 255, 0.85); }")
            progress_style = """
                QProgressBar {
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                    text-align: center;
                    background-color: #F5F5F5;
                    color: #1A1A1A;
                    font-size: 9px;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background-color: #0078D4;
                    border-radius: 3px;
                }
                QLabel {
                    color: #1A1A1A;
                }
            """
        
        self.setStyleSheet(progress_style)
    
    def update_loop(self, current, total):
        """Update loop counter"""
        if total == 0:
            self.loop_label.setText(f"{current} (∞)")
        else:
            self.loop_label.setText(f"{current}/{total}")
    
    def update_step_progress(self, current_step, total_steps):
        """Update progress bar"""
        if total_steps > 0:
            progress = int((current_step / total_steps) * 100)
            self.progress_bar.setValue(min(progress, 100))
            self.progress_bar.setFormat(f"{current_step}/{total_steps} ({progress}%)")
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("0%")
    
    def update_time(self, elapsed_seconds):
        """Update elapsed time"""
        hours = int(elapsed_seconds // 3600)
        minutes = int((elapsed_seconds % 3600) // 60)
        seconds = int(elapsed_seconds % 60)
        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def _on_pause_toggled(self, checked):
        """Toggle pause button icon"""
        if checked:
            self.pause_btn.setIcon(FIF.PLAY.icon())
            self.pause_btn.setToolTip("▶️")  # Play icon tooltip
        else:
            self.pause_btn.setIcon(FIF.PAUSE.icon())
            self.pause_btn.setToolTip("⏸️")  # Pause icon tooltip
    
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
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()
    
    def position_overlay(self):
        """Position overlay based on settings"""
        position = self.settings.value("overlay_position", "top_right")
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
            self.move(screen.right() - self.width() - margin, screen.top() + margin)
    
    def center_on_screen(self):
        """Deprecated: Use position_overlay instead"""
        self.position_overlay()
