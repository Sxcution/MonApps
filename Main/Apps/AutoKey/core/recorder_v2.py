"""
Recorder V2 - Supports relative delta mouse recording for 3D games
Features:
- Delta recording with perf_counter timestamps
- Throttling (5px or 8ms threshold)
- Auto-detect or force absolute/delta mode
- Backward compatible with old absolute mode
"""
import time
from pynput import mouse, keyboard
from PySide6.QtCore import QObject, Signal

from core.error_logger import log_exceptions
from pynput import keyboard # Ensure imported for KeyCode check

class RecorderV2(QObject):
    event_recorded = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.recording = False
        self.start_time = 0
        self.mouse_listener = None
        self.keyboard_listener = None
        self.events = []
        
        # Recording mode
        self.record_mode = "delta"  # "delta", "absolute", "auto"
        self.last_mouse_pos = None
        self.mouse_threshold_px = 0  # 0 to capture all micro-movements for 3D
        self.mouse_threshold_time = 0.001  # 1ms (1000Hz) - Optimized for file size vs accuracy
        
        # Timing
        self.last_time = 0
        
    def set_mode(self, mode):
        """Set recording mode: 'delta', 'absolute', 'auto'"""
        if mode in ["delta", "absolute", "auto"]:
            self.record_mode = mode
            print(f"📹 Recording mode set to: {mode}")
    
    def start_recording(self):
        """Start recording events"""
        self.recording = True
        self.events = []
        self.start_time = time.perf_counter()
        self.last_time = self.start_time
        self.last_mouse_pos = None
        
        # Start listeners
        self.mouse_listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll
        )
        
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        print(f"📹 Recording started in {self.record_mode} mode")
    
    def stop_recording(self):
        """Stop recording and return events"""
        self.recording = False
        
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        print(f"✅ Recording stopped: {len(self.events)} events")
        return self.events
    
    def _get_delay(self):
        """Get time delta since last event (high precision)"""
        now = time.perf_counter()
        delta = now - self.last_time
        self.last_time = now
        return delta
    
    def _should_use_delta(self):
        """Determine if delta mode should be used"""
        if self.record_mode == "delta":
            return True
        elif self.record_mode == "absolute":
            return False
        else:  # auto
            # Auto-detect: could check cursor visibility, etc.
            # For now, default to delta for better 3D support
            return True
    
    def _normalize_key(self, key, k: str) -> str:
        """
        Normalize key:
        - Convert control code to char
        """
        try:
            # If it is a non-printable character => likely Ctrl+<key>
            if isinstance(key, keyboard.KeyCode) and k and len(k) == 1 and ord(k) < 32:
                if hasattr(key, "vk") and key.vk is not None:
                    vk = key.vk
                    # A-Z
                    if 65 <= vk <= 90:
                        k = chr(vk).lower() 
                    # 0-9
                    elif 48 <= vk <= 57:
                        k = chr(vk)
            return k
        except Exception:
            from core.error_logger import log_exception
            log_exception("RecorderV2._normalize_key", extra={"key": str(key), "k": k})
            try:
                return key.char or str(key)
            except:
                return str(key)

    @log_exceptions("RecorderV2.on_move")
    def on_move(self, x, y):
        """Mouse move event"""
        if not self.recording:
            return
        
        use_delta = self._should_use_delta()
        
        if use_delta:
            # Delta mode
            if self.last_mouse_pos is None:
                self.last_mouse_pos = (x, y)
                return  # Skip first move, no delta yet
            
            dx = x - self.last_mouse_pos[0]
            dy = y - self.last_mouse_pos[1]
            
            # Throttle: skip if moved too little AND not enough time passed
            move_dist = abs(dx) + abs(dy)
            if move_dist < self.mouse_threshold_px:
                now = time.perf_counter()
                time_since_last = now - self.last_time
                if time_since_last < self.mouse_threshold_time:
                    return  # Skip this move
            
            event = {
                'type': 'mouse_move_delta',
                'dx': dx,
                'dy': dy,
                'time': self._get_delay()
            }
            
            self.last_mouse_pos = (x, y)
        else:
            # Absolute mode (legacy)
            event = {
                'type': 'mouse_move',
                'x': x,
                'y': y,
                'time': self._get_delay()
            }
        
        self.events.append(event)
    
    @log_exceptions("RecorderV2.on_click")
    def on_click(self, x, y, button, pressed):
        """Mouse click event"""
        if not self.recording:
            return
        
        event = {
            'type': 'mouse_click',
            'x': x,
            'y': y,
            'button': str(button),
            'pressed': pressed,
            'time': self._get_delay()
        }
        
        self.events.append(event)
        self.event_recorded.emit(event)
    
    @log_exceptions("RecorderV2.on_scroll")
    def on_scroll(self, x, y, dx, dy):
        """Mouse scroll event"""
        if not self.recording:
            return
        
        event = {
            'type': 'mouse_scroll',
            'x': x,
            'y': y,
            'dx': dx,
            'dy': dy,
            'time': self._get_delay()
        }
        
        self.events.append(event)
        self.event_recorded.emit(event)
    
    @log_exceptions("RecorderV2.on_press")
    def on_press(self, key):
        """Keyboard press event"""
        if not self.recording:
            return
        
        try:
            k = key.char
        except AttributeError:
            k = str(key)
        
        if k is None:
            k = str(key)
            
        k = self._normalize_key(key, k)
        
        event = {
            'type': 'key_press',
            'key': k,
            'time': self._get_delay()
        }
        
        self.events.append(event)
        self.event_recorded.emit(event)
    
    @log_exceptions("RecorderV2.on_release")
    def on_release(self, key):
        """Keyboard release event"""
        if not self.recording:
            return
        
        try:
            k = key.char
        except AttributeError:
            k = str(key)
        
        if k is None:
            k = str(key)
            
        k = self._normalize_key(key, k)
        
        event = {
            'type': 'key_release',
            'key': k,
            'time': self._get_delay()
        }
        
        self.events.append(event)
