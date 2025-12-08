# Project Structure - Android_Tool

This module provides Android ROM modification and management tools.

## Files
- `Main.py`: Entry point, MainHub class with QTabWidget containing all modules
- `window_settings.json`: Saves window size/position

## Sub-directories
- `modules/`: Contains tool modules
    - `ModAndroid/ModAndroid.pyw`: Core ROM patching module
        - ADB Comment tab: Execute ADB commands
        - Dịch ngược Jar/APK tab: Decompile/recompile tools  
        - Patch File tab: Smart ROM patcher with drag-drop support
    - `ModAndroid/worker_file_import.py`: Background workers for heavy operations
        - `FileImportWorker`: Copy large files without UI freeze
        - `AdbCommandWorker`: Run adb push/shell on background thread
    - `Telegram/telegram_module.py`: Telegram account management
- `logs/`: Application logs
- `icons/`: Tab icons (android.png, telegram.png, etc.)
- `Patched/`: Output folder for patched files

## Key Features
- Shared log panel (Function Log Output) for all modules
- Drag & drop file detection for ROM patching
- Multi-threaded patching operations
- TWRP wipe data before flash ROM (clean install)
- Background worker for heavy ADB operations (no UI freeze)

## Dependencies
- PySide6
- ADB (Android Debug Bridge)
