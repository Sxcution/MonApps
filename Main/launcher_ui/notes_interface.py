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
    
    def init_ui(self):
        """Initialize the interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Notes widget will be embedded here when needed
        # This is handled by main_window.py's embed_notes() method
    
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
