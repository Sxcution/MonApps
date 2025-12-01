# BÁO CÁO VẤN ĐỀ: Drag & Drop Mất Dòng trong AutoKey

## 📋 TÓM TẮT VẤN ĐỀ

Khi kéo thả (drag & drop) các hàng trong table chính (Macro Steps Table), hàng bị kéo bị mất hoàn toàn sau khi thả. Hàng đích vẫn giữ nguyên như cũ.

**Ví dụ:** Kéo hàng 1 đến hàng 2 → Hàng 1 bị removed hoàn toàn, hàng 2 vẫn giữ như cũ.

## 🔍 PHÂN TÍCH TỪ DEBUG LOGS

Từ console output, phát hiện các vấn đề sau:

### 1. dropEvent được gọi nhiều lần
- dropEvent được gọi nhiều lần liên tiếp
- Mỗi lần có insert rồi remove
- `moveRow` không được gọi (hoặc được gọi nhưng không hoạt động đúng)

### 2. Logic tính toán sai
- Dòng 37: "No move needed (same position)" khi source_row=0, drop_row=1
- Logic adjust `drop_row` trước khi check, dẫn đến nhận định sai

### 3. Model tự động xử lý drag & drop
- Sau khi `dropEvent` đã `accept()`, model vẫn tự động xử lý drag & drop
- Dẫn đến remove row thêm lần nữa

### 4. on_rows_removed rebuild recorded_events
- `on_rows_removed` trong `main_window.py` được gọi và rebuild `recorded_events`
- Có thể làm mất dữ liệu nếu event_id không được tìm thấy

## 📁 CÁC FILE LIÊN QUAN

### 1. `ui/steps_interface.py`
- **MacroStepsModel**: Custom model cho table chính
  - `moveRow()`: Override để xử lý move rows
  - `dropMimeData()`: Return False để ngăn default behavior
  
- **MacroStepsTableView**: Custom QTableView cho table chính
  - `dropEvent()`: Override để xử lý drag & drop thủ công
  - Logic tính toán drop_row và gọi model.moveRow()

- **SavedMacrosModel**: Custom model cho saved macros table
- **SavedMacrosTableView**: Custom QTableView cho saved macros table

### 2. `ui/main_window.py`
- **on_rows_removed()**: Rebuild `recorded_events` list sau khi rows bị remove
  - Tạo event_map từ recorded_events
  - Rebuild new_events từ model items
  - Có thể làm mất dữ liệu nếu event_id không được tìm thấy

### 3. `ui/styles.py`
- Styling cho tables (không liên quan trực tiếp đến bug)

## 🐛 VẤN ĐỀ CỤ THỂ

### Vấn đề 1: Logic tính toán drop_row sai
**Vị trí:** `MacroStepsTableView.dropEvent()` dòng 155-161

**Code hiện tại:**
```python
# If moving down, adjust destination
if source_row < drop_row:
    drop_row -= 1  # Adjust because we'll remove source first

# Only move if different position
if source_row != drop_row:
```

**Vấn đề:** 
- Khi source_row=0, drop_row=1, sau khi adjust drop_row=0
- Code nghĩ không cần move (source_row == drop_row)
- Nhưng thực tế cần move từ 0 → 1

**Đã sửa:** Check `source_row != drop_row` TRƯỚC khi adjust

### Vấn đề 2: Model vẫn tự động xử lý sau dropEvent
**Vị trí:** `MacroStepsModel` thiếu `dropMimeData()`

**Vấn đề:**
- Sau khi `dropEvent` đã `accept()`, QStandardItemModel vẫn tự động xử lý drag & drop
- Dẫn đến remove row thêm lần nữa

**Đã sửa:** Thêm `dropMimeData()` return False để ngăn default behavior

### Vấn đề 3: on_rows_removed làm mất dữ liệu
**Vị trí:** `main_window.py` dòng 479-499

**Vấn đề:**
- Khi drag & drop, `on_rows_removed` được gọi nhiều lần
- Mỗi lần rebuild `recorded_events`, có thể làm mất dữ liệu nếu event_id không được tìm thấy

**Cần kiểm tra:** 
- Event_id có được lưu đúng trong items không?
- Logic rebuild có đúng không?

## 🔧 CÁC THAY ĐỔI ĐÃ THỰC HIỆN

### 1. Tạo custom models
- `MacroStepsModel`: Custom model cho table chính
- `SavedMacrosModel`: Custom model cho saved macros table

### 2. Tạo custom table views
- `MacroStepsTableView`: Custom QTableView cho table chính
- `SavedMacrosTableView`: Custom QTableView cho saved macros table

### 3. Override methods
- `moveRow()`: Xử lý move rows với debug logs
- `dropEvent()`: Xử lý drag & drop thủ công
- `dropMimeData()`: Ngăn default behavior

### 4. Thêm debug logs
- Debug logs chi tiết trong tất cả các methods liên quan
- Prefix `[MAIN TABLE]` để phân biệt với saved table

## 📊 DEBUG LOGS MẪU

```
🔍 DEBUG [MAIN TABLE]: dropEvent called
🔍 DEBUG [MAIN TABLE]: Before drop - total rows: 4
🔍 DEBUG [MAIN TABLE]: Drop position - row: 1
🔍 DEBUG [MAIN TABLE]: Selected rows to move: [0]
🔍 DEBUG [MAIN TABLE]: No move needed (same position)  ← VẤN ĐỀ Ở ĐÂY
🔍 DEBUG [MAIN TABLE]: After drop - total rows: 4
🔍 DEBUG [MAIN TABLE]: Rows ABOUT TO BE removed 0-0  ← Model vẫn tự động remove
```

## 🎯 HƯỚNG GIẢI QUYẾT ĐỀ XUẤT

### Giải pháp 1: Sửa logic tính toán drop_row
- Check `source_row != drop_row` TRƯỚC khi adjust
- Chỉ adjust khi thực sự cần move

### Giải pháp 2: Ngăn model xử lý drag & drop
- Override `dropMimeData()` return False
- Xử lý hoàn toàn trong `dropEvent()`

### Giải pháp 3: Tạm thời disconnect signals
- Disconnect `rowsRemoved` signal trước khi moveRow
- Reconnect sau khi moveRow xong
- Tránh `on_rows_removed` được gọi nhiều lần

### Giải pháp 4: Kiểm tra event_id
- Đảm bảo event_id được lưu đúng trong items
- Kiểm tra logic rebuild trong `on_rows_removed`

## 📝 CÁC BƯỚC TIẾP THEO

1. **Test lại với code đã sửa**
   - Kiểm tra xem `moveRow` có được gọi không
   - Kiểm tra xem còn remove row thừa không

2. **Nếu vẫn mất dòng:**
   - Kiểm tra logic trong `moveRow()` - có thể QStandardItemModel.moveRow() có bug
   - Implement moveRow thủ công (remove + insert)

3. **Nếu moveRow không được gọi:**
   - Kiểm tra xem `dropMimeData` có ngăn được default behavior không
   - Có thể cần override thêm methods khác

4. **Kiểm tra on_rows_removed:**
   - Đảm bảo event_id được lưu đúng
   - Có thể cần tạm thời disable `on_rows_removed` khi drag & drop

## 🔗 TÀI LIỆU THAM KHẢO

- Qt Documentation: QStandardItemModel.moveRow()
- Qt Documentation: QTableView drag & drop
- Stack Overflow: QTableView InternalMove drag drop issues

## 📅 NGÀY TẠO BÁO CÁO

2024-12-19

## 👤 NGƯỜI XỬ LÝ

AI Assistant (Auto)

