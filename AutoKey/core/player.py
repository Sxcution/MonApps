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
        # Sort events by time just in case
        sorted_events = sorted(self.events, key=lambda x: x['time'])
        
        for event in sorted_events:
            if self.stop_event.is_set():
                break
            
            # Calculate wait time
            target_time = start_time + event['time']
            current_time = time.time()
            wait_time = target_time - current_time
            
            if wait_time > 0:
                time.sleep(wait_time)
            
            self.execute_event(event)

    def execute_event(self, event):
        etype = event['type']
        
        if etype in ['mouse_move', 'mouse_click']:
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
                # Move first if needed (usually click implies move to that spot)
                # But if ignore_coordinates is True, we are already there.
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
            
        elif etype == 'wait_image':
            from utils.image_finder import ImageFinder
            print(f"Waiting for image: {event['path']}")
            pos = ImageFinder.find_image_on_screen(event['path'], timeout=event.get('timeout', 30))
            if pos:
                print(f"Image found at {pos}")
                # Optional: Move mouse to image?
                # self.mouse.position = pos
            else:
                print("Image not found within timeout.")

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
