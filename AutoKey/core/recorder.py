import time
import threading
from pynput import mouse, keyboard
from PyQt6.QtCore import QObject, pyqtSignal

class Recorder(QObject):
    # Signal to emit recorded events: (event_type, details)
    event_recorded = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.recording = False
        self.start_time = 0
        self.mouse_listener = None
        self.keyboard_listener = None
        self.events = []

    def start_recording(self):
        self.recording = True
        self.events = []
        self.start_time = time.time()
        self.last_time = self.start_time # Initialize for relative deltas
        
        # Start listeners
        self.mouse_listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll)
        
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
            
        self.mouse_listener.start()
        self.keyboard_listener.start()
        print("Recording started...")

    def stop_recording(self):
        self.recording = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        print("Recording stopped.")
        return self.events

    def _get_delay(self):
        now = time.time()
        delta = now - self.last_time
        self.last_time = now
        return delta

    def on_move(self, x, y):
        if not self.recording: return
        # Optimization: Don't record every single pixel move if not needed, 
        # but user asked for "precise absolute", so we record.
        # We might want to throttle this in the future.
        event = {
            'type': 'mouse_move',
            'x': x,
            'y': y,
            'time': self._get_delay()
        }
        self.events.append(event)
        # self.event_recorded.emit(event) # Optional: emit for real-time update

    def on_click(self, x, y, button, pressed):
        if not self.recording: return
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

    def on_scroll(self, x, y, dx, dy):
        if not self.recording: return
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

    def on_press(self, key):
        if not self.recording: return
        try:
            k = key.char
        except AttributeError:
            k = str(key)
            
        event = {
            'type': 'key_press',
            'key': k,
            'time': self._get_delay()
        }
        self.events.append(event)
        self.event_recorded.emit(event)

    def on_release(self, key):
        if not self.recording: return
        try:
            k = key.char
        except AttributeError:
            k = str(key)
            
        event = {
            'type': 'key_release',
            'key': k,
            'time': self._get_delay()
        }
        self.events.append(event)
        # self.event_recorded.emit(event)
