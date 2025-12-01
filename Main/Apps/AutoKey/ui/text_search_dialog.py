"""
Text Search Dialog - Compact UI with Goto logic
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QComboBox, QSlider, QCheckBox, QFormLayout,
                             QDoubleSpinBox, QSpinBox)
from PySide6.QtCore import Qt

class TextSearchDialog(QDialog):
    """Compact dialog for text search configuration"""
    
    def __init__(self, parent=None, event=None):
        super().__init__(parent)
        self.setWindowTitle("Text Search Configuration")
        self.resize(500, 500)
        self.event = event if event else {}
        self.setup_ui()
        self.load_event_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Compact form layout
        form = QFormLayout()
        form.setSpacing(8)
        
        # Query
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Enter text to search...")
        form.addRow("Text:", self.query_input)
        
        # Match mode + Min score in one row
        match_row = QHBoxLayout()
        self.match_mode = QComboBox()
        self.match_mode.addItems(["Fuzzy", "Exact", "Regex"])
        match_row.addWidget(self.match_mode, 1)
        
        self.min_score = QSlider(Qt.Orientation.Horizontal)
        self.min_score.setRange(0, 100)
        self.min_score.setValue(85)
        self.min_score.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.min_score.setTickInterval(10)
        match_row.addWidget(self.min_score, 2)
        
        self.min_score_label = QLabel("85")
        self.min_score.valueChanged.connect(lambda v: self.min_score_label.setText(str(v)))
        match_row.addWidget(self.min_score_label)
        form.addRow("Match Mode:", match_row)
        
        # Languages
        self.languages = QLineEdit()
        self.languages.setText("en, vi")  # Default without ch_sim to avoid compatibility issue
        form.addRow("Languages:", self.languages)
        
        # OCR Engine (NEW!)
        self.ocr_engine = QComboBox()
        self.ocr_engine.addItems(["Windows OCR (Fast)", "EasyOCR (Accurate)"])
        form.addRow("OCR Engine:", self.ocr_engine)
        
        # Preprocessing checkbox
        self.preproc = QCheckBox("Enable preprocessing")
        form.addRow("", self.preproc)
        
        # Region with Test and Define buttons
        region_row = QHBoxLayout()
        region_row.setSpacing(8)
        
        self.region_mode = QComboBox()
        self.region_mode.addItems(["Toàn màn hình", "Cửa sổ đang focus", "Vùng tùy chỉnh"])
        self.region_mode.setCurrentText("Toàn màn hình")
        self.region_mode.setMaximumWidth(140)  # 70% of 200px
        region_row.addWidget(self.region_mode)
        
        # Test Text button
        self.btn_test_text = QPushButton("Test Text")
        self.btn_test_text.setMinimumHeight(28)
        self.btn_test_text.setMinimumWidth(80)
        self.btn_test_text.clicked.connect(self.test_text_search)
        region_row.addWidget(self.btn_test_text)
        
        # Define button
        self.btn_define = QPushButton("Define")
        self.btn_define.setMinimumHeight(28)
        self.btn_define.setMinimumWidth(60)
        self.btn_define.clicked.connect(self.define_search_region)
        self.btn_define.setVisible(False)
        region_row.addWidget(self.btn_define)
        
        region_row.addStretch()
        form.addRow("Vùng tìm:", region_row)
        
        self.region_mode.currentTextChanged.connect(self.on_region_changed)
        self.custom_region = None
        self.is_defining = False
        
        # Timeout + Interval
        timeout_row = QHBoxLayout()
        self.timeout = QDoubleSpinBox()
        self.timeout.setRange(0.1, 60.0)
        self.timeout.setValue(3.0)
        self.timeout.setSuffix(" s")
        timeout_row.addWidget(QLabel("Timeout:"))
        timeout_row.addWidget(self.timeout)
        
        self.interval = QDoubleSpinBox()
        self.interval.setRange(0.05, 5.0)
        self.interval.setValue(0.15)
        self.interval.setSingleStep(0.05)
        self.interval.setSuffix(" s")
        timeout_row.addWidget(QLabel("Interval:"))
        timeout_row.addWidget(self.interval)
        form.addRow("Timing:", timeout_row)
        
        # Action
        self.action = QComboBox()
        self.action.addItems(["None", "Click", "Double Click", "Right Click"])
        form.addRow("Action:", self.action)
        
        # Goto logic
        goto_row = QHBoxLayout()
        goto_row.setSpacing(8)
        
        # Found section
        self.goto_found = QComboBox()
        self.goto_found.addItems(["Next", "Start", "Chuyển Đến"])
        self.goto_found.currentTextChanged.connect(self.on_goto_found_changed)
        goto_row.addWidget(QLabel("Found:"))
        goto_row.addWidget(self.goto_found, 1)
        
        # Step spinbox for found (hidden by default)
        self.lbl_goto_found_step = QLabel("Step")
        self.lbl_goto_found_step.setVisible(False)
        goto_row.addWidget(self.lbl_goto_found_step)
        
        self.spin_goto_found_step = QSpinBox()
        self.spin_goto_found_step.setRange(1, 999)
        self.spin_goto_found_step.setValue(1)
        self.spin_goto_found_step.setMinimumWidth(60)
        self.spin_goto_found_step.setVisible(False)
        goto_row.addWidget(self.spin_goto_found_step)
        
        # Not Found section
        self.goto_not_found = QComboBox()
        self.goto_not_found.addItems(["Next", "Start", "Chuyển Đến"])
        self.goto_not_found.currentTextChanged.connect(self.on_goto_not_found_changed)
        goto_row.addWidget(QLabel("Not Found:"))
        goto_row.addWidget(self.goto_not_found, 1)
        
        # Step spinbox for not found (hidden by default)
        self.lbl_goto_not_found_step = QLabel("Step")
        self.lbl_goto_not_found_step.setVisible(False)
        goto_row.addWidget(self.lbl_goto_not_found_step)
        
        self.spin_goto_not_found_step = QSpinBox()
        self.spin_goto_not_found_step.setRange(1, 999)
        self.spin_goto_not_found_step.setValue(1)
        self.spin_goto_not_found_step.setMinimumWidth(60)
        self.spin_goto_not_found_step.setVisible(False)
        goto_row.addWidget(self.spin_goto_not_found_step)
        
        form.addRow("Goto:", goto_row)
        
        layout.addLayout(form)
        
        # Test result label
        self.test_result_label = QLabel("")
        self.test_result_label.setStyleSheet("font-weight: bold; padding: 8px; min-height: 30px;")
        self.test_result_label.setWordWrap(True)
        layout.addWidget(self.test_result_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add Step")
        self.add_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.add_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def on_goto_found_changed(self, text):
        """Show/hide step label and spinbox based on goto selection"""
        is_goto_step = (text == "Chuyển Đến")
        self.lbl_goto_found_step.setVisible(is_goto_step)
        self.spin_goto_found_step.setVisible(is_goto_step)
    
    def on_goto_not_found_changed(self, text):
        """Show/hide step label and spinbox based on goto selection"""
        is_goto_step = (text == "Chuyển Đến")
        self.lbl_goto_not_found_step.setVisible(is_goto_step)
        self.spin_goto_not_found_step.setVisible(is_goto_step)
    
    def load_event_data(self):
        """Load event data into dialog fields"""
        if not self.event:
            return
        
        # Load basic fields
        self.query_input.setText(self.event.get('query', ''))
        
        # Match mode
        match_map = {'fuzzy': 'Fuzzy', 'exact': 'Exact', 'regex': 'Regex'}
        match_mode = self.event.get('match', 'fuzzy')
        self.match_mode.setCurrentText(match_map.get(match_mode, 'Fuzzy'))
        
        # Min score
        self.min_score.setValue(self.event.get('min_score', 85))
        
        # Languages
        languages = self.event.get('languages', ['en', 'vi'])
        self.languages.setText(', '.join(languages))
        
        # OCR Engine
        engine_map = {'windows': 'Windows OCR (Fast)', 'easyocr': 'EasyOCR (Accurate)'}
        ocr_engine = self.event.get('ocr_engine', 'windows')
        self.ocr_engine.setCurrentText(engine_map.get(ocr_engine, 'Windows OCR (Fast)'))
        
        # Preprocessing
        self.preproc.setChecked(self.event.get('preproc', False))
        
        # Region mode
        region_map = {'screen': 'Toàn màn hình', 'window': 'Cửa sổ đang focus', 'custom': 'Vùng tùy chỉnh'}
        region_mode = self.event.get('region_mode', 'screen')
        self.region_mode.setCurrentText(region_map.get(region_mode, 'Toàn màn hình'))
        
        # Custom region
        self.custom_region = self.event.get('region_rect')
        
        # Timeout and interval
        self.timeout.setValue(self.event.get('timeout', 3.0))
        self.interval.setValue(self.event.get('interval', 0.15))
        
        # Action
        action_map = {'none': 'None', 'click': 'Click', 'double': 'Double Click', 'right': 'Right Click'}
        action = self.event.get('action', 'none')
        self.action.setCurrentText(action_map.get(action, 'None'))
        
        # Load goto_found
        goto_found = self.event.get('goto_found', 'Next')
        if goto_found.startswith('Step '):
            try:
                step_num = int(goto_found.replace('Step ', ''))
                self.goto_found.setCurrentText("Chuyển Đến")
                self.spin_goto_found_step.setValue(step_num)
                self.lbl_goto_found_step.setVisible(True)
                self.spin_goto_found_step.setVisible(True)
            except ValueError:
                self.goto_found.setCurrentText(goto_found)
        else:
            self.goto_found.setCurrentText(goto_found)
        
        # Load goto_not_found
        goto_not_found = self.event.get('goto_not_found', 'Next')
        if goto_not_found.startswith('Step '):
            try:
                step_num = int(goto_not_found.replace('Step ', ''))
                self.goto_not_found.setCurrentText("Chuyển Đến")
                self.spin_goto_not_found_step.setValue(step_num)
                self.lbl_goto_not_found_step.setVisible(True)
                self.spin_goto_not_found_step.setVisible(True)
            except ValueError:
                self.goto_not_found.setCurrentText(goto_not_found)
        else:
            self.goto_not_found.setCurrentText(goto_not_found)
    
    def get_config(self):
        match_mode_map = {"Fuzzy": "fuzzy", "Exact": "exact", "Regex": "regex"}
        action_map = {"None": "none", "Click": "click", "Double Click": "double", "Right Click": "right"}
        region_mode_map = {
            "Toàn màn hình": "screen",
            "Cửa sổ đang focus": "window", 
            "Vùng tùy chỉnh": "custom"
        }
        
        # Parse languages
        lang_str = self.languages.text()
        languages = [lang.strip() for lang in lang_str.split(',')]
        
        # OCR Engine (NEW!)
        engine_map = {"Windows OCR (Fast)": "windows", "EasyOCR (Accurate)": "easyocr"}
        ocr_engine = engine_map.get(self.ocr_engine.currentText(), "windows")
        
        # Handle goto_found
        goto_found_text = self.goto_found.currentText()
        if goto_found_text == "Chuyển Đến":
            goto_found_value = f"Step {self.spin_goto_found_step.value()}"
        else:
            goto_found_value = goto_found_text
        
        # Handle goto_not_found
        goto_not_found_text = self.goto_not_found.currentText()
        if goto_not_found_text == "Chuyển Đến":
            goto_not_found_value = f"Step {self.spin_goto_not_found_step.value()}"
        else:
            goto_not_found_value = goto_not_found_text
        
        return {
            'type': 'text_search',
            'query': self.query_input.text(),
            'languages': languages,
            'ocr_engine': ocr_engine,  # NEW!
            'match': match_mode_map[self.match_mode.currentText()],
            'min_score': self.min_score.value(),
            'timeout': self.timeout.value(),
            'interval': self.interval.value(),
            'preproc': self.preproc.isChecked(),
            'region_mode': region_mode_map[self.region_mode.currentText()],
            'region_rect': self.custom_region,
            'action': action_map[self.action.currentText()],
            'goto_found': goto_found_value,
            'goto_not_found': goto_not_found_value,
            'time': 0.5
        }
    
    def on_region_changed(self, text):
        self.btn_define.setVisible(text in ["Cửa sổ đang focus", "Vùng tùy chỉnh"])
    
    def define_search_region(self):
        try:
            self.is_defining = True
            self.blockSignals(True)
            self.setWindowModality(Qt.WindowModality.NonModal)
            self.lower()
            
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            
            if self.parent():
                self.parent().showMinimized()
            
            QApplication.processEvents()
            import time
            time.sleep(0.3)
            
            from utils.snipping_tool import SnippingWidget
            self.snipper = SnippingWidget(region_only=True)  # Don't save image
            self.snipper.region_selected.connect(self.on_region_selected)
            self.snipper.closed.connect(self.restore_ui)
            self.snipper.showFullScreen()
            
        except Exception as e:
            self.test_result_label.setText(f"❌ Lỗi: {e}")
            self.test_result_label.setStyleSheet("color: red; font-weight: bold; padding: 8px;")
            self.restore_ui()
    
    def on_region_selected(self, rect):
        self.custom_region = {
            'left': rect.x(),
            'top': rect.y(),
            'width': rect.width(),
            'height': rect.height()
        }
        self.test_result_label.setText(f"✅ Đã chọn vùng: {rect.width()}x{rect.height()}")
        self.test_result_label.setStyleSheet("color: green; font-weight: bold; padding: 8px;")
        self.btn_define.setText(f"({rect.width()}x{rect.height()})")
        self.btn_define.setStyleSheet("color: green;")
        self.restore_ui()
    
    def test_text_search(self):
        query = self.query_input.text()
        if not query:
            self.test_result_label.setText("⚠️ Nhập text trước")
            self.test_result_label.setStyleSheet("color: orange; font-weight: bold; padding: 8px;")
            return
        
        self.test_result_label.setText("🔍 Đang tìm kiếm...")
        self.test_result_label.setStyleSheet("color: blue; font-weight: bold; padding: 8px;")
        
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        
        try:
            from utils.roi_manager import ROIManager
            
            # Determine region
            region_text = self.region_mode.currentText()
            region = None
            
            if region_text == "Cửa sổ đang focus":
                from utils.window_utils import get_foreground_window_rect
                region = get_foreground_window_rect()
                if not region:
                    self.test_result_label.setText("⚠️ Không tìm thấy cửa sổ focus")
                    self.test_result_label.setStyleSheet("color: orange; font-weight: bold; padding: 8px;")
                    return
            elif region_text == "Vùng tùy chỉnh":
                if not self.custom_region:
                    self.test_result_label.setText("⚠️ Bấm Define để chọn vùng")
                    self.test_result_label.setStyleSheet("color: orange; font-weight: bold; padding: 8px;")
                    return
                region = self.custom_region
            
            # Capture
            roi_mgr = ROIManager()
            img = roi_mgr.capture(region)
            if img is None:
                self.test_result_label.setText("❌ Capture thất bại")
                self.test_result_label.setStyleSheet("color: red; font-weight: bold; padding: 8px;")
                return
            
            # Get selected engine
            config = self.get_config()
            ocr_engine_type = config['ocr_engine']
            
            # Search based on engine
            if ocr_engine_type == "windows":
                # Windows OCR
                try:
                    from utils.windows_ocr import WindowsOCR
                    if not WindowsOCR.is_available():
                        self.test_result_label.setText("❌ Windows OCR không khả dụng. Cài: pip install pywinrt")
                        self.test_result_label.setStyleSheet("color: red; font-weight: bold; padding: 8px;")
                        return
                    
                    ocr = WindowsOCR(language=config['languages'][0] if config['languages'] else 'en')
                    ocr_results = ocr.recognize(img)
                    
                    # Fuzzy matching - search in full lines AND individual words
                    from rapidfuzz import fuzz
                    best_match = None
                    best_score = 0
                    best_text = ""
                    
                    for ocr_result in ocr_results:
                        # Try matching full line
                        score = fuzz.ratio(query.lower(), ocr_result.text.lower())
                        if score > best_score and score >= self.min_score.value():
                            best_score = score
                            best_match = ocr_result
                            best_text = ocr_result.text
                        
                        # Also try matching individual words (for short queries like "Ba", "We")
                        words = ocr_result.text.split()
                        for word in words:
                            word_score = fuzz.ratio(query.lower(), word.lower())
                            if word_score > best_score and word_score >= self.min_score.value():
                                best_score = word_score
                                best_match = ocr_result
                                best_text = word
                    
                    if best_match:
                        self.test_result_label.setText(f"✅ Tìm thấy: '{best_text}' (điểm: {best_score:.0f})")
                        self.test_result_label.setStyleSheet("color: green; font-weight: bold; padding: 8px;")
                    else:
                        self.test_result_label.setText(f"❌ Không tìm thấy '{query}'")
                        self.test_result_label.setStyleSheet("color: red; font-weight: bold; padding: 8px;")
                        
                except ImportError:
                    self.test_result_label.setText("❌ Thiếu pywinrt. Chạy: pip install pywinrt")
                    self.test_result_label.setStyleSheet("color: red; font-weight: bold; padding: 8px;")
                    
            else:  # EasyOCR
                try:
                    from utils.text_search import TextSearchEngine
                    engine = TextSearchEngine(languages=config['languages'])
                    result = engine.search(
                        img, query,
                        match_mode=config['match'],
                        min_score=self.min_score.value(),
                        preproc=self.preproc.isChecked()
                    )
                    
                    if result:
                        self.test_result_label.setText(f"✅ Tìm thấy: '{result.text}' (điểm: {result.match_score:.0f})")
                        self.test_result_label.setStyleSheet("color: green; font-weight: bold; padding: 8px;")
                    else:
                        self.test_result_label.setText(f"❌ Không tìm thấy '{query}'")
                        self.test_result_label.setStyleSheet("color: red; font-weight: bold; padding: 8px;")
                        
                except ImportError as ie:
                    missing = str(ie).split("'")[1] if "'" in str(ie) else str(ie)
                    self.test_result_label.setText(f"❌ Thiếu: {missing}. Chạy: pip install easyocr rapidfuzz unidecode")
                    self.test_result_label.setStyleSheet("color: red; font-weight: bold; padding: 8px;")
                
        except Exception as e:
            self.test_result_label.setText(f"❌ Lỗi: {str(e)[:80]}")
            self.test_result_label.setStyleSheet("color: red; font-weight: bold; padding: 8px;")
    
    def restore_ui(self):
        self.is_defining = False
        self.blockSignals(False)
        
        if self.parent():
            self.parent().showNormal()
            self.parent().activateWindow()
        
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.raise_()
        self.activateWindow()
        
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
