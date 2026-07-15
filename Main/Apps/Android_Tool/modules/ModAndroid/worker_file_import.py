"""
Worker Module cho File I/O Operations
Xử lý các thao tác copy, unzip, scan file nặng trên background thread
Tránh "Not Responding" khi xử lý file lớn

Author: Mon
AI Assistant: Claude Sonnet 4.5
"""

from PySide6.QtCore import QObject, QThread, Signal, Slot
from pathlib import Path
import os
import zipfile
import time


class FileImportWorker(QObject):
    """
    Worker để import file lớn (copy + unzip) mà không block UI thread
    
    Signals:
        progress: int (0-100) - Tiến độ công việc
        log: str - Log message để hiển thị
        finished: str - Đường dẫn file đích khi hoàn thành
        error: str - Thông báo lỗi
        cancelled: void - Báo hiệu đã hủy
    """
    
    progress = Signal(int)      # 0..100
    log = Signal(str)           # Log message
    finished = Signal(str)      # Destination path
    error = Signal(str)         # Error message
    cancelled = Signal()        # Cancelled signal
    
    def __init__(self, src_path: str, dst_dir: str, *, unzip=False, chunk_mb: int = 16):
        """
        Args:
            src_path: Đường dẫn file nguồn
            dst_dir: Thư mục đích
            unzip: True nếu cần giải nén file .zip sau khi copy
            chunk_mb: Kích thước chunk đọc/ghi (MB), mặc định 16MB
        """
        super().__init__()
        self.src = Path(src_path)
        self.dst_dir = Path(dst_dir)
        self.unzip = unzip
        self.chunk = max(1, chunk_mb) * 1024 * 1024  # Convert to bytes
        self._cancel = False
        
    @Slot()
    def run(self):
        """Main worker logic - chạy trên background thread"""
        try:
            # 🔍 DEBUG: Bắt đầu import
            self.log.emit(f"🔍 [FileImportWorker] Bắt đầu import: {self.src.name}")
            self.log.emit(f"🔍 [FileImportWorker] Chunk size: {self.chunk // 1024 // 1024}MB")
            
            # Tạo thư mục đích nếu chưa có
            self.dst_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy file với progress
            dst = self.dst_dir / self.src.name
            total = os.path.getsize(self.src)
            done = 0
            
            self.log.emit(f"🔍 [FileImportWorker] File size: {total / 1024 / 1024:.2f}MB")
            self.log.emit(f"📋 Đang copy {self.src.name}...")
            
            start_time = time.time()
            
            with open(self.src, "rb", buffering=self.chunk) as rf, \
                 open(dst, "wb", buffering=self.chunk) as wf:
                
                while True:
                    # Check cancel flag
                    if self._cancel:
                        self.log.emit("🔍 [FileImportWorker] Cancel detected, cleaning up...")
                        try:
                            dst.unlink()
                        except Exception:
                            pass
                        self.cancelled.emit()
                        return
                    
                    # Read chunk
                    buf = rf.read(self.chunk)
                    if not buf:
                        break
                    
                    # Write chunk
                    wf.write(buf)
                    done += len(buf)
                    
                    # Update progress (emit mỗi chunk để không spam)
                    if total:
                        progress_pct = int(done * 100 / total)
                        self.progress.emit(progress_pct)
            
            elapsed = time.time() - start_time
            speed_mbps = (total / 1024 / 1024) / elapsed if elapsed > 0 else 0
            self.log.emit(f"✅ Copy hoàn thành → {dst.name} ({speed_mbps:.2f} MB/s)")
            
            # Unzip nếu cần
            if self.unzip and dst.suffix.lower() == ".zip":
                self.log.emit(f"🔍 [FileImportWorker] Bắt đầu giải nén...")
                self.log.emit(f"📦 Đang giải nén {dst.name}...")
                
                with zipfile.ZipFile(dst) as zf:
                    members = zf.infolist()
                    total_members = len(members)
                    
                    self.log.emit(f"🔍 [FileImportWorker] Tổng số file: {total_members}")
                    
                    for i, m in enumerate(members, 1):
                        # Check cancel
                        if self._cancel:
                            self.log.emit("🔍 [FileImportWorker] Cancel during unzip")
                            self.cancelled.emit()
                            return
                        
                        # Extract file
                        zf.extract(m, self.dst_dir)
                        
                        # Update progress (emit mỗi 10 file hoặc 5% để giảm spam)
                        if i % 10 == 0 or i == total_members:
                            progress_pct = int(i * 100 / total_members)
                            self.progress.emit(progress_pct)
                            
                            # Log mỗi 100 file để không spam
                            if i % 100 == 0:
                                self.log.emit(f"🔍 [FileImportWorker] Đã giải nén {i}/{total_members} file...")
                
                self.log.emit(f"✅ Giải nén hoàn thành: {total_members} file")
            
            # Emit finished signal
            self.log.emit("🔍 [FileImportWorker] Hoàn thành thành công")
            self.finished.emit(str(dst))
            
        except Exception as e:
            self.log.emit(f"🔍 [FileImportWorker] Exception: {type(e).__name__}: {e}")
            self.error.emit(f"Lỗi: {repr(e)}")
    
    @Slot()
    def cancel(self):
        """Đánh dấu để hủy công việc"""
        self.log.emit("🔍 [FileImportWorker] Cancel requested")
        self._cancel = True


class ZipExtractWorker(QObject):
    """
    Worker chuyên dụng cho giải nén file .zip lớn
    Xử lý theo từng file, emit progress chi tiết
    """
    
    progress = Signal(int)      # 0..100
    log = Signal(str)
    finished = Signal(str)      # Extract directory
    error = Signal(str)
    cancelled = Signal()
    
    def __init__(self, zip_path: str, extract_dir: str):
        super().__init__()
        self.zip_path = Path(zip_path)
        self.extract_dir = Path(extract_dir)
        self._cancel = False
    
    @Slot()
    def run(self):
        """Extract zip file với progress chi tiết"""
        try:
            self.log.emit(f"🔍 [ZipExtractWorker] Bắt đầu giải nén: {self.zip_path.name}")
            
            # Tạo thư mục extract nếu chưa có
            self.extract_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(self.zip_path, 'r') as zf:
                members = zf.infolist()
                total = len(members)
                
                self.log.emit(f"🔍 [ZipExtractWorker] Tổng số file: {total}")
                
                for i, member in enumerate(members, 1):
                    if self._cancel:
                        self.log.emit("🔍 [ZipExtractWorker] Cancelled")
                        self.cancelled.emit()
                        return
                    
                    # Extract file
                    zf.extract(member, self.extract_dir)
                    
                    # Update progress mỗi file hoặc mỗi 5%
                    if i % 10 == 0 or i == total:
                        progress_pct = int(i * 100 / total)
                        self.progress.emit(progress_pct)
                    
                    # Log mỗi 100 file
                    if i % 100 == 0:
                        self.log.emit(f"  Đã giải nén {i}/{total} file...")
            
            self.log.emit(f"✅ Giải nén hoàn thành: {total} file → {self.extract_dir}")
            self.finished.emit(str(self.extract_dir))
            
        except Exception as e:
            self.log.emit(f"🔍 [ZipExtractWorker] Error: {e}")
            self.error.emit(f"Lỗi giải nén: {repr(e)}")
    
    @Slot()
    def cancel(self):
        """Request cancel"""
        self._cancel = True


class FileScanWorker(QObject):
    """
    Worker để scan thư mục tìm file (không block UI)
    Dùng cho File Manager hoặc scan ROM directory
    """
    
    progress = Signal(int)      # Số file đã scan
    log = Signal(str)
    finished = Signal(list)     # Danh sách file tìm thấy
    error = Signal(str)
    cancelled = Signal()
    
    def __init__(self, root_dir: str, pattern: str = "*", recursive: bool = True):
        """
        Args:
            root_dir: Thư mục gốc để scan
            pattern: Pattern file cần tìm (vd: "*.jar", "*.prop")
            recursive: True nếu scan đệ quy vào subfolder
        """
        super().__init__()
        self.root_dir = Path(root_dir)
        self.pattern = pattern
        self.recursive = recursive
        self._cancel = False
    
    @Slot()
    def run(self):
        """Scan directory để tìm file"""
        try:
            self.log.emit(f"🔍 [FileScanWorker] Bắt đầu scan: {self.root_dir}")
            
            results = []
            count = 0
            
            if self.recursive:
                # Scan đệ quy
                for root, dirs, files in os.walk(self.root_dir):
                    if self._cancel:
                        self.cancelled.emit()
                        return
                    
                    for file in files:
                        if self._cancel:
                            self.cancelled.emit()
                            return
                        
                        count += 1
                        full_path = os.path.join(root, file)
                        
                        # Check pattern match
                        if Path(file).match(self.pattern):
                            results.append(full_path)
                        
                        # Update progress mỗi 100 file
                        if count % 100 == 0:
                            self.progress.emit(count)
            else:
                # Scan chỉ trong thư mục hiện tại
                for item in self.root_dir.iterdir():
                    if self._cancel:
                        self.cancelled.emit()
                        return
                    
                    if item.is_file() and item.match(self.pattern):
                        results.append(str(item))
                        count += 1
            
            self.log.emit(f"✅ Scan hoàn thành: Tìm thấy {len(results)}/{count} file match")
            self.finished.emit(results)
            
        except Exception as e:
            self.log.emit(f"🔍 [FileScanWorker] Error: {e}")
            self.error.emit(f"Lỗi scan: {repr(e)}")
    
    @Slot()
    def cancel(self):
        """Request cancel"""
        self._cancel = True


class AdbCommandWorker(QObject):
    """
    Worker cho các lệnh ADB nặng (push file, twrp wipe/install)
    Chạy trên background thread, emit log realtime, không block UI
    
    Signals:
        progress: int (0-100) - Tiến độ công việc (chủ yếu cho push)
        log: str - Log message realtime
        finished: bool, str - (success, result_message)
        error: str - Thông báo lỗi
        cancelled: void - Báo hiệu đã hủy
    
    Usage:
        worker = AdbCommandWorker([
            ("shell", {"cmd": "twrp set tw_ro_mode 0"}),
            ("shell", {"cmd": "twrp wipe data"}),
            ("push", {"src": "/path/to/file.zip", "dest": "/tmp/"}),
            ("shell", {"cmd": "twrp install /tmp/file.zip"})
        ], serial="abc123")
        
        worker.log.connect(log_widget.append)
        worker.finished.connect(on_done)
        
        thread = QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        thread.start()
    """
    
    progress = Signal(int)          # 0..100
    log = Signal(str)               # Realtime log
    finished = Signal(bool, str)    # (success, message)
    error = Signal(str)             # Error message
    cancelled = Signal()            # Cancelled
    
    def __init__(self, commands: list, serial: str = None):
        """
        Args:
            commands: List of (cmd_type, cmd_args) tuples
                - ("shell", {"cmd": "twrp wipe data"})
                - ("push", {"src": path, "dest": "/tmp/"})
            serial: Device serial (optional, if None uses default device)
        """
        super().__init__()
        self.commands = commands
        self.serial = serial
        self._cancel = False
        
        # Import subprocess here to avoid circular import
        import subprocess
        self.subprocess = subprocess
    
    def _get_serial_arg(self):
        """Get ADB serial argument string"""
        return f"-s {self.serial}" if self.serial else ""
    
    @Slot()
    def run(self):
        """Execute all commands sequentially on background thread"""
        import re
        
        try:
            total_commands = len(self.commands)
            success_count = 0
            
            for idx, (cmd_type, cmd_args) in enumerate(self.commands, 1):
                if self._cancel:
                    self.log.emit("⚠️ Đã hủy bởi user")
                    self.cancelled.emit()
                    return
                
                self.log.emit(f"\n📌 [{idx}/{total_commands}] Đang thực hiện: {cmd_type}")
                
                if cmd_type == "shell":
                    success = self._run_shell_command(cmd_args.get("cmd", ""))
                elif cmd_type == "push":
                    success = self._run_push_command(
                        cmd_args.get("src", ""),
                        cmd_args.get("dest", "/tmp/")
                    )
                else:
                    self.log.emit(f"   ⚠️ Không hỗ trợ command type: {cmd_type}")
                    success = False
                
                if success:
                    success_count += 1
                else:
                    self.log.emit("❌ Gặp lỗi! Hủy các lệnh tiếp theo.")
                    break
                
                # Update overall progress
                overall_progress = int(idx * 100 / total_commands)
                self.progress.emit(overall_progress)
            
            # Final result
            if success_count == total_commands:
                self.log.emit(f"\n✅ Hoàn thành tất cả {total_commands} lệnh!")
                self.finished.emit(True, f"Thành công: {success_count}/{total_commands}")
            else:
                self.log.emit(f"\n⚠️ Hoàn thành {success_count}/{total_commands} lệnh")
                self.finished.emit(False, f"Thành công: {success_count}/{total_commands}")
                
        except Exception as e:
            self.log.emit(f"❌ Lỗi: {e}")
            self.error.emit(f"Lỗi: {repr(e)}")
    
    def _run_shell_command(self, cmd: str) -> bool:
        """Run adb shell command with timeout, cancel support, and clean process tree termination"""
        if not cmd:
            return False
        
        serial_arg = self._get_serial_arg()
        full_cmd = f"adb {serial_arg} shell {cmd}".strip()
        
        self.log.emit(f"   $ {full_cmd}")
        
        import time
        start_time = time.time()
        timeout = 180  # 3 minutes timeout
        
        try:
            process = self.subprocess.Popen(
                full_cmd,
                shell=True,
                stdout=self.subprocess.PIPE,
                stderr=self.subprocess.STDOUT,
                text=True
            )
            
            output_lines = []
            
            # Non-blocking poll loop to allow cancellation and timeout checks
            try:
                while True:
                    if self._cancel:
                        self.log.emit("   ⚠️ Đang hủy lệnh shell...")
                        self.subprocess.run(f"taskkill /F /T /PID {process.pid}", shell=True, capture_output=True)
                        return False
                    
                    if time.time() - start_time > timeout:
                        self.log.emit(f"   ❌ Timeout ({timeout} giây)")
                        self.subprocess.run(f"taskkill /F /T /PID {process.pid}", shell=True, capture_output=True)
                        return False
                    
                    # Check if process is still running
                    retcode = process.poll()
                    if retcode is not None:
                        break
                    
                    time.sleep(0.5)
                
                # Get all output safely
                stdout, _ = process.communicate()
                if stdout:
                    output_lines.extend(stdout.strip().splitlines())
                    
            except Exception as e:
                # Force kill process tree if an exception occurs
                self.subprocess.run(f"taskkill /F /T /PID {process.pid}", shell=True, capture_output=True)
                raise e
            
            # Output stdout lines
            output = "\n".join(output_lines)
            for line in output_lines:
                line = line.strip()
                if line:
                    self.log.emit(f"   {line}")
            
            # Check for TWRP-specific success/error
            output_lower = output.lower()
            has_error = any(kw in output_lower for kw in [
                "error", "failed", "unable to", "cannot"
            ])
            
            if process.returncode == 0 and not has_error:
                self.log.emit(f"   ✅ Thành công")
                return True
            else:
                self.log.emit(f"   ⚠️ Exit code: {process.returncode}")
                return process.returncode == 0
                
        except Exception as e:
            self.log.emit(f"   ❌ Exception: {e}")
            return False
    
    def _run_push_command(self, src: str, dest: str) -> bool:
        """Run adb push with progress tracking"""
        import os
        
        if not src or not os.path.exists(src):
            self.log.emit(f"   ❌ File không tồn tại: {src}")
            return False
        
        serial_arg = self._get_serial_arg()
        filename = os.path.basename(src)
        dest_file = dest.rstrip('/') + '/' + filename
        
        full_cmd = f'adb {serial_arg} push "{src}" {dest_file}'.strip()
        
        self.log.emit(f"   $ {full_cmd}")
        
        # Get file size for progress
        file_size = os.path.getsize(src)
        file_size_mb = file_size / 1024 / 1024
        self.log.emit(f"   📦 File size: {file_size_mb:.2f} MB")
        
        try:
            import time
            start_time = time.time()
            
            process = self.subprocess.Popen(
                full_cmd,
                shell=True,
                stdout=self.subprocess.PIPE,
                stderr=self.subprocess.STDOUT,
                text=True
            )
            
            # Read output (adb push shows progress)
            # Throttle: chỉ emit log khi phần trăm thay đổi, tránh spam UI
            import re
            _last_pct = -1
            
            for line in iter(process.stdout.readline, ''):
                if self._cancel:
                    self.log.emit("   ⚠️ Đang hủy lệnh push...")
                    self.subprocess.run(f"taskkill /F /T /PID {process.pid}", shell=True, capture_output=True)
                    return False
                
                line = line.rstrip()
                if not line:
                    continue
                
                # Parse progress từ adb push output
                # Format: "file.zip: 50% (123456/246912)"
                match = re.search(r'(\d+)%', line)
                if match:
                    pct = int(match.group(1))
                    # Chỉ emit khi phần trăm thực sự thay đổi
                    if pct != _last_pct:
                        _last_pct = pct
                        self.progress.emit(pct)
                        # Chỉ log mỗi 10% hoặc khi hoàn thành để tránh flood UI
                        if pct % 10 == 0 or pct >= 99:
                            self.log.emit(f"   📤 {pct}%")
                else:
                    # Dòng không phải progress → emit bình thường
                    self.log.emit(f"   {line}")
            
            process.wait()
            
            elapsed = time.time() - start_time
            speed = file_size_mb / elapsed if elapsed > 0 else 0
            
            if process.returncode == 0:
                self.log.emit(f"   ✅ Push thành công ({speed:.2f} MB/s)")
                return True
            else:
                self.log.emit(f"   ❌ Push thất bại (exit code: {process.returncode})")
                return False
                
        except Exception as e:
            self.log.emit(f"   ❌ Exception: {e}")
            return False
    
    @Slot()
    def cancel(self):
        """Request cancel"""
        self.log.emit("🔍 [AdbCommandWorker] Cancel requested")
        self._cancel = True





