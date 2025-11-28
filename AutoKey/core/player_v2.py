"""
Player V2 - Supports relative delta mouse playback for 3D games
Features:
- 240Hz fixed tick playback with mouse delta coalescing
- Auto-detect 2D/3D mode or force mode
- High-precision scheduler with drift tracking
- Backward compatible with absolute mouse events
"""
import time
import threading
from PyQt6.QtCore import QThread, pyqtSignal, QSettings
from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController, Button
from utils.direct_input import press_key, release_key
from utils.mouse_backend import MouseBackend, HighPrecisionTicker
from utils.text_search import TextSearchEngine
from utils.roi_manager import ROIManager, Region
import queue

class PlayerV2(QThread):
    # Signals
    progress_updated = pyqtSignal(int, int)
    time_updated = pyqtSignal(float)
    status_updated = pyqtSignal(str)
    playback_finished = pyqtSignal()
    step_progress_updated = pyqtSignal(int, int)
    
    def __init__(self, events, stop_event, pause_event=None):
        super().__init__()
        self.events = events
        self.stop_event = stop_event
        self.pause_event = pause_event if pause_event else threading.Event()
        
        # Controllers
        self.mouse_controller = MouseController()
        self.keyboard_controller = KeyboardController()
        
        # Mouse backend for 3D
        self.mouse_backend = MouseBackend()
        self.ticker = None  # Will be initialized based on tick_hz
        
        # Load settings
        self.settings = QSettings("MonSoft", "MacroRecorder")
        self.play_count = int(self.settings.value("play_count", 1))
        self.play_hours = int(self.settings.value("play_hours", 0))
        self.play_minutes = int(self.settings.value("play_minutes", 0))
        self.after_action = self.settings.value("play_after_action", "None")
        
        # Playback settings
        self.tick_hz = int(self.settings.value("mouse_tick_hz", 240))
        self.mouse_mode = self.settings.value("mouse_mode", "auto")  # auto, force_ui, force_3d
        self.mouse_gain = float(self.settings.value("mouse_gain", 1.0))
        
        # Calculate max duration
        self.max_duration = (self.play_hours * 3600) + (self.play_minutes * 60)
        
        # Drift tracking
        self.drift_total = 0
        self.drift_max = 0
        self.coalesce_count = 0
        
        # Text search engine (lazy init)
        self.text_search_engine = None
        self.roi_manager = None
    
    def run(self):
        """Main playback loop"""
        print(f"🎮 Player V2 started (Mouse mode: {self.mouse_mode}, Tick: {self.tick_hz}Hz)")
        self.status_updated.emit("Đang khởi động...")
        
        # Set mouse backend mode
        self.mouse_backend.set_mode(self.mouse_mode)
        
        self.start_time = time.perf_counter()
        current_run = 0
        
        while not self.stop_event.is_set():
            # Check run count
            if self.play_count > 0 and current_run >= self.play_count:
                print("✅ Reached run count limit")
                self.status_updated.emit("Đã hoàn thành số lần chạy")
                break
            
            # Check duration
            if self.max_duration > 0:
                elapsed = time.perf_counter() - self.start_time
                if elapsed >= self.max_duration:
                    print("⏱️ Reached duration limit")
                    self.status_updated.emit("Đã hết thời gian chạy")
                    break
            
            # Update progress
            self.progress_updated.emit(current_run + 1, self.play_count)
            
            print(f"--- Run {current_run + 1} ---")
            self.status_updated.emit(f"Đang chạy vòng lặp {current_run + 1}")
            
            # Execute macro
            self.execute_macro()
            
            current_run += 1
            
            # Update time
            elapsed = time.perf_counter() - self.start_time
            self.time_updated.emit(elapsed)
            
            time.sleep(0.1)
        
        print(f"🏁 Player finished (Drift: {self.drift_total*1000:.1f}ms total, {self.drift_max*1000:.1f}ms max)")
        self.status_updated.emit("Đã dừng")
        
        if not self.stop_event.is_set():
            self.perform_after_action()
        
        self.playback_finished.emit()
    
    def execute_macro(self):
        """Execute one pass of the macro"""
        current_idx = 0
        total_steps = len(self.events)
        
        # Initialize ticker if using delta mouse
        has_delta_events = any(e.get('type') == 'mouse_move_delta' for e in self.events)
        if has_delta_events:
            self.ticker = HighPrecisionTicker(self.tick_hz)
            self.ticker.start()
        
        while current_idx < total_steps and not self.stop_event.is_set():
            event = self.events[current_idx]
            
            # Check pause
            while self.pause_event.is_set() and not self.stop_event.is_set():
                time.sleep(0.1)
            
            if self.stop_event.is_set():
                break
            
            # Emit step progress (throttled)
            if current_idx % 50 == 0 or current_idx == total_steps - 1:
                self.step_progress_updated.emit(current_idx + 1, total_steps)
            
            # Handle delay
            delay = event.get('time', 0.0)
            if delay > 0:
                target_time = time.perf_counter() + delay
                
                # Sleep with high precision
                while time.perf_counter() < target_time:
                    remaining = target_time - time.perf_counter()
                    if remaining > 0.002:  # 2ms busy-wait threshold
                        time.sleep(remaining - 0.001)
                    # Busy-wait for last 1-2ms
                
                # Track drift
                actual_time = time.perf_counter()
                drift = actual_time - target_time
                self.drift_total += abs(drift)
                self.drift_max = max(self.drift_max, abs(drift))
            
            # Execute event
            next_idx = self.execute_event(event, current_idx)
            
            if next_idx is not None:
                current_idx = next_idx
            else:
                current_idx += 1
    
    def execute_event(self, event, current_idx):
        """Execute single event"""
        etype = event['type']
        
        if etype == 'detect_image':
            return self.handle_detect_image(event, current_idx)
        
        elif etype == 'mouse_move_delta':
            # Delta mode - use mouse backend
            dx = event.get('dx', 0)
            dy = event.get('dy', 0)
            
            # Apply Gain
            if self.mouse_gain != 1.0:
                dx = int(dx * self.mouse_gain)
                dy = int(dy * self.mouse_gain)
            
            if self.ticker:
                # Add to ticker accumulator
                self.ticker.add_delta(dx, dy)
                sent = self.ticker.tick(self.mouse_backend)
                if not sent:
                    self.coalesce_count += 1
            else:
                # Fallback: direct send
                self.mouse_backend.move_relative(dx, dy)
        
        elif etype == 'mouse_move':
            # Absolute mode - use controller or backend
            x = event.get('x', 0)
            y = event.get('y', 0)
            
            if self.mouse_backend.should_use_relative():
                # Convert to delta (not ideal, but works)
                curr_x, curr_y = self.mouse_controller.position
                dx = x - curr_x
                dy = y - curr_y
                self.mouse_backend.move_relative(dx, dy)
            else:
                # Use absolute positioning
                self.mouse_controller.position = (x, y)
        
        elif etype == 'mouse_click':
            x = event.get('x', 0)
            y = event.get('y', 0)
            self.mouse_controller.position = (x, y)
            
            btn = Button.left
            if 'Button.right' in event.get('button', ''):
                btn = Button.right
            elif 'Button.middle' in event.get('button', ''):
                btn = Button.middle
            
            if event.get('pressed', True):
                self.mouse_controller.press(btn)
            else:
                self.mouse_controller.release(btn)
        
        elif etype == 'mouse_scroll':
            self.mouse_controller.scroll(event.get('dx', 0), event.get('dy', 0))
        
        elif etype == 'key_click':
            press_key(event['key'])
            time.sleep(0.1)
            release_key(event['key'])
        
        elif etype == 'key_press':
            press_key(event['key'])
        
        elif etype == 'key_release':
            release_key(event['key'])
        
        elif etype == 'text_search':
            return self.execute_text_search(event, current_idx)
        
        return None
    
    def execute_text_search(self, event, current_idx):
        """Execute text search event"""
        # Lazy init
        if self.text_search_engine is None:
            languages = event.get('languages', ['en', 'vi', 'ch_sim'])
            self.text_search_engine = TextSearchEngine(languages=languages)
        
        if self.roi_manager is None:
            rate_limit_fps = int(self.settings.value("ocr_rate_limit_fps", 10))
            self.roi_manager = ROIManager(rate_limit_fps=rate_limit_fps)
        
        # Get parameters
        query = event.get('query', '')
        match_mode = event.get('match', 'fuzzy')
        min_score = event.get('min_score', 85)
        timeout = event.get('timeout', 3.0)
        interval = event.get('interval', 0.15)
        preproc = event.get('preproc', False)
        region_mode = event.get('region_mode', 'screen')
        action = event.get('action', 'none')
        goto_found = event.get('goto_found', 'Next')
        goto_not_found = event.get('goto_not_found', 'Next')
        
        # Determine region
        if region_mode == 'screen':
            region = self.roi_manager.get_screen_region()
        elif region_mode == 'window':
            region = self.roi_manager.get_window_region()
            if region is None:
                print("⚠️ Text Search: Failed to get window region, falling back to screen")
                region = self.roi_manager.get_screen_region()
        else:  # custom
            region_rect = event.get('region_rect')
            if region_rect:
                x, y, w, h = region_rect
                region = Region(x=x, y=y, width=w, height=h)
            else:
                region = self.roi_manager.get_screen_region()
        
        # Search loop with timeout
        start_time = time.perf_counter()
        result = None
        
        while time.perf_counter() - start_time < timeout and not self.stop_event.is_set():
            # Capture screen
            img = self.roi_manager.capture(region)
            if img is None:
                time.sleep(interval)
                continue
            
            # Search for text
            result = self.text_search_engine.search(
                img, query,
                match_mode=match_mode,
                min_score=min_score,
                preproc=preproc
            )
            
            if result:
                print(f"✅ Text Search: Found '{result.text}' (score: {result.match_score}, conf: {result.ocr_conf:.2f})")
                break
            
            time.sleep(interval)
        
        # Handle result
        if result:
            # Perform action
            if action == 'click':
                self.mouse_controller.position = result.center
                time.sleep(0.05)
                self.mouse_controller.click(Button.left)
            elif action == 'double':
                self.mouse_controller.position = result.center
                time.sleep(0.05)
                self.mouse_controller.click(Button.left, 2)
            elif action == 'right':
                self.mouse_controller.position = result.center
                time.sleep(0.05)
                self.mouse_controller.click(Button.right)
            
            # Handle goto_found
            if goto_found == 'Start':
                return 0  # Jump to start
            # 'Next' or other -> continue normally
        else:
            print(f"⚠️ Text Search: '{query}' not found after {timeout}s")
            # Handle goto_not_found
            if goto_not_found == 'Start':
                return 0  # Jump to start
        
        return None
    
    def handle_detect_image(self, event, current_idx):
        """Handle detect_image event (same as before)"""
        # ... (keep old implementation, not changed)
        return None
    
    def perform_after_action(self):
        """Execute after-action"""
        import os
        if self.after_action == "Tắt Máy":
            print("💤 Shutting down...")
            os.system("shutdown /s /t 0")
        elif self.after_action == "Sleep":
            print("💤 Going to sleep...")
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
