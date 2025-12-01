from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import BodyLabel

class ToolsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("toolsInterface")
        
        # Empty interface - no content
        # This nav item is just used for expanding sub-menu (AutoKey, Android)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
