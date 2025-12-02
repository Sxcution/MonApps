# Project Structure - Main Launcher

This directory contains the central launcher and the sub-projects `AutoKey` and `Android_Tool`.

## Files
- `Main.pyw`: The main entry point for the launcher. Uses `PySide6-Fluent-Widgets`.
- `config.json`: Stores user configuration (Dark Mode, Startup, External Mode).
- `naming_registry.json`: Central registry for UI element IDs and config keys.
- `check_icons.py`: Utility script to list available Fluent Icons.
- `resources/`: Application resources (icons, images).
    - `app_icon.png`: Main application icon.

## Sub-directories
    - `Apps/`: Contains embedded applications
        - `AutoKey/`: Contains the AutoKey automation tool.
            - `main.py`: Entry point for AutoKey.
            - `ui/`: UI components
                - `steps_interface.py`: Macro editor interface
                - `styles.py`: Central stylesheet definitions (Light/Dark)
        - `Notes/`: Notes application
            - `notes_module.py`: Main Notes widget and logic
            - `debug_ime.py`: Debug tool for IME/Vietnamese typing issues
    - `Android_Tool/`: Contains the Android management tool.
        - `Main.py`: Entry point for Android Tool.
    - `AHK_Tool/`: Contains the AHK helper tool.
        - `MonAHKv2.ahk`: Main AHK script (Uses RunAsUser for correct IME support)
- `core/`: Core functionality
    - `config_manager.py`: Handles loading/saving config.json
    - `log_manager.py`: Singleton for capturing stdout/stderr to log interface
    - `ai_handler.py`: Handles Gemini API communication and function calling
    - `system_controller.py`: Executes system-level commands (Shutdown, Volume, etc.)
- `launcher_ui/`: UI components for the launcher
    - `main_window.py`: Main FluentWindow with independent app navigation buttons, close handlers
    - `home_interface.py`: Home page with app launch buttons
    - `chat_interface.py`: Detached Chat Bubble window with AI integration
    - `chat_settings.json`: Stores API keys and chat settings (Not tracked by Git).
    - `notes_interface.py`: Notes interface embedding the Notes module
    - `settings_interface.py`: General settings page with widget samples button
    - `tools_interface.py`: Empty placeholder interface (no content)
    - `app_settings_interface.py`: App-specific settings (placeholder)
    - `log_interface.py`: Log display with copy functionality
    - `widget_samples_interface.py`: UI Components Gallery showcasing all Fluent Design buttons and widgets

## Dependencies
- `PySide6`
- `PySide6-Fluent-Widgets`
- `pyperclip` (for log copy button)

## Key Features
- Reduced navigation panel expanded width by 50% (150px)
- AutoKey and Android Tool as **independent navigation buttons** (not submenu of Tools)
- Tools interface is empty placeholder (click shows blank page)
- Close button (✖) in AutoKey toolbar to unload embedded app
- App embedding system for AutoKey and Android Tool

## Theme System (CRITICAL - Read Before Modifications)

### Overview
The application uses a **dual-stylesheet approach** with separate `LIGHT_STYLESHEET` and `DARK_STYLESHEET` defined in `Apps/AutoKey/ui/styles.py`.

### Theme Propagation Rules

1. **Main App Theme:**
   - **Default:** `Theme.DARK` (Hardcoded preference for modern aesthetics)
   - Stored in: `launcher_ui/main_window.py` → `self.current_theme`
   - Applied via: `setTheme(Theme.DARK)` in main window `__init__()`

2. **Embedded App Theme:**
   - **MUST** receive `parent_theme` from Main app
   - Example: `AutoKeyWindow(is_embedded=True, parent_theme=self.main_window.current_theme)`
   - Embedded app stores in `self.current_theme` and applies via `apply_stylesheet()`

3. **Standalone App Theme:**
   - Defaults to `Theme.DARK` (Consistent with Main App)
   - Example: `AutoKeyWindow(is_embedded=False)` → uses Dark theme

### Styling Principles

#### 1. Use Default Fluent Styles
- Avoid hardcoding colors (e.g., `background-color: white` or `black`).
- Rely on `qfluentwidgets` default styles which handle Light/Dark modes automatically.
- Only use `styles.py` for specific overrides or non-Fluent widgets (like standard QDialogs).

#### 2. Apply Stylesheet to QApplication (CRITICAL)
**Native Qt widgets** (QInputDialog, QMessageBox, QMenu) require stylesheet on `QApplication`:

```python
def apply_stylesheet(self):
    from ui.styles import DARK_STYLESHEET
    # Default to Dark
    stylesheet = DARK_STYLESHEET
    
    # Apply to window
    self.setStyleSheet(stylesheet)
    
    # CRITICAL: Apply to QApplication for native dialogs
    app = QApplication.instance()
    if app:
        app.setStyleSheet(stylesheet)
```

#### 3. Dual Stylesheet Structure (Legacy Support)
- `LIGHT_STYLESHEET` and `DARK_STYLESHEET` are kept in `Apps/AutoKey/ui/styles.py` for reference.
- **Primary:** `DARK_STYLESHEET` is the active default.
- Styles should focus on layout and spacing, leaving colors to the Theme engine where possible.

### Key Files

- **Stylesheets:** `Apps/AutoKey/ui/styles.py`
  - `DARK_STYLESHEET`: Active default. Dark backgrounds (#1E1E1E), light text (#E0E0E0).
  - `MAIN_STYLESHEET = DARK_STYLESHEET`

- **Theme Storage:**
  - Main: `launcher_ui/main_window.py` → `current_theme`
  - AutoKey: `Apps/AutoKey/ui/main_window.py` → `current_theme`

### Common Pitfalls

1. **Title Bar Dark Issue:**
   - Cause: Missing `QInputDialog QWidget` styling
   - Fix: Ensure `DARK_STYLESHEET` covers native widget backgrounds.

2. **Hardcoded Colors:**
   - Cause: `background-color: white` left over from old code.
   - Fix: Remove local `setStyleSheet()` and let global Dark theme take over.

### Save Path Standard
- AutoKey macros: `Apps/AutoKey/Save/`
- NEVER use relative paths like `macros/` or current directory
- Always `autokey_root = os.path.dirname(os.path.dirname(__file__))`
