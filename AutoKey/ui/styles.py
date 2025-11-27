
MAIN_STYLESHEET = """
/* --- GLOBAL RESET --- */
* {
    background: transparent; /* Let the Window's white palette show through */
    color: #1A1A1A;          /* High contrast dark text (Jibit style) */
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
    selection-background-color: #0078D4;
    selection-color: #FFFFFF;
}

/* --- MAIN WINDOW & CONTAINERS --- */
QMainWindow, QWidget#CentralWidget {
    background-color: #FFFFFF;
}

/* --- TITLE BAR --- */
#TitleBar {
    background-color: #FFFFFF;
    min-height: 32px;
}
/* Bottom border for separation */
#TitleBar > QWidget { 
    border-bottom: 1px solid #E5E5E5; 
}

/* --- BUTTONS (Clean Outline Style) --- */
QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #D1D1D1;
    border-radius: 4px;
    padding: 5px 12px;
    color: #1A1A1A;
}
QPushButton:hover {
    background-color: #F5F5F5;
    border-color: #000000;
}
QPushButton:pressed {
    background-color: #E0E0E0;
}

/* --- INPUTS --- */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox {
    background-color: #FAFAFA;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    padding: 4px;
    color: #000000;
}
QLineEdit:focus, QTextEdit:focus {
    background-color: #FFFFFF;
    border: 1px solid #0078D4;
}

/* --- LISTS & TABLES --- */
QListWidget, QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E5;
    gridline-color: #F0F0F0;
}
QHeaderView::section {
    background-color: #F9F9F9;
    border: none;
    border-bottom: 1px solid #E5E5E5;
    padding: 4px;
    font-weight: bold;
}

/* --- MENUS --- */
QMenu {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px 6px 12px;
    background-color: transparent;
    color: #1A1A1A;
}
QMenu::item:selected {
    background-color: #E5F3FF;
    color: #000000;
}
"""
