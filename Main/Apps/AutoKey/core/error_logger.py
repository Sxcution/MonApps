import sys
import traceback
import threading
from datetime import datetime
import os

def log_exception(context: str = "", exc_type=None, exc_value=None, exc_tb=None, extra=None):
    """
    Log an exception causing a crash or error to error.log with details.
    """
    if exc_type is None or exc_value is None or exc_tb is None:
        exc_type, exc_value, exc_tb = sys.exc_info()
    
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    thread_name = threading.current_thread().name
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    line = f"[{ts}] [Thread={thread_name}] [Context={context}]\n{tb_str}"
    
    if extra:
        line += f"EXTRA INFO: {extra}\n"
    
    line += "-" * 50 + "\n"
    
    try:
        # Ensure we write to error.log in the current working directory or app root
        # Assuming run execution sets CWD correctly, otherwise might need absolute path logic
        with open("error.log", "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        # Fallback to stderr if file write fails
        print(f"CRITICAL: Failed to write to error.log: {e}")
        print(line)

def log_exceptions(context: str, re_raise: bool = False):
    """
    Decorator to wrap functions and log unhandled exceptions.
    Useful for callback functions in threads (like pynput listeners).
    - If re_raise = False: log error and swallow it, keeping the thread alive.
    - If re_raise = True: log error and re-raise.
    """
    def decorator(fn):
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception:
                log_exception(context)
                if re_raise:
                    raise 
        return wrapper
    return decorator
