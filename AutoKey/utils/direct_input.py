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
DIK_UP = 0xC8
DIK_LEFT = 0xCB
DIK_RIGHT = 0xCD
DIK_DOWN = 0xD0
DIK_DELETE = 0xD3

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
def PressKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput( 0, hexKeyCode, 0x0008, 0, ctypes.pointer(extra) )
    x = Input( ctypes.c_ulong(1), ii_ )
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def ReleaseKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput( 0, hexKeyCode, 0x0008 | 0x0002, 0, ctypes.pointer(extra) )
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
    'ctrl': DIK_LCONTROL, 'control': DIK_LCONTROL,
    'a': DIK_A, 's': DIK_S, 'd': DIK_D, 'f': DIK_F, 'g': DIK_G, 'h': DIK_H, 'j': DIK_J, 'k': DIK_K, 'l': DIK_L,
    ';': DIK_SEMICOLON, "'": DIK_APOSTROPHE, '`': DIK_GRAVE,
    'shift': DIK_LSHIFT, '\\': DIK_BACKSLASH,
    'z': DIK_Z, 'x': DIK_X, 'c': DIK_C, 'v': DIK_V, 'b': DIK_B, 'n': DIK_N, 'm': DIK_M,
    ',': DIK_COMMA, '.': DIK_PERIOD, '/': DIK_SLASH,
    'space': DIK_SPACE,
    'f1': DIK_F1, 'f2': DIK_F2, 'f3': DIK_F3, 'f4': DIK_F4, 'f5': DIK_F5, 'f6': DIK_F6,
    'f7': DIK_F7, 'f8': DIK_F8, 'f9': DIK_F9, 'f10': DIK_F10, 'f11': DIK_F11, 'f12': DIK_F12,
    'up': DIK_UP, 'down': DIK_DOWN, 'left': DIK_LEFT, 'right': DIK_RIGHT,
    'delete': DIK_DELETE, 'del': DIK_DELETE
}

def press_key(key_name):
    key_name = str(key_name).lower().replace("key.", "")
    if key_name in KEY_MAPPING:
        print(f"🎮 DirectInput: Pressing '{key_name}' (Code: {hex(KEY_MAPPING[key_name])})")
        PressKey(KEY_MAPPING[key_name])
    else:
        print(f"❌ DirectInput: Unknown key '{key_name}'")

def release_key(key_name):
    key_name = str(key_name).lower().replace("key.", "")
    if key_name in KEY_MAPPING:
        print(f"🎮 DirectInput: Releasing '{key_name}' (Code: {hex(KEY_MAPPING[key_name])})")
        ReleaseKey(KEY_MAPPING[key_name])
