
WHITE_THEME = """
QMainWindow {
    background-color: #ffffff;
    color: #333333;
}

QWidget {
    color: #333333;
}

QToolBar {
    background-color: #f0f0f0;
    border-bottom: 1px solid #d0d0d0;
    spacing: 10px;
    padding: 5px;
}

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 5px;
    color: #333333;
    font-weight: bold;
}

QToolButton:hover {
    background-color: #e0e0e0;
    border: 1px solid #c0c0c0;
}

QToolButton:pressed {
    background-color: #d0d0d0;
}

QToolButton::menu-indicator {
    image: none;
}

QTableView {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #d0d0d0;
    gridline-color: #e0e0e0;
    selection-background-color: #e6f3ff;
    selection-color: #000000;
}

QHeaderView::section {
    background-color: #f8f8f8;
    color: #333333;
    padding: 4px;
    border: 1px solid #e0e0e0;
    font-weight: bold;
}

QMenu {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #d0d0d0;
}

QMenu::item {
    padding: 5px 20px;
}

QMenu::item:selected {
    background-color: #e6f3ff;
    color: #000000;
}
"""
