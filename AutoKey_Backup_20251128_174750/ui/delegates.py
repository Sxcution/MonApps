from PyQt6.QtWidgets import QStyledItemDelegate, QLineEdit, QSpinBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator

class ActionDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        text = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setText(text)

    def setModelData(self, editor, model, index):
        text = editor.text()
        model.setData(index, text, Qt.ItemDataRole.EditRole)

class NumberDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        validator = QIntValidator(0, 999999, editor)
        editor.setValidator(validator)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        # Remove 's' if present for editing
        if isinstance(value, str) and value.endswith('s'):
            value = value[:-1]
        editor.setText(str(value))

    def setModelData(self, editor, model, index):
        text = editor.text()
        # Add 's' back for display if needed, but model usually stores raw data.
        # Let's store raw number in model for Delay, and format it in display.
        # But current model stores strings. Let's stick to string "X.Xs" for now to match existing logic,
        # or better, change model to store raw numbers.
        # For now, let's just save the text. The main window logic will handle parsing.
        model.setData(index, text, Qt.ItemDataRole.EditRole)
