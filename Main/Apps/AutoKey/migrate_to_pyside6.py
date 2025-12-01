import os

def migrate_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = content
        
        # 1. Basic Import Replacement
        new_content = new_content.replace("PyQt6", "PySide6")
        
        # 2. Signal/Slot/Property Replacement
        # PySide6 uses Signal, Slot, Property directly from QtCore, usually imported or available
        # But often code uses pyqtSignal, pyqtSlot.
        # We need to be careful. If they import pyqtSignal from QtCore, we change it to Signal.
        
        new_content = new_content.replace("pyqtSignal", "Signal")
        new_content = new_content.replace("pyqtSlot", "Slot")
        new_content = new_content.replace("pyqtProperty", "Property")
        
        # 3. Enum Access (PyQt6 uses Enum.Value, PySide6 also supports it but sometimes there are differences)
        # Generally PySide6 is very compatible with PyQt6 enums now.
        
        # 4. exec_ -> exec (PyQt6 already uses exec, but just in case)
        new_content = new_content.replace(".exec_()", ".exec()")
        
        if new_content != content:
            print(f"Migrating: {filepath}")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
        else:
            print(f"Skipping (no changes): {filepath}")
            
    except Exception as e:
        print(f"Error migrating {filepath}: {e}")

def main():
    files_to_migrate = [
        # AutoKey
        r"c:\Users\Mon\Desktop\Mon\AutoKey\main.py",
        r"c:\Users\Mon\Desktop\Mon\AutoKey\test_fluent.py",
        r"c:\Users\Mon\Desktop\Mon\AutoKey\ui\main_window.py",
        r"c:\Users\Mon\Desktop\Mon\AutoKey\ui\toolbar.py",
        r"c:\Users\Mon\Desktop\Mon\AutoKey\ui\styles.py",
        r"c:\Users\Mon\Desktop\Mon\AutoKey\ui\settings_dialog.py",
        r"c:\Users\Mon\Desktop\Mon\AutoKey\ui\playback_overlay.py",
        r"c:\Users\Mon\Desktop\Mon\AutoKey\ui\mouse_dialog.py",
        r"c:\Users\Mon\Desktop\Mon\AutoKey\ui\keyboard_dialog.py",
        r"c:\Users\Mon\Desktop\Mon\AutoKey\ui\image_search_dialog.py",
        r"c:\Users\Mon\Desktop\Mon\AutoKey\ui\text_search_dialog.py",
        r"c:\Users\Mon\Desktop\Mon\AutoKey\ui\text_search_overlay.py",
        r"c:\Users\Mon\Desktop\Mon\AutoKey\ui\delegates.py",
        r"c:\Users\Mon\Desktop\Mon\AutoKey\core\recorder.py",
        r"c:\Users\Mon\Desktop\Mon\AutoKey\core\player.py",
        r"c:\Users\Mon\Desktop\Mon\AutoKey\core\recorder_v2.py",
        r"c:\Users\Mon\Desktop\Mon\AutoKey\core\player_v2.py",
        r"c:\Users\Mon\Desktop\Mon\AutoKey\utils\snipping_tool.py",
        
        # Android_Tool
        r"c:\Users\Mon\Desktop\Mon\Android_Tool\Main.py",
        r"c:\Users\Mon\Desktop\Mon\Android_Tool\Main.pyw",
        r"c:\Users\Mon\Desktop\Mon\Android_Tool\modules\ModAndroid\ModAndroid.pyw",
        r"c:\Users\Mon\Desktop\Mon\Android_Tool\modules\ModAndroid\worker_file_import.py",
        r"c:\Users\Mon\Desktop\Mon\Android_Tool\modules\Notes\notes_module.py",
        r"c:\Users\Mon\Desktop\Mon\Android_Tool\modules\Telegram\telegram_module.py"
    ]
    
    for file in files_to_migrate:
        if os.path.exists(file):
            migrate_file(file)
        else:
            print(f"File not found: {file}")

if __name__ == "__main__":
    main()
