"""
Android Auto Rom (v6.0) by Mon - MODIFIED
-----------------------------------------

MỤC ĐÍCH:
Một bộ công cụ đa năng để tự động hóa quá trình vá các file hệ thống quan trọng
từ các bản ROM Android, giúp tùy biến và gỡ lỗi dễ dàng hơn.

CÁC CHỨC NĂNG CHÍNH:

1.  GPS Patcher (services.jar):
    -   Bypass quyền AppOps để không cần bật "Vị trí mô phỏng".
    -   Hợp pháp hóa vị trí giả để qua mặt các ứng dụng phát hiện mock location.

2.  Auto Start & ADB (build.prop, init.rc):
    -   Chỉnh sửa build.prop để tự động bật ADB, gỡ bỏ các giới hạn quyền.
    -   Chỉnh sửa init.rc để thêm block "on charger", giúp thiết bị tự khởi động
      vào hệ thống khi cắm sạc.

QUY TRÌNH HOẠT ĐỘNG:
-   Tool sử dụng giao diện tab để phân chia các chức năng.
-   Mỗi chức năng có luồng xử lý riêng, chạy ngầm để không làm treo giao diện.
-   Tất cả các thay đổi đều được ghi lại chi tiết trong ô log tương ứng.
"""
import sys
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
import concurrent.futures
import html
import stat
import time
import json
from pathlib import Path

from PySide6.QtCore import QThread, Signal, QDir, Qt, QObject, QEvent

# Worker for background ADB operations
try:
    from .worker_file_import import AdbCommandWorker
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    if _current_dir not in sys.path:
        sys.path.insert(0, _current_dir)
    from worker_file_import import AdbCommandWorker
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFileDialog,
    QTextEdit, QProgressBar, QLineEdit, QLabel, QTabWidget, QHBoxLayout,
    QTreeView, QMenu, QStackedWidget, QDialog, QDialogButtonBox, QMessageBox,
    QCheckBox, QInputDialog, QListWidget, QListWidgetItem, QFileSystemModel
)
from PySide6.QtGui import QFont, QScreen, QAction
from functools import partial

# Fluent UI Components
try:
    from qfluentwidgets import (
        PushButton, PrimaryPushButton, TransparentPushButton,
        LineEdit, TextEdit, ProgressBar, CheckBox,
        InfoBar, InfoBarPosition, MessageBox as FluentMessageBox,
        BodyLabel, TitleLabel, CaptionLabel
    )
    HAS_FLUENT = True
except ImportError:
    # Fallback to standard Qt widgets if qfluentwidgets not available
    from PySide6.QtWidgets import QPushButton as PushButton
    PrimaryPushButton = PushButton
    TransparentPushButton = PushButton
    HAS_FLUENT = False

# =============================================================================
# CONFIG MANAGER - Save/Load Settings
# =============================================================================
class ConfigManager:
    """Quản lý config file để lưu settings (device serial, etc)."""
    
    def __init__(self, config_file="config.json"):
        # Lưu config vào thư mục config/
        config_dir = os.path.join(os.path.dirname(__file__), "config")
        os.makedirs(config_dir, exist_ok=True)
        self.config_file = os.path.join(config_dir, config_file)
        self.config = self.load_config()
    
    def load_config(self):
        """Load config từ file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Không load được config: {e}")
                return {}
        return {}
    
    def save_config(self):
        """Save config ra file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Không save được config: {e}")
    
    def get(self, key, default=None):
        """Get giá trị từ config."""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set giá trị và save luôn."""
        self.config[key] = value
        self.save_config()

# =============================================================================
# UPDATER SCRIPT LOGIC FUNCTIONS
# =============================================================================
def find_updater_script(rom_root: str) -> str | None:
    """Finds the path to the updater-script in a given ROM root directory."""
    script_path = os.path.join(rom_root, "META-INF", "com", "google", "android", "updater-script")
    return script_path if os.path.exists(script_path) else None

def to_edify_path(abs_path: str, rom_root: str) -> tuple[str, bool] | None:
    """
    Converts an absolute file system path to a relative Edify script path.
    Returns (edify_path, is_dir) or None if the path is not within a standard partition.
    """
    try:
        # Standardize paths to avoid mixing slashes
        norm_abs_path = Path(abs_path).as_posix()
        norm_rom_root = Path(rom_root).as_posix()
        
        rel_path_str = os.path.relpath(norm_abs_path, norm_rom_root)
        rel_path = Path(rel_path_str).as_posix()

        # Find the top-level partition name (system, vendor, product, etc.)
        parts = rel_path.split('/')
        standard_partitions = ["system", "vendor", "product", "system_ext", "odm", "oem"]
        
        # Check if the path starts with a standard partition name
        if parts[0] in standard_partitions:
            edify_path = "/" + rel_path
            is_dir = os.path.isdir(abs_path)
            return edify_path, is_dir
        return None
    except ValueError:
        # This occurs if the path is not under rom_root
        return None

def build_edify_line(path_edify: str, is_dir: bool, mode_expect: str) -> str:
    """Builds a single line of Edify script for setting metadata."""
    # Ensure mode is 4 digits with leading zero, e.g., 0755
    mode_str = f"0{mode_expect}" if len(mode_expect) == 3 else mode_expect
    
    if is_dir:
        return f'set_metadata_recursive("{path_edify}", "uid", 0, "gid", 0, "mode", {mode_str});'
    return (
        f'set_metadata("{path_edify}", "uid", 0, "gid", 0, "mode", {mode_str}, '
        f'"context", "u:object_r:system_file:s0");'
    )

def ensure_edify_stat_lines(script_text: str, items: list[tuple[str, bool, str]]) -> tuple[str, int, int]:
    """
    Adds or updates set_metadata lines idempotently.
    Returns (new_script_text, added_count, updated_count)
    """
    current_text = script_text
    added = 0
    updated = 0
    
    lines_to_add = []

    # First, remove all existing lines managed by this tool to avoid duplicates
    for edify_path, is_dir, mode in items:
        path_esc = re.escape(edify_path)
        pattern = r'^\s*set_metadata(?:_recursive)?\(\s*"' + path_esc + r'"\s*,.*?\);\s*$'
        
        # Use re.subn to check if a line was removed
        current_text, count = re.subn(pattern, "", current_text, flags=re.MULTILINE)
        if count > 0:
            updated += 1
        else:
            added += 1
        
        lines_to_add.append(build_edify_line(edify_path, is_dir, mode))

    # Clean up blank lines that may result from removal
    current_text = re.sub(r'\n\s*\n', '\n', current_text)

    # Now, find the insertion point or append at the end
    mount_points = [
        r'mount("ext4", "EMMC", "/dev/block/bootdevice/by-name/system", "/system");',
        r'run_program("/system/bin/mount", "/system");',
    ]
    insertion_point = -1
    for point in mount_points:
        match = re.search(re.escape(point), current_text)
        if match:
            insertion_point = match.end()
            break
    
    new_lines_str = "\n".join(lines_to_add)
    
    if insertion_point != -1:
        # Insert after the mount command
        new_content = (current_text[:insertion_point] + 
                       "\n\n# === Tool: auto-permission ===\n" + 
                       new_lines_str + 
                       "\n# === End Tool Block ===\n" + 
                       current_text[insertion_point:])
    else:
        # Append to the end of the file
        new_content = current_text.strip() + \
                      "\n\n# === Tool: auto-permission ===\n" + \
                      new_lines_str + \
                      "\n# === End Tool Block ===\n"
                      
    # To avoid adding multiple blocks, we'll use a simpler strategy:
    # Remove any old block, and append one new, consolidated block.
    block_pattern = re.compile(r'\n*# === Tool: auto-permission ===.*?# === End Tool Block ===\n*', re.DOTALL)
    final_text = block_pattern.sub('', current_text.strip())
    
    final_text += ("\n\n# === Tool: auto-permission ===\n" +
                   "\n".join(lines_to_add) +
                   "\n# === End Tool Block ===")

    return final_text, added, updated

def update_updater_script(entries: list[dict], rom_root: str) -> dict:
    """Orchestrator function to update the updater-script."""
    result = {"script_path": None, "added": 0, "updated": 0, "skipped": 0, "notes": []}
    
    script_path = find_updater_script(rom_root)
    if not script_path:
        result["notes"].append("ROM A/B (payload) - không có updater-script. Dùng fs_config/system.img")
        return result
    
    result["script_path"] = script_path
    
    items_to_process = []
    for entry in entries:
        edify_info = to_edify_path(entry["path_abs"], rom_root)
        if edify_info:
            edify_path, is_dir = edify_info
            # The mode from PermissionThread is octal, needs to be string
            mode_str = entry["mode_expect"].replace("0o", "")
            items_to_process.append((edify_path, is_dir, mode_str))
        else:
            result["skipped"] += 1
            result["notes"].append(f"Skipped (out of scope): {os.path.basename(entry['path_abs'])}")

    if not items_to_process:
        return result

    try:
        # Create a backup
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        backup_path = f"{script_path}.bak.{timestamp}"
        shutil.copy2(script_path, backup_path)
        
        with open(script_path, "r", encoding="utf-8") as f:
            original_content = f.read()
            
        new_content, added, updated = ensure_edify_stat_lines(original_content, items_to_process)
        
        with open(script_path, "w", encoding="utf-8", newline='\n') as f:
            f.write(new_content)
            
        result.update({"added": added, "updated": updated})
        result["notes"].append(f"Backup created at: {os.path.basename(backup_path)}")

    except Exception as e:
        result["notes"].append(f"ERROR: {e}")

    return result

# =============================================================================
# THREAD CHO CHỨC NĂNG GPS PATCHER
# =============================================================================
class GpsPatcherThread(QThread):
    log_message = Signal(str)
    progress_update = Signal(int)
    patch_finished = Signal(bool, str)
    cancelled = Signal()  # NEW: Cancel signal

    def __init__(self, input_file, patched_dir, overwrite_original=False):
        super().__init__()
        self.input_file = input_file
        self.patched_dir = patched_dir
        self.overwrite_original = overwrite_original # <-- NEW ATTRIBUTE
        self._cancel_requested = False  # NEW: Cancel flag

        # Get the absolute path to the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Build the path to the java directory relative to the script's location
        self.java_dir = os.path.join(script_dir, "bin", "java")
        
        self.baksmali_path = os.path.join(self.java_dir, "baksmali.jar")
        self.smali_path = os.path.join(self.java_dir, "smali.jar")

    def run_command(self, command):
        self.log_message.emit(f"Bắt đầu tác vụ: {' '.join(command)}")
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            stdout, _ = process.communicate()
            if stdout:
                self.log_message.emit(f"Output từ tác vụ '{command[3]}':\n---BEGIN---\n{stdout.strip()}\n---END---")
            return_code = process.returncode
            if return_code != 0:
                self.log_message.emit(f"Lỗi: Tác vụ '{command[3]}' thất bại với mã thoát {return_code}")
                return False
            self.log_message.emit(f"Hoàn thành tác vụ: {command[3]}")
            return True
        except FileNotFoundError:
            self.log_message.emit(f"Lỗi: Java chưa được cài đặt hoặc không có trong PATH hệ thống.")
            return False
        except Exception as e:
            self.log_message.emit(f"Lỗi không mong muốn trong tác vụ '{command[3]}': {e}")
            return False

    def find_smali_file(self, root_dir, primary_name, search_keywords):
        self.log_message.emit(f"Đang quét tìm file chính xác: '{primary_name}' trong các thư mục smali*...")
        for subdir in os.listdir(root_dir):
            full_subdir = os.path.join(root_dir, subdir)
            if os.path.isdir(full_subdir) and subdir.startswith("smali"):
                for root, _, files in os.walk(full_subdir):
                    if primary_name in files:
                        found_path = os.path.join(root, primary_name)
                        rel_path = os.path.relpath(found_path, root_dir).replace('\\', '/')
                        self.log_message.emit(f"✅ Đã tìm thấy file tại: {rel_path}")
                        return found_path
        self.log_message.emit(f"Cảnh báo: Không tìm thấy file '{primary_name}'. Bắt đầu quét chẩn đoán...")
        possible_matches = set()
        for subdir in os.listdir(root_dir):
            full_subdir = os.path.join(root_dir, subdir)
            if os.path.isdir(full_subdir) and subdir.startswith("smali"):
                for root, _, files in os.walk(full_subdir):
                    for f in files:
                        if f.endswith(".smali"):
                            f_lower = f.lower()
                            if any(keyword in f_lower for keyword in search_keywords):
                                possible_matches.add(os.path.relpath(os.path.join(root, f), root_dir))
        if possible_matches:
            self.log_message.emit(f"--- Kết quả chẩn đoán cho các từ khóa {search_keywords} ---")
            for match in sorted(list(possible_matches))[:15]:
                fixed_match = match.replace('\\', '/')
                self.log_message.emit(f" -> {fixed_match}")
            self.log_message.emit("-------------------------------------------------")
        else:
            self.log_message.emit(f"Quét chẩn đoán không tìm thấy file nào chứa các từ khóa: {search_keywords}")
        return None

    def patch_system_app_ops_helper(self, smali_root_dir):
        import re, os
        target_file_path = self.find_smali_file(
            smali_root_dir,
            "SystemAppOpsHelper.smali",
            ["appops", "SystemAppOpsHelper"]
        )
        if not target_file_path:
            return False

        self.log_message.emit("Bắt đầu áp dụng bản vá AppOps (chỉ noteOp/noteOpNoThrow)…")

        try:
            with open(target_file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.log_message.emit(f"Lỗi đọc file '{os.path.basename(target_file_path)}': {e}")
            return False

        patched_content = content

        # --- 1) SystemAppOpsHelper: chỉ patch noteOp/ noteOpNoThrow trả boolean ---
        pattern_bool = re.compile(
            r"(\.method public noteOp(?:NoThrow)?\(.*?\)Z\s*\.registers \d+)(.*?)(\.end method)",
            re.DOTALL
        )
        replacement_bool = r"\1\n\n    const/4 v0, 0x1\n    return v0\n\n\3"
        patched_content, count_bool = pattern_bool.subn(replacement_bool, patched_content)

        # Giữ nguyên checkOpNoThrow(...)Z  -> KHÔNG regex đụng tới

        # (tuỳ ROM, nếu có các biến thể trả int I như noteOp(...)I / checkOp(...)I thì ép MODE_ALLOWED=0)
        pattern_int = re.compile(
            r"(\.method public (?:note|check)(?:Proxy)?Op(?:NoThrow)?\(.*?\)I\s*\.registers \d+)(.*?)(\.end method)",
            re.DOTALL
        )
        replacement_int = r"\1\n\n    .locals 1\n    const/4 v0, 0x0\n    return v0\n\n\3"
        patched_content, count_int = pattern_int.subn(replacement_int, patched_content)

        if count_bool == 0 and count_int == 0:
            self.log_message.emit("Cảnh báo: Không tìm thấy phương thức AppOps để vá.")
            return False

        try:
            with open(target_file_path, "w", encoding="utf-8") as f:
                f.write(patched_content)
            self.log_message.emit(f"--- AppOps patched: noteOp/noteOpNoThrow={count_bool}, int(I)={count_int} ---")
            self.log_message.emit("--- Giữ nguyên checkOpNoThrow để tránh làm hỏng logic thăm dò ---")
            return True
        except Exception as e:
            self.log_message.emit(f"Lỗi ghi file '{os.path.basename(target_file_path)}': {e}")
            return False

    def _replacer_mock_location(self, match):
        const_line_full = match.group(1)
        register = match.group(2)
        lines = match.group(3)
        invoke = match.group(4)
        
        # Ép FALSE cho setIsFromMockProvider
        patched_const_line = re.sub(r'0x1\s*$', '0x0', const_line_full.rstrip()) + "\n"
        
        # Nếu dùng pX làm tham số (rất hay gặp), khôi phục về 1 ngay sau invoke để không phá logic phía sau
        restore = f"\n    const/4 {register}, 0x1" if register.startswith('p') else ""
        
        self.log_message.emit(f"Patch setIsFromMockProvider: {register}=0 ; restore-after-invoke={'yes' if restore else 'no'}")
        
        return f"{patched_const_line}{lines}{invoke}{restore}"

    def patch_mock_location_provider(self, smali_root_dir):
        target_file_path = self.find_smali_file(smali_root_dir, "MockLocationProvider.smali", ["mock", "location"])
        if not target_file_path: return False
        self.log_message.emit("Bắt đầu áp dụng bản vá #2...")
        try:
            with open(target_file_path, "r", encoding='utf-8') as f: content = f.read()
        except Exception as e:
            self.log_message.emit(f"Lỗi đọc file '{os.path.basename(target_file_path)}': {e}"); return False
        pattern = re.compile(r"(\s*(?:const/4|const/16|const)\s+((?:p|v)\d+),\s+0x1\s*\n)((?:\s*\.line\s+\d+\s*\n)*)(\s*invoke-virtual\s+\{[^,]+,\s+\2\}, Landroid/location/Location;->setIsFromMockProvider\(Z\)V)", re.MULTILINE)
        patched_content, count = pattern.subn(self._replacer_mock_location, content)
        if count > 0:
            self.log_message.emit("--- Chi tiết bản vá #2: Hợp pháp hóa vị trí ---")
            self.log_message.emit(f" - Đã tìm thấy và vá {count} vị trí.")
            self.log_message.emit("--------------------------------------------")
            try:
                with open(target_file_path, "w", encoding='utf-8') as f: f.write(patched_content)
                return True
            except Exception as e:
                self.log_message.emit(f"Lỗi ghi file '{os.path.basename(target_file_path)}': {e}"); return False
        else:
            self.log_message.emit(f"Cảnh báo: Không tìm thấy mã cần vá trong '{os.path.basename(target_file_path)}'."); return False

    def remove_debug_lines(self, smali_root_dir):
        self.log_message.emit("Đang xóa thông tin gỡ lỗi (.line) khỏi các file smali...")
        line_num_pattern = re.compile(r"^\s*\.line\s+\d+\s*$"); files_processed = 0
        for root, _, files in os.walk(smali_root_dir):
            for file in files:
                if file.endswith(".smali"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding='utf-8') as f_in: lines = f_in.readlines()
                        with open(file_path, "w", encoding='utf-8') as f_out:
                            for line in lines:
                                if not line_num_pattern.match(line): f_out.write(line)
                        files_processed += 1
                    except Exception as e: self.log_message.emit(f"Không thể xử lý file {file_path}: {e}")
        self.log_message.emit(f"Đã xóa thông tin gỡ lỗi từ {files_processed} file.")
    
    def cancel(self):
        """Request cancellation of the patch operation"""
        self.log_message.emit("🔍 [GPSPatcherThread] Cancel requested by user")
        self._cancel_requested = True
    
    def _check_cancel(self):
        """Check if cancel was requested"""
        if self._cancel_requested:
            self.log_message.emit("⛔ Đã hủy bởi người dùng")
            self.cancelled.emit()
            return True
        return False

    def run(self):
        # --- DEPENDENCY CHECK ---
        required_jars = ['baksmali.jar', 'smali.jar']
        for jar in required_jars:
            jar_path = os.path.join(self.java_dir, jar)
            if not os.path.exists(jar_path):
                error_msg = f"❌ Không tìm thấy thư viện Java cần thiết: '{jar}' trong '{self.java_dir}'"
                self.log_message.emit(error_msg)
                self.patch_finished.emit(False, "Thiếu thư viện Java.")
                return
        
        # Check cancel before starting
        if self._check_cancel():
            return

        self.progress_update.emit(5)
        temp_dir = tempfile.mkdtemp(prefix="gps_patcher_")
        smali_base_dir = temp_dir
        try:
            # --- DECOMPILATION LOGIC (UNCHANGED) ---
            with zipfile.ZipFile(self.input_file, 'r') as zin:
                dex_files = sorted([f for f in zin.namelist() if f.startswith('classes') and f.endswith('.dex')])
            if not dex_files: self.patch_finished.emit(False, "File .jar không hợp lệ."); return
            self.log_message.emit(f"Đã tìm thấy: {', '.join(dex_files)}. Bắt đầu giải nén song song...")
            self.progress_update.emit(10)
            
            # Check cancel
            if self._check_cancel():
                return
            
            decompile_tasks = []
            with zipfile.ZipFile(self.input_file, 'r') as zin:
                for dex_file in dex_files:
                    output_dir_name = 'smali' if dex_file == 'classes.dex' else f"smali_{dex_file.replace('.dex', '')}"
                    output_path = os.path.join(smali_base_dir, output_dir_name)
                    extracted_dex_path = zin.extract(dex_file, smali_base_dir)
                    decompile_tasks.append(["java", "-jar", self.baksmali_path, "d", extracted_dex_path, "-o", output_path])
            with concurrent.futures.ThreadPoolExecutor() as executor:
                if not all(list(executor.map(self.run_command, decompile_tasks))):
                    self.patch_finished.emit(False, "Một hoặc nhiều tác vụ giải nén đã thất bại."); return
            
            # Check cancel after decompile
            if self._check_cancel():
                return
            
            # --- PATCHING LOGIC (UNCHANGED) ---
            self.progress_update.emit(40)
            self.remove_debug_lines(smali_base_dir)
            self.progress_update.emit(50)
            
            # Check cancel
            if self._check_cancel():
                return
            
            patched1 = self.patch_system_app_ops_helper(smali_base_dir)
            patched2 = self.patch_mock_location_provider(smali_base_dir)
            self.progress_update.emit(60)
            
            # Check cancel
            if self._check_cancel():
                return
            
            if not patched1 and not patched2:
                self.patch_finished.emit(False, "Không thể áp dụng bản vá. Vui lòng kiểm tra log."); return

            # --- RECOMPILATION LOGIC (UNCHANGED) ---
            self.log_message.emit("Chuẩn bị biên dịch lại các thư mục smali* song song...")
            recompile_tasks = []; recompiled_dex_files = {}
            smali_dirs = sorted([d for d in os.listdir(smali_base_dir) if d.startswith("smali") and os.path.isdir(os.path.join(smali_base_dir, d))])
            for smali_dir_name in smali_dirs:
                dex_name = 'classes.dex' if smali_dir_name == 'smali' else smali_dir_name.replace('smali_', '') + '.dex'
                smali_dir_path = os.path.join(smali_base_dir, smali_dir_name)
                output_dex_path = os.path.join(temp_dir, dex_name)
                recompiled_dex_files[dex_name] = output_dex_path
                cmd_with_api = ["java", "-jar", self.smali_path, "a", "-a", "33", smali_dir_path, "-o", output_dex_path]
                cmd_default = ["java", "-jar", self.smali_path, "a", smali_dir_path, "-o", output_dex_path]
                recompile_tasks.append({'with_api': cmd_with_api, 'default': cmd_default, 'name': smali_dir_name})
            
            def run_recompile_task(task):
                if not self.run_command(task['with_api']):
                    self.log_message.emit(f"Biên dịch lại {task['name']} với API 33 thất bại, thử lại...")
                    return self.run_command(task['default'])
                return True
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                if not all(list(executor.map(run_recompile_task, recompile_tasks))):
                    self.patch_finished.emit(False, "Một hoặc nhiều tác vụ biên dịch lại đã thất bại."); return
            
            # Check cancel after recompile
            if self._check_cancel():
                return
            
            self.progress_update.emit(90)

            # --- START: NEW CONDITIONAL SAVING LOGIC (OPTIMIZED) ---
            # 🔍 DEBUG: Bắt đầu ghi file
            self.log_message.emit("🔍 [GPSPatcherWorker] Bắt đầu ghi file với chunk optimization...")
            
            success_message = ""
            if self.overwrite_original:
                # BEHAVIOR 1: Overwrite the original services.jar
                output_path = self.input_file
                self.log_message.emit(f"Ghi đè lên file gốc: {output_path}")
                temp_zip_path = output_path + ".tmp"
                try:
                    with zipfile.ZipFile(self.input_file, 'r') as zin:
                        with zipfile.ZipFile(temp_zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
                            original_dex_files = {f for f in zin.namelist() if f.startswith('classes') and f.endswith('.dex')}
                            copied_count = 0
                            total_items = len([x for x in zin.infolist() if x.filename not in original_dex_files])
                            
                            # Copy existing files (EXCEPT old dex) với chunk
                            for item in zin.infolist():
                                if item.filename not in original_dex_files:
                                    # Đọc/ghi theo chunk 8MB để tránh OOM với file lớn
                                    with zin.open(item) as source:
                                        with zout.open(item.filename, 'w') as target:
                                            chunk_size = 8 * 1024 * 1024  # 8MB chunks
                                            while True:
                                                chunk = source.read(chunk_size)
                                                if not chunk:
                                                    break
                                                target.write(chunk)
                                    
                                    copied_count += 1
                                    # Update progress mỗi 10 file
                                    if copied_count % 10 == 0:
                                        progress = 90 + int(copied_count * 8 / total_items) if total_items > 0 else 90
                                        self.progress_update.emit(progress)
                            
                            # Write new dex files
                            self.log_message.emit("🔍 [GPSPatcherWorker] Ghi các file dex mới...")
                            for dex_name, dex_path in recompiled_dex_files.items():
                                zout.write(dex_path, dex_name)
                    
                    shutil.move(temp_zip_path, output_path)
                    success_message = "✅ THÀNH CÔNG! Đã vá và ghi đè lên file services.jar gốc."
                except Exception as e:
                    self.log_message.emit(f"🔍 [GPSPatcherWorker] Exception: {e}")
                    self.log_message.emit(f"❌ Lỗi khi ghi đè file services.jar: {e}")
                    if os.path.exists(temp_zip_path): os.remove(temp_zip_path)
                    self.patch_finished.emit(False, "Lỗi ghi file."); return
            else:
                # BEHAVIOR 2: Save to "Patched" directory with ORIGINAL filename
                output_dir = self.patched_dir
                base_name = os.path.basename(self.input_file)
                output_path = os.path.join(output_dir, base_name)  # Keep original filename
                self.log_message.emit(f"Tạo file đã vá tại: {output_path}")
                try:
                    with zipfile.ZipFile(self.input_file, 'r') as zin:
                        with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
                            original_dex_files = {f for f in zin.namelist() if f.startswith('classes') and f.endswith('.dex')}
                            copied_count = 0
                            total_items = len([x for x in zin.infolist() if x.filename not in original_dex_files])
                            
                            # Copy existing files (EXCEPT old dex) với chunk
                            for item in zin.infolist():
                                if item.filename not in original_dex_files:
                                    # Đọc/ghi theo chunk 8MB để tránh OOM với file lớn
                                    with zin.open(item) as source:
                                        with zout.open(item.filename, 'w') as target:
                                            chunk_size = 8 * 1024 * 1024  # 8MB chunks
                                            while True:
                                                chunk = source.read(chunk_size)
                                                if not chunk:
                                                    break
                                                target.write(chunk)
                                    
                                    copied_count += 1
                                    # Update progress mỗi 10 file
                                    if copied_count % 10 == 0:
                                        progress = 90 + int(copied_count * 8 / total_items) if total_items > 0 else 90
                                        self.progress_update.emit(progress)
                            
                            # Write new dex files
                            self.log_message.emit("🔍 [GPSPatcherWorker] Ghi các file dex mới...")
                            for dex_name, dex_path in recompiled_dex_files.items():
                                zout.write(dex_path, dex_name)
                    
                    success_message = f"✅ THÀNH CÔNG! File đã vá được lưu trong thư mục '{output_dir}'."
                except Exception as e:
                    self.log_message.emit(f"🔍 [GPSPatcherWorker] Exception: {e}")
                    self.log_message.emit(f"❌ Lỗi khi lưu file: {e}")
                    self.patch_finished.emit(False, "Lỗi ghi file."); return
            
            self.progress_update.emit(100)
            self.patch_finished.emit(True, success_message)
            # --- END: NEW CONDITIONAL SAVING LOGIC ---

        finally:
            self.log_message.emit("Dọn dẹp file tạm..."); shutil.rmtree(temp_dir)

# =============================================================================
# THREAD CHO CHỨC NĂNG DỊCH NGƯỢC & ĐÓNG GÓI
# =============================================================================
class DecompileThread(QThread):
    log_message = Signal(str)
    task_finished = Signal(bool, str)

    def __init__(self, mode, input_path, decompiled_dir, rebuilt_dir):
        super().__init__()
        self.mode = mode  # 'decompile' or 'recompile'
        self.input_path = input_path
        self.decompiled_dir = decompiled_dir
        self.rebuilt_dir = rebuilt_dir

        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.java_dir = os.path.join(script_dir, "bin", "java")
        self.apktool_path = os.path.join(self.java_dir, "apktool_2.12.0.jar")
        self.baksmali_path = os.path.join(self.java_dir, "baksmali.jar")
        self.smali_path = os.path.join(self.java_dir, "smali.jar")

    def run_command(self, command):
        self.log_message.emit(f"Đang thực thi: {' '.join(command)}")
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            stdout, _ = process.communicate()
            if stdout:
                self.log_message.emit(f"Output:\n---BEGIN---\n{stdout.strip()}\n---END---")
            
            if process.returncode != 0:
                self.log_message.emit(f"❌ Lỗi: Tác vụ thất bại với mã thoát {process.returncode}")
                return False
            return True
        except Exception as e:
            self.log_message.emit(f"❌ Lỗi không mong muốn: {e}")
            return False

    def run(self):
        if self.mode == 'decompile':
            filename = os.path.basename(self.input_path)
            name, ext = os.path.splitext(filename)
            
            if ext.lower() == '.apk':
                output_dir = os.path.join(self.decompiled_dir, f"apktool_{name}")
                command = ["java", "-jar", self.apktool_path, "d", self.input_path, "-f", "-o", output_dir]
                tool_name = "Apktool"
            elif ext.lower() == '.jar':
                output_dir = os.path.join(self.decompiled_dir, f"smali_{name}")
                command = ["java", "-jar", self.baksmali_path, "d", self.input_path, "-o", output_dir]
                tool_name = "Baksmali"
            else:
                self.task_finished.emit(False, "❌ Lỗi: Định dạng file không được hỗ trợ (chỉ .apk hoặc .jar).")
                return
            
            self.log_message.emit(f"--- Bắt đầu dịch ngược '{filename}' bằng {tool_name} ---")
            os.makedirs(output_dir, exist_ok=True)
            if self.run_command(command):
                self.task_finished.emit(True, f"✅ Dịch ngược thành công!\n   Kết quả được lưu tại: {os.path.abspath(output_dir)}")
            else:
                self.task_finished.emit(False, "❌ Dịch ngược thất bại. Vui lòng kiểm tra log.")

        elif self.mode == 'recompile':
            foldername = os.path.basename(self.input_path)
            
            is_apk = os.path.exists(os.path.join(self.input_path, "AndroidManifest.xml"))
            
            if is_apk:
                output_file = os.path.join(self.rebuilt_dir, f"rebuilt_{foldername}.apk")
                command = ["java", "-jar", self.apktool_path, "b", self.input_path, "-o", output_file]
                tool_name = "Apktool"
            else: # Assume JAR/smali
                output_file = os.path.join(self.rebuilt_dir, f"rebuilt_{foldername}.jar")
                command = ["java", "-jar", self.smali_path, "a", self.input_path, "-o", output_file]
                tool_name = "Smali"

            self.log_message.emit(f"--- Bắt đầu đóng gói '{foldername}' bằng {tool_name} ---")
            if self.run_command(command):
                self.task_finished.emit(True, f"✅ Đóng gói thành công!\n   File được tạo tại: {os.path.abspath(output_file)}")
            else:
                self.task_finished.emit(False, "❌ Đóng gói thất bại. Vui lòng kiểm tra log.")

# =============================================================================
# THREAD CHO CHỨC NĂNG SET QUYỀN
# =============================================================================
class PermissionThread(QThread):
    log_message = Signal(str)
    task_finished = Signal(bool)
    script_update_finished = Signal(dict) # <-- NEW SIGNAL

    def __init__(self, action_type, path, recursive=False, rom_root=None, update_script=False):
        super().__init__()
        self.action_type = action_type
        self.path = path
        self.recursive = recursive
        self.rom_root = rom_root
        self.update_script = update_script
        self.is_windows = (sys.platform == "win32")

    def _set_perms(self, target_path, is_dir):
        perm_octal = 0o755 if is_dir else 0o644
        perm_str = oct(perm_octal)
        
        rel_path = os.path.relpath(target_path) # Relative to CWD for logging
        
        if self.is_windows:
            self.log_message.emit(f"   (Windows) Log Lệnh: chmod {perm_str} \"{rel_path}\"")
            self.log_message.emit(f"   (Windows) Log Lệnh: chown root:root \"{rel_path}\"")
            return True

        try:
            os.chmod(target_path, perm_octal)
            os.chown(target_path, 0, 0) # UID=0 (root), GID=0 (root)
            return True
        except Exception as e:
            self.log_message.emit(f"   ❌ Lỗi trên '{rel_path}': {e}")
            return False

    def run(self):
        self.log_message.emit(f"\n--- Bắt đầu set quyền cho: {os.path.basename(self.path)} ---")
        if self.is_windows:
            self.log_message.emit("⚠️ Chế độ Windows: Không thể thực thi, chỉ ghi log lệnh tương đương.")

        success = True
        mode_expect_str = ""
        if self.action_type == 'apk':
            success = self._set_perms(self.path, is_dir=False)
            mode_expect_str = "644"
        elif self.action_type == 'dir':
            mode_expect_str = "755"
            if not self._set_perms(self.path, is_dir=True):
                self.task_finished.emit(False); return
            
            if self.recursive:
                self.log_message.emit("   - Áp dụng đệ quy cho các thư mục con...")
                try:
                    for root, dirs, files in os.walk(self.path):
                        for name in dirs:
                            dir_path = os.path.join(root, name)
                            if not self._set_perms(dir_path, is_dir=True):
                                success = False
                except Exception as e:
                    self.log_message.emit(f"   ❌ Lỗi nghiêm trọng khi duyệt đệ quy: {e}")
                    success = False

        if success:
            self.log_message.emit("--- ✅ Hoàn tất set quyền ---")
        else:
            self.log_message.emit("--- ❌ Hoàn tất với một hoặc nhiều lỗi ---")
            
        self.task_finished.emit(success)

        # --- NEW: HOOK FOR UPDATER-SCRIPT ---
        if success and self.update_script and self.rom_root and not self.is_windows:
            self.log_message.emit("--- Bắt đầu cập nhật updater-script... ---")
            entry = {
                "path_abs": self.path,
                "type": "dir" if self.action_type == 'dir' else "file",
                "mode_expect": mode_expect_str,
            }
            result = update_updater_script([entry], self.rom_root)
            self.script_update_finished.emit(result)

# =============================================================================
# THREAD CHO CHỨC NĂNG AUTO START & ADB
# =============================================================================
class AdbPatcherThread(QThread):
    log_message = Signal(str)
    patch_finished = Signal(bool, dict)
    cancelled = Signal()  # NEW: Cancel signal

    def __init__(self, build_prop_path, init_rc_path):
        super().__init__()
        self.build_prop_path = build_prop_path
        self.init_rc_path = init_rc_path
        self.modified_contents = {}
        self._cancel_requested = False  # NEW: Cancel flag
    
    def cancel(self):
        """Request cancellation"""
        self.log_message.emit("🔍 [ADBPatcherThread] Cancel requested by user")
        self._cancel_requested = True
    
    def _check_cancel(self):
        """Check if cancel was requested"""
        if self._cancel_requested:
            self.log_message.emit("⛔ Đã hủy bởi người dùng")
            self.cancelled.emit()
            return True
        return False

    def run(self):
        try:
            patcher = FilePatcherLogic()
            if self.build_prop_path:
                self.log_message.emit(f"--- Bắt đầu xử lý {os.path.basename(self.build_prop_path)} ---")
                content, _ = patcher.patch_build_prop(self.build_prop_path)
                self.modified_contents['build.prop'] = content
                self.log_message.emit("--- Xử lý build.prop hoàn tất ---")
                
            if self.init_rc_path:
                self.log_message.emit(f"--- Bắt đầu xử lý {os.path.basename(self.init_rc_path)} ---")
                # The init.rc logic remains inside AdbPatcherThread for now due to its complexity
                self.patch_init_rc() 
                self.log_message.emit("--- Xử lý init.rc hoàn tất ---")

            self.patch_finished.emit(True, self.modified_contents)
        except Exception as e:
            self.log_message.emit(f"Lỗi không mong muốn: {e}")
            self.patch_finished.emit(False, {})

    def patch_build_prop(self):
        self.log_message.emit(f"--- Bắt đầu xử lý {os.path.basename(self.build_prop_path)} ---")
        with open(self.build_prop_path, 'r', encoding='utf-8') as f: lines = f.readlines()
        
        props_to_patch = {
            "persist.sys.usb.config": "mtp,adb",
            "persist.service.adb.enable": "1",
            "persist.service.debuggable": "1",
            "ro.adb.secure": "0",
            "service.adb.tcp.port": "5555",
            "ro.control_privapp_permissions": "disable",
            "ro.setupwizard.mode": "DISABLED",
            "setup.wizard.has.run": "1",
            "persist.adb.notify": "0"
        }
        
        props_found = {key: False for key in props_to_patch}
        new_lines = []

        for line in lines:
            stripped_line = line.strip()
            # Bỏ qua các dòng trống hoặc comment, chỉ xử lý dòng có key=value
            is_prop_line = stripped_line and not stripped_line.startswith('#') and '=' in stripped_line
            
            if is_prop_line:
                key = stripped_line.split('=', 1)[0].strip()
                if key in props_to_patch:
                    props_found[key] = True
                    expected_value = props_to_patch[key]
                    current_value = stripped_line.split('=', 1)[1].strip()
                    if current_value != expected_value:
                        self.log_message.emit(f"Sửa: '{key}' từ '{current_value}' -> '{expected_value}'")
                        new_lines.append("# Patched by tool\n")
                        new_lines.append(f"{key}={expected_value}\n")
                    else:
                        self.log_message.emit(f"Giữ nguyên: '{key}={current_value}' (đã đúng)")
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        # First, collect all properties that need to be added into a temporary list.
        props_to_add = []
        for key, found in props_found.items():
            if not found:
                value = props_to_patch[key]
                self.log_message.emit(f"Thêm: '{key}={value}'")
                # Add the property line directly to the list. No extra newlines here.
                props_to_add.append(f"{key}={value}\n")

        # After checking all properties, if the list of new properties is not empty,
        # add them to the main content under a single header.
        if props_to_add:
            new_lines.append("\n")  # Add a single blank line to separate from previous content.
            new_lines.append("# Patched by tool\n") # The single header for the entire block.
            new_lines.extend(props_to_add) # Add all new properties. This will not add blank lines between them.

        self.modified_contents['build.prop'] = "".join(new_lines)
        self.log_message.emit("--- Xử lý build.prop hoàn tất ---")

    def patch_init_rc(self):
        self.log_message.emit(f"--- Bắt đầu xử lý {os.path.basename(self.init_rc_path)} ---")
        try:
            with open(self.init_rc_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            self.log_message.emit(f"Lỗi đọc file init.rc: {e}")
            self.modified_contents['init.rc'] = None # Báo hiệu lỗi
            return

        on_charger_pattern = re.compile(r"^\s*on\s+charger\s*$", re.MULTILINE)
        match = on_charger_pattern.search(content)

        if match:
            self.log_message.emit("Phát hiện block 'on charger'. Đang kiểm tra nội dung...")
            
            block_start_pos = match.end()
            next_on_pattern = re.compile(r"^\s*on\s+", re.MULTILINE)
            next_match = next_on_pattern.search(content, pos=block_start_pos)
            
            block_end_pos = len(content)
            if next_match:
                block_end_pos = next_match.start()
            
            charger_block_content = content[block_start_pos:block_end_pos]
            
            missing_lines = []
            if 'setprop ro.bootmode "normal"' not in charger_block_content:
                missing_lines.append('    setprop ro.bootmode "normal"')
            if 'setprop sys.powerctl "reboot"' not in charger_block_content:
                missing_lines.append('    setprop sys.powerctl "reboot"')

            if missing_lines:
                self.log_message.emit("Cập nhật: Thêm các dòng lệnh còn thiếu vào block 'on charger'.")
                lines_to_insert_str = "\n".join(missing_lines)
                insertion_point = match.end()
                
                comment_to_add = "# Patched by tool: Update 'on charger' block\n"
                # Combine parts: before the block, the comment, the 'on charger' line, the new lines, and the rest of the file.
                new_content = (content[:match.start()] +
                               comment_to_add +
                               content[match.start():insertion_point] +
                               "\n" + lines_to_insert_str +
                               content[insertion_point:])

                for line in missing_lines:
                    self.log_message.emit(f"Thêm: {line.strip()}")
                
                self.modified_contents['init.rc'] = new_content
            else:
                self.log_message.emit("Giữ nguyên: Block 'on charger' đã có đủ các dòng lệnh cần thiết.")
                self.modified_contents['init.rc'] = content
        else:
            self.log_message.emit("Thêm: Block 'on charger' vào cuối file.")
            charger_block_to_add = """

# Patched by tool: Add 'on charger' block for auto-boot
on charger
    setprop ro.bootmode "normal"
    setprop sys.powerctl "reboot"
    class_start charger
"""
            new_content = content.strip() + "\n" + charger_block_to_add
            self.modified_contents['init.rc'] = new_content
        
        self.log_message.emit("--- Xử lý init.rc hoàn tất ---")

# =============================================================================
# FILE PATCHER LOGIC (SYNCHRONOUS)
# =============================================================================
class FilePatcherLogic:
    """
    A non-threaded class containing the synchronous logic for patching
    build.prop and init.rc files. This logic is shared between the interactive
    preview dialog and the main AdbPatcherThread.
    """
    def patch_build_prop(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        props_to_patch = {
            "persist.sys.usb.config": "mtp,adb", "persist.service.adb.enable": "1",
            "persist.service.debuggable": "1", "ro.adb.secure": "0",
            "service.adb.tcp.port": "5555", "ro.control_privapp_permissions": "disable",
            "ro.setupwizard.mode": "DISABLED", "setup.wizard.has.run": "1",
            "persist.adb.notify": "0"
        }
        
        props_found = {key: False for key in props_to_patch}
        result_lines = []

        for line in lines:
            stripped_line = line.strip()
            is_prop_line = stripped_line and not stripped_line.startswith('#') and '=' in stripped_line
            
            if is_prop_line:
                key, current_value = stripped_line.split('=', 1)
                key, current_value = key.strip(), current_value.strip()

                if key in props_to_patch:
                    props_found[key] = True
                    expected_value = props_to_patch[key]
                    if current_value != expected_value:
                        result_lines.append({'type': 'modified', 'content': f"# Patched by tool\n{key}={expected_value}\n"})
                    else:
                        result_lines.append({'type': 'original', 'content': line})
                else:
                    result_lines.append({'type': 'original', 'content': line})
            else:
                result_lines.append({'type': 'original', 'content': line})
        
        props_to_add_content = []
        for key, found in props_found.items():
            if not found:
                value = props_to_patch[key]
                props_to_add_content.append(f"{key}={value}\n")

        if props_to_add_content:
            if not lines or not lines[-1].strip() == "": result_lines.append({'type': 'original', 'content': '\n'})
            result_lines.append({'type': 'added_header', 'content': '# Patched by tool\n'})
            for new_prop_line in props_to_add_content:
                 result_lines.append({'type': 'added', 'content': new_prop_line})

        final_content = "".join([line['content'] for line in result_lines])
        return final_content, result_lines

    def patch_init_rc(self, file_path):
        # Highlighting for init.rc is complex and deferred. This returns content for saving.
        thread_instance = AdbPatcherThread(None, file_path)
        thread_instance.patch_init_rc()
        final_content = thread_instance.modified_contents.get('init.rc', "")
        
        # Create a simple result structure just for display (no highlighting)
        result_lines = [{'type': 'original', 'content': line} for line in final_content.splitlines(True)]
        return final_content, result_lines

# =============================================================================
# FILE PREVIEW DIALOG
# =============================================================================
class FilePreviewDialog(QDialog):
    def __init__(self, file_key, file_path, parent=None):
        super().__init__(parent)
        self.file_key = file_key
        self.file_path = file_path
        self.parent = parent # To access MainWindow methods if needed

        self.setWindowTitle(f"Xem nội dung: {os.path.basename(self.file_path)}")
        self.setGeometry(self.parent.geometry().center().x() - 350, self.parent.geometry().center().y() - 250, 700, 500)
        
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Consolas", 10))
        layout.addWidget(self.text_edit)

        # Button Box
        self.button_box = QDialogButtonBox()
        self.open_path_button = self.button_box.addButton("Mở đường dẫn", QDialogButtonBox.ButtonRole.ActionRole) # <-- NEW
        self.patch_button = self.button_box.addButton(f"Vá lỗi {self.file_key}", QDialogButtonBox.ButtonRole.ActionRole)
        self.ok_button = self.button_box.addButton(QDialogButtonBox.StandardButton.Ok)
        layout.addWidget(self.button_box)

        # Connections
        self.ok_button.clicked.connect(self.accept)
        self.patch_button.clicked.connect(self.do_patch)
        self.open_path_button.clicked.connect(self.open_file_location) # <-- NEW

        # Initial Load
        self.load_original_content()
    
    def load_original_content(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            self.text_edit.setPlainText(content)
        except Exception as e:
            self.text_edit.setPlainText(f"Không thể đọc file:\n\n{e}")

    def do_patch(self):
        self.parent.fm_log_output.append(f"\n--- Bắt đầu vá lỗi tương tác cho {self.file_key} ---")
        patcher = FilePatcherLogic()
        
        try:
            if self.file_key == 'build.prop':
                new_content, result_lines = patcher.patch_build_prop(self.file_path)
            elif self.file_key == 'init.rc':
                new_content, result_lines = patcher.patch_init_rc(self.file_path)
            else:
                return

            self.update_text_with_highlights(result_lines)
            
            # CHANGE: Overwrite the original file
            save_path = self.file_path
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            self.parent.fm_log_output.append(f"✅ Vá lỗi và ghi đè thành công lên file: {os.path.basename(save_path)}")
            self.patch_button.setEnabled(False)
            self.patch_button.setText("Đã vá lỗi")

        except Exception as e:
            self.parent.fm_log_output.append(f"❌ Lỗi khi vá lỗi tương tác: {e}")
            self.text_edit.append(f"\n\n--- LỖI ---\n{e}")

    def update_text_with_highlights(self, result_lines):
        html_content = ""
        style_base = "font-family: Consolas; font-size: 10pt; white-space: pre-wrap; margin: 0;"
        colors = {
            'modified': 'color: lightgreen; background-color: #112811;',
            'added': 'color: orange; background-color: #332811;',
            'added_header': 'color: cyan;',
            'original': 'color: white;'
        }

        for line_data in result_lines:
            line_type = line_data.get('type', 'original')
            line_content = html.escape(line_data.get('content', ''))
            line_style = colors.get(line_type, colors['original'])
            
            # Remove trailing newline for paragraph tag, as it adds its own spacing
            if line_content.endswith('\n'):
                line_content = line_content[:-1]
                
            html_content += f'<p style="{style_base} {line_style}">{line_content}&nbsp;</p>'

        self.text_edit.setHtml(f'<html><body style="background-color: black;">{html_content}</body></html>')

    def open_file_location(self):
        """Opens the directory containing the file being previewed."""
        directory = os.path.dirname(self.file_path)
        self.parent.open_directory_in_explorer(directory)

# =============================================================================
# SCRIPT UPDATE WORKER
# =============================================================================
class ScriptUpdateWorker(QObject):
    finished = Signal(dict)
    def __init__(self, entries, rom_root):
        super().__init__()
        self.entries = entries
        self.rom_root = rom_root

    def run(self):
        result = update_updater_script(self.entries, self.rom_root)
        self.finished.emit(result)

# =============================================================================
# DEVICE MODE CHECKER THREAD
# =============================================================================
class DeviceModeCheckerThread(QThread):
    """Thread to check device mode after reboot recovery."""
    mode_detected = Signal(str, str)  # (mode, details)
    
    def __init__(self, serial, initial_delay=5, check_interval=2, timeout=30, **kwargs):
        super().__init__()
        self.serial = serial
        self.initial_delay = initial_delay
        self.check_interval = check_interval
        self.timeout = timeout
        self.should_stop = False
        # Support old delay_seconds parameter for compatibility
        if 'delay_seconds' in kwargs:
            self.initial_delay = kwargs['delay_seconds']
            self.timeout = kwargs['delay_seconds']
            self.check_interval = 1
    
    def run(self):
        """Wait and check device mode periodically."""
        import time
        
        # Initial wait (silent)
        time.sleep(self.initial_delay)
        
        if self.should_stop:
            return
        
        # Calculate how many checks to perform
        elapsed = self.initial_delay
        
        # Keep checking until TWRP detected or timeout
        while elapsed < self.timeout:
            if self.should_stop:
                return
            
            # Check device mode
            mode, details = self.detect_device_mode()
            
            # If TWRP detected, emit success
            if mode == "twrp":
                self.mode_detected.emit(mode, details)
                return
            
            # Wait for next check
            time.sleep(self.check_interval)
            elapsed += self.check_interval
        
        # Timeout reached, emit failure
        self.mode_detected.emit("timeout", "Thiết bị không ở chế độ TWRP")
    
    def detect_device_mode(self):
        """Detect current device mode."""
        serial_arg = f"-s {self.serial}" if self.serial else ""
        
        # 1. Check TWRP
        try:
            result = subprocess.run(
                f"adb {serial_arg} shell getprop ro.twrp.version",
                shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                twrp_version = result.stdout.strip()
                return "twrp", f"TWRP {twrp_version}"
        except:
            pass
        
        # 2. Check if in recovery (but not TWRP)
        try:
            result = subprocess.run(
                f"adb {serial_arg} shell getprop ro.bootmode",
                shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                bootmode = result.stdout.strip()
                if "recovery" in bootmode.lower():
                    return "recovery", f"Recovery mode ({bootmode})"
        except:
            pass
        
        # 3. Check if in Android system
        try:
            result = subprocess.run(
                f"adb {serial_arg} shell getprop ro.build.version.release",
                shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                android_version = result.stdout.strip()
                return "system", f"Android {android_version}"
        except:
            pass
        
        # 4. Check fastboot/bootloader
        try:
            result = subprocess.run(
                "fastboot devices",
                shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return "fastboot", "Fastboot/Bootloader mode"
        except:
            pass
        
        # 5. Check if device is connected via ADB at all
        try:
            result = subprocess.run(
                f"adb {serial_arg} get-state",
                shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                state = result.stdout.strip()
                return "unknown", f"ADB connected ({state})"
        except:
            pass
        
        # Device not found
        return "offline", "Không phát hiện thiết bị"
    
    def stop(self):
        """Stop the checker thread."""
        self.should_stop = True

# =============================================================================
# MULTI DEVICE WORKER THREAD
# =============================================================================
class MultiDeviceWorker(QThread):
    """Worker thread for multi-device operations."""
    log_signal = Signal(str)
    finished_signal = Signal()
    
    def __init__(self, operation, serials, **kwargs):
        super().__init__()
        self.operation = operation
        self.serials = [s for s in serials if s.strip() and s.strip() != "\\"]  # Filter invalid serials
        self.kwargs = kwargs
        self.max_workers = min(len(self.serials), 4)  # Max 4 concurrent ADB
    
    def run(self):
        """Execute operation in background thread."""
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                for idx, serial in enumerate(self.serials, 1):
                    future = executor.submit(self._execute_single, serial, idx, len(self.serials))
                    futures.append(future)
                
                # Wait for all to complete (in worker thread, not UI)
                concurrent.futures.wait(futures)
            
            self.finished_signal.emit()
        except Exception as e:
            self.log_signal.emit(f"❌ Lỗi worker: {e}")
            self.finished_signal.emit()
    
    def _execute_single(self, serial, idx, total):
        """Execute operation for single device."""
        try:
            if self.operation == "reboot_twrp":
                self._reboot_twrp_single(serial, idx, total)
            elif self.operation == "reboot_bootloader":
                self._reboot_bootloader_single(serial, idx, total)
            elif self.operation == "reboot_system":
                self._reboot_system_single(serial, idx, total)
            elif self.operation == "unlock_twrp":
                self._unlock_twrp_single(serial, idx, total)
            elif self.operation == "push_files":
                self._push_files_single(serial, idx, total)
            elif self.operation == "flash_file":
                self._flash_file_single(serial, idx, total)
        except Exception as e:
            self.log_signal.emit(f"[{idx}/{total}] ❌ {serial}: Lỗi - {e}")
    
    def _reboot_twrp_single(self, serial, idx, total):
        cmd = f"adb -s {serial} reboot recovery"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            self.log_signal.emit(f"[{idx}/{total}] ✅ {serial}: Đã gửi lệnh reboot TWRP")
        else:
            self.log_signal.emit(f"[{idx}/{total}] ❌ {serial}: Reboot thất bại")
    
    def _reboot_bootloader_single(self, serial, idx, total):
        cmd = f"adb -s {serial} reboot bootloader"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            self.log_signal.emit(f"[{idx}/{total}] ✅ {serial}: Đã gửi lệnh reboot bootloader")
        else:
            self.log_signal.emit(f"[{idx}/{total}] ❌ {serial}: Reboot thất bại")
    
    def _reboot_system_single(self, serial, idx, total):
        cmd = f"adb -s {serial} reboot"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            self.log_signal.emit(f"[{idx}/{total}] ✅ {serial}: Đã gửi lệnh reboot system")
        else:
            self.log_signal.emit(f"[{idx}/{total}] ❌ {serial}: Reboot thất bại")
    
    def _unlock_twrp_single(self, serial, idx, total):
        logs = []
        logs.append(f"[{idx}/{total}] 📱 {serial}: Đang unlock TWRP...")
        
        # Method 1
        cmd1 = f'adb -s {serial} shell twrp set tw_ro_mode 0'
        result1 = subprocess.run(cmd1, shell=True, capture_output=True, text=True, timeout=10)
        if result1.returncode == 0:
            logs.append(f"[{idx}/{total}] ✅ {serial}: Unlock thành công")
            self.log_signal.emit("\n".join(logs))
            return
        
        # Method 2
        cmd2 = f'adb -s {serial} shell input swipe 100 1000 900 1000 100'
        result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True, timeout=10)
        if result2.returncode == 0:
            logs.append(f"[{idx}/{total}] ✅ {serial}: Unlock bằng swipe")
        else:
            logs.append(f"[{idx}/{total}] ⚠️ {serial}: Unlock thất bại")
        
        self.log_signal.emit("\n".join(logs))
    
    def _push_files_single(self, serial, idx, total):
        files = self.kwargs.get('files', [])
        for file_path in files:
            file_name = os.path.basename(file_path)
            cmd = f'adb -s {serial} push "{file_path}" /tmp/'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                self.log_signal.emit(f"[{idx}/{total}] ✅ {serial}: Đã push {file_name}")
            else:
                self.log_signal.emit(f"[{idx}/{total}] ❌ {serial}: Push thất bại - {file_name}")
    
    def _flash_file_single(self, serial, idx, total):
        file_path = self.kwargs.get('file_path')
        dest_path = self.kwargs.get('dest_path', '/tmp/')
        method = self.kwargs.get('method', 'twrp_install')
        
        logs = []
        file_name = os.path.basename(file_path)
        logs.append(f"[{idx}/{total}] 📱 {serial}: Bắt đầu flash {file_name}...")
        
        # Step 1: Unlock TWRP
        unlock_cmd = f'adb -s {serial} shell twrp set tw_ro_mode 0'
        result = subprocess.run(unlock_cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logs.append(f"[{idx}/{total}] 🔓 {serial}: TWRP đã unlock")
        
        # Step 2: Format data (heavier than wipe)
        logs.append(f"[{idx}/{total}] 🗑️ {serial}: Đang format data...")
        wipe_cmd = f'adb -s {serial} shell twrp format data'
        result = subprocess.run(wipe_cmd, shell=True, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            logs.append(f"[{idx}/{total}] ✅ {serial}: Format data thành công")
        else:
            logs.append(f"[{idx}/{total}] ⚠️ {serial}: Format có thể không thành công")
        
        # Step 3: Push file
        dest_file = dest_path.rstrip('/') + '/' + file_name
        push_cmd = f'adb -s {serial} push "{file_path}" {dest_file}'
        result = subprocess.run(push_cmd, shell=True, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            logs.append(f"[{idx}/{total}] ❌ {serial}: Push thất bại!")
            self.log_signal.emit("\n".join(logs))
            return
        
        logs.append(f"[{idx}/{total}] ✅ {serial}: Push thành công")
        
        # Step 4: Flash ROM
        if method == "twrp_install":
            flash_cmd = f'adb -s {serial} shell twrp install {dest_file}'
            result = subprocess.run(flash_cmd, shell=True, capture_output=True, text=True, timeout=300)
            
            output_lower = ((result.stdout or "") + (result.stderr or "")).lower()
            has_error = any(kw in output_lower for kw in ["error installing", "script aborted", "installation failed"])
            has_success = any(kw in output_lower for kw in ["successful", "done", "installation complete"])
            
            if has_error:
                logs.append(f"[{idx}/{total}] ❌ {serial}: Flash thất bại!")
            elif has_success or result.returncode == 0:
                logs.append(f"[{idx}/{total}] ✅ {serial}: Flash thành công!")
            else:
                logs.append(f"[{idx}/{total}] ⚠️ {serial}: Không rõ kết quả")
        
        self.log_signal.emit("\n".join(logs))

# =============================================================================
# GIAO DIỆN CHÍNH
# =============================================================================
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Android Auto Rom v6.0 by Mon")
        self.setAcceptDrops(True)
        self.setFixedSize(700, 550)
        self.center_window()
        
        self.modified_adb_files = {}
        self.valid_files = {}
        
        # Multi-device worker
        self.multi_device_worker = None

        # --- Initialize Config Manager ---
        self.config = ConfigManager()
        import logging
        logging.info(f"💾 Config loaded from: {self.config.config_file}")

        # --- Centralize and create output directories ---
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.script_dir, "data")
        self.config_dir = os.path.join(self.script_dir, "config")
        self.patched_dir = os.path.join(self.data_dir, "Patched")  # Thư mục đã Patched
        self.decompiled_dir = os.path.join(self.data_dir, "Decompiled")
        self.rebuilt_dir = os.path.join(self.data_dir, "Rebuilt")
        
        os.makedirs(self.patched_dir, exist_ok=True)
        os.makedirs(self.decompiled_dir, exist_ok=True)
        os.makedirs(self.rebuilt_dir, exist_ok=True)

        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        # Tăng chiều cao tab +10% bằng padding (từ 8px -> 9px) + Modern styling với viền xeon
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                padding: 9px 16px;
                margin-right: 3px;
                margin-top: 2px;
                border-radius: 6px;
                background-color: #2d2d2d;
                color: #aaaaaa;
                border: 2px solid #404040;
                outline: none !important;
            }
            
            QTabBar::tab:selected {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 2px solid #00aaff !important;
                box-shadow: 0 0 10px #00aaff, inset 0 0 5px #00aaff;
                outline: none !important;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #353535;
                color: #dddddd;
                border: 2px solid #555555;
            }
            
            QTabBar::tab:focus {
                outline: none !important;
            }
        """)
        
        # Disable drops on tabs to allow propagation to child tab widgets
        self.tabs.setAcceptDrops(False)
        
        main_layout.addWidget(self.tabs)

        # --- START ADB COMMENT TAB CODE ---
        self.adb_comment_tab = QWidget()
        self.tabs.addTab(self.adb_comment_tab, "💬 ADB Comment")
        self.init_adb_comment_tab()
        # --- END ADB COMMENT TAB CODE ---
        
        # --- START NEW DECOMPILE TAB CODE ---
        self.decompile_tab = QWidget()
        self.tabs.addTab(self.decompile_tab, "🔧 Dịch ngược Jar/APK")
        self.init_decompile_tab()
        # --- END NEW DECOMPILE TAB CODE ---
        
        # --- PATCH FILE TAB (Combined: Auto Rom + GPS Patcher + Auto Start & ADB) ---
        self.rom_tools_tab = QWidget()
        self.tabs.addTab(self.rom_tools_tab, "📄 Patch File")
        self.init_rom_tools_tab()
        
        # Shared log output (set by Main.pyw) - LOG TRỰC TIẾP VÀO ĐÂY
        self.shared_log_output = None
        
        # Create fake log outputs để giữ compatibility với code cũ
        self.gps_log_output = self
        self.adb_log_output = self
        self.decompile_log_output = self
        self.adb_comment_log = self
        self.fm_log_output = self
        
        # Device mode checker thread
        self.device_mode_checker_thread = None
    
    def set_shared_log_output(self, shared_log_widget):
        """Set shared log output - LOG TRỰC TIẾP."""
        self.shared_log_output = shared_log_widget
        import logging
        logging.info("📋 All function logs connected to shared output panel")
    
    def append(self, text):
        """Append text to shared log (compatibility method)."""
        if self.shared_log_output:
            self.shared_log_output.append(text)
            # Auto-scroll to bottom
            from PySide6.QtGui import QTextCursor
            cursor = self.shared_log_output.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.shared_log_output.setTextCursor(cursor)
    
    def clear(self):
        """Clear shared log (compatibility method)."""
        if self.shared_log_output:
            self.shared_log_output.clear()

    def init_rom_tools_tab(self):
        """Initialize Smart ROM Patcher - Auto-detect and patch files intelligently."""
        layout = QVBoxLayout(self.rom_tools_tab)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Enable drag & drop for this tab
        self.rom_tools_tab.setAcceptDrops(True)
        self.rom_tools_tab.dragEnterEvent = lambda event: self.rom_tools_tab_dragEnterEvent(event)
        self.rom_tools_tab.dropEvent = lambda event: self.rom_tools_tab_dropEvent(event)
        
        # Instructions (no header)
        instructions = QLabel(
            "📥 Kéo thả file/thư mục vào đây:<br>"
            "   • <b>services.jar</b> → Patch GPS (bypass mock location)<br>"
            "   • <b>build.prop</b> → Enable ADB, disable permissions<br>"
            "   • <b>init.rc</b> → Auto-boot on charger<br>"
            "   • <b>Thư mục ROM</b> → Tự động tìm và patch tất cả file trên"
        )
        instructions.setTextFormat(Qt.TextFormat.RichText)  # Enable HTML rendering
        instructions.setWordWrap(True)
        instructions.setStyleSheet("padding: 10px; border: 1px solid #555; border-radius: 5px;")
        instructions.setAcceptDrops(False)  # Ensure drops go to parent
        layout.addWidget(instructions)
        
        # File selection area
        file_select_layout = QHBoxLayout()
        lbl_file_folder = QLabel("File/Folder đã chọn:")
        lbl_file_folder.setAcceptDrops(False)
        file_select_layout.addWidget(lbl_file_folder)
        self.smart_file_display = QLineEdit()
        self.smart_file_display.setPlaceholderText("Chưa chọn file hoặc thư mục")
        self.smart_file_display.setReadOnly(True)
        self.smart_file_display.setAcceptDrops(False)  # Ensure drops go to parent
        file_select_layout.addWidget(self.smart_file_display, 1)
        
        self.smart_choose_btn = PushButton("📁 Chọn...")
        self.smart_choose_btn.clicked.connect(self.smart_choose_file_or_folder)
        self.smart_choose_btn.setAcceptDrops(False)
        file_select_layout.addWidget(self.smart_choose_btn)
        layout.addLayout(file_select_layout)
        
        # Main action button (use default PyQt6 style)
        self.smart_patch_btn = PushButton("⚡ Phân tích và Tự động lưu")
        self.smart_patch_btn.clicked.connect(self.smart_auto_patch)
        self.smart_patch_btn.setEnabled(False)
        self.smart_patch_btn.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
        self.smart_patch_btn.setAcceptDrops(False)
        layout.addWidget(self.smart_patch_btn)
        
        # Progress bar
        self.smart_progress_bar = QProgressBar()
        self.smart_progress_bar.setValue(0)
        self.smart_progress_bar.setAcceptDrops(False)
        layout.addWidget(self.smart_progress_bar)
        
        # Utility buttons + Overwrite checkbox
        utility_layout = QHBoxLayout()
        self.smart_open_folder_btn = PushButton("📂 Mở thư mục đã Patched")
        self.smart_open_folder_btn.clicked.connect(self.open_patched_folder)
        self.smart_open_folder_btn.setAcceptDrops(False)
        utility_layout.addWidget(self.smart_open_folder_btn)
        
        self.smart_overwrite_checkbox = CheckBox("Ghi đè file gốc")
        self.smart_overwrite_checkbox.setToolTip("Khi tích, file sẽ được patch và ghi đè trực tiếp vào file gốc thay vì lưu vào thư mục Patched")
        self.smart_overwrite_checkbox.setAcceptDrops(False)
        utility_layout.addWidget(self.smart_overwrite_checkbox)
        
        utility_layout.addStretch()
        layout.addLayout(utility_layout)
        
        # Add stretch at the end
        layout.addStretch()
        
        # Store selected files/folders
        self.smart_selected_paths = []
        self.smart_detected_files = {}

    def init_gps_tab(self):
        layout = QVBoxLayout(self.gps_tab)
        layout.setSpacing(8)  # Reduce spacing between widgets
        layout.setContentsMargins(10, 10, 10, 10)  # Reduce margins
        layout.addWidget(QLabel("1. Kéo và thả file services.jar vào đây hoặc chọn file:"))
        self.gps_file_path_edit = QLineEdit(); self.gps_file_path_edit.setPlaceholderText("Chưa chọn file services.jar"); self.gps_file_path_edit.setReadOnly(True)
        layout.addWidget(self.gps_file_path_edit)
        self.gps_choose_file_btn = PushButton("Chọn File services.jar"); self.gps_choose_file_btn.clicked.connect(self.select_gps_file)
        layout.addWidget(self.gps_choose_file_btn)
        
        self.gps_patch_btn = PushButton("Bắt đầu vá lỗi GPS")
        self.gps_patch_btn.clicked.connect(self.start_gps_patch)
        self.gps_patch_btn.setEnabled(False)
        self.gps_patch_btn.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))

        self.gps_open_folder_btn = PushButton("📂 Mở thư mục đã vá")
        self.gps_open_folder_btn.clicked.connect(self.open_patched_folder)
        self.gps_open_folder_btn.setEnabled(True)

        button_layout_gps = QHBoxLayout()
        button_layout_gps.addWidget(self.gps_patch_btn)
        button_layout_gps.addWidget(self.gps_open_folder_btn)
        layout.addLayout(button_layout_gps)

        self.gps_progress_bar = QProgressBar()
        layout.addWidget(self.gps_progress_bar)
        layout.addStretch()  # Push content to top

    def init_adb_tab(self):
        layout = QVBoxLayout(self.adb_tab)
        layout.setSpacing(8)  # Reduce spacing between widgets
        layout.setContentsMargins(10, 10, 10, 10)  # Reduce margins
        layout.addWidget(QLabel("1. Chọn file build.prop và/hoặc init.rc:"))
        self.adb_file_path_edit = QLineEdit(); self.adb_file_path_edit.setPlaceholderText("Chưa chọn file"); self.adb_file_path_edit.setReadOnly(True)
        layout.addWidget(self.adb_file_path_edit)
        self.adb_choose_file_btn = PushButton("Chọn File (build.prop, init.rc)"); self.adb_choose_file_btn.clicked.connect(self.select_adb_files)
        layout.addWidget(self.adb_choose_file_btn)
        self.adb_patch_btn = PushButton("Phân tích và Tự động lưu"); self.adb_patch_btn.clicked.connect(self.start_adb_patch); self.adb_patch_btn.setEnabled(False)
        self.adb_patch_btn.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
        
        self.adb_open_folder_btn = PushButton("📂 Mở thư mục đã vá")
        self.adb_open_folder_btn.clicked.connect(self.open_patched_folder)
        self.adb_open_folder_btn.setEnabled(True)

        button_layout_adb = QHBoxLayout()
        button_layout_adb.addWidget(self.adb_patch_btn)
        button_layout_adb.addWidget(self.adb_open_folder_btn)
        layout.addLayout(button_layout_adb)
        layout.addStretch()  # Push content to top

    def init_fm_tab(self):
        layout = QVBoxLayout(self.fm_tab)
        layout.setSpacing(8)  # Reduce spacing between widgets
        layout.setContentsMargins(10, 10, 10, 10)  # Reduce margins
        
        # 1. Action Buttons Area (No changes here)
        action_layout = QHBoxLayout()
        self.fm_autopatch_btn = PushButton("🚀 Auto Patch")
        self.fm_autopatch_btn.clicked.connect(self.start_auto_patching)
        self.fm_autopatch_btn.setEnabled(False)
        self.fm_autopatch_btn.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
        
        self.fm_view_buildprop_btn = PushButton("Xem build.prop")
        self.fm_view_buildprop_btn.clicked.connect(lambda: self.show_file_preview('build.prop'))
        self.fm_view_buildprop_btn.setEnabled(False)
        
        self.fm_view_initrc_btn = PushButton("Xem init.rc")
        self.fm_view_initrc_btn.clicked.connect(lambda: self.show_file_preview('init.rc'))
        self.fm_view_initrc_btn.setEnabled(False)

        action_layout.addWidget(self.fm_autopatch_btn)
        action_layout.addWidget(self.fm_view_buildprop_btn)
        action_layout.addWidget(self.fm_view_initrc_btn)
        
        self.fm_auto_update_script_checkbox = QCheckBox("Auto-update updater-script")
        self.fm_auto_update_script_checkbox.setChecked(True)
        self.fm_auto_update_script_checkbox.setToolTip("Tự động cập nhật META-INF/com/google/android/updater-script khi Set quyền.")
        action_layout.addWidget(self.fm_auto_update_script_checkbox)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        # 2. Tree View Area - REFACTORED TO USE QStackedWidget
        self.fm_stack = QStackedWidget() # Create the stack
        
        # Page 0: The Placeholder Label
        self.fm_placeholder_label = QLabel("🗂️ Kéo thả thư mục ROM unpacked vào đây để bắt đầu")
        self.fm_placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fm_placeholder_label.setStyleSheet("color: #888; font-style: italic;")
        
        # Page 1: The Tree View (existing code)
        self.fm_model = QFileSystemModel()
        self.fm_tree_view = QTreeView()
        self.fm_tree_view.setModel(self.fm_model)
        self.fm_tree_view.setRootIndex(self.fm_model.index("")) # Important to keep this
        self.fm_tree_view.setColumnWidth(0, 250)
        self.fm_tree_view.setAnimated(False)
        self.fm_tree_view.setIndentation(20)
        self.fm_tree_view.setSortingEnabled(True)
        self.fm_tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.fm_tree_view.customContextMenuRequested.connect(self.show_fm_context_menu)
        
        # Add widgets to the stack
        self.fm_stack.addWidget(self.fm_placeholder_label) # Index 0
        self.fm_stack.addWidget(self.fm_tree_view)         # Index 1
        
        # Set the initial view to the placeholder
        self.fm_stack.setCurrentIndex(0)
        
        # Add the stack to the main layout
        layout.addWidget(self.fm_stack)
        
        # Log output removed - using shared log panel

    def init_decompile_tab(self):
        layout = QVBoxLayout(self.decompile_tab)
        layout.setSpacing(8)  # Reduce spacing between widgets
        layout.setContentsMargins(10, 10, 10, 10)  # Reduce margins

        # Decompile Section
        layout.addWidget(QLabel("1. Kéo thả file .jar/.apk hoặc chọn để dịch ngược:"))
        self.decompile_input_path = QLineEdit(); self.decompile_input_path.setReadOnly(True); self.decompile_input_path.setPlaceholderText("Chưa chọn file")
        decompile_buttons_layout = QHBoxLayout()
        decompile_buttons_layout.addWidget(self.decompile_input_path)
        decompile_select_btn = PushButton("Chọn File"); decompile_select_btn.clicked.connect(self.select_decompile_file)
        decompile_buttons_layout.addWidget(decompile_select_btn)
        layout.addLayout(decompile_buttons_layout)
        
        self.decompile_btn = PushButton("Dịch ngược"); self.decompile_btn.clicked.connect(self.start_decompile); self.decompile_btn.setEnabled(False)
        self.decompile_btn.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
        layout.addWidget(self.decompile_btn)

        # Recompile Section
        layout.addWidget(QLabel("2. Kéo thả thư mục đã chỉnh sửa hoặc chọn để đóng gói lại:"))
        self.recompile_input_path = QLineEdit(); self.recompile_input_path.setReadOnly(True); self.recompile_input_path.setPlaceholderText("Chưa chọn thư mục")
        recompile_buttons_layout = QHBoxLayout()
        recompile_buttons_layout.addWidget(self.recompile_input_path)
        recompile_select_btn = PushButton("Chọn Thư mục"); recompile_select_btn.clicked.connect(self.select_recompile_folder)
        recompile_buttons_layout.addWidget(recompile_select_btn)
        layout.addLayout(recompile_buttons_layout)

        self.recompile_btn = PushButton("Đóng gói lại"); self.recompile_btn.clicked.connect(self.start_recompile); self.recompile_btn.setEnabled(False)
        self.recompile_btn.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
        layout.addWidget(self.recompile_btn)
        
        # Open folder button
        open_output_btn = PushButton("📂 Mở thư mục Output (Decompiled/Rebuilt)"); open_output_btn.clicked.connect(self.open_output_folders)
        layout.addWidget(open_output_btn)
        layout.addStretch()  # Push content to top

    def init_adb_comment_tab(self):
        """Initialize ADB Comment tab for executing ADB commands."""
        layout = QVBoxLayout(self.adb_comment_tab)
        layout.setSpacing(5)  # Minimal spacing between widgets
        layout.setContentsMargins(5, 5, 5, 5)  # Minimal margins
        
        # Input field style - subtle border only
        input_style = "QLineEdit, QTextEdit { border: 1px solid #555; padding: 4px; border-radius: 3px; }"
        
        # Enable drag & drop for this tab
        self.adb_comment_tab.setAcceptDrops(True)
        self.adb_comment_tab.dragEnterEvent = self.adb_tab_dragEnterEvent
        self.adb_comment_tab.dropEvent = self.adb_tab_dropEvent
        
        # Store dropped files
        self.adb_dropped_files = []
        
        # Multi device list - load from config and filter invalid serials
        saved_serials_text = self.config.get("multi_device_serials", "")
        self.multi_device_serials = [
            s.strip() for s in saved_serials_text.split('\n') 
            if s.strip() and s.strip() != "\\"
        ] if saved_serials_text else []
        
        # Create uploaded files directory
        self.uploaded_files_dir = os.path.join(os.path.dirname(__file__), 'data', 'uploaded_files')
        os.makedirs(self.uploaded_files_dir, exist_ok=True)
        
        # Currently selected file
        self.current_selected_file = None
        
        # Row 1: Device Serial + File Display (Combined)
        top_row_layout = QHBoxLayout()
        top_row_layout.setSpacing(5)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        
        # Serial thiết bị section
        top_row_layout.addWidget(QLabel("📱 Serial thiết bị:"))
        self.adb_serial_input = QLineEdit()
        self.adb_serial_input.setPlaceholderText("Nhập serial hoặc click để chọn")
        self.adb_serial_input.setStyleSheet(input_style)
        self.adb_serial_input.setMaximumWidth(250)  # Giảm 20% chiều rộng
        
        # Load saved serial from config
        saved_serial = self.config.get("adb_device_serial", "")
        if saved_serial:
            self.adb_serial_input.setText(saved_serial)
            print(f"💾 Đã load serial đã lưu: {saved_serial}")
        
        # Auto-save when user changes serial
        self.adb_serial_input.textChanged.connect(self.on_serial_changed)
        
        top_row_layout.addWidget(self.adb_serial_input)
        
        # Auto-detect device button (inline)
        auto_detect_btn = PushButton("🔍")
        auto_detect_btn.setMaximumWidth(40)
        auto_detect_btn.setToolTip("Tự động phát hiện thiết bị")
        auto_detect_btn.clicked.connect(self.detect_adb_device)
        top_row_layout.addWidget(auto_detect_btn)
        
        # Multi Device toggle button
        self.multi_device_btn = PushButton("📱 Multi")
        self.multi_device_btn.setMaximumWidth(70)
        self.multi_device_btn.setCheckable(True)
        self.multi_device_btn.setToolTip("Điều khiển nhiều thiết bị cùng lúc")
        self.multi_device_btn.clicked.connect(self.toggle_multi_device)
        self.multi_device_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #555;
            }
            QPushButton:checked {
                background-color: #00aaff;
                border: 1px solid #00aaff;
                color: white;
                font-weight: bold;
            }
        """)
        top_row_layout.addWidget(self.multi_device_btn)
        
        # Separator
        top_row_layout.addWidget(QLabel("|"))
        
        # Danh sách File button (replacement for "Tệp đã chọn")
        self.file_list_btn = PushButton("📄 Danh sách File")
        self.file_list_btn.clicked.connect(self.show_file_list_menu)
        self.file_list_btn.setMinimumWidth(150)
        top_row_layout.addWidget(self.file_list_btn)
        
        # File display (shows currently selected file)
        self.adb_file_display = QLineEdit()
        self.adb_file_display.setReadOnly(True)
        self.adb_file_display.setPlaceholderText("Kéo thả file vào đây hoặc chọn từ danh sách...")
        self.adb_file_display.setStyleSheet(input_style)
        top_row_layout.addWidget(self.adb_file_display)
        
        # File command menu button
        self.file_cmd_btn = PushButton("📁 Lệnh Tệp Tin")
        self.file_cmd_btn.clicked.connect(self.show_file_command_menu)
        top_row_layout.addWidget(self.file_cmd_btn)
        
        layout.addLayout(top_row_layout)
        
        # Row 2: Command Input Section + Quick Buttons
        cmd_row_layout = QHBoxLayout()
        cmd_row_layout.setSpacing(5)
        cmd_row_layout.setContentsMargins(0, 0, 0, 0)
        
        # Lệnh ADB input (left side)
        self.adb_command_input = QTextEdit()
        self.adb_command_input.setPlaceholderText("💬 Nhập lệnh ADB (vd: shell getprop ro.build.version.release)\nMỗi dòng là 1 lệnh riêng.")
        self.adb_command_input.setMaximumHeight(100)
        self.adb_command_input.setStyleSheet(input_style)
        cmd_row_layout.addWidget(self.adb_command_input, 7)  # 70% width
        
        # Quick command buttons (right side)
        quick_buttons_container = QVBoxLayout()
        quick_buttons_container.setSpacing(3)
        quick_buttons_container.setContentsMargins(0, 0, 0, 0)
        
        # Quick command buttons: Mode, Reboot, Logcat
        # Mode button (với menu dropdown)
        self.mode_btn = PushButton("🔧 Mode")
        self.mode_btn.clicked.connect(self.show_mode_menu)
        quick_buttons_container.addWidget(self.mode_btn)
        
        # Reboot button
        reboot_btn = PushButton("🔌 Reboot")
        reboot_btn.clicked.connect(partial(self.insert_quick_command, "adb reboot"))
        quick_buttons_container.addWidget(reboot_btn)
        
        # Logcat button
        logcat_btn = PushButton("📊 Logcat")
        logcat_btn.clicked.connect(partial(self.insert_quick_command, "adb logcat -d | tail -50"))
        quick_buttons_container.addWidget(logcat_btn)
        
        cmd_row_layout.addLayout(quick_buttons_container, 3)  # 30% width
        
        layout.addLayout(cmd_row_layout)
        
        # Execute Button (giữ nguyên vị trí cũ)
        self.adb_exec_btn = PushButton("▶️ Thực thi lệnh")
        self.adb_exec_btn.clicked.connect(self.execute_adb_commands)
        self.adb_exec_btn.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
        layout.addWidget(self.adb_exec_btn)
        
        # Push all content to top
        layout.addStretch()

    def adb_tab_dragEnterEvent(self, event):
        """Handle drag enter event for ADB Comment tab."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def adb_tab_dropEvent(self, event):
        """Handle drop event for ADB Comment tab."""
        urls = event.mimeData().urls()
        if urls:
            for url in urls:
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    self.adb_dropped_files.append(file_path)
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                    self.adb_comment_log.append(f"📥 Đã nhận file: {file_name} ({file_size:.2f} MB)")
                elif os.path.isdir(file_path):
                    self.adb_dropped_files.append(file_path)
                    dir_name = os.path.basename(file_path)
                    self.adb_comment_log.append(f"📂 Đã nhận thư mục: {dir_name}")
                else:
                    self.adb_comment_log.append(f"⚠️ Bỏ qua: {os.path.basename(file_path)} (không tồn tại)")
            
            # Update file display with file/folder names
            if self.adb_dropped_files:
                items = [os.path.basename(f) for f in self.adb_dropped_files]
                if len(items) == 1:
                    self.adb_file_display.setText(items[0])
                else:
                    self.adb_file_display.setText(f"{items[0]} (+{len(items)-1} items)")
            
            event.acceptProposedAction()
    
    def rom_tools_tab_dragEnterEvent(self, event):
        """Handle drag enter event for ROM Tools tab."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def rom_tools_tab_dropEvent(self, event):
        """Handle drop event for ROM Tools tab."""
        try:
            urls = event.mimeData().urls()
            if urls:
                paths = []
                for url in urls:
                    path = url.toLocalFile()
                    if os.path.exists(path):
                        paths.append(path)
                
                if paths:
                    self.smart_handle_dropped_paths(paths)
                
                event.acceptProposedAction()
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def show_file_command_menu(self):
        """Show file command menu with options."""
        menu = QMenu(self)
        
        # Action 0: Unlock TWRP
        unlock_twrp_action = QAction("🔓 Unlock TWRP (Bypass Swipe)", self)
        unlock_twrp_action.triggered.connect(self.unlock_twrp)
        menu.addAction(unlock_twrp_action)
        
        menu.addSeparator()
        
        # Action 1: Push to /tmp
        push_tmp_action = QAction("📤 Đưa file vào /tmp (TWRP)", self)
        push_tmp_action.triggered.connect(self.push_files_to_tmp)
        menu.addAction(push_tmp_action)
        
        # Action 2: Flash file
        flash_action = QAction("⚡ Flash ZIP/IMG", self)
        flash_action.triggered.connect(self.show_flash_file_dialog)
        menu.addAction(flash_action)
        
        menu.addSeparator()
        
        # Action 3: Set permissions 644
        chmod_action = QAction("🔒 Set quyền 644", self)
        chmod_action.triggered.connect(self.set_file_permissions_644)
        menu.addAction(chmod_action)
        
        # Action 4: Create ZIP package
        create_zip_action = QAction("📦 Đóng .zip", self)
        create_zip_action.triggered.connect(self.create_zip_package)
        menu.addAction(create_zip_action)
        
        menu.addSeparator()
        
        # Action 5: Clear file list
        clear_action = QAction("🗑️ Xóa danh sách file", self)
        clear_action.triggered.connect(self.clear_dropped_files)
        menu.addAction(clear_action)
        
        # Show menu at button position
        menu.exec(self.file_cmd_btn.mapToGlobal(self.file_cmd_btn.rect().bottomLeft()))
    
    def unlock_twrp(self):
        """Unlock TWRP by disabling read-only mode."""
        # Check multi device mode
        if self.multi_device_btn.isChecked() and self.multi_device_serials:
            self.adb_comment_log.append(f"\n{'='*30}")
            self.adb_comment_log.append(f"🔓 MULTI DEVICE - Unlock TWRP cho {len(self.multi_device_serials)} thiết bị (max 4 parallel)")
            self.adb_comment_log.append(f"{'='*30}\n")
            
            if self.multi_device_worker and self.multi_device_worker.isRunning():
                self.multi_device_worker.wait()
            
            self.multi_device_worker = MultiDeviceWorker("unlock_twrp", self.multi_device_serials)
            self.multi_device_worker.log_signal.connect(self.adb_comment_log.append)
            self.multi_device_worker.finished_signal.connect(
                lambda: self.adb_comment_log.append(f"\n{'='*30}\n✅ HOÀN TẤT! Đã unlock TWRP\n{'='*30}\n")
            )
            self.multi_device_worker.start()
            return
        
        # Single device mode
        serial = self.adb_serial_input.text().strip()
        
        self.adb_comment_log.append(f"\n{'='*30}")
        self.adb_comment_log.append("🔓 Unlock TWRP (Bypass Swipe)...")
        if serial:
            self.adb_comment_log.append(f"📱 Serial: {serial}")
        self.adb_comment_log.append(f"{'='*30}\n")
        
        unlock_success = False
        
        # Method 1: Disable read-only mode via TWRP command
        self.adb_comment_log.append("📍 Method 1: Disable read-only mode...")
        cmd1 = f'adb -s {serial} shell twrp set tw_ro_mode 0' if serial else 'adb shell twrp set tw_ro_mode 0'
        
        try:
            result1 = subprocess.run(cmd1, shell=True, capture_output=True, text=True, timeout=10)
            
            if result1.returncode == 0:
                self.adb_comment_log.append("   ✅ Đã disable read-only mode")
                unlock_success = True
            else:
                self.adb_comment_log.append("   ⚠️ Method 1 thất bại, thử method 2...")
                
                # Method 2: Simulate swipe gesture
                self.adb_comment_log.append("\n📍 Method 2: Simulate swipe gesture...")
                cmd2 = f'adb -s {serial} shell input swipe 100 1000 900 1000 100' if serial else 'adb shell input swipe 100 1000 900 1000 100'
                
                result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True, timeout=10)
                
                if result2.returncode == 0:
                    self.adb_comment_log.append("   ✅ Đã simulate swipe gesture")
                    unlock_success = True
                else:
                    self.adb_comment_log.append("   ❌ Method 2 cũng thất bại!")
                    if result2.stderr:
                        self.adb_comment_log.append(f"   Error: {result2.stderr.strip()}")
            
            # Verify TWRP state
            self.adb_comment_log.append("\n📍 Kiểm tra trạng thái TWRP...")
            verify_cmd = f'adb -s {serial} shell getprop ro.twrp.boot' if serial else 'adb shell getprop ro.twrp.boot'
            verify_result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True, timeout=5)
            
            is_in_twrp = False
            if verify_result.returncode == 0 and verify_result.stdout.strip():
                twrp_boot = verify_result.stdout.strip()
                self.adb_comment_log.append(f"   ℹ️ TWRP boot: {twrp_boot}")
                is_in_twrp = (twrp_boot == "1")
            else:
                self.adb_comment_log.append("   ⚠️ Không detect được TWRP property")
            
            # Final result
            if not is_in_twrp:
                self.adb_comment_log.append("\n❌ Thiết bị KHÔNG Ở TRONG TWRP!")
                self.adb_comment_log.append("⚠️ Vui lòng reboot vào TWRP trước:")
                self.adb_comment_log.append("   adb reboot recovery")
            elif unlock_success:
                self.adb_comment_log.append("\n✅ TWRP đã unlock thành công!")
            else:
                self.adb_comment_log.append("\n⚠️ Unlock thất bại nhưng đã ở trong TWRP!")
                self.adb_comment_log.append("💡 Tip: Thử gạt thanh thủ công hoặc flash trực tiếp.")
                    
        except subprocess.TimeoutExpired:
            self.adb_comment_log.append("\n❌ Timeout: Lệnh không phản hồi!")
            self.adb_comment_log.append("⚠️ Đảm bảo thiết bị đã vào TWRP!")
        except Exception as e:
            self.adb_comment_log.append(f"\n❌ Lỗi: {e}")
        
        self.adb_comment_log.append(f"\n{'='*30}\n")
    
    def push_files_to_tmp(self):
        """Push the currently selected file to /tmp on device using background worker."""
        # Get the file to push - prioritize current_selected_file, then last in adb_dropped_files
        file_to_push = None
        
        if hasattr(self, 'current_selected_file') and self.current_selected_file and os.path.exists(self.current_selected_file):
            file_to_push = self.current_selected_file
        elif self.adb_dropped_files:
            file_to_push = self.adb_dropped_files[-1]  # Last added file
        
        if not file_to_push:
            self.adb_comment_log.append("❌ Không có file nào để push!")
            return
        
        file_name = os.path.basename(file_to_push)
        
        # Check multi device mode
        if self.multi_device_btn.isChecked() and self.multi_device_serials:
            self.adb_comment_log.append(f"\n{'='*30}")
            self.adb_comment_log.append(f"📤 MULTI DEVICE - Push {file_name} cho {len(self.multi_device_serials)} thiết bị (max 4 parallel)")
            self.adb_comment_log.append(f"{'='*30}\n")
            
            if self.multi_device_worker and self.multi_device_worker.isRunning():
                self.multi_device_worker.wait()
            
            self.multi_device_worker = MultiDeviceWorker("push_files", self.multi_device_serials, files=[file_to_push])
            self.multi_device_worker.log_signal.connect(self.adb_comment_log.append)
            self.multi_device_worker.finished_signal.connect(
                lambda: self.adb_comment_log.append(f"\n{'='*30}\n✅ HOÀN TẤT! Đã push file\n{'='*30}\n")
            )
            self.multi_device_worker.start()
            return
        
        # Single device mode - use background worker
        serial = self.adb_serial_input.text().strip()
        
        self.adb_comment_log.append(f"\n{'='*30}")
        self.adb_comment_log.append(f"📤 Push file: {file_name}")
        if serial:
            self.adb_comment_log.append(f"📱 Serial: {serial}")
        self.adb_comment_log.append(f"{'='*30}")
        
        # Build command for single file
        commands = [("push", {"src": file_to_push, "dest": "/tmp/"})]
        
        # Start background worker
        self._start_push_worker(commands, serial)
    
    def _start_push_worker(self, commands, serial):
        """Start ADB worker for push operation on background thread."""
        self.push_worker = AdbCommandWorker(commands, serial=serial)
        self.push_thread = QThread()
        
        self.push_worker.moveToThread(self.push_thread)
        
        self.push_thread.started.connect(self.push_worker.run)
        self.push_worker.log.connect(self.adb_comment_log.append)
        self.push_worker.progress.connect(lambda p: None)  # Progress handler
        self.push_worker.finished.connect(self._on_push_finished)
        self.push_worker.error.connect(lambda e: self.adb_comment_log.append(f"❌ {e}"))
        self.push_worker.finished.connect(self.push_thread.quit)
        self.push_worker.finished.connect(self.push_worker.deleteLater)
        self.push_thread.finished.connect(self.push_thread.deleteLater)
        
        self.push_thread.start()
        self.adb_comment_log.append("\n🚀 Đang push (background thread - UI không đơ)...")
    
    def _on_push_finished(self, success, message):
        """Handle push completion."""
        self.adb_comment_log.append(f"\n{'='*30}")
        if success:
            self.adb_comment_log.append(f"✅ PUSH HOÀN TẤT! {message}")
        else:
            self.adb_comment_log.append(f"⚠️ Push kết thúc: {message}")
        self.adb_comment_log.append(f"{'='*30}\n")
    
    def show_flash_file_dialog(self):
        """Show dialog to select and flash file."""
        if not self.adb_dropped_files:
            self.adb_comment_log.append("❌ Không có file nào để flash!")
            return
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("⚡ Flash ZIP/IMG")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        # File selection
        layout.addWidget(QLabel("Chọn file để flash:"))
        file_list = QTextEdit()
        file_list.setReadOnly(True)
        file_list.setMaximumHeight(150)
        
        for idx, file_path in enumerate(self.adb_dropped_files, 1):
            file_name = os.path.basename(file_path)
            file_list.append(f"{idx}. {file_name}")
        
        layout.addWidget(file_list)
        
        # File index input
        index_layout = QHBoxLayout()
        index_layout.addWidget(QLabel("Nhập số thứ tự file:"))
        index_input = QLineEdit()
        index_input.setPlaceholderText("1")
        index_layout.addWidget(index_input)
        layout.addLayout(index_layout)
        
        # Destination path
        dest_layout = QHBoxLayout()
        dest_layout.addWidget(QLabel("Đường dẫn đích:"))
        dest_input = QLineEdit()
        dest_input.setText("/tmp/")
        dest_layout.addWidget(dest_input)
        layout.addLayout(dest_layout)
        
        # Flash method
        layout.addWidget(QLabel("Phương thức flash:"))
        method_layout = QHBoxLayout()
        
        twrp_install_btn = PushButton("TWRP Install (twrp install)")
        twrp_install_btn.clicked.connect(lambda: self.execute_flash(
            index_input.text(), dest_input.text(), "twrp_install", dialog
        ))
        
        dd_flash_btn = PushButton("DD Flash (dd if=... of=...)")
        dd_flash_btn.clicked.connect(lambda: self.execute_flash(
            index_input.text(), dest_input.text(), "dd", dialog
        ))
        
        method_layout.addWidget(twrp_install_btn)
        method_layout.addWidget(dd_flash_btn)
        layout.addLayout(method_layout)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def execute_flash(self, index_text, dest_path, method, dialog):
        """Execute flash command using background worker (non-blocking UI)."""
        try:
            index = int(index_text.strip() or "1") - 1
            if index < 0 or index >= len(self.adb_dropped_files):
                self.adb_comment_log.append(f"❌ Số thứ tự không hợp lệ! (1-{len(self.adb_dropped_files)})")
                return
            
            file_path = self.adb_dropped_files[index]
            file_name = os.path.basename(file_path)
            
            dialog.accept()  # Close dialog
            
            # Check multi device mode
            if self.multi_device_btn.isChecked() and self.multi_device_serials:
                self.adb_comment_log.append(f"\n{'='*30}")
                self.adb_comment_log.append(f"⚡ MULTI DEVICE - Flash {file_name} cho {len(self.multi_device_serials)} thiết bị (max 4 parallel)")
                self.adb_comment_log.append(f"{'='*30}\n")
                
                if self.multi_device_worker and self.multi_device_worker.isRunning():
                    self.multi_device_worker.wait()
                
                self.multi_device_worker = MultiDeviceWorker(
                    "flash_file", 
                    self.multi_device_serials, 
                    file_path=file_path, 
                    dest_path=dest_path, 
                    method=method
                )
                self.multi_device_worker.log_signal.connect(self.adb_comment_log.append)
                self.multi_device_worker.finished_signal.connect(
                    lambda: self.adb_comment_log.append(f"\n{'='*30}\n✅ HOÀN TẤT! Đã flash\n{'='*30}\n")
                )
                self.multi_device_worker.start()
                return
            
            # Single device mode - use background worker
            serial = self.adb_serial_input.text().strip()
            
            # Validate serial
            if not serial:
                self.adb_comment_log.append("❌ Chưa nhập serial thiết bị!")
                return
            
            self.adb_comment_log.append(f"\n{'='*30}")
            self.adb_comment_log.append(f"⚡ Bắt đầu flash: {file_name}")
            self.adb_comment_log.append(f"📱 Serial: {serial}")
            self.adb_comment_log.append(f"{'='*30}")
            
            # Build command list for worker
            dest_file = dest_path.rstrip('/') + '/' + file_name
            
            if method == "twrp_install":
                commands = [
                    ("shell", {"cmd": "twrp set tw_ro_mode 0"}),  # Unlock TWRP
                    ("shell", {"cmd": "twrp format data"}),        # Format data (heavier than wipe)
                    ("push", {"src": file_path, "dest": dest_path}),  # Push file
                    ("shell", {"cmd": f"twrp install {dest_file}"})   # Flash ROM
                ]
                self.adb_comment_log.append("\n📋 Quy trình: Unlock → Format Data → Push → Flash")
            else:  # dd method
                self.adb_comment_log.append(f"\n⚠️ DD Flash cần chỉ định partition thủ công!")
                self.adb_comment_log.append(f"   Ví dụ: adb shell dd if={dest_file} of=/dev/block/...")
                return
            
            # Create and start worker
            self._start_flash_worker(commands, serial)
            
        except ValueError:
            self.adb_comment_log.append("❌ Số thứ tự không hợp lệ!")
        except Exception as e:
            self.adb_comment_log.append(f"❌ Lỗi: {e}")
    
    def _start_flash_worker(self, commands, serial):
        """Start ADB worker for flash operation on background thread."""
        # Create worker
        self.flash_worker = AdbCommandWorker(commands, serial=serial)
        self.flash_thread = QThread()
        
        # Move worker to thread
        self.flash_worker.moveToThread(self.flash_thread)
        
        # Connect signals
        self.flash_thread.started.connect(self.flash_worker.run)
        self.flash_worker.log.connect(self.adb_comment_log.append)
        self.flash_worker.progress.connect(self._on_flash_progress)
        self.flash_worker.finished.connect(self._on_flash_finished)
        self.flash_worker.error.connect(lambda e: self.adb_comment_log.append(f"❌ {e}"))
        self.flash_worker.finished.connect(self.flash_thread.quit)
        self.flash_worker.finished.connect(self.flash_worker.deleteLater)
        self.flash_thread.finished.connect(self.flash_thread.deleteLater)
        
        # Start worker thread
        self.flash_thread.start()
        self.adb_comment_log.append("\n🚀 Đang thực hiện (background thread)...")
    
    def _on_flash_progress(self, progress):
        """Handle flash progress update."""
        # Can update a progress bar here if needed
        pass
    
    def _on_flash_finished(self, success, message):
        """Handle flash completion."""
        self.adb_comment_log.append(f"\n{'='*30}")
        if success:
            self.adb_comment_log.append(f"✅ FLASH HOÀN TẤT! {message}")
        else:
            self.adb_comment_log.append(f"⚠️ Flash kết thúc: {message}")
        self.adb_comment_log.append(f"{'='*30}\n")
    
    def clear_dropped_files(self):
        """Clear the list of dropped files."""
        count = len(self.adb_dropped_files)
        self.adb_dropped_files.clear()
        self.adb_file_display.clear()
        self.adb_comment_log.append(f"🗑️ Đã xóa {count} file khỏi danh sách.")
    
    def set_file_permissions_644(self):
        """Set file permissions to 644 using WSL."""
        if not self.adb_dropped_files:
            self.adb_comment_log.append("❌ Không có file nào để set quyền!")
            return
        
        self.adb_comment_log.append(f"\n{'='*30}")
        self.adb_comment_log.append(f"🔒 Bắt đầu set quyền 644 cho {len(self.adb_dropped_files)} file...")
        self.adb_comment_log.append(f"{'='*30}\n")
        
        for idx, file_path in enumerate(self.adb_dropped_files, 1):
            file_name = os.path.basename(file_path)
            self.adb_comment_log.append(f"[{idx}/{len(self.adb_dropped_files)}] {file_name}")
            
            # Convert Windows path to WSL path
            wsl_path = file_path.replace('\\', '/').replace('C:', '/mnt/c')
            
            # Run chmod command via WSL
            cmd = f'wsl chmod 644 "{wsl_path}"'
            
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    self.adb_comment_log.append(f"   ✅ Đã set quyền 644")
                    
                    # Verify permissions
                    verify_cmd = f'wsl stat -c "%a" "{wsl_path}"'
                    verify_result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True, timeout=5)
                    if verify_result.returncode == 0:
                        perm = verify_result.stdout.strip()
                        self.adb_comment_log.append(f"   ℹ️ Quyền hiện tại: {perm}")
                else:
                    self.adb_comment_log.append(f"   ❌ Thất bại!")
                    if result.stderr:
                        self.adb_comment_log.append(f"   Error: {result.stderr.strip()}")
                        
            except subprocess.TimeoutExpired:
                self.adb_comment_log.append(f"   ❌ Timeout!")
            except Exception as e:
                self.adb_comment_log.append(f"   ❌ Lỗi: {e}")
            
            self.adb_comment_log.append("")
        
        self.adb_comment_log.append(f"{'='*30}")
        self.adb_comment_log.append("✅ Hoàn tất set quyền!")
        self.adb_comment_log.append(f"{'='*30}\n")
    
    def create_zip_package(self):
        """Create ZIP package using WSL zip command."""
        if not self.adb_dropped_files:
            self.adb_comment_log.append("❌ Không có file nào để đóng gói!")
            return
        
        # Check if it's a directory or files
        if len(self.adb_dropped_files) == 1 and os.path.isdir(self.adb_dropped_files[0]):
            # Single directory - zip its contents
            source_dir = self.adb_dropped_files[0]
            dir_name = os.path.basename(source_dir.rstrip('/\\'))
            parent_dir = os.path.dirname(source_dir)
            output_zip = os.path.join(parent_dir, f"{dir_name}_package.zip")
            
            self.adb_comment_log.append(f"\n{'='*30}")
            self.adb_comment_log.append(f"📦 Đóng gói thư mục: {dir_name}")
            self.adb_comment_log.append(f"{'='*30}\n")
            
            # Convert to WSL paths
            wsl_source = source_dir.replace('\\', '/').replace('C:', '/mnt/c')
            wsl_output = output_zip.replace('\\', '/').replace('C:', '/mnt/c')
            
            # Create ZIP with store mode (no compression)
            cmd = f'wsl bash -c "cd {wsl_source} && zip -r {wsl_output} * -0"'
            
        else:
            # Multiple files - create dialog to get output name
            output_name, ok = self._get_zip_output_name()
            if not ok or not output_name:
                self.adb_comment_log.append("❌ Đã hủy đóng gói.")
                return
            
            # Get first file's directory as output location
            first_file_dir = os.path.dirname(self.adb_dropped_files[0])
            output_zip = os.path.join(first_file_dir, output_name if output_name.endswith('.zip') else f"{output_name}.zip")
            
            self.adb_comment_log.append(f"\n{'='*30}")
            self.adb_comment_log.append(f"📦 Đóng gói {len(self.adb_dropped_files)} file...")
            self.adb_comment_log.append(f"{'='*30}\n")
            
            # Convert to WSL paths
            wsl_output = output_zip.replace('\\', '/').replace('C:', '/mnt/c')
            wsl_files = [f'"{f.replace(chr(92), "/").replace("C:", "/mnt/c")}"' for f in self.adb_dropped_files]
            
            # Create ZIP with store mode
            cmd = f'wsl zip {wsl_output} {" ".join(wsl_files)} -0'
        
        try:
            self.adb_comment_log.append("⏳ Đang tạo ZIP package...")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                output_size = os.path.getsize(output_zip) / (1024 * 1024)
                self.adb_comment_log.append(f"\n✅ Đã tạo ZIP thành công!")
                self.adb_comment_log.append(f"   📄 File: {os.path.basename(output_zip)}")
                self.adb_comment_log.append(f"   📊 Kích thước: {output_size:.2f} MB")
                self.adb_comment_log.append(f"   📁 Đường dẫn: {output_zip}")
                
                # Ask if user wants to add this ZIP to the list
                reply = QMessageBox.question(
                    self, "Thêm vào danh sách?",
                    f"Thêm {os.path.basename(output_zip)} vào danh sách file?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.adb_dropped_files.append(output_zip)
                    self.adb_file_display.setText(os.path.basename(output_zip))
                    self.adb_comment_log.append(f"   ✅ Đã thêm vào danh sách.")
                    
            else:
                self.adb_comment_log.append(f"\n❌ Tạo ZIP thất bại!")
                if result.stderr:
                    self.adb_comment_log.append(f"   Error: {result.stderr.strip()}")
                    
        except subprocess.TimeoutExpired:
            self.adb_comment_log.append("❌ Timeout: Đóng gói mất quá nhiều thời gian!")
        except Exception as e:
            self.adb_comment_log.append(f"❌ Lỗi: {e}")
        
        self.adb_comment_log.append(f"\n{'='*30}\n")
    
    def _get_zip_output_name(self):
        """Show dialog to get ZIP output name."""
        text, ok = QInputDialog.getText(
            self, "Tên file ZIP",
            "Nhập tên file ZIP output:",
            QLineEdit.EchoMode.Normal,
            "package.zip"
        )
        return text, ok
    
    def detect_adb_device(self):
        """Detect connected ADB devices and show selection dialog."""
        self.adb_comment_log.append("🔍 Đang phát hiện thiết bị...")
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
            output = result.stdout.strip()
            
            lines = output.split('\n')[1:]  # Skip header
            devices = [line.split()[0] for line in lines if 'device' in line and not line.startswith('*')]
            
            if not devices:
                self.adb_comment_log.append("❌ Không tìm thấy thiết bị nào!")
                QMessageBox.warning(self, "Không có thiết bị", "Không tìm thấy thiết bị ADB nào được kết nối!")
                return
            
            self.adb_comment_log.append(f"✅ Tìm thấy {len(devices)} thiết bị")
            
            # Show device selection dialog
            if len(devices) == 1:
                # Only one device, auto-select
                selected_device = devices[0]
                self.adb_serial_input.setText(selected_device)
                self.adb_comment_log.append(f"   📱 Đã chọn: {selected_device}")
            else:
                # Multiple devices, show selection dialog
                selected_device = self._show_device_selection_dialog(devices)
                if selected_device:
                    self.adb_serial_input.setText(selected_device)
                    self.adb_comment_log.append(f"   📱 Đã chọn: {selected_device}")
                else:
                    self.adb_comment_log.append("   ⚠️ Không chọn thiết bị nào")
                    
        except subprocess.TimeoutExpired:
            self.adb_comment_log.append("❌ Timeout: ADB không phản hồi!")
            QMessageBox.critical(self, "Lỗi", "ADB không phản hồi (timeout)!")
        except FileNotFoundError:
            self.adb_comment_log.append("❌ Lỗi: Không tìm thấy ADB. Đảm bảo ADB đã được cài đặt và thêm vào PATH!")
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy ADB!\n\nĐảm bảo ADB đã được cài đặt và thêm vào PATH.")
        except Exception as e:
            self.adb_comment_log.append(f"❌ Lỗi: {e}")
            QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định:\n{e}")
    
    def _show_device_selection_dialog(self, devices):
        """Show dialog to select device from list."""
        dialog = QDialog(self)
        dialog.setWindowTitle("📱 Chọn thiết bị ADB")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Info label
        info_label = QLabel(f"Tìm thấy {len(devices)} thiết bị. Chọn thiết bị để sử dụng:")
        layout.addWidget(info_label)
        
        # Device list
        device_list = QListWidget()
        device_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        
        for idx, device in enumerate(devices, 1):
            item = QListWidgetItem(f"{idx}. {device}")
            item.setData(Qt.ItemDataRole.UserRole, device)
            device_list.addItem(item)
        
        # Auto-select first item
        device_list.setCurrentRow(0)
        
        # Double-click to select
        device_list.itemDoubleClicked.connect(lambda: dialog.accept())
        
        layout.addWidget(device_list)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            current_item = device_list.currentItem()
            if current_item:
                return current_item.data(Qt.ItemDataRole.UserRole)
        
        return None
    
    def on_serial_changed(self, text):
        """Auto-save serial when user changes it."""
        if text.strip():
            self.config.set("adb_device_serial", text.strip())
            import logging
            logging.info(f"💾 Đã lưu serial: {text.strip()}")
    
    def toggle_multi_device(self):
        """Toggle multi device mode and show configuration dialog."""
        if self.multi_device_btn.isChecked():
            # Show dialog to input multiple device serials
            dialog = QDialog(self)
            dialog.setWindowTitle("📱 Cấu hình Multi Device")
            dialog.setMinimumWidth(500)
            dialog.setMinimumHeight(400)
            
            layout = QVBoxLayout(dialog)
            
            # Info label
            info_label = QLabel("📝 Nhập Serial của các thiết bị (mỗi dòng một serial):")
            info_label.setStyleSheet("font-weight: bold; padding: 8px;")
            layout.addWidget(info_label)
            
            # Text edit for serials
            serials_input = QTextEdit()
            serials_input.setPlaceholderText("Ví dụ:\n28b85ba51b1c7ece\nR58M419FFEJ\nemulator-5554\n...")
            serials_input.setFont(QFont('Consolas', 10))
            
            # Load saved serials from config or current list
            saved_serials = self.config.get("multi_device_serials", "")
            if saved_serials:
                serials_input.setPlainText(saved_serials)
            elif self.multi_device_serials:
                serials_input.setPlainText("\n".join(self.multi_device_serials))
            
            layout.addWidget(serials_input)
            
            # Info about current devices
            info_text = QLabel("💡 Tip: Sử dụng lệnh 'adb devices' để xem danh sách thiết bị kết nối")
            info_text.setStyleSheet("color: #888; font-size: 9pt; padding: 5px;")
            layout.addWidget(info_text)
            
            # Buttons
            button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            # Show dialog
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Parse serials
                serials_text = serials_input.toPlainText().strip()
                if serials_text:
                    self.multi_device_serials = [s.strip() for s in serials_text.split('\n') if s.strip()]
                    
                    if self.multi_device_serials:
                        # Save to config
                        self.config.set("multi_device_serials", serials_text)
                        
                        self.adb_comment_log.append(f"\n{'='*30}")
                        self.adb_comment_log.append(f"📱 Đã kích hoạt Multi Device mode")
                        self.adb_comment_log.append(f"📊 Số thiết bị: {len(self.multi_device_serials)}")
                        for idx, serial in enumerate(self.multi_device_serials, 1):
                            self.adb_comment_log.append(f"   {idx}. {serial}")
                        self.adb_comment_log.append(f"{'='*30}\n")
                    else:
                        self.adb_comment_log.append("⚠️ Danh sách serial trống! Tắt Multi Device mode.")
                        self.multi_device_btn.setChecked(False)
                else:
                    self.adb_comment_log.append("⚠️ Chưa nhập serial! Tắt Multi Device mode.")
                    self.multi_device_btn.setChecked(False)
            else:
                # User cancelled
                self.multi_device_btn.setChecked(False)
        else:
            # Toggle OFF
            self.adb_comment_log.append(f"\n{'='*30}")
            self.adb_comment_log.append("📱 Đã tắt Multi Device mode")
            self.adb_comment_log.append("💡 Chuyển về chế độ single device")
            self.adb_comment_log.append(f"{'='*30}\n")
    
    def show_mode_menu(self):
        """Show mode menu with device status check and boot options."""
        # Check if multi device mode is enabled
        if self.multi_device_btn.isChecked() and self.multi_device_serials:
            # Multi device mode - check all devices
            self.adb_comment_log.append(f"\n{'='*30}")
            self.adb_comment_log.append(f"🔍 MULTI DEVICE - Kiểm tra trạng thái {len(self.multi_device_serials)} thiết bị")
            self.adb_comment_log.append(f"{'='*30}\n")
            
            for idx, serial in enumerate(self.multi_device_serials, 1):
                self.adb_comment_log.append(f"\n[{idx}/{len(self.multi_device_serials)}] 📱 {serial}")
                mode, details = self.detect_current_device_mode(serial)
                
                # Log the result
                if mode == "twrp":
                    self.adb_comment_log.append(f"   ✅ TWRP - {details}")
                elif mode == "recovery":
                    self.adb_comment_log.append(f"   ✅ Recovery - {details}")
                elif mode == "system":
                    self.adb_comment_log.append(f"   ✅ System - {details}")
                elif mode == "fastboot":
                    self.adb_comment_log.append(f"   ✅ Fastboot - {details}")
                else:
                    self.adb_comment_log.append(f"   ⚠️ {details}")
            
            self.adb_comment_log.append(f"\n{'='*30}\n")
        else:
            # Single device mode
            serial = self.adb_serial_input.text().strip()
            
            # First, check current device mode
            self.adb_comment_log.append(f"\n{'='*30}")
            self.adb_comment_log.append("🔍 Đang kiểm tra trạng thái thiết bị...")
            if serial:
                self.adb_comment_log.append(f"📱 Serial: {serial}")
            self.adb_comment_log.append(f"{'='*30}\n")
            
            # Detect current mode
            mode, details = self.detect_current_device_mode(serial)
            
            # Log the result
            if mode == "twrp":
                self.adb_comment_log.append(f"✅ Trạng thái hiện tại: TWRP")
                self.adb_comment_log.append(f"   ℹ️ {details}")
            elif mode == "recovery":
                self.adb_comment_log.append(f"✅ Trạng thái hiện tại: Recovery Mode")
                self.adb_comment_log.append(f"   ℹ️ {details}")
            elif mode == "system":
                self.adb_comment_log.append(f"✅ Trạng thái hiện tại: Android System")
                self.adb_comment_log.append(f"   ℹ️ {details}")
            elif mode == "fastboot":
                self.adb_comment_log.append(f"✅ Trạng thái hiện tại: Fastboot/Bootloader")
                self.adb_comment_log.append(f"   ℹ️ {details}")
            else:
                self.adb_comment_log.append(f"⚠️ Trạng thái: {details}")
            
            self.adb_comment_log.append(f"\n{'='*30}\n")
        
        # Create menu
        menu = QMenu(self)
        
        # TWRP option
        twrp_action = QAction("🔧 Khởi động vào TWRP", self)
        twrp_action.triggered.connect(self.reboot_to_twrp_wrapper)
        menu.addAction(twrp_action)
        
        # Bootloader option
        bootloader_action = QAction("⚡ Khởi động vào Bootloader/Download", self)
        bootloader_action.triggered.connect(self.reboot_to_bootloader_wrapper)
        menu.addAction(bootloader_action)
        
        # Reboot System option
        reboot_system_action = QAction("🔄 Reboot System", self)
        reboot_system_action.triggered.connect(self.reboot_to_system_wrapper)
        menu.addAction(reboot_system_action)
        
        menu.addSeparator()
        
        # Refresh status
        refresh_action = QAction("🔄 Làm mới trạng thái", self)
        refresh_action.triggered.connect(self.show_mode_menu)
        menu.addAction(refresh_action)
        
        # Show menu at button position
        menu.exec(self.mode_btn.mapToGlobal(self.mode_btn.rect().bottomLeft()))
    
    def detect_current_device_mode(self, serial):
        """Detect current device mode."""
        serial_arg = f"-s {serial}" if serial else ""
        
        # 1. Check TWRP
        try:
            result = subprocess.run(
                f"adb {serial_arg} shell getprop ro.twrp.version",
                shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                twrp_version = result.stdout.strip()
                return "twrp", f"TWRP {twrp_version}"
        except:
            pass
        
        # 2. Check if in recovery (but not TWRP)
        try:
            result = subprocess.run(
                f"adb {serial_arg} shell getprop ro.bootmode",
                shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                bootmode = result.stdout.strip()
                if "recovery" in bootmode.lower():
                    return "recovery", f"Recovery mode ({bootmode})"
        except:
            pass
        
        # 3. Check if in Android system
        try:
            result = subprocess.run(
                f"adb {serial_arg} shell getprop ro.build.version.release",
                shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                android_version = result.stdout.strip()
                return "system", f"Android {android_version}"
        except:
            pass
        
        # 4. Check fastboot/bootloader
        try:
            result = subprocess.run(
                "fastboot devices",
                shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return "fastboot", "Fastboot/Bootloader mode"
        except:
            pass
        
        # 5. Device not found
        return "offline", "Không phát hiện thiết bị"
    
    def reboot_to_twrp_wrapper(self):
        """Wrapper for reboot_to_twrp to support multi-device mode."""
        if self.multi_device_btn.isChecked() and self.multi_device_serials:
            # Multi device mode - run in worker thread
            self.adb_comment_log.append(f"\n{'='*30}")
            self.adb_comment_log.append(f"🔧 MULTI DEVICE - Khởi động {len(self.multi_device_serials)} thiết bị vào TWRP (max 4 parallel)")
            self.adb_comment_log.append(f"{'='*30}\n")
            
            # Stop previous worker if running
            if self.multi_device_worker and self.multi_device_worker.isRunning():
                self.multi_device_worker.wait()
            
            # Create and start worker
            self.multi_device_worker = MultiDeviceWorker("reboot_twrp", self.multi_device_serials)
            self.multi_device_worker.log_signal.connect(self.adb_comment_log.append)
            self.multi_device_worker.finished_signal.connect(
                lambda: self.adb_comment_log.append(f"\n{'='*30}\n✅ HOÀN TẤT! Đã gửi lệnh reboot TWRP\n{'='*30}\n")
            )
            self.multi_device_worker.start()
        else:
            # Single device mode
            serial = self.adb_serial_input.text().strip()
            self.reboot_to_twrp(serial)
    
    def reboot_to_bootloader_wrapper(self):
        """Wrapper for reboot_to_bootloader to support multi-device mode."""
        if self.multi_device_btn.isChecked() and self.multi_device_serials:
            self.adb_comment_log.append(f"\n{'='*30}")
            self.adb_comment_log.append(f"⚡ MULTI DEVICE - Khởi động {len(self.multi_device_serials)} thiết bị vào Bootloader (max 4 parallel)")
            self.adb_comment_log.append(f"{'='*30}\n")
            
            if self.multi_device_worker and self.multi_device_worker.isRunning():
                self.multi_device_worker.wait()
            
            self.multi_device_worker = MultiDeviceWorker("reboot_bootloader", self.multi_device_serials)
            self.multi_device_worker.log_signal.connect(self.adb_comment_log.append)
            self.multi_device_worker.finished_signal.connect(
                lambda: self.adb_comment_log.append(f"\n{'='*30}\n✅ HOÀN TẤT! Đã reboot bootloader\n{'='*30}\n")
            )
            self.multi_device_worker.start()
        else:
            serial = self.adb_serial_input.text().strip()
            self.reboot_to_bootloader(serial)
    
    def reboot_to_system_wrapper(self):
        """Wrapper for reboot_to_system to support multi-device mode."""
        if self.multi_device_btn.isChecked() and self.multi_device_serials:
            self.adb_comment_log.append(f"\n{'='*30}")
            self.adb_comment_log.append(f"🔄 MULTI DEVICE - Reboot {len(self.multi_device_serials)} thiết bị vào System (max 4 parallel)")
            self.adb_comment_log.append(f"{'='*30}\n")
            
            if self.multi_device_worker and self.multi_device_worker.isRunning():
                self.multi_device_worker.wait()
            
            self.multi_device_worker = MultiDeviceWorker("reboot_system", self.multi_device_serials)
            self.multi_device_worker.log_signal.connect(self.adb_comment_log.append)
            self.multi_device_worker.finished_signal.connect(
                lambda: self.adb_comment_log.append(f"\n{'='*30}\n✅ HOÀN TẤT! Đã reboot system\n{'='*30}\n")
            )
            self.multi_device_worker.start()
        else:
            serial = self.adb_serial_input.text().strip()
            self.reboot_to_system(serial)
    
    def reboot_to_twrp(self, serial):
        """Reboot to TWRP, wait, and unlock."""
        self.adb_comment_log.append(f"\n{'='*30}")
        self.adb_comment_log.append("🔧 Bắt đầu khởi động vào TWRP...")
        if serial:
            self.adb_comment_log.append(f"📱 Serial: {serial}")
        self.adb_comment_log.append(f"{'='*30}\n")
        
        # Reboot to recovery
        serial_arg = f"-s {serial}" if serial else ""
        cmd = f"adb {serial_arg} reboot recovery"
        
        self.adb_comment_log.append(f"$ {cmd}")
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.adb_comment_log.append("✅ Đã gửi lệnh reboot recovery")
                self.adb_comment_log.append("⏳ Đang đợi thiết bị vào TWRP (timeout 30s)...")
                
                # Start checker thread: wait 5s then check every 2s, timeout 30s
                self.device_mode_checker_thread = DeviceModeCheckerThread(
                    serial, 
                    initial_delay=5, 
                    check_interval=2, 
                    timeout=30
                )
                self.device_mode_checker_thread.mode_detected.connect(self.on_twrp_mode_detected)
                self.device_mode_checker_thread.start()
            else:
                self.adb_comment_log.append(f"❌ Thất bại! Exit code: {result.returncode}")
                if result.stderr:
                    self.adb_comment_log.append(f"   Error: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            self.adb_comment_log.append("❌ Timeout: Lệnh reboot chạy quá lâu!")
        except Exception as e:
            self.adb_comment_log.append(f"❌ Lỗi: {e}")
    
    def on_twrp_mode_detected(self, mode, details):
        """Handle TWRP mode detection after reboot."""
        if mode == "timeout":
            # Timeout - device not in TWRP
            self.adb_comment_log.append(f"\n⚠️ {details}")
            self.adb_comment_log.append(f"{'='*30}\n")
            return
        
        # TWRP detected
        self.adb_comment_log.append(f"\n✅ {details}")
        
        if mode == "twrp":
            # Auto unlock TWRP
            self.adb_comment_log.append("\n🔓 Tự động unlock TWRP...")
            serial = self.adb_serial_input.text().strip()
            serial_arg = f"-s {serial}" if serial else ""
            
            # Method 1: Disable read-only mode
            cmd = f"adb {serial_arg} shell twrp set tw_ro_mode 0"
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.adb_comment_log.append("   ✅ Đã unlock TWRP (bypass swipe)")
                else:
                    # Try Method 2: Simulate swipe
                    cmd2 = f"adb {serial_arg} shell input swipe 100 1000 900 1000 100"
                    result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True, timeout=5)
                    if result2.returncode == 0:
                        self.adb_comment_log.append("   ✅ Đã simulate swipe gesture")
                    else:
                        self.adb_comment_log.append("   ⚠️ Unlock thất bại, thử thủ công")
            except Exception as e:
                self.adb_comment_log.append(f"   ⚠️ Lỗi unlock: {e}")
            
            self.adb_comment_log.append(f"\n{'='*30}")
            self.adb_comment_log.append("✅ Hoàn tất! Thiết bị đã sẵn sàng.")
            self.adb_comment_log.append(f"{'='*30}\n")
        else:
            self.adb_comment_log.append(f"\n⚠️ Thiết bị không ở chế độ TWRP!")
            self.adb_comment_log.append(f"{'='*30}\n")
    
    def reboot_to_bootloader(self, serial):
        """Reboot to bootloader/download mode."""
        self.adb_comment_log.append(f"\n{'='*30}")
        self.adb_comment_log.append("⚡ Bắt đầu khởi động vào Bootloader...")
        if serial:
            self.adb_comment_log.append(f"📱 Serial: {serial}")
        self.adb_comment_log.append(f"{'='*30}\n")
        
        serial_arg = f"-s {serial}" if serial else ""
        cmd = f"adb {serial_arg} reboot bootloader"
        
        self.adb_comment_log.append(f"$ {cmd}")
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.adb_comment_log.append("✅ Đã gửi lệnh reboot bootloader")
                self.adb_comment_log.append("\n💡 Tip: Với Samsung, thiết bị sẽ vào Download mode")
                self.adb_comment_log.append("   Sử dụng Odin để flash hoặc 'fastboot' để tương tác")
                self.adb_comment_log.append(f"\n{'='*30}\n")
            else:
                self.adb_comment_log.append(f"❌ Thất bại! Exit code: {result.returncode}")
                if result.stderr:
                    self.adb_comment_log.append(f"   Error: {result.stderr.strip()}")
                self.adb_comment_log.append(f"{'='*30}\n")
        except subprocess.TimeoutExpired:
            self.adb_comment_log.append("❌ Timeout: Lệnh reboot chạy quá lâu!")
            self.adb_comment_log.append(f"{'='*30}\n")
        except Exception as e:
            self.adb_comment_log.append(f"❌ Lỗi: {e}")
            self.adb_comment_log.append(f"{'='*30}\n")
    
    def reboot_to_system(self, serial):
        """Reboot to Android system."""
        self.adb_comment_log.append(f"\n{'='*30}")
        self.adb_comment_log.append("🔄 Bắt đầu khởi động vào System...")
        if serial:
            self.adb_comment_log.append(f"📱 Serial: {serial}")
        self.adb_comment_log.append(f"{'='*30}\n")
        
        serial_arg = f"-s {serial}" if serial else ""
        cmd = f"adb {serial_arg} reboot"
        
        self.adb_comment_log.append(f"$ {cmd}")
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.adb_comment_log.append("✅ Đã gửi lệnh reboot system")
                self.adb_comment_log.append("💡 Thiết bị sẽ khởi động vào hệ thống Android")
                self.adb_comment_log.append(f"\n{'='*30}\n")
            else:
                self.adb_comment_log.append(f"❌ Thất bại! Exit code: {result.returncode}")
                if result.stderr:
                    self.adb_comment_log.append(f"   Error: {result.stderr.strip()}")
                self.adb_comment_log.append(f"{'='*30}\n")
        except subprocess.TimeoutExpired:
            self.adb_comment_log.append("❌ Timeout: Lệnh reboot chạy quá lâu!")
            self.adb_comment_log.append(f"{'='*30}\n")
        except Exception as e:
            self.adb_comment_log.append(f"❌ Lỗi: {e}")
            self.adb_comment_log.append(f"{'='*30}\n")

    def insert_quick_command(self, command):
        """Insert a quick command into the command input."""
        current_text = self.adb_command_input.toPlainText()
        if current_text and not current_text.endswith('\n'):
            current_text += '\n'
        self.adb_command_input.setPlainText(current_text + command)

    def execute_adb_commands(self):
        """Execute ADB commands from the input field."""
        commands_text = self.adb_command_input.toPlainText().strip()
        
        if not commands_text:
            self.adb_comment_log.append("❌ Chưa nhập lệnh!")
            return
        
        commands = [cmd.strip() for cmd in commands_text.split('\n') if cmd.strip()]
        
        # Check if multi device mode is enabled
        if self.multi_device_btn.isChecked() and self.multi_device_serials:
            # Multi device mode
            self.adb_comment_log.append(f"\n{'='*30}")
            self.adb_comment_log.append(f"▶️ MULTI DEVICE MODE - Thực thi trên {len(self.multi_device_serials)} thiết bị")
            self.adb_comment_log.append(f"📋 Lệnh: {len(commands)}")
            self.adb_comment_log.append(f"{'='*30}\n")
            
            for device_idx, serial in enumerate(self.multi_device_serials, 1):
                self.adb_comment_log.append(f"\n╔═══ DEVICE {device_idx}/{len(self.multi_device_serials)}: {serial} ═══╗\n")
                self._execute_commands_for_device(serial, commands)
            
            self.adb_comment_log.append(f"\n{'='*30}")
            self.adb_comment_log.append(f"✅ HOÀN TẤT MULTI DEVICE!")
            self.adb_comment_log.append(f"📊 Đã thực thi trên {len(self.multi_device_serials)} thiết bị")
            self.adb_comment_log.append(f"{'='*30}\n")
        else:
            # Single device mode
            serial = self.adb_serial_input.text().strip()
            self.adb_comment_log.append(f"\n{'='*30}")
            self.adb_comment_log.append(f"▶️ Bắt đầu thực thi {len(commands)} lệnh...")
            if serial:
                self.adb_comment_log.append(f"📱 Serial: {serial}")
            self.adb_comment_log.append(f"{'='*30}\n")
            
            reboot_recovery_executed = self._execute_commands_for_device(serial, commands)
            
            self.adb_comment_log.append(f"{'='*30}")
            self.adb_comment_log.append(f"✅ Hoàn tất thực thi {len(commands)} lệnh!")
            self.adb_comment_log.append(f"{'='*30}\n")
            
            # If reboot recovery was executed, start device mode checker
            if reboot_recovery_executed:
                self.start_device_mode_checker(serial)
        
        # Clear input field after execution
        self.adb_command_input.clear()
    
    def _execute_commands_for_device(self, serial, commands):
        """Execute commands for a specific device. Returns True if reboot recovery was executed."""
        reboot_recovery_executed = False
        
        for idx, cmd in enumerate(commands, 1):
            self.adb_comment_log.append(f"[{idx}/{len(commands)}] $ {cmd}")
            
            # Check if this is a reboot recovery command
            if "reboot" in cmd.lower() and "recovery" in cmd.lower():
                reboot_recovery_executed = True
            
            # Build full command
            if serial and not cmd.startswith('adb '):
                full_cmd = f"adb -s {serial} {cmd}"
            elif serial and cmd.startswith('adb '):
                full_cmd = cmd.replace('adb ', f'adb -s {serial} ', 1)
            else:
                full_cmd = cmd if cmd.startswith('adb ') else f"adb {cmd}"
            
            try:
                result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=30)
                
                if result.stdout and result.stdout.strip():
                    self.adb_comment_log.append(f"📤 Output:\n{result.stdout.strip()}")
                elif result.returncode == 0 and not result.stdout.strip():
                    self.adb_comment_log.append(f"📤 Output: (trống - property không tồn tại hoặc chưa set)")
                
                if result.stderr:
                    self.adb_comment_log.append(f"⚠️ Error:\n{result.stderr.strip()}")
                
                if result.returncode != 0:
                    self.adb_comment_log.append(f"❌ Exit code: {result.returncode}")
                else:
                    self.adb_comment_log.append("✅ Thành công!")
                    
            except subprocess.TimeoutExpired:
                self.adb_comment_log.append("❌ Timeout: Lệnh chạy quá lâu!")
            except Exception as e:
                self.adb_comment_log.append(f"❌ Lỗi: {e}")
            
            self.adb_comment_log.append("")  # Blank line between commands
        
        return reboot_recovery_executed
    
    def start_device_mode_checker(self, serial):
        """Start device mode checker thread after reboot recovery."""
        # Stop previous checker if running
        if self.device_mode_checker_thread and self.device_mode_checker_thread.isRunning():
            self.device_mode_checker_thread.stop()
            self.device_mode_checker_thread.wait()
        
        # Start new checker
        self.adb_comment_log.append("\n🔍 Bắt đầu kiểm tra chế độ thiết bị sau 10 giây...")
        self.device_mode_checker_thread = DeviceModeCheckerThread(serial, delay_seconds=10)
        self.device_mode_checker_thread.mode_detected.connect(self.handle_mode_detected)
        self.device_mode_checker_thread.start()
    
    def handle_mode_detected(self, mode, details):
        """Handle device mode detection result."""
        if mode == "waiting":
            self.adb_comment_log.append(f"⏳ {details}")
            return
        
        self.adb_comment_log.append(f"\n{'='*30}")
        self.adb_comment_log.append("📊 KẾT QUẢ KIỂM TRA CHẾ ĐỘ THIẾT BỊ")
        self.adb_comment_log.append(f"{'='*30}")
        
        if mode == "twrp":
            self.adb_comment_log.append(f"✅ Thiết bị đã vào chế độ TWRP!")
            self.adb_comment_log.append(f"📱 Chi tiết: {details}")
        elif mode == "recovery":
            self.adb_comment_log.append(f"✅ Thiết bị đã vào chế độ Recovery!")
            self.adb_comment_log.append(f"📱 Chi tiết: {details}")
            self.adb_comment_log.append(f"⚠️ Lưu ý: Không phải TWRP")
        elif mode == "system":
            self.adb_comment_log.append(f"📱 Thiết bị đang ở chế độ System")
            self.adb_comment_log.append(f"📱 Chi tiết: {details}")
            self.adb_comment_log.append(f"⚠️ Chưa vào Recovery")
        elif mode == "fastboot":
            self.adb_comment_log.append(f"⚡ Thiết bị đang ở chế độ Fastboot/Bootloader")
            self.adb_comment_log.append(f"📱 Chi tiết: {details}")
        elif mode == "unknown":
            self.adb_comment_log.append(f"❓ Thiết bị đang kết nối nhưng không xác định được chế độ")
            self.adb_comment_log.append(f"📱 Chi tiết: {details}")
        else:  # offline
            self.adb_comment_log.append(f"❌ Chưa phát hiện thiết bị trong TWRP/Recovery")
            self.adb_comment_log.append(f"📱 Chi tiết: {details}")
            self.adb_comment_log.append(f"💡 Tip: Kiểm tra lại kết nối hoặc đợi thêm vài giây")
        
        self.adb_comment_log.append(f"{'='*30}\n")

    def center_window(self):
        qr = self.frameGeometry()
        if self.screen():
            cp = self.screen().availableGeometry().center(); qr.moveCenter(cp); self.move(qr.topLeft())
    
    # ==========================================================================
    # UI STATE MANAGEMENT - Prevent "Not Responding" during heavy I/O
    # ==========================================================================
    def _beginBusy(self):
        """
        Disable các nút quan trọng khi worker đang chạy
        Tránh user click nhiều lần gây conflict
        """
        # Disable các nút chọn file
        if hasattr(self, 'smart_choose_btn'):
            self.smart_choose_btn.setEnabled(False)
        if hasattr(self, 'smart_patch_btn'):
            self.smart_patch_btn.setEnabled(False)
        
        # Disable GPS tab buttons
        if hasattr(self, 'gps_choose_file_btn'):
            self.gps_choose_file_btn.setEnabled(False)
        if hasattr(self, 'gps_patch_btn'):
            self.gps_patch_btn.setEnabled(False)
        
        # Disable ADB tab buttons
        if hasattr(self, 'adb_choose_file_btn'):
            self.adb_choose_file_btn.setEnabled(False)
        if hasattr(self, 'adb_patch_btn'):
            self.adb_patch_btn.setEnabled(False)
        
        # Disable decompile buttons
        if hasattr(self, 'decompile_choose_btn'):
            self.decompile_choose_btn.setEnabled(False)
        if hasattr(self, 'decompile_btn'):
            self.decompile_btn.setEnabled(False)
        if hasattr(self, 'recompile_choose_btn'):
            self.recompile_choose_btn.setEnabled(False)
        if hasattr(self, 'recompile_btn'):
            self.recompile_btn.setEnabled(False)
        
        # Show cursor as busy
        from PySide6.QtGui import QCursor
        from PySide6.QtCore import Qt
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        
        # Log status
        import logging
        logging.info("🔒 UI Locked - Worker running")
    
    def _endBusy(self):
        """
        Re-enable các nút sau khi worker hoàn thành
        """
        # Re-enable các nút chọn file
        if hasattr(self, 'smart_choose_btn'):
            self.smart_choose_btn.setEnabled(True)
        
        # Re-enable smart patch button (check if files detected)
        if hasattr(self, 'smart_patch_btn') and hasattr(self, 'smart_detected_files'):
            if self.smart_detected_files:
                self.smart_patch_btn.setEnabled(True)
        
        # Re-enable GPS tab buttons (check if file selected)
        if hasattr(self, 'gps_choose_file_btn'):
            self.gps_choose_file_btn.setEnabled(True)
        if hasattr(self, 'gps_file_path_edit') and self.gps_file_path_edit.text():
            if hasattr(self, 'gps_patch_btn'):
                self.gps_patch_btn.setEnabled(True)
        
        # Re-enable ADB tab buttons (check if file selected)
        if hasattr(self, 'adb_choose_file_btn'):
            self.adb_choose_file_btn.setEnabled(True)
        if hasattr(self, 'adb_file_path_edit') and self.adb_file_path_edit.text():
            if hasattr(self, 'adb_patch_btn'):
                self.adb_patch_btn.setEnabled(True)
        
        # Re-enable decompile buttons
        if hasattr(self, 'decompile_choose_btn'):
            self.decompile_choose_btn.setEnabled(True)
        if hasattr(self, 'decompile_input_path') and self.decompile_input_path.text():
            if hasattr(self, 'decompile_btn'):
                self.decompile_btn.setEnabled(True)
        
        if hasattr(self, 'recompile_choose_btn'):
            self.recompile_choose_btn.setEnabled(True)
        if hasattr(self, 'recompile_input_path') and self.recompile_input_path.text():
            if hasattr(self, 'recompile_btn'):
                self.recompile_btn.setEnabled(True)
        
        # Restore cursor
        QApplication.restoreOverrideCursor()
        
        # Log status
        import logging
        logging.info("🔓 UI Unlocked - Worker finished")
    
    def _import_large_file(self, src_path: str, dst_dir: str, unzip: bool = False):
        """
        Import file lớn với worker để tránh block UI
        
        Args:
            src_path: Đường dẫn file nguồn
            dst_dir: Thư mục đích
            unzip: True nếu cần giải nén sau khi copy
        """
        # Import worker
        from worker_file_import import FileImportWorker
        
        # Create thread and worker
        self._file_import_thread = QThread(self)
        self._file_import_worker = FileImportWorker(src_path, dst_dir, unzip=unzip, chunk_mb=16)
        self._file_import_worker.moveToThread(self._file_import_thread)
        
        # Connect signals
        self._file_import_thread.started.connect(self._file_import_worker.run)
        
        # Progress signal
        if hasattr(self, 'smart_progress_bar'):
            self._file_import_worker.progress.connect(
                self.smart_progress_bar.setValue,
                Qt.ConnectionType.QueuedConnection
            )
        
        # Log signal
        self._file_import_worker.log.connect(self.append)
        
        # Finished signal
        self._file_import_worker.finished.connect(
            lambda p: self._on_file_import_finished(p)
        )
        
        # Error signal
        self._file_import_worker.error.connect(
            lambda e: self._on_file_import_error(e)
        )
        
        # Cancelled signal
        self._file_import_worker.cancelled.connect(
            lambda: self._on_file_import_cancelled()
        )
        
        # Cleanup
        self._file_import_thread.finished.connect(self._file_import_thread.deleteLater)
        
        # Lock UI and start
        self._beginBusy()
        self._file_import_thread.start()
    
    def _on_file_import_finished(self, dst_path: str):
        """Callback khi import file hoàn thành"""
        self._file_import_thread.quit()
        self._file_import_thread.wait()
        self._endBusy()
        self.append(f"✔ Hoàn thành: {dst_path}")
    
    def _on_file_import_error(self, error_msg: str):
        """Callback khi import file lỗi"""
        self._file_import_thread.quit()
        self._file_import_thread.wait()
        self._endBusy()
        self.append(f"✖ Lỗi: {error_msg}")
    
    def _on_file_import_cancelled(self):
        """Callback khi import file bị hủy"""
        self._file_import_thread.quit()
        self._file_import_thread.wait()
        self._endBusy()
        self.append("⛔ Đã hủy import file")

    # --- Logic cho Tab GPS ---
    def select_gps_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file services.jar", "", "Java Archives (*.jar)")
        if file_path: self.set_input_file(file_path, 'gps')
    
    def start_gps_patch(self, overwrite=None):
        if not self.gps_file_path_edit.text(): return
        
        # 🔍 DEBUG: Start GPS patch
        self.append("🔍 [UI] Starting GPS patch...")
        
        self.gps_progress_bar.setValue(0)
        self.gps_log_output.clear()
        
        # Check overwrite checkbox if not explicitly provided
        if overwrite is None:
            overwrite = self.smart_overwrite_checkbox.isChecked() if hasattr(self, 'smart_overwrite_checkbox') else False
        
        # Lock UI BEFORE starting thread
        self._beginBusy()
        
        self.gps_patcher_thread = GpsPatcherThread(self.gps_file_path_edit.text(), self.patched_dir, overwrite_original=overwrite)
        self.gps_patcher_thread.log_message.connect(self.gps_log_output.append)
        self.gps_patcher_thread.progress_update.connect(self.gps_progress_bar.setValue)
        self.gps_patcher_thread.patch_finished.connect(self.on_gps_patch_finished)
        self.gps_patcher_thread.cancelled.connect(self.on_gps_patch_cancelled)
        self.gps_patcher_thread.start()

    def on_gps_patch_finished(self, success, message):
        # Unlock UI
        self._endBusy()
        
        log_method = self.gps_log_output.append
        if success:
            log_method(message)
            self.append("🔍 [UI] GPS patch completed successfully")
        else:
            log_method(f"❌ THẤT BẠI: {message}")
            self.append("🔍 [UI] GPS patch failed")
    
    def on_gps_patch_cancelled(self):
        """Callback khi GPS patch bị cancel"""
        self._endBusy()
        self.gps_log_output.append("⛔ Đã hủy GPS patch")
        self.append("🔍 [UI] GPS patch cancelled")

    # --- Logic cho Tab ADB ---
    def select_adb_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Chọn build.prop và/hoặc init.rc", "", "All Files (*)")
        if file_paths: self.set_input_file(file_paths, 'adb')

    def start_adb_patch(self):
        build_prop = self.adb_files.get('build.prop')
        init_rc = self.adb_files.get('init.rc')
        if not build_prop and not init_rc: return
        
        # 🔍 DEBUG: Start ADB patch
        self.append("🔍 [UI] Starting ADB patch...")
        
        self.adb_log_output.clear()
        
        # Lock UI BEFORE starting thread
        self._beginBusy()
        
        self.adb_patcher_thread = AdbPatcherThread(build_prop, init_rc)
        self.adb_patcher_thread.log_message.connect(self.adb_log_output.append)
        self.adb_patcher_thread.patch_finished.connect(self.on_adb_patch_finished)
        self.adb_patcher_thread.cancelled.connect(self.on_adb_patch_cancelled)
        self.adb_patcher_thread.start()

    # THAY ĐỔI: Tự động lưu sau khi vá
    def on_adb_patch_finished(self, success, modified_contents):
        # Unlock UI
        self._endBusy()
        
        if success and modified_contents:
            self.adb_log_output.append("\n✅ Phân tích và chỉnh sửa hoàn tất. Tự động lưu...")
            self.modified_adb_files = modified_contents
            self.save_adb_files_auto()
            self.append("🔍 [UI] ADB patch completed successfully")
        else:
            self.adb_log_output.append("\n❌ THẤT BẠI: Quá trình chỉnh sửa gặp lỗi.")
            self.append("🔍 [UI] ADB patch failed")
    
    def on_adb_patch_cancelled(self):
        """Callback khi ADB patch bị cancel"""
        self._endBusy()
        self.adb_log_output.append("⛔ Đã hủy ADB patch")
        self.append("🔍 [UI] ADB patch cancelled")

    # THAY ĐỔI: Hàm lưu tự động, không cần chọn thư mục
    def save_adb_files_auto(self):
        if not self.modified_adb_files: return
        
        # Check overwrite checkbox
        overwrite = self.smart_overwrite_checkbox.isChecked() if hasattr(self, 'smart_overwrite_checkbox') else False
        
        try:
            for filename, content in self.modified_adb_files.items():
                if overwrite:
                    # Overwrite original file
                    if filename == 'build.prop' and hasattr(self, 'adb_files') and 'build.prop' in self.adb_files:
                        save_path = self.adb_files['build.prop']
                    elif filename == 'init.rc' and hasattr(self, 'adb_files') and 'init.rc' in self.adb_files:
                        save_path = self.adb_files['init.rc']
                    else:
                        save_path = os.path.join(self.patched_dir, filename)
                    
                    self.adb_log_output.append(f"✏️ Ghi đè file gốc: {save_path}")
                else:
                    # Save to Patched folder
                    save_path = os.path.join(self.patched_dir, filename)
                    self.adb_log_output.append(f"💾 Lưu vào Patched: {save_path}")
                
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            self.adb_log_output.append("✅ Tất cả file đã được lưu thành công.")
        except Exception as e:
            self.adb_log_output.append(f"❌ Lỗi khi lưu file: {e}")

    def open_patched_folder(self):
        """Opens the 'Patched' directory using the helper method."""
        self.open_directory_in_explorer(self.patched_dir)

    # --- Smart ROM Patcher Methods ---
    def smart_choose_file_or_folder(self):
        """Open dialog to choose file or folder."""
        # First try folder
        folder_path = QFileDialog.getExistingDirectory(self, "Chọn thư mục ROM hoặc ...")
        if folder_path:
            self.smart_handle_dropped_paths([folder_path])
            return
        
        # If cancelled, try file
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Chọn file (services.jar, build.prop, init.rc)", 
            "", 
            "All Files (*);;JAR Files (*.jar);;Text Files (*.prop *.rc)"
        )
        if file_path:
            self.smart_handle_dropped_paths([file_path])
    
    def smart_handle_dropped_paths(self, paths):
        """Handle dropped files/folders - auto-detect type with multi-file support.
        Files ACCUMULATE across multiple drops until patched or cleared."""
        self.smart_selected_paths.extend(paths) if hasattr(self, 'smart_selected_paths') else setattr(self, 'smart_selected_paths', paths)
        
        # DO NOT reset - accumulate files across multiple drops
        # Format: { 'services.jar': [{'path': ..., 'source': ...}, ...] }
        new_detected = {}
        self.smart_progress_bar.setValue(0)
        
        for path in paths:
            if os.path.isdir(path):
                # Scan directory for known files
                self.fm_log_output.append(f"📂 Quét thư mục: {path}")
                self._smart_scan_directory_multi(path, new_detected)
            elif os.path.isfile(path):
                # Detect single file type
                file_type = self.smart_detect_file_type(path)
                if file_type:
                    source_folder = os.path.basename(os.path.dirname(path))
                    self._add_detected_file(new_detected, file_type, path, source_folder)
                else:
                    self.fm_log_output.append(f"⚠️ Không nhận diện được: {os.path.basename(path)}")
        
        # Merge new files with existing (accumulate)
        self._merge_detected_files(new_detected)
        
        # Update UI
        try:
            if self.smart_detected_files:
                # Build display string showing all files
                display_parts = []
                total_files = 0
                for file_type, file_list in self.smart_detected_files.items():
                    total_files += len(file_list)
                    if len(file_list) == 1:
                        display_parts.append(f"{file_type} ({file_list[0]['source']})")
                    else:
                        display_parts.append(f"{file_type} ({len(file_list)} files)")
                
                self.smart_file_display.setText(", ".join(display_parts))
                self.smart_patch_btn.setEnabled(True)
                self.fm_log_output.append(f"\n🎯 TỔNG CỘNG: {total_files} file sẵn sàng patch")
                QApplication.processEvents()
            else:
                self.smart_file_display.setText("Không tìm thấy file hợp lệ")
                self.smart_patch_btn.setEnabled(False)
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def _merge_detected_files(self, new_detected):
        """Merge new detected files with existing, checking for duplicates."""
        for file_type, new_files in new_detected.items():
            if file_type not in self.smart_detected_files:
                self.smart_detected_files[file_type] = []
            
            # Check for duplicates before adding
            existing_paths = [f['path'] for f in self.smart_detected_files[file_type]]
            
            for new_file in new_files:
                if new_file['path'] in existing_paths:
                    # Duplicate path - warn and skip
                    self.fm_log_output.append(f"⚠️ Đã có sẵn: {os.path.basename(new_file['path'])} [{new_file['source']}]")
                else:
                    # Check if same filename from different source (potential conflict)
                    new_basename = os.path.basename(new_file['path'])
                    existing_basenames = {os.path.basename(f['path']): f['source'] for f in self.smart_detected_files[file_type]}
                    
                    if new_basename in existing_basenames:
                        # Same filename, different source - this is the duplicate scenario
                        existing_source = existing_basenames[new_basename]
                        self.fm_log_output.append(f"📋 Thêm file trùng tên: {new_basename}")
                        self.fm_log_output.append(f"   - Đã có: [{existing_source}]")
                        self.fm_log_output.append(f"   - Thêm: [{new_file['source']}]")
                    
                    self.smart_detected_files[file_type].append(new_file)
    
    def _add_detected_file(self, detected_dict, file_type, path, source):
        """Add a file to detected dict, checking for duplicates."""
        if file_type not in detected_dict:
            detected_dict[file_type] = []
        
        # Check if this exact path already exists
        existing_paths = [f['path'] for f in detected_dict[file_type]]
        if path not in existing_paths:
            detected_dict[file_type].append({'path': path, 'source': source})
            self.fm_log_output.append(f"✅ Phát hiện: {file_type} → {os.path.basename(path)} [{source}]")
    
    def _check_and_merge_duplicates(self, new_detected):
        """Check for duplicates and show warning dialog if found."""
        duplicates_found = False
        
        for file_type, new_files in new_detected.items():
            if len(new_files) > 1:
                # Multiple files of same type detected
                duplicates_found = True
                self.fm_log_output.append(f"\n⚠️ CẢNH BÁO: Phát hiện {len(new_files)} file {file_type} trùng loại!")
                for i, f in enumerate(new_files, 1):
                    self.fm_log_output.append(f"   {i}. {f['path']}")
                
                # Show confirmation dialog
                from PySide6.QtWidgets import QMessageBox
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("Phát hiện file trùng loại")
                msg.setText(f"Phát hiện {len(new_files)} file {file_type} từ các thư mục khác nhau.\n\nBạn muốn xử lý thế nào?")
                
                btn_all = msg.addButton("Patch tất cả", QMessageBox.ButtonRole.AcceptRole)
                btn_last = msg.addButton("Chỉ file cuối", QMessageBox.ButtonRole.DestructiveRole)
                btn_cancel = msg.addButton("Hủy", QMessageBox.ButtonRole.RejectRole)
                
                msg.exec()
                
                clicked = msg.clickedButton()
                if clicked == btn_all:
                    self.fm_log_output.append(f"✅ Đã chọn: Patch tất cả {len(new_files)} file {file_type}")
                    if file_type not in self.smart_detected_files:
                        self.smart_detected_files[file_type] = []
                    self.smart_detected_files[file_type].extend(new_files)
                elif clicked == btn_last:
                    self.fm_log_output.append(f"✅ Đã chọn: Chỉ patch file cuối {new_files[-1]['path']}")
                    self.smart_detected_files[file_type] = [new_files[-1]]
                else:
                    self.fm_log_output.append(f"❌ Đã hủy patch {file_type}")
                    # Don't add this file type
            else:
                # Single file - just add
                if file_type not in self.smart_detected_files:
                    self.smart_detected_files[file_type] = []
                self.smart_detected_files[file_type].extend(new_files)
        
        return duplicates_found
    
    def _smart_scan_directory_multi(self, directory, detected_dict):
        """Scan directory recursively with multi-file support (uses deferred processing)."""
        # Use QApplication.processEvents() periodically to keep UI responsive
        file_count = 0
        for root, dirs, files in os.walk(directory):
            for filename in files:
                file_path = os.path.join(root, filename)
                file_type = self.smart_detect_file_type(file_path)
                
                if file_type:
                    # Validate content before adding
                    is_valid = False
                    if file_type == 'services.jar':
                        is_valid = True
                    elif file_type == 'build.prop':
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read(1024)  # Read only first 1KB for speed
                                is_valid = 'ro.build' in content or 'ro.product' in content
                        except:
                            pass
                    elif file_type == 'init.rc':
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read(1024)
                                is_valid = 'service' in content or 'on boot' in content
                        except:
                            pass
                    
                    if is_valid:
                        source_folder = os.path.basename(root)
                        self._add_detected_file(detected_dict, file_type, file_path, source_folder)
                
                # Process events every 10 files to keep UI responsive
                file_count += 1
                if file_count % 10 == 0:
                    QApplication.processEvents()
    
    def smart_detect_file_type(self, file_path):
        """Detect file type based on name and content."""
        filename = os.path.basename(file_path).lower()
        
        if filename == 'services.jar' or filename.endswith('.jar'):
            return 'services.jar'
        elif filename == 'build.prop' or 'build.prop' in filename:
            return 'build.prop'
        elif filename == 'init.rc' or 'init.rc' in filename or filename.endswith('.rc'):
            return 'init.rc'
        
        return None
    
    def smart_scan_directory(self, directory):
        """Scan directory recursively to find known files."""
        for root, dirs, files in os.walk(directory):
            for filename in files:
                file_path = os.path.join(root, filename)
                file_type = self.smart_detect_file_type(file_path)
                
                if file_type and file_type not in self.smart_detected_files:
                    # Validate content before adding
                    if file_type == 'services.jar':
                        self.smart_detected_files[file_type] = file_path
                        self.fm_log_output.append(f"   ✅ Tìm thấy: services.jar")
                    elif file_type == 'build.prop':
                        # Check if valid build.prop
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if 'ro.build' in content or 'ro.product' in content:
                                    self.smart_detected_files[file_type] = file_path
                                    self.fm_log_output.append(f"   ✅ Tìm thấy: build.prop")
                        except:
                            pass
                    elif file_type == 'init.rc':
                        # Check if valid init.rc
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if 'service' in content or 'on boot' in content:
                                    self.smart_detected_files[file_type] = file_path
                                    self.fm_log_output.append(f"   ✅ Tìm thấy: init.rc")
                        except:
                            pass
    
    def smart_auto_patch(self):
        """Auto-patch all detected files (supports multiple files per type)."""
        if not self.smart_detected_files:
            self.fm_log_output.append("❌ Không có file nào để patch!")
            return
        
        self.fm_log_output.clear()
        
        # Lock UI BEFORE starting threads
        self._beginBusy()
        
        # Check overwrite mode
        overwrite = self.smart_overwrite_checkbox.isChecked()
        mode_text = "GHI ĐÈ FILE GỐC" if overwrite else f"LƯU VÀO PATCHED"
        
        self.fm_log_output.append("="*30)
        self.fm_log_output.append(f"🚀 BẮT ĐẦU PATCH TỰ ĐỘNG ({mode_text})")
        self.fm_log_output.append("="*30 + "\n")
        
        # Count total files
        total_files = sum(len(files) for files in self.smart_detected_files.values())
        self._smart_patch_completed = 0
        self._smart_patch_total = total_files
        self._smart_patch_threads = []
        
        # Patch all services.jar files
        if 'services.jar' in self.smart_detected_files:
            jar_files = self.smart_detected_files['services.jar']
            self.fm_log_output.append(f"📦 Patch {len(jar_files)} file services.jar (GPS)...")
            
            for file_info in jar_files:
                jar_path = file_info['path']
                source = file_info['source']
                self.fm_log_output.append(f"   → {os.path.basename(jar_path)} [{source}]")
                
                # Create thread for each file
                thread = GpsPatcherThread(jar_path, self.patched_dir, overwrite_original=overwrite)
                thread.log_message.connect(self.fm_log_output.append)
                thread.patch_finished.connect(lambda success, msg, s=source: self._on_smart_file_done(success, msg, 'services.jar', s))
                thread.cancelled.connect(self.smart_on_cancelled)
                self._smart_patch_threads.append(thread)
                thread.start()
        
        # Patch all build.prop and init.rc files
        build_prop_files = self.smart_detected_files.get('build.prop', [])
        init_rc_files = self.smart_detected_files.get('init.rc', [])
        
        # Group build.prop and init.rc from same source for batch processing
        # For now, process each file individually
        for file_info in build_prop_files:
            path = file_info['path']
            source = file_info['source']
            self.fm_log_output.append(f"📝 Patch build.prop (ADB) [{source}]...")
            
            thread = AdbPatcherThread(path, None)
            thread.log_message.connect(self.fm_log_output.append)
            thread.patch_finished.connect(lambda success, files, ow=overwrite, s=source: self._on_smart_adb_done(success, files, ow, 'build.prop', s))
            thread.cancelled.connect(self.smart_on_cancelled)
            self._smart_patch_threads.append(thread)
            thread.start()
        
        for file_info in init_rc_files:
            path = file_info['path']
            source = file_info['source']
            self.fm_log_output.append(f"⚙️ Patch init.rc (Auto-boot) [{source}]...")
            
            thread = AdbPatcherThread(None, path)
            thread.log_message.connect(self.fm_log_output.append)
            thread.patch_finished.connect(lambda success, files, ow=overwrite, s=source: self._on_smart_adb_done(success, files, ow, 'init.rc', s))
            thread.cancelled.connect(self.smart_on_cancelled)
            self._smart_patch_threads.append(thread)
            thread.start()
        
        self.fm_log_output.append(f"\n{'='*30}")
        self.fm_log_output.append(f"⏳ Đang xử lý {total_files} file...")
        self.fm_log_output.append("="*30)
    
    def _on_smart_file_done(self, success, msg, file_type, source):
        """Callback for single file patch completion."""
        self._smart_patch_completed += 1
        progress = int(self._smart_patch_completed / self._smart_patch_total * 100)
        self.smart_progress_bar.setValue(progress)
        
        if success:
            self.fm_log_output.append(f"✅ {file_type} [{source}]: {msg}")
        else:
            self.fm_log_output.append(f"❌ {file_type} [{source}]: {msg}")
        
        # Check if all done
        if self._smart_patch_completed >= self._smart_patch_total:
            self._end_smart_patch()
    
    def _on_smart_adb_done(self, success, modified_files, overwrite, file_type, source):
        """Callback for ADB file patch completion with auto-save."""
        if success and modified_files:
            # Auto-save the patched files
            for filename, content in modified_files.items():
                try:
                    if overwrite:
                        # Find original path
                        original_path = None
                        for f in self.smart_detected_files.get(file_type, []):
                            if f['source'] == source:
                                original_path = f['path']
                                break
                        if original_path:
                            with open(original_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            self.fm_log_output.append(f"💾 Đã ghi đè: {original_path}")
                    else:
                        # Save to patched folder with source subfolder
                        patched_subdir = os.path.join(self.patched_dir, source)
                        os.makedirs(patched_subdir, exist_ok=True)
                        save_path = os.path.join(patched_subdir, filename)
                        with open(save_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        self.fm_log_output.append(f"💾 Đã lưu: {save_path}")
                except Exception as e:
                    self.fm_log_output.append(f"❌ Lỗi lưu {filename}: {e}")
        
        self._on_smart_file_done(success, "OK" if success else "Failed", file_type, source)
    
    def _end_smart_patch(self):
        """End smart patch and unlock UI."""
        self._endBusy()
        overwrite = self.smart_overwrite_checkbox.isChecked()
        
        self.fm_log_output.append(f"\n{'='*30}")
        self.fm_log_output.append(f"✅ HOÀN TẤT! Đã patch {self._smart_patch_completed}/{self._smart_patch_total} file")
        if not overwrite:
            self.fm_log_output.append(f"📁 File đã lưu tại: {self.patched_dir}")
        self.fm_log_output.append("="*30)
        
        # Reset detected files for next batch
        self.smart_detected_files = {}
        self.smart_selected_paths = []
        self.smart_file_display.setText("")
        self.smart_patch_btn.setEnabled(False)
        self.fm_log_output.append("\n💡 Kéo thả file mới để tiếp tục...")
    
    def smart_on_gps_finished(self, success, msg):
        """Callback for GPS patch finished in smart auto patch"""
        self.fm_log_output.append(msg if success else f"❌ {msg}")
        # Check if all threads done
        self._check_smart_patch_complete()
    
    def smart_on_cancelled(self):
        """Callback for cancelled in smart auto patch"""
        self._endBusy()
        self.fm_log_output.append("⛔ Đã hủy")
        self.append("🔍 [UI] Smart patch cancelled")
    
    def _check_smart_patch_complete(self):
        """Check if all smart patch threads are done and unlock UI"""
        # Simple check: if both threads finished or don't exist
        gps_done = not hasattr(self, 'gps_patcher_thread') or not self.gps_patcher_thread.isRunning()
        adb_done = not hasattr(self, 'adb_patcher_thread') or not self.adb_patcher_thread.isRunning()
        
        if gps_done and adb_done:
            self._endBusy()
            self.append("🔍 [UI] All smart patches completed")
    
    def smart_save_adb_files(self, success, modified_files, overwrite):
        """Save patched ADB files (build.prop, init.rc) from Smart Patcher."""
        if not success or not modified_files:
            self._check_smart_patch_complete()
            return
        
        try:
            for filename, content in modified_files.items():
                if overwrite:
                    # Overwrite original file
                    if filename == 'build.prop' and 'build.prop' in self.smart_detected_files:
                        save_path = self.smart_detected_files['build.prop']
                    elif filename == 'init.rc' and 'init.rc' in self.smart_detected_files:
                        save_path = self.smart_detected_files['init.rc']
                    else:
                        save_path = os.path.join(self.patched_dir, filename)
                    
                    self.fm_log_output.append(f"✏️ Ghi đè file gốc: {save_path}")
                else:
                    # Save to Patched folder
                    save_path = os.path.join(self.patched_dir, filename)
                    self.fm_log_output.append(f"💾 Lưu vào Patched: {save_path}")
                
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            self.fm_log_output.append("✅ Đã lưu tất cả file ADB.")
        except Exception as e:
            self.fm_log_output.append(f"❌ Lỗi khi lưu file: {e}")
        finally:
            # Check if all done
            self._check_smart_patch_complete()

    # --- Logic cho File Manager Tab ---
    def select_fm_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Chọn thư mục gốc (thường là 'system')")
        if dir_path:
            self.load_directory_view(dir_path)

    def choose_rom_directory(self):
        """Open dialog to choose ROM directory."""
        dir_path = QFileDialog.getExistingDirectory(self, "Chọn thư mục ROM unpacked", "")
        if dir_path:
            self.load_directory_view(dir_path)
            self.fm_rom_root_label.setText(dir_path)
            self.fm_rom_root_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def load_directory_view(self, path):
        self.fm_log_output.clear()
        self.fm_log_output.append(f"Đang quét thư mục: {path}")
        self.fm_tree_view.setRootIndex(self.fm_model.setRootPath(path))
        
        # --- START NEW CODE ---
        self.fm_stack.setCurrentIndex(1) # Switch from placeholder to tree view
        # --- END NEW CODE ---
        
        self.scan_and_auto_patch(path)

    def scan_and_auto_patch(self, root_path):
        self.fm_log_output.append("\n--- Bắt đầu quét và xác thực file hệ thống ---")
        self.valid_files = {}  # Reset on each scan
        
        # List to store potential init.rc candidates
        init_rc_candidates = []

        # Validation Keywords
        build_prop_keywords = ['ro.adb.secure', 'persist.sys.usb.config', 'ro.product.system.model']
        build_prop_check_missing = ['persist.service.adb.enable=1', 'ro.control_privapp_permissions=disable', 'setup.wizard.has.run=1']

        for dirpath, _, filenames in os.walk(root_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                normalized_file_path = os.path.normpath(file_path).replace('\\', '/')

                # --- Validate build.prop ---
                if filename == 'build.prop' and 'build.prop' not in self.valid_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        if any(key in content for key in build_prop_keywords):
                            self.valid_files['build.prop'] = file_path
                            rel_path = os.path.relpath(file_path, root_path)
                            self.fm_log_output.append(f"✅ Đã tìm thấy build.prop hợp lệ tại: {rel_path}")
                            if not all(check in content for check in build_prop_check_missing):
                                self.fm_log_output.append("   ⚠️ Cảnh báo: File này chưa đầy đủ cấu hình Auto ADB.")
                    except Exception as e:
                        self.fm_log_output.append(f"❌ Lỗi đọc build.prop: {e}")

                # --- Collect init.rc candidates, excluding apex ---
                if filename == 'init.rc':
                    if '/apex/' not in normalized_file_path:
                        init_rc_candidates.append(file_path)

                # --- Validate services.jar by path ---
                if filename == 'services.jar' and 'services.jar' not in self.valid_files:
                    if normalized_file_path.endswith('/system/framework/services.jar'):
                        self.valid_files['services.jar'] = file_path
                        self.fm_log_output.append(f"✅ Đã tìm thấy services.jar tại: .../system/framework/services.jar")

        # --- START: New init.rc validation logic (post-scan) ---
        if init_rc_candidates:
            # Custom sorting key for init.rc priority
            def init_rc_sort_key(path):
                norm_path = os.path.normpath(path).replace('\\', '/')
                if norm_path.endswith('/system/etc/init/hw/init.rc'):
                    return 0  # Highest priority
                if norm_path.endswith('/system/etc/init.rc'):
                    return 1  # Second priority
                return 2      # Lower priority

            init_rc_candidates.sort(key=init_rc_sort_key)
            
            init_rc_validated = False
            for candidate_path in init_rc_candidates:
                rel_path = os.path.relpath(candidate_path, root_path)
                try:
                    with open(candidate_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # The primary validation check: does it contain 'on charger'?
                    if 'on charger' in content:
                        self.valid_files['init.rc'] = candidate_path
                        self.fm_log_output.append(f"✅ Đã tìm thấy init.rc hợp lệ tại: {rel_path}")
                        if 'setprop sys.powerctl "reboot"' not in content:
                            self.fm_log_output.append("   ⚠️ Cảnh báo: File này có thể chưa có cấu hình tự khởi động khi sạc.")
                        init_rc_validated = True
                        break # Stop after finding the first valid, highest-priority file
                    else:
                        self.fm_log_output.append(f"   ℹ️ Ghi nhận file init.rc tại '{rel_path}', nhưng không chứa 'on charger'. Bỏ qua.")

                except Exception as e:
                    self.fm_log_output.append(f"❌ Lỗi đọc init.rc tại '{rel_path}': {e}")
            
            if not init_rc_validated:
                 self.fm_log_output.append("⚠️ Quét init.rc hoàn tất, không tìm thấy file nào chứa block 'on charger'.")

        # --- END: New init.rc validation logic ---

        if not self.valid_files:
            self.fm_log_output.append("--- Quét hoàn tất: Không tìm thấy file hợp lệ nào để vá. ---")
        else:
            self.fm_log_output.append("--- Quét hoàn tất. Sẵn sàng để vá. ---")
        
        self.update_fm_buttons_state()

    def update_fm_buttons_state(self):
        """Enables or disables buttons based on scan results."""
        self.fm_autopatch_btn.setEnabled('services.jar' in self.valid_files or 'build.prop' in self.valid_files or 'init.rc' in self.valid_files)
        self.fm_view_buildprop_btn.setEnabled('build.prop' in self.valid_files)
        self.fm_view_initrc_btn.setEnabled('init.rc' in self.valid_files)

    def start_auto_patching(self):
        """Starts the patching process for all validated files."""
        if not self.valid_files:
            self.fm_log_output.append("Lỗi: Không có file hợp lệ nào để vá.")
            return

        self.fm_autopatch_btn.setEnabled(False) # Disable button during patching
        self.fm_log_output.append("\n--- Bắt đầu quá trình Auto Patch ---")
        
        # Trigger GPS Patcher if services.jar is valid
        if 'services.jar' in self.valid_files:
            self.fm_log_output.append("\nKích hoạt GPS Patcher cho services.jar...")
            self.fm_gps_patcher_thread = GpsPatcherThread(self.valid_files['services.jar'], self.patched_dir, overwrite_original=True)
            self.fm_gps_patcher_thread.log_message.connect(self.fm_log_output.append)
            self.fm_gps_patcher_thread.patch_finished.connect(self.on_fm_patch_finished)
            self.fm_gps_patcher_thread.start()

        # Trigger ADB Patcher if build.prop or init.rc is valid
        build_prop_path = self.valid_files.get('build.prop')
        init_rc_path = self.valid_files.get('init.rc')
        if build_prop_path or init_rc_path:
            self.fm_log_output.append("\nKích hoạt ADB & AutoStart Patcher...")
            self.fm_adb_patcher_thread = AdbPatcherThread(build_prop_path, init_rc_path)
            self.fm_adb_patcher_thread.log_message.connect(self.fm_log_output.append)
            self.fm_adb_patcher_thread.patch_finished.connect(self.on_fm_adb_patch_finished)
            self.fm_adb_patcher_thread.start()

    def show_file_preview(self, file_key):
        """Shows the custom dialog to preview and interactively patch a file."""
        if file_key not in self.valid_files:
            return
        
        file_path = self.valid_files[file_key]
        dialog = FilePreviewDialog(file_key, file_path, self)
        dialog.exec()

    def on_fm_patch_finished(self, success, message):
        log_method = self.fm_log_output.append
        if success:
            # The 'message' variable already contains the correct context-aware string
            # (e.g., "...ghi đè lên file gốc" or "...lưu trong thư mục 'Patched'")
            log_method(message)
            # --- START: Backup Logic for services.jar ---
            if 'services.jar' in self.valid_files:
                try:
                    rom_folder_name = os.path.basename(os.path.normpath(self.fm_model.rootPath()))
                    backup_dir = os.path.join(self.patched_dir, rom_folder_name)
                    os.makedirs(backup_dir, exist_ok=True)
                    original_path = self.valid_files['services.jar']
                    shutil.copy2(original_path, os.path.join(backup_dir, os.path.basename(original_path)))
                    log_method(f"   - ✅ Đã sao lưu file vào: {backup_dir}")
                except Exception as e:
                    log_method(f"   - ❌ Lỗi sao lưu services.jar: {e}")
            # --- END: Backup Logic ---
        else:
            log_method(f"❌ Vá file services.jar THẤT BẠI: {message}")
        
        self.fm_autopatch_btn.setEnabled(True) # Re-enable the button

    def on_fm_adb_patch_finished(self, success, modified_contents):
        """Callback for AdbPatcherThread from the 'Auto Rom' tab to handle file overwriting."""
        if success and modified_contents:
            self.fm_log_output.append("   - Phân tích hoàn tất, bắt đầu ghi đè file...")
            try:
                # --- START: Backup Logic ---
                rom_folder_name = os.path.basename(os.path.normpath(self.fm_model.rootPath()))
                backup_dir = os.path.join(self.patched_dir, rom_folder_name)
                os.makedirs(backup_dir, exist_ok=True)
                # --- END: Backup Logic ---

                for file_key, content in modified_contents.items():
                    if file_key in self.valid_files:
                        original_path = self.valid_files[file_key]
                        # Overwrite original file
                        with open(original_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        self.fm_log_output.append(f"   - ✅ Đã ghi đè thành công: {os.path.basename(original_path)}")
                        # Copy to backup directory
                        shutil.copy2(original_path, os.path.join(backup_dir, os.path.basename(original_path)))
                self.fm_log_output.append(f"   - ✅ Đã sao lưu file vào: {backup_dir}")
                self.fm_log_output.append("✅ Xử lý build.prop/init.rc hoàn tất.")
            except Exception as e:
                self.fm_log_output.append(f"❌ Lỗi khi ghi đè file: {e}")
        else:
            self.fm_log_output.append("❌ Lỗi xử lý build.prop/init.rc.")

    def open_directory_in_explorer(self, path):
        """Opens a given directory path in the system's file explorer."""
        if not os.path.isdir(path):
            current_log_widget = self.tabs.currentWidget().findChild(QTextEdit)
            if current_log_widget:
                current_log_widget.append(f"❌ Lỗi: Thư mục '{path}' không tồn tại.")
            return
        
        try:
            if sys.platform == "win32":
                os.startfile(os.path.realpath(path))
            elif sys.platform == "darwin": # macOS
                subprocess.Popen(["open", path])
            else: # Linux and other Unix-like OS
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            current_log_widget = self.tabs.currentWidget().findChild(QTextEdit)
            if current_log_widget:
                current_log_widget.append(f"❌ Không thể mở thư mục: {e}")

    def show_fm_context_menu(self, position):
        index = self.fm_tree_view.indexAt(position)
        if not index.isValid():
            return

        file_path = self.fm_model.filePath(index)
        is_dir = self.fm_model.isDir(index)
        is_apk = not is_dir and file_path.lower().endswith('.apk')

        menu = QMenu()
        action = None

        if is_dir:
            action = QAction("Set quyền 755 (dir) + root:root", self)
            action.triggered.connect(partial(self.handle_dir_permission_request, file_path))
        elif is_apk:
            action = QAction("Set quyền 644 (APK) + root:root", self)
            action.triggered.connect(partial(self.handle_apk_permission_request, file_path))
        
        if action:
            menu.addAction(action)
            menu.addSeparator()

            # Add a new action for updating the script without setting permissions
            update_script_action = QAction("Cập nhật updater-script (quyền đã đặt)", self)
            update_script_action.triggered.connect(partial(self.handle_update_script_only_request, file_path))
            menu.addAction(update_script_action)

            menu.exec(self.fm_tree_view.viewport().mapToGlobal(position))
        # If it's another file type, do nothing - no menu will be shown.

    def handle_dir_permission_request(self, path):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle("Xác nhận thao tác đệ quy")
        msg_box.setText("Áp dụng quyền cho thư mục con?")
        msg_box.setInformativeText("Bạn có muốn áp dụng quyền 755 + root:root cho TẤT CẢ các thư mục con không?\n\n(Quyền của các file bên trong sẽ không thay đổi.)")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        is_recursive = (msg_box.exec() == QMessageBox.StandardButton.Yes)
        
        should_update_script = self.fm_auto_update_script_checkbox.isChecked()
        current_rom_root = self.fm_model.rootPath()
        
        self.perm_thread = PermissionThread('dir', path, recursive=is_recursive, 
                                            rom_root=current_rom_root, 
                                            update_script=should_update_script)
        self.perm_thread.log_message.connect(self.fm_log_output.append)
        self.perm_thread.script_update_finished.connect(self.on_script_update_finished) # <-- CONNECT NEW SIGNAL
        self.perm_thread.start()

    def handle_apk_permission_request(self, path):
        should_update_script = self.fm_auto_update_script_checkbox.isChecked()
        current_rom_root = self.fm_model.rootPath()

        self.perm_thread = PermissionThread('apk', path,
                                            rom_root=current_rom_root,
                                            update_script=should_update_script)
        self.perm_thread.log_message.connect(self.fm_log_output.append)
        self.perm_thread.script_update_finished.connect(self.on_script_update_finished) # <-- CONNECT NEW SIGNAL
        self.perm_thread.start()

    def on_script_update_finished(self, result: dict):
        """Slot to handle the result from the updater script logic."""
        notes = result.get("notes", [])
        for note in notes:
            self.fm_log_output.append(f"   - {note}")
        
        if result.get("script_path"):
            summary = f"Updater-script: added={result['added']}, updated={result['updated']}, skipped={result['skipped']}"
            self.fm_log_output.append(f"--- ✅ Cập nhật script hoàn tất: {summary} ---")
        else:
            # This handles the A/B ROM case where script_path is None
            self.fm_log_output.append("--- ⚠️ Cập nhật script: Hoàn tất với cảnh báo. ---")

    def handle_update_script_only_request(self, path):
        """Handles the context menu action to only update the script."""
        self.fm_log_output.append(f"\n--- Bắt đầu cập nhật script cho: {os.path.basename(path)} ---")
        try:
            st = os.stat(path)
            mode = stat.S_IMODE(st.st_mode)
            mode_str = f"{mode:o}"[-3:] # Get '755' or '644'
            is_dir = stat.S_ISDIR(st.st_mode)

            if not (is_dir and mode_str == '755') and not (not is_dir and mode_str == '644'):
                 self.fm_log_output.append(f"   - Cảnh báo: Quyền hiện tại là '{mode_str}', không khớp chuẩn 755/644.")
            
            entry = {
                "path_abs": path,
                "type": "dir" if is_dir else "file",
                "mode_expect": mode_str,
            }
            rom_root = self.fm_model.rootPath()
            # This can be slow, run in a thread
            self.script_update_thread = QThread() # Generic thread
            self.script_worker = ScriptUpdateWorker([entry], rom_root)
            self.script_worker.moveToThread(self.script_update_thread)
            self.script_update_thread.started.connect(self.script_worker.run)
            self.script_worker.finished.connect(self.on_script_update_finished)
            self.script_worker.finished.connect(self.script_update_thread.quit)
            self.script_worker.finished.connect(self.script_worker.deleteLater)
            self.script_update_thread.finished.connect(self.script_update_thread.deleteLater)
            self.script_update_thread.start()

        except Exception as e:
            self.fm_log_output.append(f"   - ❌ Lỗi khi đọc quyền file: {e}")

    def select_decompile_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file .jar hoặc .apk", "", "Java/Android Archives (*.jar *.apk)")
        if file_path:
            self.decompile_input_path.setText(file_path)
            self.decompile_btn.setEnabled(True)

    def select_recompile_folder(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Chọn thư mục đã dịch ngược")
        if dir_path:
            self.recompile_input_path.setText(dir_path)
            self.recompile_btn.setEnabled(True)

    def start_decompile(self):
        input_path = self.decompile_input_path.text()
        if not input_path: return
        self.decompile_btn.setEnabled(False)
        self.decompile_log_output.clear()
        self.decompile_thread = DecompileThread(mode='decompile', input_path=input_path, decompiled_dir=self.decompiled_dir, rebuilt_dir=self.rebuilt_dir)
        self.decompile_thread.log_message.connect(self.decompile_log_output.append)
        self.decompile_thread.task_finished.connect(self.on_decompile_task_finished)
        self.decompile_thread.start()

    def start_recompile(self):
        input_path = self.recompile_input_path.text()
        if not input_path: return
        self.recompile_btn.setEnabled(False)
        self.decompile_log_output.clear()
        self.decompile_thread = DecompileThread(mode='recompile', input_path=input_path, decompiled_dir=self.decompiled_dir, rebuilt_dir=self.rebuilt_dir)
        self.decompile_thread.log_message.connect(self.decompile_log_output.append)
        self.decompile_thread.task_finished.connect(self.on_decompile_task_finished)
        self.decompile_thread.start()

    def on_decompile_task_finished(self, success, message):
        self.decompile_log_output.append(f"\n{message}")
        # Re-enable buttons
        if self.decompile_input_path.text(): self.decompile_btn.setEnabled(True)
        if self.recompile_input_path.text(): self.recompile_btn.setEnabled(True)

    def open_output_folders(self):
        self.open_directory_in_explorer(self.decompiled_dir)
        self.open_directory_in_explorer(self.rebuilt_dir)

    # --- Logic chung ---
    def set_input_file(self, path, tab_type):
        if tab_type == 'gps':
            self.gps_file_path_edit.setText(path)
            self.gps_patch_btn.setEnabled(True)
            self.gps_log_output.append(f"Đã chọn file: {path}")
        elif tab_type == 'adb':
            self.adb_files = {}
            paths = [path] if isinstance(path, str) else path
            display_paths = []
            for p in paths:
                filename = os.path.basename(p)
                if 'build.prop' in filename: self.adb_files['build.prop'] = p
                elif 'init.rc' in filename: self.adb_files['init.rc'] = p
                display_paths.append(filename)
            
            self.adb_file_path_edit.setText(" | ".join(display_paths))
            self.adb_patch_btn.setEnabled(True)
            self.adb_log_output.append(f"Đã chọn các file: {', '.join(display_paths)}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls: return
        
        current_tab_index = self.tabs.currentIndex()
        paths = [url.toLocalFile() for url in urls if url.isLocalFile()]

        if current_tab_index == 0: # Tab ROM Tools - Smart Auto-Detect
            # Use smart handler for all dropped paths
            self.smart_handle_dropped_paths(paths)
        
        elif current_tab_index == 1: # Tab Decompile Jar/APK
            files = [p for p in paths if os.path.isfile(p) and (p.lower().endswith('.jar') or p.lower().endswith('.apk'))]
            dirs = [p for p in paths if os.path.isdir(p)]

            if files:
                self.decompile_input_path.setText(files[0])
                self.decompile_btn.setEnabled(True)
                self.decompile_log_output.append(f"Đã chọn file để dịch ngược: {files[0]}")
            
            if dirs:
                self.recompile_input_path.setText(dirs[0])
                self.recompile_btn.setEnabled(True)
                self.decompile_log_output.append(f"Đã chọn thư mục để đóng gói lại: {dirs[0]}")
        
        # Tab 2 (ADB Comment) has its own drag & drop handling
    
    def adb_tab_dragEnterEvent(self, event):
        """Handle drag enter event for ADB Comment tab."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def adb_tab_dropEvent(self, event):
        """Handle drop event for ADB Comment tab - save files to storage."""
        urls = event.mimeData().urls()
        if not urls:
            return
        
        paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        
        for file_path in paths:
            if os.path.isfile(file_path):
                # Copy file to uploaded_files directory
                file_name = os.path.basename(file_path)
                dest_path = os.path.join(self.uploaded_files_dir, file_name)
                
                # Check if file already exists
                if os.path.exists(dest_path):
                    # Show confirmation dialog
                    reply = QMessageBox.question(
                        self,
                        "⚠️ File trùng lặp",
                        f"File '{file_name}' đã tồn tại trong danh sách!\n\nBạn có muốn ghi đè file không?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.No:
                        self.adb_comment_log.append(f"⚠️ Đã bỏ qua file trùng: {file_name}")
                        continue
                
                # Copy file
                try:
                    import shutil
                    shutil.copy2(file_path, dest_path)
                    
                    # Set as current selected file
                    self.current_selected_file = dest_path
                    self.adb_file_display.setText(file_name)
                    
                    # Update adb_dropped_files for compatibility
                    if dest_path not in self.adb_dropped_files:
                        self.adb_dropped_files.append(dest_path)
                    
                    self.adb_comment_log.append(f"✅ Đã lưu file: {file_name}")
                    self.adb_comment_log.append(f"   📁 Đường dẫn: {dest_path}\n")
                    
                except Exception as e:
                    self.adb_comment_log.append(f"❌ Lỗi khi lưu file {file_name}: {e}")
    
    def show_file_list_menu(self):
        """Show menu with list of saved files."""
        # Get list of files in uploaded_files directory
        try:
            files = os.listdir(self.uploaded_files_dir)
            files = [f for f in files if os.path.isfile(os.path.join(self.uploaded_files_dir, f))]
        except Exception as e:
            self.adb_comment_log.append(f"❌ Lỗi đọc danh sách file: {e}")
            return
        
        if not files:
            self.adb_comment_log.append("📭 Danh sách file trống! Kéo thả file vào đây để thêm.")
            return
        
        # Create menu
        menu = QMenu(self)
        
        # Add file list
        for file_name in sorted(files):
            file_path = os.path.join(self.uploaded_files_dir, file_name)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            
            action = QAction(f"📄 {file_name} ({file_size:.2f} MB)", self)
            action.triggered.connect(lambda checked, fp=file_path, fn=file_name: self.select_file_from_list(fp, fn))
            menu.addAction(action)
        
        menu.addSeparator()
        
        # Add management actions
        clear_action = QAction("🗑️ Xóa tất cả file", self)
        clear_action.triggered.connect(self.clear_all_files)
        menu.addAction(clear_action)
        
        open_folder_action = QAction("📂 Mở thư mục lưu trữ", self)
        open_folder_action.triggered.connect(lambda: self.open_directory_in_explorer(self.uploaded_files_dir))
        menu.addAction(open_folder_action)
        
        # Show menu at button position
        menu.exec(self.file_list_btn.mapToGlobal(self.file_list_btn.rect().bottomLeft()))
    
    def select_file_from_list(self, file_path, file_name):
        """Select a file from the list."""
        self.current_selected_file = file_path
        self.adb_file_display.setText(file_name)
        
        # Update adb_dropped_files for compatibility
        if file_path not in self.adb_dropped_files:
            self.adb_dropped_files.clear()  # Clear old list
            self.adb_dropped_files.append(file_path)
        
        self.adb_comment_log.append(f"✅ Đã chọn file: {file_name}")
        self.adb_comment_log.append(f"   📁 {file_path}\n")
    
    def clear_all_files(self):
        """Clear all files from storage."""
        reply = QMessageBox.question(
            self,
            "⚠️ Xác nhận xóa",
            "Bạn có chắc chắn muốn xóa TẤT CẢ file đã lưu không?\n\nHành động này không thể hoàn tác!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                import shutil
                # Remove all files in directory
                for file_name in os.listdir(self.uploaded_files_dir):
                    file_path = os.path.join(self.uploaded_files_dir, file_name)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                
                # Clear current selection
                self.current_selected_file = None
                self.adb_file_display.clear()
                self.adb_dropped_files.clear()
                
                self.adb_comment_log.append("✅ Đã xóa tất cả file khỏi danh sách lưu trữ!")
                
            except Exception as e:
                self.adb_comment_log.append(f"❌ Lỗi khi xóa file: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
