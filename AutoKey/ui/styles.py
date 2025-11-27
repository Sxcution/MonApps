
MAIN_STYLESHEET = """

/* --- Main Container --- */

QMainWindow, QDialog {
    background-color: #FFFFFF;
}



/* --- Base Widget Styling --- */

QWidget {
    background-color: #FFFFFF;
    color: #000000;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}



/* --- Title Bar (Custom) --- */

#TitleBar, QFrame#TitleBar {
    background-color: #F5F5F5; /* Slightly darker header */
    border-bottom: 1px solid #E0E0E0;
}
#TitleBar QLabel {
    color: #000000;
    font-weight: bold;
}
/* Title Bar Buttons */
#btnMinimize, #btnMaximize, #btnClose {
    background-color: transparent;
    color: #333333;
    border: none;
    font-weight: bold;
}
#btnClose:hover {
    background-color: #E81123;
    color: #FFFFFF;
}
#btnMinimize:hover, #btnMaximize:hover {
    background-color: #E0E0E0;
}



/* --- Input Fields --- */

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    padding: 5px;
    color: #000000;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #0078D4; /* Blue Focus */
}



/* --- Buttons --- */

QPushButton {
    background-color: #F0F0F0;
    border: 1px solid #D0D0D0;
    border-radius: 4px;
    padding: 6px 12px;
    color: #000000;
}
QPushButton:hover {
    background-color: #E5E5E5;
    border-color: #B0B0B0;
}
QPushButton:pressed {
    background-color: #D5D5D5;
}



/* --- Lists & Tables --- */

QListWidget, QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    alternate-background-color: #FAFAFA;
}
QListWidget::item:selected, QTableWidget::item:selected {
    background-color: #E5F3FF;
    color: #000000;
    border: none;
}
QHeaderView::section {
    background-color: #F7F7F7;
    border: none;
    border-bottom: 1px solid #E0E0E0;
    padding: 4px;
}
"""
