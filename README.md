# 🖥️ MonApps — Personal Productivity Launcher

> A modular desktop productivity suite built with **Python + PySide6 Fluent Design**, designed to unify multiple personal tools under a single, elegant Windows application.

---

## 📌 Overview

**MonApps** is a custom-built Windows desktop launcher that consolidates five standalone productivity tools into one seamless application. Powered by the **PySide6-Fluent-Widgets** framework, it delivers a modern Fluent Design UI with a persistent dark theme, single-instance enforcement, and deeply embedded sub-applications — all accessible from a unified navigation panel.

This project prioritizes **developer-grade tooling**: ADB device management, macro automation, AI-assisted chat, and ROM patching — all within a single window, no context switching required.

---

## ✨ Features

| Module | Description |
|---|---|
| 🚀 **Launcher** | Fluent Design main window with sidebar navigation, single-instance guard, system tray integration |
| 🤖 **AutoKey** | Macro recorder & editor — create step-by-step keyboard/mouse automation sequences |
| 🤖 **AIChat** | Gemini API-powered AI chatbot with Markdown rendering, chat history & session logging |
| 📱 **Android Tool** | ADB command runner, APK decompiler/recompiler, smart ROM patcher with parallel processing |
| 📝 **Notes** | Embedded rich-text notes module with IME/Vietnamese input support |
| 🔧 **AHK Tool** | AutoHotkey v2 integration — runs via `RunAsUser` for correct IME handling |

---

## 🗂️ Project Structure

```
MonApps/
├── Main/
│   ├── Main.pyw               # Entry point (no console window)
│   ├── Main.py                # Debug entry point (with console)
│   ├── config.json            # User settings (theme, startup, etc.)
│   ├── naming_registry.json   # Central registry of all UI IDs & config keys
│   ├── project_structure.md   # Internal architecture documentation
│   ├── Rule.md                # AI agent development rules
│   ├── core/
│   │   ├── config_manager.py          # Load/save config.json
│   │   ├── log_manager.py             # Singleton stdout/stderr capture
│   │   ├── single_instance_manager.py # Windows Named Mutex single-instance
│   │   └── system_controller.py       # System-level commands (volume, shutdown)
│   ├── launcher_ui/
│   │   ├── main_window.py             # FluentWindow — top-level navigation
│   │   ├── home_interface.py          # Home screen with app launch buttons
│   │   ├── notes_interface.py         # Embedded Notes module
│   │   ├── log_interface.py           # Live log viewer with copy support
│   │   ├── settings_interface.py      # General settings panel
│   │   ├── app_settings_interface.py  # Per-app settings
│   │   └── widget_samples_interface.py # Fluent UI component gallery
│   └── Apps/
│       ├── AutoKey/           # Macro automation tool
│       ├── AIChat/            # Gemini AI chatbot
│       ├── Android_Tool/      # ADB + ROM patching suite
│       ├── Notes/             # Notes app module
│       └── AHK_Tool/          # AutoHotkey v2 scripts
└── Rule.md                    # Top-level AI development rules
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **GUI Framework** | [PySide6](https://doc.qt.io/qtforpython/) + [PySide6-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) |
| **Language** | Python 3.10+ |
| **AI Integration** | Google Gemini API |
| **Android Management** | ADB (Android Debug Bridge) |
| **Automation** | AutoHotkey v2 (AHK) |
| **Clipboard** | `pyperclip` |
| **OS Target** | Windows 10/11 (64-bit) |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Windows 10/11
- ADB installed and added to `PATH` (for Android Tool)
- AutoHotkey v2 installed (for AHK Tool)

### Installation

```bash
# Clone the repository
git clone https://github.com/Sxcution/MonApps.git
cd MonApps

# Install Python dependencies
pip install PySide6 PySide6-Fluent-Widgets pyperclip
```

### Running the App

```bash
# Run with console (debug mode)
python Main/Main.py

# Run without console window (production mode)
pythonw Main/Main.pyw
```

---

## 🔌 Module Details

### 🤖 AutoKey
A step-by-step macro editor where users build automation sequences using keyboard shortcuts, mouse clicks, delays, and conditional logic. Macros are saved in `Apps/AutoKey/Save/` and persist across sessions.

### 🤖 AIChat
A Gemini-powered AI assistant embedded directly in the launcher. Supports:
- Multi-turn conversation with session logging
- Markdown rendering (code blocks, headers, bold/italic)
- Chat history saved to `Apps/AIChat/data/saved_chats/`
- Configurable API key via `Apps/AIChat/config/chat_settings.json`

### 📱 Android Tool
Full ADB management suite with three tabs:
- **ADB Commands** — Execute arbitrary ADB shell commands
- **Decompile/Recompile** — Jar/APK reverse engineering via integrated toolchain
- **ROM Patcher** — Smart multi-file patcher with drag-and-drop, duplicate detection, and parallel patching threads

### 📝 Notes
A lightweight rich-text notes module with built-in Vietnamese IME compatibility fixes. Handles Unicode input correctly even when running under elevated privileges.

---

## ⚙️ Configuration

All user preferences are stored in `Main/config.json`:

```json
{
  "dark_mode": true,
  "startup": false,
  "external_mode": false
}
```

The `naming_registry.json` serves as the **single source of truth** for all UI element IDs and configuration keys, ensuring consistency across development sessions.

---

## 🏗️ Architecture Highlights

- **Single Instance Guard** — Uses Windows Named Mutex to prevent duplicate launcher instances; focuses the existing window if already running.
- **Dual Stylesheet System** — `DARK_STYLESHEET` / `LIGHT_STYLESHEET` defined in `Apps/AutoKey/ui/styles.py`; applied globally to both Fluent widgets and native Qt dialogs.
- **Embedded App Pattern** — Sub-applications are instantiated with `is_embedded=True` and injected directly into the main window's navigation stack — no separate windows or process spawning.
- **UIPI Bypass** — Enables drag-and-drop from standard Explorer windows into elevated app instances via `ChangeWindowMessageFilter`.
- **Global Exception Handler** — Catches all unhandled exceptions via `sys.excepthook` and surfaces them as user-friendly dialogs without crashing the app.

---

## 📄 License

This project is **private / for personal use**. All rights reserved © Sxcution.

---

## 👤 Author

**Sxcution** — [github.com/Sxcution](https://github.com/Sxcution)
