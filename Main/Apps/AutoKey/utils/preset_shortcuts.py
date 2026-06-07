# preset_shortcuts.py - Preset Keyboard Shortcut Definitions
# Common keyboard shortcuts that cannot be captured by QKeySequenceEdit

PRESET_SHORTCUTS = {
    "Custom": None,  # User manually inputs key
    "Alt+Tab": {"alt": True, "key": "Tab"},
    "Ctrl+Shift+Esc": {"ctrl": True, "shift": True, "key": "Esc"},
    "Win+D": {"win": True, "key": "D"},
    "Alt+F4": {"alt": True, "key": "F4"}
}

def get_preset_names():
    """Return list of preset shortcut names for ComboBox"""
    return list(PRESET_SHORTCUTS.keys())

def get_preset_data(preset_name):
    """Get the key combination data for a preset shortcut"""
    return PRESET_SHORTCUTS.get(preset_name)
