"""
Standalone test for SnippingWidget - NO dialog, NO main window
Just pure snipping tool to see if it works
"""
import sys
from PyQt6.QtWidgets import QApplication
from utils.snipping_tool import SnippingWidget

def main():
    app = QApplication(sys.argv)
    
    print("=" * 50)
    print("STANDALONE SNIPPING TOOL TEST")
    print("=" * 50)
    
    snipper = SnippingWidget()
    print("Snipper created, showing now...")
    snipper.show()
    snipper.raise_()
    snipper.activateWindow()
    print("Snipper should be visible now!")
    print("Press ESC to close, or drag to select region")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
