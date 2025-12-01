import sys
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget, QTextEdit, QLabel, QLineEdit
from PySide6.QtCore import Qt
try:
    from qfluentwidgets import TextEdit as FluentTextEdit, LineEdit as FluentLineEdit
except ImportError:
    FluentTextEdit = QTextEdit
    FluentLineEdit = QLineEdit

class AutoSaveTextEdit(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, True)

class DebugWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IME Debugger")
        self.resize(600, 500)
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("1. Standard QLineEdit (Check this first):"))
        self.le1 = QLineEdit()
        layout.addWidget(self.le1)
        
        layout.addWidget(QLabel("2. Standard QTextEdit:"))
        self.te1 = QTextEdit()
        layout.addWidget(self.te1)
        
        layout.addWidget(QLabel("3. Fluent TextEdit:"))
        self.te2 = FluentTextEdit()
        layout.addWidget(self.te2)
        
        layout.addWidget(QLabel("4. AutoSaveTextEdit (My Subclass):"))
        self.te3 = AutoSaveTextEdit()
        layout.addWidget(self.te3)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = DebugWindow()
    w.show()
    print("Debug window opened. Please try typing Vietnamese in all 4 boxes.")
    sys.exit(app.exec())
