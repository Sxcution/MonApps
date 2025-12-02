# GEMINI AGENT RULES

## I. DEBUGGING PROTOCOL
1. **Interactive/Hardware Debug (Hotkeys, UI, Mouse):**
   - **Action:** Inject print logs directly into the main source code (e.g., `main.py`).
   - **Execution:** Instruct user to run the app in their current IDE Terminal.
   - **Constraint:** Disable auto-restart/admin checks temporarily if they obscure logs. Do NOT ask user to open external `cmd.exe` or run separate scripts unless unavoidable.

2. **Logic/Automated Debug (Algorithms, Data Processing):**
   - **Action:** Create self-contained test scripts (e.g., `test_logic.py`).
   - **Execution:** Auto-run these scripts using your tools and analyze the output yourself.
   - **Constraint:** Do NOT burden the user with logs or manual execution for tasks you can verify automatically.

## II. WORKFLOW & VERIFICATION
3. **Post-Implementation Verification (Self-Correction):**
   - **Action:** After ANY code modification, YOU must automatically run the app/script (e.g., `python main.py`) in the terminal to check for syntax errors or immediate crashes.
   - **Constraint:** NEVER ask the user to run the app if you haven't verified it starts successfully first. If it crashes, fix it silently before notifying the user.

## III. CODING STANDARDS
4. **Naming & Commenting Standards:**
   - **Code Identifiers (Variables, IDs, Classes):** MUST use English, descriptive names (e.g., `btn_save_settings`, `input_user_password`). NO Vietnamese in code logic.
   - **Comments:** MUST be bilingual or Vietnamese for UI elements to ensure clarity.
     - Format: `<!-- [English_ID] : [Vietnamese_Description] -->`
     - Example: `<!-- btn_submit_login : Nút đăng nhập -->`
   - **Consistency:** Stick to one convention (e.g., snake_case for Python/IDs, camelCase for JS). Do not mix `login_password` and `passwordInput`.

5. **Naming Registry Protocol (Single Source of Truth):**
   - **Mandatory File:** Every project MUST have a `naming_registry.json` (or `ui_constants.py`) file at the root.
   - **Workflow:**
     1. **Read First:** Before writing any code, READ this file to reuse existing variable names/IDs.
     2. **Create/Update:** If the file is missing, CREATE it immediately. If adding new features/variables, YOU MUST UPDATE this file with the new keys.
   - **Goal:** Ensure absolute consistency across different AI sessions. No "magic strings" or duplicate variables allowed.

## IV. ARCHITECTURE & FILE MANAGEMENT
6. **Project Structure Protocol:**
   - **Mandatory File:** Maintain a `project_structure.md` file at the root.
   - **Content:** List all project files, their purpose, and key dependencies (which file calls which).
   - **Workflow:**
     - **New File:** When creating a file, add it to the list immediately.
     - **Delete File:** When removing a feature/file, remove it from the list.
   - **Goal:** Prevent "orphan files" and help AI understand the project architecture instantly.

## V. SESSION STARTUP PROTOCOL
7. **Context Loading:**
   - **Action:** At the start of any new session or task, YOU MUST:
     1. Read `project_structure.md` to understand the file layout.
     2. Read `naming_registry.json` to load existing variable names.
   - **Goal:** Eliminate "hallucinated" files or inconsistent naming from the very first step.

## VI. UI & STYLING PROTOCOL
8. **Centralized Styling:**
   - **Single Source:** ALL styling (CSS/QSS) must reside in a dedicated file (e.g., `styles.py`, `styles.css`).
   - **No Inline Styles:** Avoid `widget.setStyleSheet("...")` in Python logic unless dynamic values are required.
   - **Global Reset Awareness:** When using global resets (e.g., `* { background: transparent; }`), YOU MUST explicitly style complex widgets (Tooltip, Menu, ComboBox) to prevent rendering artifacts.

9. **Input Field Standards:**
   - **No Spinners:** NEVER include "spinner" controls (up/down arrows) for numeric inputs.
     - **Desktop (Qt):** Hide via QSS: `QSpinBox::up-button, QSpinBox::down-button { width: 0; }`.
     - **Web (CSS):** Hide via CSS: `input[type=number]::-webkit-inner-spin-button { -webkit-appearance: none; }`.

## VII. WEB APP DASHBOARD PROTOCOL
10. **Notification & Dialog Standards:**
    - **Custom Modals Only:** Critical actions (Delete, Confirm, Save) MUST use custom Dashboard Modals (e.g., Bootstrap Modal, Custom Overlay).
    - **No Native Alerts:** NEVER use native browser alerts (`alert()`, `confirm()`, `prompt()`).

## VIII. DESKTOP PYTHON UI PROTOCOL (PySide6-Fluent-Widgets)
11. **Default Desktop UI Framework:**
    - **Action:** All Python desktop applications using Qt MUST use `PySide6-Fluent-Widgets` as the primary UI framework, instead of raw widgets or scattered custom styleSheets.
    - **Constraints:**
      - Do NOT mix multiple style systems (native Qt + custom QSS + Fluent) unless strictly necessary.
      - When using `FluentWindow` or `MSFluentWindow`, the entire main layout MUST follow the Navigation + Pages structure.

12. **Window & Navigation Standard:**
    - **Main Window:** The main window MUST inherit from `FluentWindow` or `MSFluentWindow` (or the official equivalents inside PySide6-Fluent-Widgets).
    - **Navigation Layout:**
      - Use `NavigationInterface` (or the framework’s built-in navigation system) to manage app pages such as Home, Settings, Logs, and Tools.
      - The Home page MUST be defined explicitly with consistent IDs, for example: `page_home`, `btn_nav_home`.
      - DO NOT create multiple pseudo-home screens (e.g., using Main, Start, Dashboard as separate “homes”).

13. **Settings UI Standard:**
    - **Component Consistency:** ALWAYS use standard `qfluentwidgets` components for settings pages to ensure visual consistency.
      - Use `SwitchSettingCard` for toggle settings.
      - Use `PrimaryPushSettingCard` for navigation or actions.
      - Use `ExpandGroupSettingCard` for grouped settings.

14. **Theme Consistency Protocol:**
    - **Ignore System Theme:** Do NOT rely on the user's OS system theme (e.g., Dark Mode) for the application's default appearance.
    - **Enforce App Theme:** Explicitly set the theme (e.g., `setTheme(Theme.LIGHT)`) in the main window's `__init__` method to ensure consistent rendering regardless of system settings.
    - **Button & Panel Sync:** Ensure that buttons, panels, and tables share the same theme (Light/Dark) to avoid visual discrepancies (e.g., black buttons on white panels).
    - **Avoid Custom Cards:** Do NOT manually create `CardWidget` with custom layouts for standard settings unless absolutely necessary for a unique feature not covered by standard components.
