import ctypes
import time

# DirectInput Scan Codes
DIK_ESCAPE = 0x01
DIK_1 = 0x02
DIK_2 = 0x03
DIK_3 = 0x04
DIK_4 = 0x05
DIK_5 = 0x06
DIK_6 = 0x07
DIK_7 = 0x08
DIK_8 = 0x09
DIK_9 = 0x0A
DIK_0 = 0x0B
DIK_MINUS = 0x0C
DIK_EQUALS = 0x0D
DIK_BACK = 0x0E
DIK_TAB = 0x0F
DIK_Q = 0x10
DIK_W = 0x11
DIK_E = 0x12
DIK_R = 0x13
DIK_T = 0x14
DIK_Y = 0x15
DIK_U = 0x16
DIK_I = 0x17
DIK_O = 0x18
DIK_P = 0x19
DIK_LBRACKET = 0x1A
DIK_RBRACKET = 0x1B
DIK_RETURN = 0x1C
DIK_LCONTROL = 0x1D
DIK_A = 0x1E
DIK_S = 0x1F
DIK_D = 0x20
DIK_F = 0x21
DIK_G = 0x22
DIK_H = 0x23
DIK_J = 0x24
DIK_K = 0x25
DIK_L = 0x26
DIK_SEMICOLON = 0x27
DIK_APOSTROPHE = 0x28
DIK_GRAVE = 0x29
DIK_LSHIFT = 0x2A
DIK_BACKSLASH = 0x2B
DIK_Z = 0x2C
DIK_X = 0x2D
DIK_C = 0x2E
DIK_V = 0x2F
DIK_B = 0x30
DIK_N = 0x31
DIK_M = 0x32
DIK_COMMA = 0x33
DIK_PERIOD = 0x34
DIK_SLASH = 0x35
DIK_RSHIFT = 0x36
DIK_MULTIPLY = 0x37
DIK_LMENU = 0x38
DIK_SPACE = 0x39
DIK_CAPITAL = 0x3A
DIK_F1 = 0x3B
DIK_F2 = 0x3C
DIK_F3 = 0x3D
DIK_F4 = 0x3E
DIK_F5 = 0x3F
DIK_F6 = 0x40
DIK_F7 = 0x41
DIK_F8 = 0x42
DIK_F9 = 0x43
DIK_F10 = 0x44
DIK_NUMLOCK = 0x45
DIK_SCROLL = 0x46
DIK_NUMPAD7 = 0x47
DIK_NUMPAD8 = 0x48
DIK_NUMPAD9 = 0x49
DIK_SUBTRACT = 0x4A
DIK_NUMPAD4 = 0x4B
DIK_NUMPAD5 = 0x4C
DIK_NUMPAD6 = 0x4D
DIK_ADD = 0x4E
DIK_NUMPAD1 = 0x4F
DIK_NUMPAD2 = 0x50
DIK_NUMPAD3 = 0x51
DIK_NUMPAD0 = 0x52
DIK_DECIMAL = 0x53
DIK_F11 = 0x57
DIK_F12 = 0x58

# Extended scan codes (require KEYEVENTF_EXTENDEDKEY flag)
DIK_RCONTROL = 0x9D  # Right Control (extended)
DIK_RMENU = 0xB8     # Right Alt / AltGr (extended)
DIK_HOME = 0xC7      # Home (extended)
DIK_UP_EXT = 0xC8    # Up Arrow (extended)
DIK_PRIOR = 0xC9     # Page Up (extended)
DIK_LEFT_EXT = 0xCB  # Left Arrow (extended)
DIK_RIGHT_EXT = 0xCD # Right Arrow (extended)
DIK_END = 0xCF       # End (extended)
DIK_DOWN_EXT = 0xD0  # Down Arrow (extended)
DIK_NEXT = 0xD1      # Page Down (extended)
DIK_INSERT = 0xD2    # Insert (extended)
DIK_DELETE_EXT = 0xD3 # Delete (extended)
DIK_LWIN = 0xDB      # Left Windows key (extended)
DIK_RWIN = 0xDC      # Right Windows key (extended)

# Compatibility aliases (use non-extended for numpad compatibility)
DIK_UP = 0x48      # Can be NUMPAD8 or Up Arrow
DIK_LEFT = 0x4B    # Can be NUMPAD4 or Left Arrow
DIK_RIGHT = 0x4D   # Can be NUMPAD6 or Right Arrow
DIK_DOWN = 0x50    # Can be NUMPAD2 or Down Arrow
DIK_DELETE = 0x53  # Can be DECIMAL or Delete

# C struct redefinitions 
PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_ushort),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

# Actuals Functions
def PressKey(hexKeyCode, flags=0, wVk=0):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    # 0x0008 is KEYEVENTF_SCANCODE
    ii_.ki = KeyBdInput( wVk, hexKeyCode, 0x0008 | flags, 0, ctypes.pointer(extra) )
    x = Input( ctypes.c_ulong(1), ii_ )
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def ReleaseKey(hexKeyCode, flags=0, wVk=0):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    # 0x0008 is KEYEVENTF_SCANCODE, 0x0002 is KEYEVENTF_KEYUP
    ii_.ki = KeyBdInput( wVk, hexKeyCode, 0x0008 | 0x0002 | flags, 0, ctypes.pointer(extra) )
    x = Input( ctypes.c_ulong(1), ii_ )
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

# Map string keys to DIK codes
KEY_MAPPING = {
    'escape': DIK_ESCAPE, 'esc': DIK_ESCAPE,
    '1': DIK_1, '2': DIK_2, '3': DIK_3, '4': DIK_4, '5': DIK_5,
    '6': DIK_6, '7': DIK_7, '8': DIK_8, '9': DIK_9, '0': DIK_0,
    '-': DIK_MINUS, '=': DIK_EQUALS, 'backspace': DIK_BACK, 'tab': DIK_TAB,
    'q': DIK_Q, 'w': DIK_W, 'e': DIK_E, 'r': DIK_R, 't': DIK_T, 'y': DIK_Y, 'u': DIK_U, 'i': DIK_I, 'o': DIK_O, 'p': DIK_P,
    '[': DIK_LBRACKET, ']': DIK_RBRACKET, 'enter': DIK_RETURN, 'return': DIK_RETURN,
    # Control keys
    'ctrl': DIK_LCONTROL, 'ctrl_l': DIK_LCONTROL, 'ctrl_r': DIK_RCONTROL,
    'control': DIK_LCONTROL, 'control_l': DIK_LCONTROL, 'control_r': DIK_RCONTROL,
    # Letter keys
    'a': DIK_A, 's': DIK_S, 'd': DIK_D, 'f': DIK_F, 'g': DIK_G, 'h': DIK_H, 'j': DIK_J, 'k': DIK_K, 'l': DIK_L,
    ';': DIK_SEMICOLON, "'": DIK_APOSTROPHE, '`': DIK_GRAVE,
    # Shift keys
    'shift': DIK_LSHIFT, 'shift_l': DIK_LSHIFT, 'shift_r': DIK_RSHIFT, '\\': DIK_BACKSLASH,
    'z': DIK_Z, 'x': DIK_X, 'c': DIK_C, 'v': DIK_V, 'b': DIK_B, 'n': DIK_N, 'm': DIK_M,
    ',': DIK_COMMA, '.': DIK_PERIOD, '/': DIK_SLASH,
    # Special keys
    'space': DIK_SPACE, 'caps_lock': DIK_CAPITAL,
    # Alt keys
    'alt': DIK_LMENU, 'alt_l': DIK_LMENU, 'alt_r': DIK_RMENU, 'alt_gr': DIK_RMENU,
    # Windows keys
    'cmd': DIK_LWIN, 'cmd_l': DIK_LWIN, 'cmd_r': DIK_RWIN,
    # Function keys
    'f1': DIK_F1, 'f2': DIK_F2, 'f3': DIK_F3, 'f4': DIK_F4, 'f5': DIK_F5, 'f6': DIK_F6,
    'f7': DIK_F7, 'f8': DIK_F8, 'f9': DIK_F9, 'f10': DIK_F10, 'f11': DIK_F11, 'f12': DIK_F12,
    # Arrow keys (extended)
    'up': DIK_UP_EXT, 'down': DIK_DOWN_EXT, 'left': DIK_LEFT_EXT, 'right': DIK_RIGHT_EXT,
    # Navigation keys (extended)
    'insert': DIK_INSERT, 'delete': DIK_DELETE_EXT, 'del': DIK_DELETE_EXT,
    'home': DIK_HOME, 'end': DIK_END,
    'page_up': DIK_PRIOR, 'page_down': DIK_NEXT,
    'pageup': DIK_PRIOR, 'pagedown': DIK_NEXT,  # Alternative naming
    
    # Numpad keys
    'num 0': DIK_NUMPAD0, 'num 1': DIK_NUMPAD1, 'num 2': DIK_NUMPAD2,
    'num 3': DIK_NUMPAD3, 'num 4': DIK_NUMPAD4, 'num 5': DIK_NUMPAD5,
    'num 6': DIK_NUMPAD6, 'num 7': DIK_NUMPAD7, 'num 8': DIK_NUMPAD8,
    'num 9': DIK_NUMPAD9,
    'num0': DIK_NUMPAD0, 'num1': DIK_NUMPAD1, 'num2': DIK_NUMPAD2,
    'num3': DIK_NUMPAD3, 'num4': DIK_NUMPAD4, 'num5': DIK_NUMPAD5,
    'num6': DIK_NUMPAD6, 'num7': DIK_NUMPAD7, 'num8': DIK_NUMPAD8,
    'num9': DIK_NUMPAD9,
    '+': DIK_ADD, 'add': DIK_ADD,
    'subtract': DIK_SUBTRACT,  # '-' is already mapped to DIK_MINUS (standard), but Numpad - is DIK_SUBTRACT
    'decimal': DIK_DECIMAL, 'num .': DIK_DECIMAL, 'num.': DIK_DECIMAL,
    'divide': DIK_SLASH, 'num /': DIK_SLASH, 'num/': DIK_SLASH, # Numpad / often shares DIK_SLASH or has its own? DIK_DIVIDE = 0xB5 (extended)
    'multiply': DIK_MULTIPLY, 'num *': DIK_MULTIPLY, 'num*': DIK_MULTIPLY
}

EXTENDED_KEYS = [
    'up', 'down', 'left', 'right',
    'delete', 'del', 'insert',
    'home', 'end', 'page_up', 'page_down', 'pageup', 'pagedown',
    'shift_r', 'ctrl_r', 'control_r', 'alt_r', 'alt_gr',
    'cmd', 'cmd_l', 'cmd_r'
]

def press_key(key_name):
    key_name = str(key_name).lower().replace("key.", "")
    if key_name in KEY_MAPPING:
        scancode = KEY_MAPPING[key_name]
        flags = 0x0001 if key_name in EXTENDED_KEYS else 0
        # Map Scancode to Virtual Key (MAPVK_VSC_TO_VK = 1)
        vk = ctypes.windll.user32.MapVirtualKeyW(scancode, 1)
        
        print(f"🎮 DirectInput: Pressing '{key_name}' (Scan: {hex(scancode)}, VK: {hex(vk)}, Flags: {flags})")
        PressKey(scancode, flags, vk)
    else:
        print(f"❌ DirectInput: Unknown key '{key_name}'")

def release_key(key_name):
    key_name = str(key_name).lower().replace("key.", "")
    if key_name in KEY_MAPPING:
        scancode = KEY_MAPPING[key_name]
        flags = 0x0001 if key_name in EXTENDED_KEYS else 0
        # Map Scancode to Virtual Key (MAPVK_VSC_TO_VK = 1)
        vk = ctypes.windll.user32.MapVirtualKeyW(scancode, 1)
        
        print(f"🎮 DirectInput: Releasing '{key_name}' (Scan: {hex(scancode)}, VK: {hex(vk)}, Flags: {flags})")
        ReleaseKey(scancode, flags, vk)
