"""
Playback Log Dialog - Display real-time playback logs
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
                             QSplitter, QListWidget, QListWidgetItem, QLabel, QWidget)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from datetime import datetime

class PlaybackLogDialog(QDialog):
    """Dialog hiển thị log của playback với thông tin chi tiết"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Playback Log")
        self.resize(1000, 600)
        self.setup_ui()
        self.log_entries = []
        self.sessions = []  # List of playback sessions
        self.current_session = None
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Splitter: Sessions list (left) + Log table (right)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Playback sessions list
        left_panel = QVBoxLayout()
        sessions_label = QLabel("Playback Sessions")
        sessions_label.setStyleSheet("font-weight: bold; font-size: 12pt; padding: 5px;")
        left_panel.addWidget(sessions_label)
        
        self.sessions_list = QListWidget()
        self.sessions_list.setAlternatingRowColors(True)
        self.sessions_list.currentItemChanged.connect(self.on_session_selected)
        left_panel.addWidget(self.sessions_list)
        
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMinimumWidth(250)
        left_widget.setMaximumWidth(350)
        splitter.addWidget(left_widget)
        
        # Right panel: Log table
        right_panel = QVBoxLayout()
        logs_label = QLabel("Event Logs")
        logs_label.setStyleSheet("font-weight: bold; font-size: 12pt; padding: 5px;")
        right_panel.addWidget(logs_label)
        
        # Table widget for logs
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(["Thời gian", "Step", "Action", "Delay"])
        
        # Configure table
        self.log_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.log_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.log_table.setAlternatingRowColors(True)
        
        # Column widths
        header = self.log_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 150)  # Thời gian
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 80)   # Step
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Action
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(3, 120)  # Delay
        
        right_panel.addWidget(self.log_table)
        
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        splitter.addWidget(right_widget)
        
        # Set splitter proportions
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        layout.addWidget(splitter)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Clear Logs")
        self.clear_btn.clicked.connect(self.clear_logs)
        btn_layout.addWidget(self.clear_btn)
        
        btn_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
        # ✅ Apply Dark Theme Styles
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTableWidget {
                background-color: #1e1e1e;
                border: 1px solid #454545;
                border-radius: 4px;
                gridline-color: #3d3d3d;
                color: #ffffff;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QHeaderView::section {
                background-color: #2b2b2b;
                color: #ffffff;
                border: none;
                border-right: 1px solid #454545;
                border-bottom: 1px solid #454545;
                padding: 8px;
                font-weight: bold;
            }
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #454545;
                border-radius: 4px;
                color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                padding: 8px 16px;
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #1084d9;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QSplitter::handle {
                background-color: #454545;
            }
        """)
    
    def start_new_session(self, filename="Untitled"):
        """Start a new playback session"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session = {
            'filename': filename,
            'timestamp': timestamp,
            'start_time': datetime.now(),
            'logs': []
        }
        self.sessions.append(session)
        self.current_session = session
        
        # Add to sessions list
        item = QListWidgetItem(f"{filename}\n{timestamp}")
        item.setData(Qt.ItemDataRole.UserRole, len(self.sessions) - 1)  # Store session index
        item.setForeground(QColor("#0078d4"))
        self.sessions_list.insertItem(0, item)  # Add to top
        
        # Select this session
        self.sessions_list.setCurrentRow(0)
        
        # Clear current log table
        self.log_table.setRowCount(0)
        self.log_entries.clear()
    
    def on_session_selected(self, current, previous):
        """Handle session selection - load session logs"""
        if not current:
            return
        
        session_idx = current.data(Qt.ItemDataRole.UserRole)
        if session_idx is None or session_idx >= len(self.sessions):
            return
        
        session = self.sessions[session_idx]
        
        # Clear table
        self.log_table.setRowCount(0)
        
        # Load session logs
        for log in session['logs']:
            if log['type'] == 'entry':
                self.add_log(log['step'], log['action'], log['delay'])
            elif log['type'] == 'loop':
                self.add_loop_marker(log['loop_num'])
            elif log['type'] == 'status':
                self.add_status_message(log['message'], log.get('color', '#666666'))
    
    def add_log(self, step_num, action_text, delay_text=""):
        """Add a log entry to the table"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # HH:MM:SS.mmm
        
        row_position = self.log_table.rowCount()
        self.log_table.insertRow(row_position)
        
        # Thời gian
        time_item = QTableWidgetItem(timestamp)
        time_item.setForeground(QColor("#cccccc")) # Light gray for dark theme
        self.log_table.setItem(row_position, 0, time_item)
        
        # Step
        step_item = QTableWidgetItem(f"Step {step_num}")
        step_item.setForeground(QColor("#0078d4"))
        step_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.log_table.setItem(row_position, 1, step_item)
        
        # Action
        action_item = QTableWidgetItem(action_text)
        self.log_table.setItem(row_position, 2, action_item)
        
        # Delay
        delay_item = QTableWidgetItem(delay_text)
        if delay_text and delay_text != "-":
            delay_item.setForeground(QColor("#ff8c00"))  # Orange for delays
        delay_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.log_table.setItem(row_position, 3, delay_item)
        
        # Auto scroll to bottom
        self.log_table.scrollToBottom()
        
        # Store entry in current session
        entry = {
            'type': 'entry',
            'timestamp': timestamp,
            'step': step_num,
            'action': action_text,
            'delay': delay_text
        }
        self.log_entries.append(entry)
        if self.current_session:
            self.current_session['logs'].append(entry)
    
    def add_loop_marker(self, loop_num):
        """Add a loop separator marker"""
        row_position = self.log_table.rowCount()
        self.log_table.insertRow(row_position)
        
        # Merge all columns for loop marker
        loop_text = f"═══════ Loop {loop_num} ═══════"
        item = QTableWidgetItem(loop_text)
        item.setBackground(QColor("#004578")) # Dark blue background
        item.setForeground(QColor("#ffffff")) # White text
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Set span to merge columns
        self.log_table.setSpan(row_position, 0, 1, 4)
        self.log_table.setItem(row_position, 0, item)
        
        # Auto scroll
        self.log_table.scrollToBottom()
        
        # Store in current session
        if self.current_session:
            self.current_session['logs'].append({
                'type': 'loop',
                'loop_num': loop_num
            })
    
    def add_status_message(self, message, color="#cccccc"):
        """Add a status message (non-step log)"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        row_position = self.log_table.rowCount()
        self.log_table.insertRow(row_position)
        
        # Time
        time_item = QTableWidgetItem(timestamp)
        time_item.setForeground(QColor(color))
        self.log_table.setItem(row_position, 0, time_item)
        
        # Message spans columns 1-3
        msg_item = QTableWidgetItem(message)
        msg_item.setForeground(QColor(color))
        self.log_table.setSpan(row_position, 1, 1, 3)
        self.log_table.setItem(row_position, 1, msg_item)
        
        # Auto scroll
        self.log_table.scrollToBottom()
        
        # Store in current session
        if self.current_session:
            self.current_session['logs'].append({
                'type': 'status',
                'message': message,
                'color': color
            })
    
    def clear_logs(self):
        """Clear all log entries and sessions"""
        self.log_table.setRowCount(0)
        self.log_entries.clear()
        self.sessions.clear()
        self.sessions_list.clear()
        self.current_session = None
    
    def closeEvent(self, event):
        """Override close event to hide instead of close"""
        self.hide()
        event.ignore()  # Prevent actual closing

