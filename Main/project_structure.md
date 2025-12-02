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
    - `widget_samples_interface.py`: Widget showcase with copyable code samples

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
   - Stored in: `launcher_ui/main_window.py` → `self.current_theme` (Theme.LIGHT or Theme.DARK)
   - Loaded from: `config.json` → `dark_mode` key
   - Applied via: `setTheme(self.current_theme)` in main window `__init__()`

2. **Embedded App Theme:**
   - **MUST** receive `parent_theme` from Main app
   - Example: `AutoKeywindow(is_embedded=True, parent_theme=self.main_window.current_theme)`
   - Embedded app stores in `self.current_theme` and applies via `apply_stylesheet()`

3. **Standalone App Theme:**
   - Defaults to `Theme.LIGHT`
   - Example: `AutoKeyWindow(is_embedded=False)` → uses Light theme

### Styling Principles

#### 1. NEVER Hardcode Colors
❌ **BAD:**
```python
self.table.setStyleSheet("QTableView { background-color: white; }")
```

✅ **GOOD:**
```python
# Let global stylesheet handle it
# No local setStyleSheet() call
```

#### 2. Apply Stylesheet to QApplication (CRITICAL)
**Native Qt widgets** (QInputDialog, QMessageBox, QMenu) require stylesheet on `QApplication`:

```python
def apply_stylesheet(self):
    from ui.styles import LIGHT_STYLESHEET, DARK_STYLESHEET
    stylesheet = DARK_STYLESHEET if self.current_theme == Theme.DARK else LIGHT_STYLESHEET
    
    # Apply to window
    self.setStyleSheet(stylesheet)
    
    # CRITICAL: Apply to QApplication for native dialogs
    app = QApplication.instance()
    if app:
        app.setStyleSheet(stylesheet)
```

#### 3. Dual Stylesheet Structure
Both `LIGHT_STYLESHEET` and `DARK_STYLESHEET` MUST style:
- QTableView (background, alternating rows, selection, gridlines)
- QHeaderView::section (headers)
- QInputDialog, QMessageBox, QMenu (native widgets)
- QListWidget (custom lists)
- QPushButton, QLineEdit, QComboBox, QSpinBox
- QLabel, QToolTip

### Key Files

- **Stylesheets:** `Apps/AutoKey/ui/styles.py`
  - `LIGHT_STYLESHEET`: White backgrounds (#FFFFFF), dark text (#1A1A1A)
  - `DARK_STYLESHEET`: Dark backgrounds (#1E1E1E), light text (#E0E0E0)
  - `MAIN_STYLESHEET = LIGHT_STYLESHEET` (backward compatibility)

- **Theme Storage:**
  - Main: `launcher_ui/main_window.py` → `current_theme`
  - AutoKey: `Apps/AutoKey/ui/main_window.py` → `current_theme`
  - Config: `config.json` → `dark_mode` (bool)

- **Theme Toggle:** `launcher_ui/settings_interface.py`
  - Updates `config.json`
  - Updates `main_window.current_theme`
  - Calls `qfluentwidgets.setTheme()`

### Common Pitfalls

1. **Title Bar Dark Issue:**
   - Cause: Missing `QInputDialog QWidget` styling
   - Fix: Add to both LIGHT/DARK stylesheets

2 **Table/Panel White in Dark Mode:**
   - Cause: Hardcoded `background-color: white` in component
   - Fix: Remove local `setStyleSheet()`, rely on global

3. **Theme Not Updating:**
   - Cause: Not calling `apply_stylesheet()` after theme change
   - Fix: Call `apply_stylesheet()` or reload app

### Save Path Standard
- AutoKey macros: `Apps/AutoKey/Save/`
- NEVER use relative paths like `macros/` or current directory
- Always `autokey_root = os.path.dirname(os.path.dirname(__file__))`
