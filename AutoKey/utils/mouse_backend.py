"""
Mouse Backend for 3D Games
Provides relative delta mouse movement using SendInput
"""
import ctypes
from ctypes import wintypes
import time

# Windows constants
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_ABSOLUTE = 0x8000

# Input structures
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_input", _INPUT)
    ]

INPUT_MOUSE = 0

class MouseBackend:
    """
    Backend for mouse movement with 2D/3D mode detection
    """
    
    def __init__(self):
        self.mode = "auto"  # "auto", "force_ui", "force_3d"
        self._is_3d_active = False
        
    def detect_3d_mode(self):
        """
        Auto-detect if we're in 3D mode by checking:
        - Cursor visibility
        - Cursor lock (ClipCursor)
        - Raw input mode
        """
        try:
            # Check if cursor is hidden
            cursor_info = wintypes.CURSORINFO()
            cursor_info.cbSize = ctypes.sizeof(cursor_info)
            if ctypes.windll.user32.GetCursorInfo(ctypes.byref(cursor_info)):
                if cursor_info.flags == 0:  # Cursor hidden
                    return True
            
            # Check if cursor is clipped (locked to window)
            rect = wintypes.RECT()
            if ctypes.windll.user32.GetClipCursor(ctypes.byref(rect)):
                # If clipped to small area, likely 3D
                width = rect.right - rect.left
                height = rect.bottom - rect.top
                if width < 1920 and height < 1080:  # Smaller than full screen
                    return True
            
            return False
        except:
            return False
    
    def should_use_relative(self):
        """Determine if we should use relative delta movement"""
        if self.mode == "force_3d":
            return True
        elif self.mode == "force_ui":
            return False
        else:  # auto
            self._is_3d_active = self.detect_3d_mode()
            return self._is_3d_active
    
    def move_relative(self, dx, dy):
        """
        Move mouse by relative delta using SendInput
        Does NOT move cursor position, for 3D camera control
        """
        input_struct = INPUT()
        input_struct.type = INPUT_MOUSE
        input_struct.mi = MOUSEINPUT()
        input_struct.mi.dx = int(dx)
        input_struct.mi.dy = int(dy)
        input_struct.mi.dwFlags = MOUSEEVENTF_MOVE  # Relative movement
        input_struct.mi.time = 0
        input_struct.mi.dwExtraInfo = None
        
        ctypes.windll.user32.SendInput(1, ctypes.byref(input_struct), ctypes.sizeof(input_struct))
    
    def move_absolute(self, x, y):
        """
        Move cursor to absolute position (for 2D UI)
        """
        # Scale to 0-65535 range
        screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        screen_height = ctypes.windll.user32.GetSystemMetrics(1)
        
        abs_x = int(x * 65535 / screen_width)
        abs_y = int(y * 65535 / screen_height)
        
        input_struct = INPUT()
        input_struct.type = INPUT_MOUSE
        input_struct.mi = MOUSEINPUT()
        input_struct.mi.dx = abs_x
        input_struct.mi.dy = abs_y
        input_struct.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
        input_struct.mi.time = 0
        input_struct.mi.dwExtraInfo = None
        
        ctypes.windll.user32.SendInput(1, ctypes.byref(input_struct), ctypes.sizeof(input_struct))
    
    def set_mode(self, mode):
        """Set mouse mode: 'auto', 'force_ui', 'force_3d'"""
        if mode in ["auto", "force_ui", "force_3d"]:
            self.mode = mode
            print(f"Mouse mode set to: {mode}")


class HighPrecisionTicker:
    """
    Fixed tick playback at ≥240Hz with coalescing
    """
    
    def __init__(self, tick_hz=240):
        self.tick_hz = tick_hz
        self.tick_interval = 1.0 / tick_hz
        self.accumulated_dx = 0
        self.accumulated_dy = 0
        self.last_tick_time = 0
        
    def start(self):
        """Start ticker"""
        self.last_tick_time = time.perf_counter()
        self.accumulated_dx = 0
        self.accumulated_dy = 0
    
    def add_delta(self, dx, dy):
        """Accumulate mouse delta"""
        self.accumulated_dx += dx
        self.accumulated_dy += dy
    
    def tick(self, mouse_backend):
        """
        Execute one tick:
        - Wait until next tick time
        - Flush accumulated delta
        - Return True if delta was sent, False if coalesced
        """
        now = time.perf_counter()
        next_tick = self.last_tick_time + self.tick_interval
        
        # Wait until next tick
        wait = next_tick - now
        if wait > 0:
            time.sleep(wait)
        
        # Send accumulated delta
        if self.accumulated_dx != 0 or self.accumulated_dy != 0:
            mouse_backend.move_relative(self.accumulated_dx, self.accumulated_dy)
            self.accumulated_dx = 0
            self.accumulated_dy = 0
            sent = True
        else:
            sent = False
        
        self.last_tick_time = next_tick
        return sent
