from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, PrimaryPushButton, PushButton, ToolButton,
    TransparentToolButton, HyperlinkButton, RadioButton, CheckBox, SwitchButton,
    ComboBox, LineEdit, TextEdit, SpinBox, Slider, ProgressBar,
    ProgressRing, IndeterminateProgressRing, CardWidget, SimpleCardWidget,
    ElevatedCardWidget, FluentIcon as FIF, InfoBar, ToggleButton,
    TransparentPushButton, PasswordLineEdit, SearchLineEdit, ScrollArea,
    DropDownPushButton, SplitPushButton, PrimaryToolButton, TransparentTogglePushButton,
    DropDownToolButton, SplitToolButton, CommandButton, HyperlinkCard, HeaderCardWidget,
    SwitchSettingCard, ExpandSettingCard, OptionsSettingCard, RangeSettingCard,
    PushSettingCard, PrimaryPushSettingCard, HyperlinkCard
)
import pyperclip

class WidgetSamplesInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("widgetSamplesInterface")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Header
        title = SubtitleLabel("Mẫu Widget - PySide6-Fluent-Widgets", self)
        main_layout.addWidget(title)
        
        # Create scroll area for samples
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(30)
        
        # Add all widget categories
        self._add_buttons_section(scroll_layout)
        self._add_inputs_section(scroll_layout)
        self._add_cards_section(scroll_layout)
        self._add_progress_section(scroll_layout)
        
        scroll_layout.addStretch(1)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
    
    def _create_category(self, layout, title):
        """Create a category header"""
        label = SubtitleLabel(title, self)
        layout.addWidget(label)
    
    def _create_grid_section(self, layout, items_per_row=4):
        """Create a grid layout for samples"""
        grid = QGridLayout()
        grid.setSpacing(15)
        return grid
    
    def _create_sample_card(self, widget_name, code_snippet, demo_widget=None):
        """Create a compact sample card with demo and copy button"""
        card = SimpleCardWidget(self)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)
        card_layout.setContentsMargins(12, 12, 12, 12)
        
        # Widget name  
        name_label = BodyLabel(widget_name, self)
        name_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        card_layout.addWidget(name_label)
        
        # Demo widget if provided
        if demo_widget:
            card_layout.addWidget(demo_widget)
        
        card_layout.addStretch(1)
        
        # Copy button (compact)
        copy_btn = PushButton(FIF.COPY, "Sao chép", self)
        copy_btn.clicked.connect(lambda: self._copy_code(code_snippet, widget_name))
        card_layout.addWidget(copy_btn)
        
        return card
    
    def _copy_code(self, code, widget_name):
        """Copy code to clipboard and show feedback"""
        pyperclip.copy(code)
        InfoBar.success("Đã sao chép", f"Code mẫu {widget_name}", parent=self.window())
    
    def _add_buttons_section(self, layout):
        """Add button samples in grid"""
        self._create_category(layout, "🔘 Buttons")
        
        grid = self._create_grid_section(layout)
        row, col = 0, 0
        items_per_row = 4
        
        # All button samples
        samples = [
            ("PrimaryPushButton", PrimaryPushButton(FIF.ADD, "Primary", self), 
             "from qfluentwidgets import PrimaryPushButton, FluentIcon as FIF\n\nbtn = PrimaryPushButton(FIF.ADD, \"Primary\")"),
            
            ("PushButton", PushButton(FIF.SETTING, "Normal", self),
             "from qfluentwidgets import PushButton, FluentIcon as FIF\n\nbtn = PushButton(FIF.SETTING, \"Normal\")"),
            
            ("TransparentPushButton", TransparentPushButton(FIF.LIBRARY, "Transparent", self),
             "from qfluentwidgets import TransparentPushButton, FluentIcon as FIF\n\nbtn = TransparentPushButton(FIF.LIBRARY, \"Transparent\")"),
            
            ("TogglePushButton", ToggleButton("Toggle", self),
             "from qfluentwidgets import TogglePushButton\n\nbtn = TogglePushButton(\"Toggle\")"),
            
            ("TransparentTogglePushButton", TransparentTogglePushButton("Toggle", self),
             "from qfluentwidgets import TransparentTogglePushButton\n\nbtn = TransparentTogglePushButton(\"Toggle\")"),
            
            ("DropDownPushButton", DropDownPushButton("Dropdown", self),
             "from qfluentwidgets import DropDownPushButton\n\nbtn = DropDownPushButton(\"Dropdown\")"),
            
            ("SplitPushButton", SplitPushButton("Split", self),
             "from qfluentwidgets import SplitPushButton\n\nbtn = SplitPushButton(\"Split\")"),
            
            ("ToolButton", ToolButton(FIF.DOWNLOAD, self),
             "from qfluentwidgets import ToolButton, FluentIcon as FIF\n\nbtn = ToolButton(FIF.DOWNLOAD)"),
            
            ("PrimaryToolButton", PrimaryToolButton(FIF.SAVE, self),
             "from qfluentwidgets import PrimaryToolButton, FluentIcon as FIF\n\nbtn = PrimaryToolButton(FIF.SAVE)"),
            
            ("TransparentToolButton", TransparentToolButton(FIF.DELETE, self),
             "from qfluentwidgets import TransparentToolButton, FluentIcon as FIF\n\nbtn = TransparentToolButton(FIF.DELETE)"),
            
            ("DropDownToolButton", DropDownToolButton(FIF.MENU, self),
             "from qfluentwidgets import DropDownToolButton, FluentIcon as FIF\n\nbtn = DropDownToolButton(FIF.MENU)"),
            
            ("SplitToolButton", SplitToolButton(FIF.SEND, self),
             "from qfluentwidgets import SplitToolButton, FluentIcon as FIF\n\nbtn = SplitToolButton(FIF.SEND)"),
            
            ("HyperlinkButton", HyperlinkButton("https://github.com", "Link", self),
             "from qfluentwidgets import HyperlinkButton\n\nbtn = HyperlinkButton(\"https://github.com\", \"Link\")"),
        ]
        
        for name, demo, code in samples:
            card = self._create_sample_card(name, code, demo)
            grid.addWidget(card, row, col)
            col += 1
            if col >= items_per_row:
                col = 0
                row += 1
        
        layout.addLayout(grid)
    
    def _add_inputs_section(self, layout):
        """Add input controls in grid"""
        self._create_category(layout, "📝 Input Controls")
        
        grid = self._create_grid_section(layout)
        row, col = 0, 0
        items_per_row = 4
        
        samples = [
            ("LineEdit", LineEdit(self), 
             "from qfluentwidgets import LineEdit\n\ninput = LineEdit()\ninput.setPlaceholderText(\"Text...\")"),
            
            ("PasswordLineEdit", PasswordLineEdit(self),
             "from qfluentwidgets import PasswordLineEdit\n\npwd = PasswordLineEdit()"),
            
            ("SearchLineEdit", SearchLineEdit(self),
             "from qfluentwidgets import SearchLineEdit\n\nsearch = SearchLineEdit()"),
            
            ("ComboBox", ComboBox(self),
             "from qfluentwidgets import ComboBox\n\ncombo = ComboBox()\ncombo.addItems([\"A\", \"B\", \"C\"])"),
            
            ("CheckBox", CheckBox("Check", self),
             "from qfluentwidgets import CheckBox\n\ncheck = CheckBox(\"Check\")"),
            
            ("RadioButton", RadioButton("Radio", self),
             "from qfluentwidgets import RadioButton\n\nradio = RadioButton(\"Radio\")"),
            
            ("SwitchButton", SwitchButton(self),
             "from qfluentwidgets import SwitchButton\n\nswitch = SwitchButton()"),
            
            ("Slider", Slider(Qt.Orientation.Horizontal, self),
             "from qfluentwidgets import Slider\nfrom PySide6.QtCore import Qt\n\nslider = Slider(Qt.Orientation.Horizontal)"),
            
            ("SpinBox", SpinBox(self),
             "from qfluentwidgets import SpinBox\n\nspin = SpinBox()\nspin.setRange(0, 100)"),
        ]
        
        # Set placeholders for line edits
        samples[0][1].setPlaceholderText("Enter text...")
        samples[1][1].setPlaceholderText("Password...")
        samples[2][1].setPlaceholderText("Search...")
        samples[3][1].addItems(["Option 1", "Option 2"])
        samples[7][1].setValue(50)
        
        for name, demo, code in samples:
            card = self._create_sample_card(name, code, demo)
            grid.addWidget(card, row, col)
            col += 1
            if col >= items_per_row:
                col = 0
                row += 1
        
        layout.addLayout(grid)
    
    def _add_cards_section(self, layout):
        """Add card samples"""
        self._create_category(layout, "🃏 Cards & Containers")
        
        grid = self._create_grid_section(layout)
        row, col = 0, 0
        items_per_row = 3
        
        samples = [
            ("CardWidget", None,
             "from qfluentwidgets import CardWidget\n\ncard = CardWidget()\nlayout = QVBoxLayout(card)"),
            
            ("SimpleCardWidget", None,
             "from qfluentwidgets import SimpleCardWidget\n\ncard = SimpleCardWidget()"),
            
            ("ElevatedCardWidget", None,
             "from qfluentwidgets import ElevatedCardWidget\n\ncard = ElevatedCardWidget()"),
            
            ("HeaderCardWidget", None,
             "from qfluentwidgets import HeaderCardWidget\n\ncard = HeaderCardWidget()"),
        ]
        
        for name, demo, code in samples:
            card = self._create_sample_card(name, code, demo)
            grid.addWidget(card, row, col)
            col += 1
            if col >= items_per_row:
                col = 0
                row += 1
        
        layout.addLayout(grid)
    
    def _add_progress_section(self, layout):
        """Add progress indicators"""
        self._create_category(layout, "⏳ Progress Indicators")
        
        grid = self._create_grid_section(layout)
        row, col = 0, 0
        items_per_row = 3
        
        samples = [
            ("ProgressBar", ProgressBar(self),
             "from qfluentwidgets import ProgressBar\n\nprogress = ProgressBar()\nprogress.setValue(60)"),
            
            ("ProgressRing", ProgressRing(self),
             "from qfluentwidgets import ProgressRing\n\nring = ProgressRing()\nring.setValue(75)"),
            
            ("IndeterminateProgressRing", IndeterminateProgressRing(self),
             "from qfluentwidgets import IndeterminateProgressRing\n\nring = IndeterminateProgressRing()"),
        ]
        
        samples[0][1].setValue(60)
        samples[1][1].setValue(75)
        
        for name, demo, code in samples:
            card = self._create_sample_card(name, code, demo)
            grid.addWidget(card, row, col)
            col += 1
            if col >= items_per_row:
                col = 0
                row += 1
        
        layout.addLayout(grid)
