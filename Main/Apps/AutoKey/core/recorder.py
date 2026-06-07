import ctypes
import sys
import threading
import time
from ctypes import wintypes

from PySide6.QtCore import QObject, Signal

from core.error_logger import log_exception, log_exceptions


IS_WINDOWS = sys.platform.startswith("win")

if IS_WINDOWS:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong
    LRESULT = ctypes.c_longlong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long
    HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

    WH_KEYBOARD_LL = 13
    WH_MOUSE_LL = 14
    HC_ACTION = 0
    WM_QUIT = 0x0012

    WM_MOUSEMOVE = 0x0200
    WM_LBUTTONDOWN = 0x0201
    WM_LBUTTONUP = 0x0202
    WM_RBUTTONDOWN = 0x0204
    WM_RBUTTONUP = 0x0205
    WM_MBUTTONDOWN = 0x0207
    WM_MBUTTONUP = 0x0208
    WM_MOUSEWHEEL = 0x020A

    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101
    WM_SYSKEYDOWN = 0x0104
    WM_SYSKEYUP = 0x0105

    class POINT(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

    class MSLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ("pt", POINT),
            ("mouseData", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class KBDLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ("vkCode", wintypes.DWORD),
            ("scanCode", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    user32.SetWindowsHookExW.argtypes = [
        ctypes.c_int,
        HOOKPROC,
        wintypes.HINSTANCE,
        wintypes.DWORD,
    ]
    user32.SetWindowsHookExW.restype = wintypes.HHOOK
    user32.CallNextHookEx.argtypes = [
        wintypes.HHOOK,
        ctypes.c_int,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    user32.CallNextHookEx.restype = LRESULT
    user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
    user32.UnhookWindowsHookEx.restype = wintypes.BOOL
    user32.PostThreadMessageW.argtypes = [
        wintypes.DWORD,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    user32.PostThreadMessageW.restype = wintypes.BOOL
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = wintypes.HMODULE


class Recorder(QObject):
    event_recorded = Signal(dict)

    def __init__(self):
        super().__init__()
        self.recording = False
        self.start_time = 0
        self.last_time = 0
        self.events = []

        self.mouse_move_interval = 0.05
        self.mouse_move_min_distance = 2
        self.last_mouse_move_time = 0
        self.last_mouse_position = None
        self.pending_mouse_position = None

        self._event_lock = threading.RLock()
        self._pressed_vk_codes = set()

        self.mouse_listener = None
        self.keyboard_listener = None
        self._mouse_thread = None
        self._keyboard_thread = None
        self._mouse_hook = None
        self._keyboard_hook = None
        self._mouse_proc = None
        self._keyboard_proc = None
        self._mouse_thread_id = 0
        self._keyboard_thread_id = 0
        self._mouse_ready = threading.Event()
        self._keyboard_ready = threading.Event()

    def start_recording(self):
        self.recording = True
        self.events = []
        self.start_time = time.time()
        self.last_time = self.start_time
        self.last_mouse_move_time = 0
        self.last_mouse_position = None
        self.pending_mouse_position = None
        self._pressed_vk_codes.clear()
        self._mouse_ready.clear()
        self._keyboard_ready.clear()

        if IS_WINDOWS:
            self._start_windows_hooks()
        else:
            self._start_pynput_fallback()

        print("Recording started...")

    def stop_recording(self):
        self._flush_pending_mouse_move()
        self.recording = False

        if IS_WINDOWS:
            self._stop_windows_hooks()
        else:
            self._stop_pynput_fallback()

        print(f"Recording stopped. Captured {len(self.events)} events.")
        return list(self.events)

    def _start_windows_hooks(self):
        self._mouse_thread = threading.Thread(
            target=self._mouse_hook_loop,
            name="AutoKeyMouseHook",
            daemon=True,
        )
        self._keyboard_thread = threading.Thread(
            target=self._keyboard_hook_loop,
            name="AutoKeyKeyboardHook",
            daemon=True,
        )
        self._mouse_thread.start()
        self._keyboard_thread.start()

        mouse_ok = self._mouse_ready.wait(1.0) and bool(self._mouse_hook)
        keyboard_ok = self._keyboard_ready.wait(1.0) and bool(self._keyboard_hook)
        print(f"Recorder hooks: mouse={mouse_ok}, keyboard={keyboard_ok}")

    def _stop_windows_hooks(self):
        if self._mouse_hook:
            user32.UnhookWindowsHookEx(self._mouse_hook)
            self._mouse_hook = None
        if self._keyboard_hook:
            user32.UnhookWindowsHookEx(self._keyboard_hook)
            self._keyboard_hook = None

        if self._mouse_thread_id:
            user32.PostThreadMessageW(self._mouse_thread_id, WM_QUIT, 0, 0)
        if self._keyboard_thread_id:
            user32.PostThreadMessageW(self._keyboard_thread_id, WM_QUIT, 0, 0)

        for thread in [self._mouse_thread, self._keyboard_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=1.0)

        self._mouse_thread = None
        self._keyboard_thread = None
        self._mouse_proc = None
        self._keyboard_proc = None
        self._mouse_thread_id = 0
        self._keyboard_thread_id = 0

    def _mouse_hook_loop(self):
        try:
            self._mouse_thread_id = kernel32.GetCurrentThreadId()

            @HOOKPROC
            def mouse_proc(n_code, w_param, l_param):
                try:
                    if n_code == HC_ACTION and self.recording:
                        info = ctypes.cast(l_param, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                        self._handle_mouse_message(w_param, info)
                except Exception:
                    log_exception("Recorder.mouse_proc")
                return user32.CallNextHookEx(self._mouse_hook, n_code, w_param, l_param)

            self._mouse_proc = mouse_proc
            self._mouse_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, mouse_proc, None, 0)
            self._mouse_ready.set()

            if not self._mouse_hook:
                log_exception(
                    "Recorder._mouse_hook_loop",
                    extra={"last_error": ctypes.get_last_error()},
                )
                return

            self._message_loop()
        except Exception:
            self._mouse_ready.set()
            log_exception("Recorder._mouse_hook_loop")

    def _keyboard_hook_loop(self):
        try:
            self._keyboard_thread_id = kernel32.GetCurrentThreadId()

            @HOOKPROC
            def keyboard_proc(n_code, w_param, l_param):
                try:
                    if n_code == HC_ACTION and self.recording:
                        info = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                        self._handle_keyboard_message(w_param, info)
                except Exception:
                    log_exception("Recorder.keyboard_proc")
                return user32.CallNextHookEx(self._keyboard_hook, n_code, w_param, l_param)

            self._keyboard_proc = keyboard_proc
            self._keyboard_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, keyboard_proc, None, 0)
            self._keyboard_ready.set()

            if not self._keyboard_hook:
                log_exception(
                    "Recorder._keyboard_hook_loop",
                    extra={"last_error": ctypes.get_last_error()},
                )
                return

            self._message_loop()
        except Exception:
            self._keyboard_ready.set()
            log_exception("Recorder._keyboard_hook_loop")

    def _message_loop(self):
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def _handle_mouse_message(self, message, info):
        x, y = int(info.pt.x), int(info.pt.y)

        if message == WM_MOUSEMOVE:
            self.on_move(x, y)
        elif message in (WM_LBUTTONDOWN, WM_LBUTTONUP):
            self.on_click(x, y, "Button.left", message == WM_LBUTTONDOWN)
        elif message in (WM_RBUTTONDOWN, WM_RBUTTONUP):
            self.on_click(x, y, "Button.right", message == WM_RBUTTONDOWN)
        elif message in (WM_MBUTTONDOWN, WM_MBUTTONUP):
            self.on_click(x, y, "Button.middle", message == WM_MBUTTONDOWN)
        elif message == WM_MOUSEWHEEL:
            raw_delta = (int(info.mouseData) >> 16) & 0xFFFF
            if raw_delta >= 0x8000:
                raw_delta -= 0x10000
            dy = int(raw_delta / 120) if raw_delta else 0
            self.on_scroll(x, y, 0, dy)

    def _handle_keyboard_message(self, message, info):
        vk_code = int(info.vkCode)
        scan_code = int(info.scanCode)
        is_press = message in (WM_KEYDOWN, WM_SYSKEYDOWN)
        is_release = message in (WM_KEYUP, WM_SYSKEYUP)

        if is_press:
            if vk_code in self._pressed_vk_codes:
                return
            self._pressed_vk_codes.add(vk_code)
            self._record_key("key_press", self._key_name_from_vk(vk_code, scan_code))
        elif is_release:
            self._pressed_vk_codes.discard(vk_code)
            self._record_key("key_release", self._key_name_from_vk(vk_code, scan_code))

    def _start_pynput_fallback(self):
        from pynput import keyboard, mouse

        self.mouse_listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll,
        )
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release,
        )
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def _stop_pynput_fallback(self):
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()

    def _get_delay_unlocked(self):
        now = time.time()
        delta = now - self.last_time
        self.last_time = now
        return delta

    @log_exceptions("Recorder.on_move")
    def on_move(self, x, y):
        if not self.recording:
            return

        with self._event_lock:
            now = time.time()
            current_position = (x, y)

            if self.last_mouse_position is not None:
                dx = abs(x - self.last_mouse_position[0])
                dy = abs(y - self.last_mouse_position[1])
                moved_too_little = dx < self.mouse_move_min_distance and dy < self.mouse_move_min_distance
                too_soon = (now - self.last_mouse_move_time) < self.mouse_move_interval

                if moved_too_little or too_soon:
                    self.pending_mouse_position = current_position
                    return

            self._record_mouse_move_unlocked(x, y, now)

    def _record_mouse_move_unlocked(self, x, y, event_time=None):
        event = {
            "type": "mouse_move",
            "x": int(x),
            "y": int(y),
            "time": self._get_delay_unlocked(),
        }
        self.events.append(event)
        self.last_mouse_position = (int(x), int(y))
        self.last_mouse_move_time = event_time if event_time is not None else time.time()
        self.pending_mouse_position = None

    def _flush_pending_mouse_move(self):
        with self._event_lock:
            if not self.pending_mouse_position:
                return

            x, y = self.pending_mouse_position
            if self.last_mouse_position == (x, y):
                self.pending_mouse_position = None
                return

            self._record_mouse_move_unlocked(x, y, time.time())

    @log_exceptions("Recorder.on_click")
    def on_click(self, x, y, button, pressed):
        if not self.recording:
            return

        with self._event_lock:
            event = {
                "type": "mouse_click",
                "x": int(x),
                "y": int(y),
                "button": str(button),
                "pressed": bool(pressed),
                "time": self._get_delay_unlocked(),
            }
            self.events.append(event)

    @log_exceptions("Recorder.on_scroll")
    def on_scroll(self, x, y, dx, dy):
        if not self.recording:
            return

        with self._event_lock:
            event = {
                "type": "mouse_scroll",
                "x": int(x),
                "y": int(y),
                "dx": int(dx),
                "dy": int(dy),
                "time": self._get_delay_unlocked(),
            }
            self.events.append(event)

    @log_exceptions("Recorder.on_press")
    def on_press(self, key):
        self._record_key("key_press", self._normalize_pynput_key(key))

    @log_exceptions("Recorder.on_release")
    def on_release(self, key):
        self._record_key("key_release", self._normalize_pynput_key(key))

    def _record_key(self, event_type, key_name):
        if not self.recording or not key_name:
            return

        with self._event_lock:
            event = {
                "type": event_type,
                "key": key_name,
                "time": self._get_delay_unlocked(),
            }
            self.events.append(event)


    def _normalize_pynput_key(self, key):
        try:
            from pynput import keyboard

            try:
                key_name = key.char
            except AttributeError:
                key_name = str(key)

            if key_name is None:
                key_name = str(key)

            if isinstance(key, keyboard.KeyCode) and key_name and len(key_name) == 1 and ord(key_name) < 32:
                vk = getattr(key, "vk", None)
                if vk is not None:
                    if 65 <= vk <= 90:
                        key_name = chr(vk).lower()
                    elif 48 <= vk <= 57:
                        key_name = chr(vk)

            if isinstance(key_name, str) and key_name.startswith("Key."):
                key_name = key_name.replace("Key.", "")
                if key_name.endswith("_l") or key_name.endswith("_r"):
                    key_name = key_name[:-2]
                key_name = key_name.title()

            vk = getattr(key, "vk", None)
            if vk is not None and 96 <= vk <= 105:
                key_name = f"Num {vk - 96}"

            return key_name
        except Exception:
            log_exception("Recorder._normalize_pynput_key", extra={"key": str(key)})
            return str(key)

    def _key_name_from_vk(self, vk_code, scan_code):
        if 0x41 <= vk_code <= 0x5A:
            return chr(vk_code).lower()
        if 0x30 <= vk_code <= 0x39:
            return chr(vk_code)
        if 0x60 <= vk_code <= 0x69:
            return f"Num {vk_code - 0x60}"
        if 0x70 <= vk_code <= 0x7B:
            return f"F{vk_code - 0x6F}"

        special_keys = {
            0x08: "Backspace",
            0x09: "Tab",
            0x0D: "Enter",
            0x10: "Shift",
            0x11: "Ctrl",
            0x12: "Alt",
            0x14: "Caps_Lock",
            0x1B: "Esc",
            0x20: "Space",
            0x21: "Page_Up",
            0x22: "Page_Down",
            0x23: "End",
            0x24: "Home",
            0x25: "Left",
            0x26: "Up",
            0x27: "Right",
            0x28: "Down",
            0x2D: "Insert",
            0x2E: "Delete",
            0x5B: "LWin",
            0x5C: "RWin",
            0xA0: "Shift",
            0xA1: "Shift",
            0xA2: "Ctrl",
            0xA3: "Ctrl",
            0xA4: "Alt",
            0xA5: "Alt",
            0x6A: "Num *",
            0x6B: "Num +",
            0x6D: "Num -",
            0x6E: "Num .",
            0x6F: "Num /",
            0xBA: ";",
            0xBB: "=",
            0xBC: ",",
            0xBD: "-",
            0xBE: ".",
            0xBF: "/",
            0xC0: "`",
            0xDB: "[",
            0xDC: "\\",
            0xDD: "]",
            0xDE: "'",
        }
        if vk_code in special_keys:
            return special_keys[vk_code]

        char = self._unicode_from_vk(vk_code, scan_code)
        if char:
            return char.lower() if char.isalpha() else char

        return f"VK_{vk_code}"

    def _unicode_from_vk(self, vk_code, scan_code):
        if not IS_WINDOWS:
            return None
        try:
            state = (ctypes.c_ubyte * 256)()
            user32.GetKeyboardState(ctypes.byref(state))
            buff = ctypes.create_unicode_buffer(8)
            result = user32.ToUnicode(vk_code, scan_code, state, buff, len(buff), 0)
            if result == 1 and buff.value:
                return buff.value[0]
        except Exception:
            log_exception("Recorder._unicode_from_vk")
        return None
