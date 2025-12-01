import sys
from PySide6.QtCore import QObject, Signal

class LogManager(QObject):
    log_signal = Signal(str)
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self

    def write(self, text):
        if self.original_stdout:
            try:
                self.original_stdout.write(text)
            except Exception:
                pass
        if "Unknown property box-shadow" not in text and "QFont::setPointSize" not in text:
            self.log_signal.emit(text)

    def flush(self):
        if self.original_stdout:
            try:
                self.original_stdout.flush()
            except Exception:
                pass

    @property
    def buffer(self):
        """Return buffer attribute for compatibility with TextIOWrapper"""
        if self.original_stdout and hasattr(self.original_stdout, 'buffer'):
            return self.original_stdout.buffer
        # Fallback: return sys.__stdout__.buffer if available
        if hasattr(sys.__stdout__, 'buffer'):
            return sys.__stdout__.buffer
        return None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
