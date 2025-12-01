# Project Structure: AutoKey

## Root Directory
- `main.py`: Entry point of the application. Handles Admin check, Qt setup, and global exception hooks.
- `naming_registry.json`: Central registry for UI variable names and configuration keys.
- `run.bat`: Batch script to run the application.
- `FarmGym.json`: Sample macro file (JSON format).
- `work.md`: Developer notes/scratchpad.

## Core (`core/`)
- `recorder.py`: Handles keyboard/mouse recording using `pynput`.
- `player.py`: Handles macro playback using `utils.direct_input` and `pynput`.
- `models.py`: Data models (if any).

## UI (`ui/`)
- `main_window.py`: Main GUI logic, hotkey handling, and event table management.
- `settings_dialog.py`: Configuration dialog for Hotkeys, Play settings, etc.
- `toolbar.py`: Custom toolbar implementation.
- `playback_overlay.py`: Overlay window shown during playback.
- `image_search_dialog.py`: Dialog for configuring "Wait for Image" events.
- `auto_detect_dialog.py`: Dialog for configuring Auto Detect with multiple images/text detection.
- `text_search_dialog.py`: Dialog for configuring text search events.
- `mouse_dialog.py`: Dialog for editing mouse events.
- `keyboard_dialog.py`: Dialog for editing keyboard events.
- `delegates.py`: Custom Qt item delegates for table rendering.
- `steps_interface.py`: Steps/Macro interface page with table and saved macros list.
- `playback_log_dialog.py`: Dialog showing playback logs and errors.
- `styles.py`: CSS stylesheets for the application.

## Utils (`utils/`)
- `direct_input.py`: Low-level Windows API wrapper for DirectInput simulation (games).
- `image_finder.py`: OpenCV wrapper for image matching.
- `window_utils.py`: Helpers for window management (focus, rect).
- `ocr_engine.py`: OCR functionality (Tesseract/Windows OCR).
- `snipping_tool.py`: Screen capture/snipping tool for defining regions.

## Tests (`/`)

