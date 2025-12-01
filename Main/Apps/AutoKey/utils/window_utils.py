import ctypes
from ctypes import wintypes

def get_foreground_window_rect():
    """Get the rectangle of the currently focused window"""
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    if not hwnd:
        return None
        
    rect = wintypes.RECT()
    if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return {
            'left': rect.left,
            'top': rect.top,
            'width': rect.right - rect.left,
            'height': rect.bottom - rect.top
        }
    return None

def get_screen_rect():
    """Get the primary screen rectangle"""
    user32 = ctypes.windll.user32
    return {
        'left': 0,
        'top': 0,
        'width': user32.GetSystemMetrics(0), # SM_CXSCREEN
        'height': user32.GetSystemMetrics(1) # SM_CYSCREEN
    }
