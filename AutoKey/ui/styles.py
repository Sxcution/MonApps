
MAIN_STYLESHEET = """
/* --- GLOBAL RESET --- */
* {
    background: transparent;
    color: #1A1A1A;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
    selection-background-color: #0078D4;
    selection-color: #FFFFFF;
    outline: none;
}

/* --- WINDOWS & DIALOGS --- */
QMainWindow, QDialog {
    background-color: #FFFFFF;
}

QWidget#CentralWidget {
    background-color: #FFFFFF;
}

/* --- MENUS --- */
QMenu {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 28px 6px 12px;
    background-color: transparent;
    color: #1A1A1A;
    border-radius: 3px;
}
QMenu::item:selected {
    background-color: #E5F3FF;
    color: #000000;
}
QMenu::separator {
    height: 1px;
    background: #E0E0E0;
    margin: 4px 0;
}

/* --- TABLE VIEW --- */
QTableView {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    gridline-color: #E0E0E0;
    selection-background-color: #E5F3FF;
    selection-color: #000000;
}
QHeaderView::section {
    background-color: #F5F5F5;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #CCCCCC;
    border-right: 1px solid #E0E0E0;
    font-weight: bold;
    color: #333333;
}
QTableView::item {
    padding: 5px;
    height: 40px; /* Increase row height for icons */
}

/* --- BUTTONS --- */
QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    padding: 6px 16px;
    color: #1A1A1A;
    min-width: 60px;
}
QPushButton:hover {
    background-color: #F5F5F5;
    border-color: #999999;
}
QPushButton:pressed {
    background-color: #E5E5E5;
    border-color: #999999;
}

/* --- INPUTS --- */
QLineEdit, QSpinBox, QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    padding: 4px 8px;
    color: #1A1A1A;
    min-height: 20px;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #0078D4;
    background-color: #FFFFFF;
}

/* Hide SpinBox Up/Down Buttons */
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    width: 0px;
    height: 0px;
    border: none;
    background: transparent;
}

/* --- COMBO BOX --- */
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 0px;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
}
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    selection-background-color: #E5F3FF;
    selection-color: #000000;
}

/* --- GROUP BOX --- */
QGroupBox {
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    margin-top: 1.5em; /* leave space at the top for the title */
    padding-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #555555;
    font-weight: bold;
}

/* --- LABELS & OTHERS --- */
QLabel {
    color: #1A1A1A;
    background: transparent;
}
QCheckBox, QRadioButton {
    spacing: 8px;
    color: #1A1A1A;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #CCCCCC;
    background: #FFFFFF;
    border-radius: 8px; /* Circular for radio */
}
QCheckBox::indicator {
    border-radius: 3px; /* Square for checkbox */
}
QRadioButton::indicator:checked {
    background-color: #0078D4;
    border: 1px solid #0078D4;
    image: none; /* We can use a simple dot if needed, or just color */
}
QCheckBox::indicator:checked {
    background-color: #0078D4;
    border: 1px solid #0078D4;
}
/* Simple dot for radio checked */
QRadioButton::indicator:checked::after {
    content: "";
    display: block;
    width: 8px;
    height: 8px;
    margin: 3px;
    background: white;
    border-radius: 4px;
}
"""
