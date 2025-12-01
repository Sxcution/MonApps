from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (SubtitleLabel, BodyLabel, PushButton, CardWidget, 
                            FluentIcon as FIF, InfoBar)

class HomeInterface(QWidget):
    # btn_new_macro : Nút tạo macro mới
    new_macro_requested = Signal()
    # btn_open_macro : Nút mở macro
    open_macro_requested = Signal()
    # btn_start_record : Nút bắt đầu ghi
    start_record_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("homeInterface")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title - Tiêu đề
        title = SubtitleLabel("AutoKey Macro Recorder", self)
        layout.addWidget(title)
        
        # Description - Mô tả
        desc = BodyLabel(
            "Công cụ ghi và phát lại macro tự động.\n"
            "Chọn chức năng từ menu bên trái hoặc sử dụng các nút nhanh bên dưới.",
            self
        )
        layout.addWidget(desc)
        
        # Quick Actions Card - Card hành động nhanh
        actions_card = CardWidget(self)
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setContentsMargins(20, 20, 20, 20)
        actions_layout.setSpacing(15)
        
        card_title = SubtitleLabel("Hành động nhanh", actions_card)
        actions_layout.addWidget(card_title)
        
        # Button row - Hàng nút
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # btn_new_macro : Nút tạo macro mới
        self.new_btn = PushButton(FIF.ADD, "Tạo macro mới", actions_card)
        self.new_btn.clicked.connect(self.new_macro_requested.emit)
        btn_layout.addWidget(self.new_btn)
        
        # btn_open_macro : Nút mở macro
        self.open_btn = PushButton(FIF.FOLDER, "Mở macro", actions_card)
        self.open_btn.clicked.connect(self.open_macro_requested.emit)
        btn_layout.addWidget(self.open_btn)
        
        # btn_start_record : Nút bắt đầu ghi
        self.record_btn = PushButton(FIF.VIDEO, "Bắt đầu ghi", actions_card)
        self.record_btn.clicked.connect(self.start_record_requested.emit)
        btn_layout.addWidget(self.record_btn)
        
        btn_layout.addStretch(1)
        actions_layout.addLayout(btn_layout)
        
        layout.addWidget(actions_card)
        layout.addStretch(1)
