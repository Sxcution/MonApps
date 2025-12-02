"""
Notes Interface for Main Launcher
Embeds the Notes module with Fluent UI integration
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt
import sys
import os


class NotesInterface(QWidget):
    """Notes interface for Main launcher."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("notesInterface")
        self.embedded_notes = None
        self.init_ui()
        self.setup_styles()  # ✅ Apply dark theme styles
    
    def init_ui(self):
        """Initialize the interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Notes widget will be embedded here when needed
        # This is handled by main_window.py's embed_notes() method
    
    def setup_styles(self):
        """Thiết lập màu sắc chuẩn Dark Mode cho Notes"""
        
        # Style for text editor (if exists in embedded widget)
        style_editor = """
            QTextEdit, QPlainTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #454545;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                selection-background-color: #0078d4;
                selection-color: #ffffff;
            }
            QTextEdit:focus, QPlainTextEdit:focus {
                border: 1px solid #0078d4;
            }
        """
        
        # Style for context menus
        style_menu = """
            QMenu {
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                background-color: transparent;
                color: #ffffff;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QMenu::icon {
                padding-left: 8px;
            }
        """
        
        # Apply combined styles to the interface
        self.setStyleSheet(style_editor + style_menu)
    
    def embed_notes_widget(self):
        """Embed the Notes widget from Apps/Notes."""
        if self.embedded_notes is not None:
            # Already embedded
            return
        
        try:
            # Add Apps to path (Notes is now at Apps/Notes, not Android_Tool/modules)
            apps_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                "Apps"
            )
            if apps_path not in sys.path:
                sys.path.insert(0, apps_path)
            
            # Import Notes module
            from Notes.notes_module import NotesWidget
            
            # Create Notes widget
            self.embedded_notes = NotesWidget()
            self.embedded_notes.setObjectName("embeddedNotes")
            
            # Add to layout
            self.layout().addWidget(self.embedded_notes)
            
            print("✓ Notes widget embedded successfully")
            
        except Exception as e:
            import traceback
            print(f"❌ Error embedding Notes widget:")
            traceback.print_exc()
    
    def clear_notes_widget(self):
        """Clear the embedded Notes widget."""
        if self.embedded_notes:
            self.layout().removeWidget(self.embedded_notes)
            self.embedded_notes.deleteLater()
            self.embedded_notes = None
            print("✓ Notes widget cleared")
