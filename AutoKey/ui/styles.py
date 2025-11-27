
WHITE_THEME = """
QMainWindow {
    background-color: #ffffff;
    color: #333333;
}

QWidget {
    color: #333333;
}

QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e0e0e0;
    spacing: 5px;
    padding: 2px;
}

QToolBar::separator {
    background-color: #e0e0e0;
    width: 1px;
    margin: 5px 0px;
}

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 8px;
    color: #333333;
    font-weight: bold;
    font-size: 13px;
}

QToolButton:hover {
    background-color: #f0f8ff; /* AliceBlue */
    border: 1px solid #cceeff;
}

QToolButton:pressed {
    background-color: #e0f0ff;
}

QToolButton::menu-indicator {
    image: none;
    width: 0px;
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
