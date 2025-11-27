import time
import threading
import pyautogui
import random
import ctypes
from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController, Button

class Player(threading.Thread):
    def __init__(self, events, stop_event):
        super().__init__()
        self.events = events
        self.stop_event = stop_event
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self.daemon = True

    def run(self):
        start_time = time.time()
        # Sort events by time just in case, but for GoTo we need index access
        # We assume events are already sorted or we sort them once
        self.events.sort(key=lambda x: x['time'])
        
        # We need to handle "Go to" which means jumping indexes.
        # But the events have 'time' which is relative to start. 
        # If we jump, we might need to adjust timing or just execute logic.
        # For simplicity in this macro recorder, "Go to" usually implies logic flow.
        
        idx = 0
        while idx < len(self.events):
            if self.stop_event.is_set():
                break
                
            event = self.events[idx]
            
            # Calculate wait time
            # Note: If we jumped, the time logic might be tricky. 
            # Simple approach: Respect the 'time' delta from previous event or start.
            # But 'time' in event is absolute offset from start.
            # If we jump back, we can't wait for absolute time.
            # We'll just execute immediately if we jumped, or use simple delays.
            # For now, let's stick to the original timing logic for sequential, 
            # but if we jump, we might need to reset start_time or ignore timing.
            
            # BETTER APPROACH for Logic Macros:
            # Execute step, then wait for next step's delay?
            # The current model has 'time' as "Time since start".
            # Let's try to respect it if we are moving forward, but if we jump, we just run.
            
            target_time = start_time + event['time']
            current_time = time.time()
            wait_time = target_time - current_time
            
            if wait_time > 0:
                time.sleep(wait_time)
            
            # Execute and check for flow control
            next_idx = self.execute_event(event, idx)
            
            if next_idx is not None:
                idx = next_idx
                # Reset start time to align with new sequence if needed?
                # Or just let it run fast until it catches up?
                # For loops, we usually want to run as fast as possible or with fixed delays.
                # Let's just update idx.
            else:
                idx += 1

    def execute_event(self, event, current_idx):
        """
        Executes event. Returns next_idx if a jump is needed, else None.
        """
        etype = event['type']
        
        if etype == 'detect_image':
            return self.handle_detect_image(event, current_idx)
            
        elif etype in ['mouse_move', 'mouse_click']:
            # ... existing mouse logic ...
            self._handle_mouse(event)
            
        elif etype == 'mouse_scroll':
            self.mouse.scroll(event.get('dx', 0), event.get('dy', 0))
            
        elif etype == 'key_press':
            key = self._parse_key(event['key'])
            if key:
                self.keyboard.press(key)
            
        elif etype == 'key_release':
            key = self._parse_key(event['key'])
            if key:
                self.keyboard.release(key)
                
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
                # Not implemented yet, default to full screen
                pass
        
        # Wait for image
        timeout = event.get('wait_timeout', 0)
        tolerance = event.get('tolerance', 0)
        # Convert tolerance 0-255 to confidence 0.0-1.0 (inverted)
        # 0 tolerance = 1.0 confidence? Or 0 tolerance = exact match?
        # Usually tolerance means "how much difference is allowed".
        # 0 tolerance -> 1.0 confidence. 255 tolerance -> 0.0 confidence.
        # Let's map: confidence = 1.0 - (tolerance / 255.0)
        # Adjusted: 0 tolerance now maps to ~0.9975 to allow tiny rendering differences
        confidence = 1.0 - ((tolerance + 1) / 400.0) # slightly looser mapping
        if confidence < 0.1: confidence = 0.1
        
        print(f"Waiting for image: {image_path}, timeout={timeout}, conf={confidence}")
        
        found_rect = wait_for_image(image_path, timeout=timeout, confidence=confidence, region=region)
        
        if found_rect:
            print(f"Image found at {found_rect}")
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
            goto = event.get('goto_found', 'Start')
            return self._resolve_goto(goto, current_idx)
            
        else:
            print("Image NOT found")
            # Not found logic
            goto = event.get('goto_not_found', 'End')
            return self._resolve_goto(goto, current_idx)

    def _resolve_goto(self, goto_str, current_idx):
        if goto_str == 'Start':
            return 0
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

    def _parse_key(self, key_str):
        from pynput.keyboard import Key
        if key_str.startswith('Key.'):
            # It's a special key
            attr = key_str.split('.')[1]
            try:
                return getattr(Key, attr)
            except AttributeError:
                print(f"Unknown key: {key_str}")
                return None
        elif len(key_str) > 1 and key_str.startswith("'") and key_str.endswith("'"):
             # It might be a quoted char like "'a'"
             return key_str[1:-1]
        else:
            # Regular char
            return key_str
