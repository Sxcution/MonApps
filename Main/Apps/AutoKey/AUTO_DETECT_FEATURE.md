# Auto Detect Feature - Tài liệu kỹ thuật

## Tổng quan
Auto Detect là tính năng phát hiện tự động cho phép quét liên tục nhiều ảnh trên màn hình và thực hiện hành động tương ứng khi tìm thấy. Tính năng này được thiết kế cho các tác vụ phức tạp như tự động hóa game.

## Vị trí trong Menu
Auto Detect được thêm vào menu giữa **Keyboard Action** và **Image**:
- Mouse Action
- Keyboard Action
- **Auto Detect** ← MỚI
- Image
  - Detect image [I]
- Text
  - Search Text [T]

## Cấu trúc Dialog

### Tab 1: Hình Ảnh
Dialog có 2 tab, mặc định hiển thị tab **Hình Ảnh**:

#### Chức năng chính:
1. **Thêm nhiều ảnh**: Cho phép thêm nhiều ảnh detect với button "**+ Thêm Ảnh**"
2. **Mỗi ảnh bao gồm**:
   - Thumbnail preview (150x150)
   - Nút **Nhập Ảnh** (load từ file)
   - Nút **Cắt Ảnh** (capture từ màn hình)
   - **Vùng Tìm**: toàn màn hình / cửa sổ đang focus / vùng tùy chỉnh
   - **Độ dung sai**: 0-255
   - **Hành động** khi tìm thấy:
     - Không làm gì
     - Press Key (A, D, F...)
     - Click chuột trái
     - Click chuột phải
     - Hold chuột trái (với thời gian ms)
   - **Grayscale**: Tìm kiếm ở chế độ đen trắng
   - **Multi-scale**: Tìm kiếm ở nhiều tỉ lệ
   - Nút **Test**: Test tìm ảnh ngay lập tức
   - Nút **✖ Xóa**: Xóa ảnh này (chỉ hiển thị nếu có > 1 ảnh)

#### Layout:
```
+--------------------------------------------------+
| Ảnh #1                                  [✖ Xóa]  |
|                                                  |
| [Thumbnail]    Vùng Tìm: [toàn màn hình] [Define]|
|                Độ dung sai: [0 / 255]    [Test] |
| [Nhập Ảnh]     Hành động: [Press Key]           |
| [Cắt Ảnh]      Tham số: [A]                     |
|                [✓] Grayscale [✓] Multi-scale    |
|                Status: ✅ Tìm thấy: 100, 200     |
+--------------------------------------------------+
```

### Tab 2: Text
Tab Text hiện tại chỉ có placeholder, sẽ phát triển trong tương lai với chức năng OCR tương tự.

### Cài đặt chung
- **Quét lại mỗi**: 200ms (mặc định) - Khoảng thời gian giữa các lần quét
- **Thời gian chờ tối đa**: 65535 giây (mặc định) - Thời gian tối đa chờ trước khi timeout
- **Nếu hết thời gian chờ**: Tiếp theo / Bắt đầu / Kết thúc

## Cấu trúc dữ liệu

### Event Data Structure
```json
{
  "type": "auto_detect",
  "scan_interval": 200,
  "max_duration": 65535,
  "goto_timeout": "Next",
  "image_detects": [
    {
      "image_path": "path/to/image1.png",
      "search_area": "entire screen",
      "custom_region": null,
      "tolerance": 0,
      "grayscale": false,
      "multi_scale": false,
      "action": "press_key",
      "action_param": "A"
    },
    {
      "image_path": "path/to/image2.png",
      "search_area": "custom region",
      "custom_region": {
        "left": 100,
        "top": 200,
        "width": 300,
        "height": 400
      },
      "tolerance": 10,
      "grayscale": true,
      "multi_scale": false,
      "action": "left_click",
      "action_param": ""
    }
  ],
  "time": 0.5
}
```

## File Changes

### 1. Tạo mới: `ui/auto_detect_dialog.py`
**Classes:**
- `ImageDetectItem(QWidget)`: Widget đại diện cho 1 item ảnh detect
  - Chứa preview, controls, test button
  - Signal: `remove_requested` khi click nút xóa
  - Methods: `get_data()`, `set_data(data)`, `test_image_search()`

- `AutoDetectDialog(QDialog)`: Dialog chính
  - Tab widget với 2 tab: Hình Ảnh và Text
  - Quản lý danh sách `image_items`
  - Methods: `add_image_item()`, `remove_image_item()`, `get_data()`, `load_event_data()`

**UI Components:**
- Reuse `StyledComboBox`, `StyledCheckBox`, `ImagePreviewLabel` từ `image_search_dialog.py`
- ScrollArea để chứa nhiều ImageDetectItem
- Button "**+ Thêm Ảnh**" để thêm item mới

### 2. Cập nhật: `ui/main_window.py`

#### Thêm menu item:
```python
def show_setup_menu(self, index):
    # ...
    auto_detect_action = menu.addAction("Auto Detect")
    # ...
    elif action == auto_detect_action:
        self.open_auto_detect_dialog(index.row())
```

#### Thêm handler:
```python
def open_auto_detect_dialog(self, row):
    from ui.auto_detect_dialog import AutoDetectDialog
    event = self.recorded_events[row]
    dialog = AutoDetectDialog(self, event)
    if dialog.exec():
        new_data = dialog.get_data()
        self.update_event(row, new_data)
```

#### Render trong table:
```python
# Action column
elif event['type'] == 'auto_detect':
    image_count = len(event.get('image_detects', []))
    action_text = f"Auto Detect ({image_count} ảnh)"

# Details column
elif event['type'] == 'auto_detect':
    scan_interval = event.get('scan_interval', 200)
    max_duration = event.get('max_duration', 65535)
    image_count = len(event.get('image_detects', []))
    details = f"Quét {image_count} ảnh mỗi {scan_interval}ms, max {max_duration}s"
```

### 3. Cập nhật: `core/player.py`

#### Thêm event handler:
```python
def execute_event(self, event):
    # ...
    elif etype == 'auto_detect':
        return self.handle_auto_detect(event, current_idx)
```

#### Implement `handle_auto_detect()`:
**Logic:**
1. Lấy danh sách `image_detects` từ event
2. Loop liên tục trong khoảng thời gian `max_duration`:
   - Quét từng ảnh trong danh sách
   - Nếu tìm thấy ảnh:
     - Thực hiện hành động tương ứng (press key / click / hold)
     - Log kết quả
     - Chờ `scan_interval` rồi tiếp tục quét
   - Nếu không tìm thấy: Tiếp tục quét
3. Khi hết timeout: Return goto_timeout

**Actions supported:**
- `press_key`: Nhấn phím (sử dụng DirectInput cho game)
- `left_click`: Click chuột trái tại center của ảnh
- `right_click`: Click chuột phải tại center của ảnh
- `hold_left`: Giữ chuột trái trong X ms

### 4. Cập nhật: `naming_registry.json`
Thêm các UI element IDs:
- `UI_AUTO_DETECT_DIALOG`: Tab widget, buttons, spinboxes
- `UI_IMAGE_DETECT_ITEM`: Preview, combo boxes, inputs cho mỗi item

### 5. Cập nhật: `project_structure.md`
Thêm `auto_detect_dialog.py` vào danh sách file UI

## Use Case Example: Game Câu Cá

### Scenario:
1. Thanh thể lực giảm → UI biến mất
2. Nút "A" xuất hiện → Press A
3. Nút "D" xuất hiện → Press D
4. UI phần thưởng xuất hiện → Press F

### Cấu hình:
**Auto Detect với 4 ảnh:**

1. **Ảnh #1: Thanh thể lực**
   - Vùng: vùng tùy chỉnh (vùng thanh thể lực)
   - Hành động: Hold chuột trái (1000ms)

2. **Ảnh #2: Nút A**
   - Vùng: toàn màn hình
   - Hành động: Press Key (A)

3. **Ảnh #3: Nút D**
   - Vùng: toàn màn hình
   - Hành động: Press Key (D)

4. **Ảnh #4: UI phần thưởng**
   - Vùng: toàn màn hình
   - Hành động: Press Key (F)

**Cài đặt chung:**
- Quét lại mỗi: 100ms (quét nhanh)
- Thời gian chờ tối đa: 300 giây
- Nếu hết thời gian: Tiếp theo

### Flow thực thi:
```
Loop (max 300s):
  1. Quét 4 ảnh
  2. Nếu tìm thấy bất kỳ ảnh nào:
     - Thực hiện hành động tương ứng
     - Log result
  3. Chờ 100ms
  4. Lặp lại
```

## Technical Notes

### Image Detection
- Sử dụng `utils.image_finder.find_image_on_screen()`
- Hỗ trợ region (entire screen / focused window / custom)
- Confidence = 1.0 - ((tolerance + 1) / 400.0)
- Grayscale mode: Tăng tốc độ tìm kiếm
- Multi-scale: Tìm kiếm ở nhiều kích thước

### Performance
- Scan interval tối thiểu: 50ms
- Mỗi lần quét sẽ check tất cả ảnh theo thứ tự
- Khi tìm thấy ảnh đầu tiên → Thực hiện action → Chờ interval → Quét lại
- Không dừng lại sau khi tìm thấy (continuous detection)

### Snipping Tool Integration
- Mỗi ImageDetectItem có thể mở Snipping Tool độc lập
- Dialog được minimize khi snipping
- Main window được minimize khi snipping
- Restore UI sau khi snipping xong

### Signal Handling
- `remove_requested(object)`: Khi user click xóa ảnh
- Dialog sử dụng `accept()` và `reject()` signals chuẩn
- Integration với main_window qua `update_event(row, new_data)`

## Testing Checklist

✅ Dialog mở được từ menu "Auto Detect"
✅ Tab Hình Ảnh hiển thị đúng
✅ Button "Thêm Ảnh" tạo item mới
✅ Button "Xóa" xóa item (không cho xóa item cuối)
✅ Nhập ảnh từ file
✅ Cắt ảnh từ màn hình
✅ Define vùng tùy chỉnh
✅ Test tìm ảnh hoạt động
✅ Combobox hành động hiển thị input tham số đúng
✅ Dialog lưu data đúng format
✅ Event hiển thị trong table với text "Auto Detect (X ảnh)"
✅ Player thực thi auto_detect event
✅ Press key hoạt động
✅ Click chuột hoạt động
✅ Hold chuột hoạt động
✅ Timeout goto logic hoạt động

## Future Enhancements

### Tab Text (Chưa implement)
- OCR continuous detection
- Tương tự như tab Image nhưng dùng text matching
- Hỗ trợ fuzzy matching
- Hỗ trợ nhiều ngôn ngữ

### Advanced Features
- Priority system cho các ảnh (ảnh nào detect trước)
- Cooldown time cho mỗi action (tránh spam)
- Combo detection (cần tìm thấy 2+ ảnh cùng lúc)
- Conditional chains (nếu thấy A mà không thấy B thì...)
- Export/Import detection profiles

## Naming Convention

### UI Element IDs (English)
- `tab_widget`: Tab container
- `tab_image_detect`: Image tab
- `btn_add_image`: Add image button
- `container_image_items`: Items container
- `spin_scan_interval`: Scan interval spinbox
- `combo_action`: Action combobox

### Comments (Vietnamese)
```python
# btn_add_image : Nút thêm ảnh mới
# tab_image_detect : Tab Hình Ảnh
# img_preview : Preview ảnh
```

## Dependencies
- PySide6 (Qt6)
- OpenCV (cv2) - via `utils.image_finder`
- PIL (Pillow) - for image handling
- pynput - for mouse/keyboard control
- utils.direct_input - for game input simulation

