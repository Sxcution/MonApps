
MAIN_STYLESHEET = """
/* --- FORCE OPAQUE BACKGROUND --- */
QMainWindow, QDialog, #CentralWidget {
    background-color: #FFFFFF;
    color: #000000;
}

/* --- Title Bar --- */
#TitleBar {
    background-color: #F3F3F3; /* Light Gray Header */
    border-bottom: 1px solid #E5E5E5;
}
#TitleBar QLabel {
    color: #000000;
    font-weight: bold;
}

/* --- Base Widget Styling --- */
QWidget {
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
    color: #000000;
}

/* --- Buttons, Inputs, Tables (Keep your existing styles or use below) --- */
QPushButton {
    background-color: #F0F0F0;
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    color: #000000;
    padding: 5px 10px;
}
QLineEdit, QTableView {
    background-color: #FFFFFF;
    color: #000000;
    border: 1px solid #CCCCCC;
    gridline-color: #EEEEEE;
}
QHeaderView::section {
    background-color: #FAFAFA;
    color: #000000;
    border: none;
    border-bottom: 1px solid #CCCCCC;
}
"""
