
# Light Theme Stylesheet
LIGHT_STYLESHEET = """
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

/* --- TOOLTIPS --- */
QToolTip {
    background-color: #FFFFFF;
    color: #1A1A1A;
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    padding: 4px;
}

/* --- WINDOWS & DIALOGS --- */
QMainWindow, QDialog, QMessageBox, QInputDialog {
    background-color: #FFFFFF;
    color: #000000;
}

QWidget#CentralWidget {
    background-color: #FFFFFF;
}

/* --- INPUT DIALOGS (QInputDialog, QFileDialog) --- */
QInputDialog {
    background-color: #FFFFFF;
    color: #000000;
}

QInputDialog QLabel {
    background-color: transparent;
    color: #000000;
}

QInputDialog QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    padding: 6px 16px;
    color: #000000;
}

QInputDialog QPushButton:hover {
    background-color: #F5F5F5;
    border-color: #999999;
}

QInputDialog QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    padding: 4px 8px;
    color: #000000;
}

/* --- MESSAGE BOX --- */
QMessageBox {
    background-color: #FFFFFF;
}

QMessageBox QLabel {
    background-color: transparent;
    color: #000000;
}

QMessageBox QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    padding: 6px 16px;
    color: #000000;
    min-width: 60px;
}

QMessageBox QPushButton:hover {
    background-color: #F5F5F5;
}

/* --- MENUS --- */
QMenu {
    background-color: #FFFFFF;
    color: #000000;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 28px 6px 12px;
    background-color: transparent;
    color: #000000;
    border-radius: 4px;
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
    height: 40px;
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
    border: 2px solid #000000;
    border-radius: 4px;
    selection-background-color: #E5F3FF;
    selection-color: #000000;
    outline: none;
    padding: 0px;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #0078D4;
    color: #FFFFFF;
    border: 1px solid #000000;
}
QComboBox QAbstractItemView::item {
    padding: 4px 8px;
    border: none;
    background-color: transparent;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #E5F3FF;
    border: none;
}

/* --- GROUP BOX --- */
QGroupBox {
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    margin-top: 1.5em;
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
    border-radius: 8px;
}
QCheckBox::indicator {
    border-radius: 3px;
}
QRadioButton::indicator:checked {
    background-color: #0078D4;
    border: 1px solid #0078D4;
}
QCheckBox::indicator{
    background-color: #0078D4;
    border: 1px solid #0078D4;
}

/* --- LIST WIDGET --- */
QListWidget {
    background-color: #FFFFFF;
    border: none;
    border-radius: 0px;
}
QListWidget::item {
    padding: 5px;
    padding-left: 8px;
    height: 40px;
    border-bottom: 1px solid #E0E0E0;
    color: #1A1A1A;
}
QListWidget::item:hover {
    background-color: #F5F5F5;
}
QListWidget::item:selected {
    background-color: #E5F3FF;
    color: #1976D2;
}

/* --- DIALOG TITLE BAR FIX --- */
QInputDialog QWidget {
    background-color: #FFFFFF;
}
"""

# Dark Theme Stylesheet
DARK_STYLESHEET = """
/* --- GLOBAL RESET --- */
* {
    background: transparent;
    color: #E0E0E0;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
    selection-background-color: #0078D4;
    selection-color: #FFFFFF;
    outline: none;
}

/* --- TOOLTIPS --- */
QToolTip {
    background-color: #2B2B2B;
    color: #E0E0E0;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 4px;
}

/* --- WINDOWS & DIALOGS --- */
QMainWindow, QDialog, QMessageBox, QInputDialog {
    background-color: #1E1E1E;
    color: #E0E0E0;
}

QWidget#CentralWidget {
    background-color: #1E1E1E;
}

/* --- INPUT DIALOGS (QInputDialog, QFileDialog) --- */
QInputDialog {
    background-color: #1E1E1E;
    color: #E0E0E0;
}

QInputDialog QLabel {
    background-color: transparent;
    color: #E0E0E0;
}

QInputDialog QPushButton {
    background-color: #2B2B2B;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 6px 16px;
    color: #E0E0E0;
}

QInputDialog QPushButton:hover {
    background-color: #3A3A3A;
    border-color: #666666;
}

QInputDialog QLineEdit {
    background-color: #2B2B2B;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 4px 8px;
    color: #E0E0E0;
}

/* --- MESSAGE BOX --- */
QMessageBox {
    background-color: #1E1E1E;
}

QMessageBox QLabel {
    background-color: transparent;
    color: #E0E0E0;
}

QMessageBox QPushButton {
    background-color: #2B2B2B;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 6px 16px;
    color: #E0E0E0;
    min-width: 60px;
}

QMessageBox QPushButton:hover {
    background-color: #3A3A3A;
}

/* --- MENUS --- */
QMenu {
    background-color: #2B2B2B;
    color: #E0E0E0;
    border: 1px solid #444444;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 28px 6px 12px;
    background-color: transparent;
    color: #E0E0E0;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #3A3A3A;
    color: #FFFFFF;
}
QMenu::separator {
    height: 1px;
    background: #444444;
    margin: 4px 0;
}

/* --- TABLE VIEW --- */
QTableView {
    background-color: #1E1E1E;
    border: 1px solid #444444;
    gridline-color: #3A3A3A;
    selection-background-color: #0078D4;
    selection-color: #FFFFFF;
}
QHeaderView::section {
    background-color: #2B2B2B;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #444444;
    border-right: 1px solid #3A3A3A;
    font-weight: bold;
    color: #E0E0E0;
}
QTableView::item {
    padding: 5px;
    height: 40px;
    color: #E0E0E0;
}

/* --- BUTTONS --- */
QPushButton {
    background-color: #2B2B2B;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 6px 16px;
    color: #E0E0E0;
    min-width: 60px;
}
QPushButton:hover {
    background-color: #3A3A3A;
    border-color: #666666;
}
QPushButton:pressed {
    background-color: #4A4A4A;
    border-color: #666666;
}

/* --- INPUTS --- */
QLineEdit, QSpinBox, QComboBox {
    background-color: #2B2B2B;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 4px 8px;
    color: #E0E0E0;
    min-height: 20px;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #0078D4;
    background-color: #2B2B2B;
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
    background-color: #2B2B2B;
    border: 2px solid #444444;
    border-radius: 4px;
    selection-background-color: #0078D4;
    selection-color: #FFFFFF;
    outline: none;
    padding: 0px;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #0078D4;
    color: #FFFFFF;
    border: 1px solid #444444;
}
QComboBox QAbstractItemView::item {
    padding: 4px 8px;
    border: none;
    background-color: transparent;
    color: #E0E0E0;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #3A3A3A;
    border: none;
}

/* --- GROUP BOX --- */
QGroupBox {
    border: 1px solid #444444;
    border-radius: 4px;
    margin-top: 1.5em;
    padding-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #AAAAAA;
    font-weight: bold;
}

/* --- LABELS & OTHERS --- */
QLabel {
    color: #E0E0E0;
    background: transparent;
}
QCheckBox, QRadioButton {
    spacing: 8px;
    color: #E0E0E0;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #444444;
    background: #2B2B2B;
    border-radius: 8px;
}
QCheckBox::indicator {
    border-radius: 3px;
}
QRadioButton::indicator:checked {
    background-color: #0078D4;
    border: 1px solid #0078D4;
}
QCheckBox::indicator:checked {
    background-color: #0078D4;
    border: 1px solid #0078D4;
}

/* --- LIST WIDGET --- */
QListWidget {
    background-color: #1E1E1E;
    border: none;
    border-radius: 0px;
}
QListWidget::item {
    padding: 5px;
    padding-left: 8px;
    height: 40px;
    border-bottom: 1px solid #3A3A3A;
    color: #E0E0E0;
}
QListWidget::item:hover {
    background-color: #3A3A3A;
}
QListWidget::item:selected {
    background-color: #0078D4;
    color: #FFFFFF;
}

/* --- DIALOG TITLE BAR FIX --- */
QInputDialog QWidget {
    background-color: #1E1E1E;
}
"""

# Keep backward compatibility
MAIN_STYLESHEET = LIGHT_STYLESHEET

