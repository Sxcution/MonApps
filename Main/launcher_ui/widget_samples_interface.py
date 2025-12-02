from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QAction
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, PrimaryPushButton, PushButton, ToolButton,
    TransparentToolButton, HyperlinkButton, RadioButton, CheckBox, SwitchButton,
    ComboBox, LineEdit, TextEdit, SpinBox, Slider, ProgressBar,
    ProgressRing, IndeterminateProgressRing, CardWidget, SimpleCardWidget,
    ElevatedCardWidget, FluentIcon as FIF, InfoBar, ToggleButton,
    TransparentPushButton, PasswordLineEdit, SearchLineEdit, ScrollArea,
    DropDownPushButton, SplitPushButton, PrimaryToolButton, TransparentTogglePushButton,
    DropDownToolButton, SplitToolButton, HeaderCardWidget,
    SwitchSettingCard, PushSettingCard, PrimaryPushSettingCard,
    RoundMenu, PillPushButton, StrongBodyLabel, TitleLabel,
    PlainTextEdit, DoubleSpinBox, CompactSpinBox, CompactDoubleSpinBox,
    TimeEdit, DateEdit, DateTimeEdit, CompactTimeEdit, CompactDateEdit, CompactDateTimeEdit,
    ExpandSettingCard, OptionsSettingCard, RangeSettingCard, ColorSettingCard,
    InfoBadge, StateToolTip, ToolTip, TeachingTip,
    SegmentedWidget, Pivot, BreadcrumbBar, CommandBar, CommandBarView,
    ListWidget, TreeWidget, TableWidget, FlowLayout,
    AvatarWidget, IconWidget, ImageLabel, PixmapLabel,
    TogglePushButton, HyperlinkCard, ElevatedCardWidget, TransparentToggleToolButton
)
import pyperclip

class WidgetSamplesInterface(QWidget):
    """
    Giao diện mẫu trưng bày đầy đủ các widget của PySide6-Fluent-Widgets.
    Hỗ trợ copy tên widget và code mẫu.
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("widgetSamplesInterface")
        
        # Main layout - Reduced margins for full width
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create scroll area for samples (with horizontal scrollbar enabled)
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Enable horizontal scroll
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea {border: none; background: transparent;}")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        
        # Add all widget categories
        self._add_buttons_section(scroll_layout)
        self._add_advanced_buttons_section(scroll_layout)
        self._add_inputs_section(scroll_layout)
        self._add_text_inputs_section(scroll_layout)
        self._add_datetime_section(scroll_layout)
        self._add_cards_section(scroll_layout)
        self._add_progress_section(scroll_layout)
        self._add_settings_cards_section(scroll_layout)
        self._add_badges_tooltips_section(scroll_layout)
        self._add_navigation_section(scroll_layout)
        
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
        """Create a compact sample card with demo and SplitToolButton for copy"""
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
        
        # SplitToolButton: Main click = Copy name, Arrow click = Menu with "Copy Code"
        copy_btn = SplitToolButton(FIF.COPY, self)
        copy_btn.setToolTip(f"Click để copy tên: {widget_name}")
        
        # Main button action: Copy widget name
        copy_btn.clicked.connect(lambda: self._copy_name(widget_name))
        
        # Flyout menu with "Copy Code" option
        copy_menu = RoundMenu(parent=self)
        copy_code_action = QAction(FIF.CODE.icon(), "Copy Code", self)
        copy_code_action.triggered.connect(lambda: self._copy_code(code_snippet, widget_name))
        copy_menu.addAction(copy_code_action)
        copy_btn.setFlyout(copy_menu)
        
        card_layout.addWidget(copy_btn)
        
        return card
    
    def _copy_name(self, widget_name):
        """Copy widget name to clipboard"""
        pyperclip.copy(widget_name)
        InfoBar.success("Đã sao chép tên", f"{widget_name}", parent=self.window())
    
    def _copy_code(self, code, widget_name):
        """Copy code to clipboard and show feedback"""
        pyperclip.copy(code)
        InfoBar.success("Đã sao chép code", f"Code mẫu {widget_name}", parent=self.window())
    
    def _add_buttons_section(self, layout):
        """Add basic button samples in grid"""
        self._create_category(layout, "🔘 Basic Buttons")
        
        grid = self._create_grid_section(layout)
        row, col = 0, 0
        items_per_row = 4
        
        samples = [
            ("PrimaryPushButton", PrimaryPushButton(FIF.ADD, "Primary", self), 
             "from qfluentwidgets import PrimaryPushButton, FluentIcon as FIF\n\nbtn = PrimaryPushButton(FIF.ADD, \"Primary\")"),
            
            ("PushButton", PushButton(FIF.SETTING, "Normal", self),
             "from qfluentwidgets import PushButton, FluentIcon as FIF\n\nbtn = PushButton(FIF.SETTING, \"Normal\")"),
            
            ("TransparentPushButton", TransparentPushButton(FIF.LIBRARY, "Transparent", self),
             "from qfluentwidgets import TransparentPushButton, FluentIcon as FIF\n\nbtn = TransparentPushButton(FIF.LIBRARY, \"Transparent\")"),
            
            ("TogglePushButton", TogglePushButton("Toggle", self),
             "from qfluentwidgets import TogglePushButton\n\nbtn = TogglePushButton(\"Toggle\")"),
            
            ("TransparentTogglePushButton", TransparentTogglePushButton("Toggle", self),
             "from qfluentwidgets import TransparentTogglePushButton\n\nbtn = TransparentTogglePushButton(\"Toggle\")"),
            
            ("ToolButton", ToolButton(FIF.DOWNLOAD, self),
             "from qfluentwidgets import ToolButton, FluentIcon as FIF\n\nbtn = ToolButton(FIF.DOWNLOAD)"),
            
            ("PrimaryToolButton", PrimaryToolButton(FIF.SAVE, self),
             "from qfluentwidgets import PrimaryToolButton, FluentIcon as FIF\n\nbtn = PrimaryToolButton(FIF.SAVE)"),
            
            ("TransparentToolButton", TransparentToolButton(FIF.DELETE, self),
             "from qfluentwidgets import TransparentToolButton, FluentIcon as FIF\n\nbtn = TransparentToolButton(FIF.DELETE)"),
            
            ("HyperlinkButton", HyperlinkButton("https://github.com", "Link", self),
             "from qfluentwidgets import HyperlinkButton\n\nbtn = HyperlinkButton(\"https://github.com\", \"Link\")"),
            
            ("PillPushButton", PillPushButton("Tag", self),
             "from qfluentwidgets import PillPushButton\n\nbtn = PillPushButton(\"Tag\")"),
        ]
        
        for name, demo, code in samples:
            card = self._create_sample_card(name, code, demo)
            grid.addWidget(card, row, col)
            col += 1
            if col >= items_per_row:
                col = 0
                row += 1
        
        layout.addLayout(grid)
    
    def _add_advanced_buttons_section(self, layout):
        """Add advanced buttons with menus"""
        self._create_category(layout, "⚙️ Advanced Buttons (Menu)")
        
        grid = self._create_grid_section(layout)
        row, col = 0, 0
        items_per_row = 4
        
        dropdown_btn = DropDownPushButton(FIF.MAIL, "Dropdown", self)
        dropdown_menu = RoundMenu(parent=self)
        dropdown_menu.addAction(QAction(FIF.SEND.icon(), "Send", self))
        dropdown_menu.addAction(QAction(FIF.SHARE.icon(), "Share", self))
        dropdown_btn.setMenu(dropdown_menu)
        
        split_btn = SplitPushButton(FIF.SAVE, "Split", self)
        split_menu = RoundMenu(parent=self)
        split_menu.addAction(QAction(FIF.SAVE.icon(), "Save", self))
        split_menu.addAction(QAction(FIF.SAVE_AS.icon(), "Save As", self))
        split_btn.setFlyout(split_menu)
        
        dropdown_tool = DropDownToolButton(FIF.MENU, self)
        dropdown_tool_menu = RoundMenu(parent=self)
        dropdown_tool_menu.addAction(QAction(FIF.EDIT.icon(), "Edit", self))
        dropdown_tool.setMenu(dropdown_tool_menu)
        
        split_tool = SplitToolButton(FIF.SEND, self)
        split_tool_menu = RoundMenu(parent=self)
        split_tool_menu.addAction(QAction(FIF.SEND.icon(), "Send Now", self))
        split_tool.setFlyout(split_tool_menu)
        
        samples = [
            ("DropDownPushButton", dropdown_btn,
             "from qfluentwidgets import DropDownPushButton, RoundMenu, FluentIcon as FIF\nfrom PySide6.QtGui import QAction\n\nbtn = DropDownPushButton(FIF.MAIL, \"Dropdown\")\nmenu = RoundMenu(parent=self)\nmenu.addAction(QAction(FIF.SEND.icon(), \"Send\", self))\nbtn.setMenu(menu)"),
            
            ("SplitPushButton", split_btn,
             "from qfluentwidgets import SplitPushButton, RoundMenu, FluentIcon as FIF\nfrom PySide6.QtGui import QAction\n\nbtn = SplitPushButton(FIF.SAVE, \"Split\")\nmenu = RoundMenu(parent=self)\nmenu.addAction(QAction(FIF.SAVE.icon(), \"Save\", self))\nbtn.setFlyout(menu)"),
            
            ("DropDownToolButton", dropdown_tool,
             "from qfluentwidgets import DropDownToolButton, RoundMenu, FluentIcon as FIF\nfrom PySide6.QtGui import QAction\n\nbtn = DropDownToolButton(FIF.MENU)\nmenu = RoundMenu(parent=self)\nmenu.addAction(QAction(FIF.EDIT.icon(), \"Edit\", self))\nbtn.setMenu(menu)"),
            
            ("SplitToolButton", split_tool,
             "from qfluentwidgets import SplitToolButton, RoundMenu, FluentIcon as FIF\nfrom PySide6.QtGui import QAction\n\nbtn = SplitToolButton(FIF.SEND)\nmenu = RoundMenu(parent=self)\nmenu.addAction(QAction(FIF.SEND.icon(), \"Send\", self))\nbtn.setFlyout(menu)"),
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
        
        line_edit = LineEdit(self)
        line_edit.setPlaceholderText("Enter text...")
        
        pwd_edit = PasswordLineEdit(self)
        pwd_edit.setPlaceholderText("Password...")
        
        search_edit = SearchLineEdit(self)
        search_edit.setPlaceholderText("Search...")
        
        combo = ComboBox(self)
        combo.addItems(["Option 1", "Option 2", "Option 3"])
        
        checkbox = CheckBox("Check", self)
        radio = RadioButton("Radio", self)
        switch = SwitchButton(self)
        
        slider = Slider(Qt.Orientation.Horizontal, self)
        slider.setValue(50)
        
        spinbox = SpinBox(self)
        spinbox.setRange(0, 100)
        spinbox.setValue(50)
        
        compact_spin = CompactSpinBox(self)
        compact_spin.setRange(0, 100)
        
        double_spin = DoubleSpinBox(self)
        double_spin.setRange(0.0, 100.0)
        double_spin.setValue(50.5)
        
        compact_double = CompactDoubleSpinBox(self)
        compact_double.setRange(0.0, 100.0)
        
        samples = [
            ("LineEdit", line_edit, 
             "from qfluentwidgets import LineEdit\n\ninput = LineEdit()\ninput.setPlaceholderText(\"Text...\")"),
            
            ("PasswordLineEdit", pwd_edit,
             "from qfluentwidgets import PasswordLineEdit\n\npwd = PasswordLineEdit()"),
            
            ("SearchLineEdit", search_edit,
             "from qfluentwidgets import SearchLineEdit\n\nsearch = SearchLineEdit()"),
            
            ("ComboBox", combo,
             "from qfluentwidgets import ComboBox\n\ncombo = ComboBox()\ncombo.addItems([\"A\", \"B\", \"C\"])"),
            
            ("CheckBox", checkbox,
             "from qfluentwidgets import CheckBox\n\ncheck = CheckBox(\"Check\")"),
            
            ("RadioButton", radio,
             "from qfluentwidgets import RadioButton\n\nradio = RadioButton(\"Radio\")"),
            
            ("SwitchButton", switch,
             "from qfluentwidgets import SwitchButton\n\nswitch = SwitchButton()"),
            
            ("Slider", slider,
             "from qfluentwidgets import Slider\nfrom PySide6.QtCore import Qt\n\nslider = Slider(Qt.Orientation.Horizontal)"),
            
            ("SpinBox", spinbox,
             "from qfluentwidgets import SpinBox\n\nspin = SpinBox()\nspin.setRange(0, 100)"),
            
            ("CompactSpinBox", compact_spin,
             "from qfluentwidgets import CompactSpinBox\n\nspin = CompactSpinBox()\nspin.setRange(0, 100)"),
            
            ("DoubleSpinBox", double_spin,
             "from qfluentwidgets import DoubleSpinBox\n\nspin = DoubleSpinBox()\nspin.setRange(0.0, 100.0)"),
            
            ("CompactDoubleSpinBox", compact_double,
             "from qfluentwidgets import CompactDoubleSpinBox\n\nspin = CompactDoubleSpinBox()"),
        ]
        
        for name, demo, code in samples:
            card = self._create_sample_card(name, code, demo)
            grid.addWidget(card, row, col)
            col += 1
            if col >= items_per_row:
                col = 0
                row += 1
        
        layout.addLayout(grid)
    
    def _add_text_inputs_section(self, layout):
        """Add text input widgets"""
        self._create_category(layout, "📄 Text Inputs")
        
        grid = self._create_grid_section(layout)
        row, col = 0, 0
        items_per_row = 3
        
        text_edit = TextEdit(self)
        text_edit.setPlaceholderText("Rich text editor...")
        text_edit.setFixedHeight(80)
        
        plain_text = PlainTextEdit(self)
        plain_text.setPlaceholderText("Plain text editor...")
        plain_text.setFixedHeight(80)
        
        samples = [
            ("TextEdit", text_edit,
             "from qfluentwidgets import TextEdit\n\ntext = TextEdit()\ntext.setPlaceholderText(\"Rich text...\")"),
            
            ("PlainTextEdit", plain_text,
             "from qfluentwidgets import PlainTextEdit\n\ntext = PlainTextEdit()\ntext.setPlaceholderText(\"Plain text...\")"),
        ]
        
        for name, demo, code in samples:
            card = self._create_sample_card(name, code, demo)
            grid.addWidget(card, row, col)
            col += 1
            if col >= items_per_row:
                col = 0
                row += 1
        
        layout.addLayout(grid)
    
    def _add_datetime_section(self, layout):
        """Add date/time widgets"""
        self._create_category(layout, "📅 Date & Time")
        
        grid = self._create_grid_section(layout)
        row, col = 0, 0
        items_per_row = 4
        
        samples = [
            ("TimeEdit", TimeEdit(self),
             "from qfluentwidgets import TimeEdit\n\ntime = TimeEdit()"),
            
            ("CompactTimeEdit", CompactTimeEdit(self),
             "from qfluentwidgets import CompactTimeEdit\n\ntime = CompactTimeEdit()"),
            
            ("DateEdit", DateEdit(self),
             "from qfluentwidgets import DateEdit\n\ndate = DateEdit()"),
            
            ("CompactDateEdit", CompactDateEdit(self),
             "from qfluentwidgets import CompactDateEdit\n\ndate = CompactDateEdit()"),
            
            ("DateTimeEdit", DateTimeEdit(self),
             "from qfluentwidgets import DateTimeEdit\n\ndt = DateTimeEdit()"),
            
            ("CompactDateTimeEdit", CompactDateTimeEdit(self),
             "from qfluentwidgets import CompactDateTimeEdit\n\ndt = CompactDateTimeEdit()"),
        ]
        
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
        
        progress_bar = ProgressBar(self)
        progress_bar.setValue(60)
        
        progress_ring = ProgressRing(self)
        progress_ring.setValue(75)
        
        indeterminate_ring = IndeterminateProgressRing(self)
        
        samples = [
            ("ProgressBar", progress_bar,
             "from qfluentwidgets import ProgressBar\n\nprogress = ProgressBar()\nprogress.setValue(60)"),
            
            ("ProgressRing", progress_ring,
             "from qfluentwidgets import ProgressRing\n\nring = ProgressRing()\nring.setValue(75)"),
            
            ("IndeterminateProgressRing", indeterminate_ring,
             "from qfluentwidgets import IndeterminateProgressRing\n\nring = IndeterminateProgressRing()"),
        ]
        
        for name, demo, code in samples:
            card = self._create_sample_card(name, code, demo)
            grid.addWidget(card, row, col)
            col += 1
            if col >= items_per_row:
                col = 0
                row += 1
        
        layout.addLayout(grid)
    
    def _add_settings_cards_section(self, layout):
        """Add settings card samples"""
        self._create_category(layout, "⚙️ Settings Cards")
        
        grid = self._create_grid_section(layout)
        row, col = 0, 0
        items_per_row = 2
        
        switch_card = SwitchSettingCard(
            FIF.BRUSH,
            "Dark Mode",
            "Enable dark theme",
            configItem=None,
            parent=self
        )
        
        push_card = PushSettingCard(
            "Open",
            FIF.FOLDER,
            "Open Folder",
            "Click to select folder",
            self
        )
        
        primary_push_card = PrimaryPushSettingCard(
            "Save",
            FIF.SAVE,
            "Save Settings",
            "Click to save configuration",
            self
        )
        
        expand_card = ExpandSettingCard(
            FIF.SETTING,
            "Advanced Settings",
            "Click to expand",
            self
        )
        
        samples = [
            ("SwitchSettingCard", switch_card,
             "from qfluentwidgets import SwitchSettingCard, FluentIcon as FIF\n\ncard = SwitchSettingCard(\n    FIF.BRUSH,\n    \"Dark Mode\",\n    \"Enable dark theme\",\n    configItem=None,\n    parent=self\n)"),
            
            ("PushSettingCard", push_card,
             "from qfluentwidgets import PushSettingCard, FluentIcon as FIF\n\ncard = PushSettingCard(\n    \"Open\",\n    FIF.FOLDER,\n    \"Open Folder\",\n    \"Click to select\",\n    self\n)"),
            
            ("PrimaryPushSettingCard", primary_push_card,
             "from qfluentwidgets import PrimaryPushSettingCard, FluentIcon as FIF\n\ncard = PrimaryPushSettingCard(\n    \"Save\",\n    FIF.SAVE,\n    \"Save Settings\",\n    \"Click to save\",\n    self\n)"),
            
            ("ExpandSettingCard", expand_card,
             "from qfluentwidgets import ExpandSettingCard, FluentIcon as FIF\n\ncard = ExpandSettingCard(\n    FIF.SETTING,\n    \"Advanced\",\n    \"Click to expand\",\n    self\n)"),
        ]
        
        for name, demo, code in samples:
            card = self._create_sample_card(name, code, demo)
            grid.addWidget(card, row, col)
            col += 1
            if col >= items_per_row:
                col = 0
                row += 1
        
        layout.addLayout(grid)
    
    def _add_badges_tooltips_section(self, layout):
        """Add badges and tooltips"""
        self._create_category(layout, "🏷️ Badges & Tooltips")
        
        grid = self._create_grid_section(layout)
        row, col = 0, 0
        items_per_row = 4
        
        badge = InfoBadge.success("New", self)
        
        samples = [
            ("InfoBadge", badge,
             "from qfluentwidgets import InfoBadge\n\nbadge = InfoBadge.success(\"New\", self)"),
        ]
        
        for name, demo, code in samples:
            card = self._create_sample_card(name, code, demo)
            grid.addWidget(card, row, col)
            col += 1
            if col >= items_per_row:
                col = 0
                row += 1
        
        layout.addLayout(grid)
    
    def _add_navigation_section(self, layout):
        """Add navigation widgets"""
        self._create_category(layout, "🧭 Navigation")
        
        grid = self._create_grid_section(layout)
        row, col = 0, 0
        items_per_row = 3
        
        segmented = SegmentedWidget(self)
        segmented.addItem("tab1", "Tab 1")
        segmented.addItem("tab2", "Tab 2")
        segmented.addItem("tab3", "Tab 3")
        
        pivot = Pivot(self)
        pivot.addItem("home", "Home", lambda: None)
        pivot.addItem("settings", "Settings", lambda: None)
        
        samples = [
            ("SegmentedWidget", segmented,
             "from qfluentwidgets import SegmentedWidget\n\nseg = SegmentedWidget()\nseg.addItem(\"tab1\", \"Tab 1\")"),
            
            ("Pivot", pivot,
             "from qfluentwidgets import Pivot\n\npivot = Pivot()\npivot.addItem(\"home\", \"Home\", lambda: None)"),
        ]
        
        for name, demo, code in samples:
            card = self._create_sample_card(name, code, demo)
            grid.addWidget(card, row, col)
            col += 1
            if col >= items_per_row:
                col = 0
                row += 1
        
        layout.addLayout(grid)
