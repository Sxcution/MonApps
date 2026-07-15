# Work Log / Nhật ký làm việc

## 2026-07-13

- **11:48**: Phân tích nguyên nhân MonApp bị đơ (Not Responding) khi chạy ADB tự động.
- **11:49**: Xác định 2 nguyên nhân chính:
  1. **Blocking `.wait()` trên UI thread**: 6 chỗ gọi `self.multi_device_worker.wait()` + 3 chỗ gọi `self._file_import_thread.wait()` chặn cứng giao diện.
  2. **Signal flooding từ `adb push`**: `self.log.emit()` được gọi hàng nghìn lần/giây cho mỗi dòng progress output → quá tải QTextEdit rendering.
- **11:50**: Fix `worker_file_import.py` - Thêm throttling cho `_run_push_command()`: chỉ emit progress signal khi % thay đổi, chỉ log text mỗi 10%.
- **11:52**: Fix `ModAndroid.pyw`:
  - 6 chỗ `multi_device_worker.wait()` → thay bằng guard: warn + return early nếu worker đang chạy (không block UI).
  - 3 chỗ `_file_import_thread.wait()` → thêm timeout 3000ms: `.wait(3000)` thay vì chặn vô thời hạn.
- **11:52**: Lưu ý quan trọng: **TUYỆT ĐỐI KHÔNG gọi `.wait()` không timeout trên main/UI thread trong Qt** — đây là nguyên nhân #1 gây Not Responding.
