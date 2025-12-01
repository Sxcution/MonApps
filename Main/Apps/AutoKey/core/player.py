import time
import pyautogui
import random
import ctypes
import os
from PySide6.QtCore import QSettings, QThread, Signal
from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController, Button
from utils.direct_input import press_key, release_key

class Player(QThread):
    # Signals for UI updates
    progress_updated = Signal(int, int)  # current_run, total_runs
    time_updated = Signal(float)  # elapsed_seconds
    status_updated = Signal(str)  # status message
    playback_finished = Signal()  # playback completed
    step_progress_updated = Signal(int, int)  # current_step, total_steps
    
    # Log signals
    log_entry = Signal(int, str, str)  # step_num, action_text, delay_text
    log_loop_marker = Signal(int)  # loop_num
    log_status = Signal(str, str)  # message, color
    
    
    def __init__(self, events, stop_event, pause_event=None):
        super().__init__()
        self.events = events
        self.stop_event = stop_event
        self.pause_event = pause_event if pause_event else threading.Event()
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        
        # Load Play Settings
        self.settings = QSettings("MonSoft", "MacroRecorder")
        self.play_count = int(self.settings.value("play_count", 1))
        self.play_hours = int(self.settings.value("play_hours", 0))
        self.play_minutes = int(self.settings.value("play_minutes", 0))
        self.loop_delay = int(self.settings.value("loop_delay", 0))  # ms
        self.after_action = self.settings.value("play_after_action", "None")
        
        # Calculate max duration in seconds
        self.max_duration = (self.play_hours * 3600) + (self.play_minutes * 60)

    def run(self):
        print("Player started")
        self.status_updated.emit("Đang khởi động...")
        
        self.start_time = time.time()
        current_run = 0
        
        while not self.stop_event.is_set():
            # Check Run Count (0 means infinite)
            if self.play_count > 0 and current_run >= self.play_count:
                print("Reached run count limit.")
                self.status_updated.emit("Đã hoàn thành số lần chạy")
                break
                
            # Check Duration
            if self.max_duration > 0:
                elapsed = time.time() - self.start_time
                if elapsed >= self.max_duration:
                    print("Reached duration limit.")
                    self.status_updated.emit("Đã hết thời gian chạy")
                    break
            
            # Update progress
            self.progress_updated.emit(current_run + 1, self.play_count)
            
            print(f"--- Starting Run {current_run + 1} ---")
            self.status_updated.emit(f"Đang chạy vòng lặp {current_run + 1}")
            
            # Emit loop marker to log
            self.log_loop_marker.emit(current_run + 1)
            
            self.execute_macro()
            
            current_run += 1
            
            # Update time periodically
            elapsed = time.time() - self.start_time
            self.time_updated.emit(elapsed)
            
            # Loop delay - wait after completing a loop before starting next loop
            if self.loop_delay > 0 and not self.stop_event.is_set():
                delay_seconds = self.loop_delay / 1000.0
                print(f"⏳ Loop delay: waiting {delay_seconds:.2f}s before next loop...")
                self.status_updated.emit(f"Chờ {delay_seconds:.1f}s trước vòng tiếp theo...")
                time.sleep(delay_seconds)
            elif self.loop_delay == 0:
                # Small delay between runs to prevent CPU hogging if macro is empty
                time.sleep(0.1)
            
        print("Player finished")
        self.status_updated.emit("Đã dừng")
        
        # Perform After Action if not stopped manually
        if not self.stop_event.is_set():
            self.perform_after_action()
        
        self.playback_finished.emit()

    def execute_macro(self):
        """Executes one pass of the macro"""
        current_idx = 0
        total_steps = len(self.events)
        
        while current_idx < total_steps and not self.stop_event.is_set():
            event = self.events[current_idx]
            
            # Check if paused - wait until resumed
            while self.pause_event.is_set() and not self.stop_event.is_set():
                time.sleep(0.1)  # Check every 100ms
            
            # If stopped while paused, exit
            if self.stop_event.is_set():
                break
            
            # Emit step progress (1-indexed for display)
            self.step_progress_updated.emit(current_idx + 1, total_steps)
            
            # Check duration limit
            if self.max_duration > 0:
                elapsed = (time.time() - self.start_time) / 60 # minutes
                if elapsed >= self.max_duration:
                    print("⏱️ Max duration reached. Stopping.")
                    return

            # Get action description for log
            action_text = self._get_action_description(event)
            
            # Execute event FIRST
            next_idx = self.execute_event(event, current_idx)
            
            # THEN handle delay AFTER executing the event
            delay = event.get('time', 0.0)
            delay_text = ""
            if delay > 0 and not self.stop_event.is_set():
                delay_text = f"Đợi {delay:.1f}s"
                print(f"⏳ Event delay: waiting {delay:.1f}s after step {current_idx + 1}...")
                self.status_updated.emit(f"Chờ {delay:.1f}s...")
                time.sleep(delay)
            else:
                delay_text = "-"
            
            # Emit log entry
            self.log_entry.emit(current_idx + 1, action_text, delay_text)
            
            if next_idx is not None:
                current_idx = next_idx
            else:
                current_idx += 1


    def execute_event(self, event, current_idx):
        """
        Executes event. Returns next_idx if a jump is needed, else None.
        """
        etype = event['type']
        
        if etype == 'detect_image':
            return self.handle_detect_image(event, current_idx)
        
        elif etype == 'text_search':
            return self.handle_text_search(event, current_idx)
            
        elif etype in ['mouse_move', 'mouse_click', 'mouse_hold']:
            self._handle_mouse(event)
            
        elif etype == 'mouse_scroll':
            self.mouse.scroll(event.get('dx', 0), event.get('dy', 0))
            
        elif etype == 'key_click':
            # Use DirectInput for games: Press -> Wait -> Release
            press_key(event['key'])
            time.sleep(0.1) # Short hold to ensure game registers it
            release_key(event['key'])

        elif etype == 'key_press':
            # Use DirectInput for games
            press_key(event['key'])
            
            # If hold_duration is specified, hold the key then release
            if 'hold_duration' in event and event['hold_duration'] > 0:
                hold_ms = event['hold_duration']
                time.sleep(hold_ms / 1000.0)  # Convert ms to seconds
                release_key(event['key'])
            
        elif etype == 'key_release':
            # Use DirectInput for games
            release_key(event['key'])
            
        return None

    def handle_detect_image(self, event, current_idx):
        from utils.image_finder import wait_for_image
        from utils.window_utils import get_foreground_window_rect
        
        image_path = event.get('image_path')
        if not image_path:
            print("No image path for detect_image")
            return None
            
        # Determine Search Region
        region = None
        if event.get('restrict_area', False):
            area_type = event.get('search_area', 'focused window')
            if area_type == 'focused window':
                region = get_foreground_window_rect()
                print(f"Searching in focused window: {region}")
            elif area_type == 'custom region':
                region = event.get('custom_region')
                if region:
                     print(f"Searching in custom region: {region}")
        
        # Wait for image
        timeout = event.get('wait_timeout', 0)
        tolerance = event.get('tolerance', 0)
        # Convert tolerance 0-255 to confidence 0.0-1.0 (inverted)
        # Adjusted: 0 tolerance now maps to ~0.9975 to allow tiny rendering differences
        confidence = 1.0 - ((tolerance + 1) / 400.0) 
        if confidence < 0.1: confidence = 0.1
        
        print(f"Waiting for image: {image_path}, timeout={timeout}, conf={confidence}")
        self.status_updated.emit(f"Đang tìm ảnh...")
        
        grayscale = event.get('grayscale', False)
        multi_scale = event.get('multi_scale', False)
        
        found_rect = wait_for_image(
            image_path, 
            timeout=timeout, 
            confidence=confidence, 
            region=region,
            grayscale=grayscale,
            multi_scale=multi_scale
        )
        
        if found_rect:
            print(f"Image found at {found_rect}")
            self.log_status.emit(f"✅ Tìm thấy ảnh tại ({found_rect[0]}, {found_rect[1]})", "#00aa00")
            x, y, w, h = found_rect
            center_x = x + w // 2
            center_y = y + h // 2
            
            # Mouse Action
            if event.get('mouse_action_enabled', False):
                action = event.get('mouse_action', 'Move')
                pos_type = event.get('mouse_position', 'Centered')
                
                target_x, target_y = center_x, center_y
                if pos_type == 'Top-Left': target_x, target_y = x, y
                # ... other positions ...
                
                self.mouse.position = (target_x, target_y)
                
                if action == 'Click':
                    self.mouse.click(Button.left)
                elif action == 'Double Click':
                    self.mouse.click(Button.left, 2)
                elif action == 'Right Click':
                    self.mouse.click(Button.right)
            
            # Go to
            goto = event.get('goto_found', 'Next')
            return self._resolve_goto(goto, current_idx)
            
        else:
            print("Image NOT found")
            self.log_status.emit(f"⚠️ Không tìm thấy ảnh sau {timeout}s", "#ff8c00")
            # Not found logic
            goto = event.get('goto_not_found', 'End')
            return self._resolve_goto(goto, current_idx)

    def handle_text_search(self, event, current_idx):
        """Handle text search event with goto logic"""
        try:
            from utils.text_search import TextSearchEngine
            from utils.roi_manager import ROIManager, Region
            from utils.windows_ocr import WindowsOCR
            from rapidfuzz import fuzz
        except ImportError as e:
            print(f"❌ Text Search: Missing dependencies - {e}")
            self.log_status.emit(f"❌ Text Search: Thiếu thư viện - {e}", "#ff0000")
            goto = event.get('goto_not_found', 'Next')
            return self._resolve_goto(goto, current_idx)
        
        query = event.get('query', '')
        if not query:
            print("⚠️ Text Search: No query specified")
            goto = event.get('goto_not_found', 'Next')
            return self._resolve_goto(goto, current_idx)
        
        # Get parameters
        match_mode = event.get('match', 'fuzzy')
        min_score = event.get('min_score', 85)
        timeout = event.get('timeout', 3.0)
        interval = event.get('interval', 0.15)
        region_mode = event.get('region_mode', 'screen')
        ocr_engine = event.get('ocr_engine', 'windows')
        action = event.get('action', 'none')
        goto_found = event.get('goto_found', 'Next')
        goto_not_found = event.get('goto_not_found', 'Next')
        
        # Determine region
        roi_mgr = ROIManager()
        if region_mode == 'window':
            from utils.window_utils import get_foreground_window_rect
            region_dict = get_foreground_window_rect()
            if region_dict:
                region = Region(
                    x=region_dict['left'],
                    y=region_dict['top'],
                    width=region_dict['width'],
                    height=region_dict['height']
                )
            else:
                region = roi_mgr.get_screen_region()
        elif region_mode == 'custom' and event.get('region_rect'):
            r = event['region_rect']
            region = Region(x=r['left'], y=r['top'], width=r['width'], height=r['height'])
        else:
            region = roi_mgr.get_screen_region()
        
        print(f"🔍 Text Search: Looking for '{query}' (timeout: {timeout}s)")
        self.status_updated.emit(f"Đang tìm text '{query}'...")
        
        # Search loop with timeout
        start_time = time.time()
        result = None
        
        while time.time() - start_time < timeout and not self.stop_event.is_set():
            # Capture screen
            img = roi_mgr.capture(region)
            if img is None:
                time.sleep(interval)
                continue
            
            # Search using selected engine
            if ocr_engine == 'windows':
                try:
                    languages = event.get('languages', ['en'])
                    lang = languages[0] if languages else 'en'
                    ocr = WindowsOCR(language=lang)
                    ocr_results = ocr.recognize(img)
                    
                    # Fuzzy matching
                    best_match = None
                    best_score = 0
                    
                    for ocr_result in ocr_results:
                        # Try full line
                        score = fuzz.ratio(query.lower(), ocr_result.text.lower())
                        if score >= min_score and score > best_score:
                            best_score = score
                            best_match = ocr_result
                        
                        # Try individual words
                        words = ocr_result.text.split()
                        for word in words:
                            word_score = fuzz.ratio(query.lower(), word.lower())
                            if word_score >= min_score and word_score > best_score:
                                best_score = word_score
                                best_match = ocr_result
                    
                    if best_match:
                        result = best_match
                        break
                        
                except Exception as e:
                    print(f"❌ Windows OCR error: {e}")
                    
            else:  # EasyOCR
                try:
                    languages = event.get('languages', ['en', 'vi'])
                    engine = TextSearchEngine(languages=languages)
                    preproc = event.get('preproc', False)
                    result = engine.search(img, query, match_mode=match_mode, min_score=min_score, preproc=preproc)
                    if result:
                        break
                except Exception as e:
                    print(f"❌ EasyOCR error: {e}")
            
            time.sleep(interval)
        
        # Handle result
        if result:
            print(f"✅ Text Search: Found '{query}'")
            self.log_status.emit(f"✅ Tìm thấy text: '{query}'", "#00aa00")
            
            # Perform action
            if action == 'click' or action == 'double' or action == 'right':
                from pynput.mouse import Button
                if hasattr(result, 'center'):
                    self.mouse.position = result.center
                elif hasattr(result, 'bbox'):
                    # Calculate center from bbox
                    x = result.bbox.left + result.bbox.width // 2
                    y = result.bbox.top + result.bbox.height // 2
                    self.mouse.position = (x, y)
                
                time.sleep(0.05)
                if action == 'click':
                    self.mouse.click(Button.left)
                elif action == 'double':
                    self.mouse.click(Button.left, 2)
                elif action == 'right':
                    self.mouse.click(Button.right)
            
            # Goto found
            return self._resolve_goto(goto_found, current_idx)
        else:
            print(f"⚠️ Text Search: '{query}' not found after {timeout}s")
            self.log_status.emit(f"⚠️ Không tìm thấy text: '{query}'", "#ff8c00")
            
            # Goto not found
            return self._resolve_goto(goto_not_found, current_idx)
    
    def _resolve_goto(self, goto_str, current_idx):
        if goto_str == 'Start':
            return 0
        elif goto_str == 'Next':
            return None # Continue loop
        elif goto_str == 'End':
            return len(self.events) # Break loop
        elif goto_str.startswith('Step '):
            try:
                step = int(goto_str.replace('Step ', ''))
                return step - 1 # 0-indexed
            except:
                pass
        return None

    def _handle_mouse(self, event):
        etype = event['type']
        # Calculate Target Coordinates
        target_x = event.get('x', 0)
        target_y = event.get('y', 0)
        
        # 1. Handle Ignore Coordinates (Current Position)
        if event.get('ignore_coordinates', False):
            target_x, target_y = self.mouse.position
        else:
            # 2. Handle Coordinate Modes
            mode = event.get('coordinate_mode', 'absolute')
            
            if mode == 'relative':
                # Relative to active window
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                if hwnd:
                    rect = ctypes.wintypes.RECT()
                    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    target_x += rect.left
                    target_y += rect.top
                    
            elif mode == 'offset':
                # Offset from current position
                curr_x, curr_y = self.mouse.position
                target_x += curr_x
                target_y += curr_y
        
        # 3. Handle Randomization
        rand_pixels = event.get('randomize_pixels', 0)
        if rand_pixels > 0:
            target_x += random.randint(-rand_pixels, rand_pixels)
            target_y += random.randint(-rand_pixels, rand_pixels)
        
        # Execute
        if etype == 'mouse_move':
            self.mouse.position = (target_x, target_y)
            
        elif etype == 'mouse_click':
            self.mouse.position = (target_x, target_y)
            
            # pynput button mapping
            btn = Button.left
            if 'Button.right' in event.get('button', ''):
                btn = Button.right
            elif 'Button.middle' in event.get('button', ''):
                btn = Button.middle
            
            if event.get('pressed', True):
                self.mouse.press(btn)
            else:
                self.mouse.release(btn)
        
        elif etype == 'mouse_hold':
            # Move to position, press, hold, release
            self.mouse.position = (target_x, target_y)
            
            # Always use left button for hold
            self.mouse.press(Button.left)
            
            # Hold for duration
            duration_ms = event.get('duration', 1000)
            time.sleep(duration_ms / 1000.0)
            
            # Release
            self.mouse.release(Button.left)

    def _parse_key(self, key_str):
        from pynput.keyboard import Key
        
        # 1. Handle pynput format (Key.space)
        if key_str.startswith('Key.'):
            attr = key_str.split('.')[1]
            try:
                return getattr(Key, attr)
            except AttributeError:
                pass

        # 2. Handle Quoted chars ('a')
        if len(key_str) > 1 and key_str.startswith("'") and key_str.endswith("'"):
             return key_str[1:-1]
             
        # 3. Handle Qt/Common Key Names
        key_map = {
            "Down": Key.down,
            "Up": Key.up,
            "Left": Key.left,
            "Right": Key.right,
            "Enter": Key.enter,
            "Return": Key.enter,
            "Esc": Key.esc,
            "Escape": Key.esc,
            "Space": Key.space,
            "Tab": Key.tab,
            "Backspace": Key.backspace,
            "Delete": Key.delete,
            "Del": Key.delete,
            "Shift": Key.shift,
            "Ctrl": Key.ctrl,
            "Control": Key.ctrl,
            "Alt": Key.alt,
            "PgUp": Key.page_up,
            "Page Up": Key.page_up,
            "PgDown": Key.page_down,
            "Page Down": Key.page_down,
            "Home": Key.home,
            "End": Key.end,
            "Insert": Key.insert,
            "F1": Key.f1, "F2": Key.f2, "F3": Key.f3, "F4": Key.f4,
            "F5": Key.f5, "F6": Key.f6, "F7": Key.f7, "F8": Key.f8,
            "F9": Key.f9, "F10": Key.f10, "F11": Key.f11, "F12": Key.f12
        }
        
        if key_str in key_map:
            return key_map[key_str]
            
        # 4. Handle Single Chars (a, b, 1)
        if len(key_str) == 1:
            return key_str.lower()
            
        print(f"Unknown key: {key_str}")
        return None

    def _get_action_description(self, event):
        """Get human-readable description of event action"""
        event_type = event.get('type', 'unknown')
        
        if event_type == 'mouse_click':
            button = event.get('button', 'left')
            return f"Mouse Click ({button})"
        elif event_type == 'mouse_move':
            x = event.get('x', 0)
            y = event.get('y', 0)
            return f"Mouse Move to ({x}, {y})"
        elif event_type == 'mouse_scroll':
            delta = event.get('delta_y', 0)
            direction = "Up" if delta > 0 else "Down"
            return f"Mouse Scroll {direction}"
        elif event_type == 'mouse_hold':
            duration = event.get('duration', 0)
            return f"Mouse Hold ({duration}ms)"
        elif event_type == 'key_press':
            key = event.get('key', 'unknown')
            return f"Key Press: {key}"
        elif event_type == 'key_release':
            key = event.get('key', 'unknown')
            return f"Key Release: {key}"
        elif event_type == 'key_click':
            key = event.get('key', 'unknown')
            return f"Key Click: {key}"
        elif event_type == 'detect_image':
            image = event.get('image_path', '')
            image_name = image.split('/')[-1] if image else 'unknown'
            return f"Detect Image: {image_name}"
        elif event_type == 'text_search':
            query = event.get('query', '')
            return f"Text Search: {query}"
        else:
            return event_type.replace('_', ' ').title()
    
    def perform_after_action(self):
        """Executes the configured after-action"""
        if self.after_action == "Tắt Máy":
            print("Shutting down...")
            os.system("shutdown /s /t 0")
        elif self.after_action == "Sleep":
            print("Going to sleep...")
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
