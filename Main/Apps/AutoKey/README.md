# AutoKey - Macro Recorder & Player

Ứng dụng ghi và phát lại macro cho Windows, hỗ trợ DirectInput cho game.

## ✨ Tính năng

### Core Features
- ⌨️ **Ghi/phát keyboard & mouse** - Hỗ trợ DirectInput cho game
- 🖼️ **Image Detection** - Tìm và click vào ảnh trên màn hình
- 📝 **Text Search** - OCR để tìm text (Windows OCR / EasyOCR)
- 🤖 **Auto Detect** - Quét liên tục nhiều ảnh và thực hiện action tương ứng
- 🎯 **Goto Logic** - Nhảy đến step bất kỳ dựa trên điều kiện
- ⚡ **Hotkey Support** - Ghi/phát nhanh bằng phím tắt

### Advanced
- 🎮 Mouse modes: Absolute / Relative / Delta
- 🔄 Loop: Count-based hoặc Duration-based
- 📊 Playback overlay với progress bar
- 💾 Lưu/Load macro dạng JSON
- 🎨 Modern UI với PySide6-Fluent-Widgets

## 📋 Yêu cầu

### Python
- Python 3.11+
- PySide6
- PySide6-Fluent-Widgets
- pynput
- opencv-python
- pywin32

### Cài đặt
```bash
pip install PySide6 PySide6-Fluent-Widgets pynput opencv-python pywin32
```

## 🚀 Sử dụng

### Chạy ứng dụng
```bash
python main.py
```

hoặc

```bash
run.bat
```

### Hotkeys mặc định
- **F9**: Bắt đầu ghi
- **F10**: Dừng ghi
- **F11**: Phát/Dừng macro

## 📁 Cấu trúc dự án

```
AutoKey/
├── main.py                 # Entry point
├── naming_registry.json    # UI naming convention
├── project_structure.md    # Project documentation
│
├── core/                   # Core logic
│   ├── recorder.py         # Ghi macro
│   └── player.py           # Phát macro
│
├── ui/                     # Giao diện
│   ├── main_window.py      # Main window
│   ├── steps_interface.py  # Steps table
│   ├── auto_detect_dialog.py    # Auto Detect dialog
│   ├── image_search_dialog.py   # Image search
│   ├── settings_dialog.py       # Settings
│   └── ...
│
└── utils/                  # Utilities
    ├── direct_input.py     # DirectInput cho game
    ├── image_finder.py     # OpenCV image matching
    ├── snipping_tool.py    # Screen capture
    └── ...
```

## 🎯 Auto Detect Feature

Auto Detect cho phép quét liên tục nhiều ảnh và thực hiện hành động tương ứng.

### Use Case: Game Câu Cá
```
Ảnh #1: Nút A → Press A
Ảnh #2: Nút D → Press D  
Ảnh #3: Thanh HP giảm → Hold chuột 1s
Ảnh #4: Bảng thưởng → Press F → Goto Start (quay lại câu tiếp)
```

### Actions hỗ trợ
- **Press Key**: Nhấn phím (A, D, F...)
- **Key Down**: Giữ phím X ms rồi thả (A:1000)
- **Click**: Left/Right click tại vị trí ảnh
- **Hold**: Giữ chuột trái X ms

### Goto Options
- **Không làm gì**: Tiếp tục quét
- **Tiếp theo**: Chuyển step tiếp theo
- **Bắt đầu**: Quay lại step 1
- **Kết thúc**: Dừng macro
- **Chuyển Đến**: Nhảy đến step X

Chi tiết: [AUTO_DETECT_FEATURE.md](AUTO_DETECT_FEATURE.md)

## 📝 Naming Convention

Tất cả UI elements và config keys được define trong `naming_registry.json`:
- **Code/IDs**: English (snake_case)
- **Comments**: Vietnamese (bilingual)
- **UI Text**: Vietnamese

Ví dụ:
```python
# btn_add_image : Nút thêm ảnh mới
self.btn_add_image = QPushButton("+ Thêm Ảnh")
```

## 🔧 Development

### Coding Rules
1. UI thread chỉ vẽ & nhận event
2. I/O và CPU nặng → worker thread/process
3. Mọi thay đổi file → kill Python và restart
4. Không commit khi chưa test

### Files không push lên Git
- `Save/` - Macro đã lưu của user
- `captures/` - Ảnh đã cắt
- `*.log` - Log files
- `__pycache__/` - Python cache

## 📚 Documentation

- [AUTO_DETECT_FEATURE.md](AUTO_DETECT_FEATURE.md) - Technical docs
- [AUTO_DETECT_UI_GUIDE.md](AUTO_DETECT_UI_GUIDE.md) - User guide
- [BAO_CAO_DRAG_DROP.md](BAO_CAO_DRAG_DROP.md) - Drag & drop issues
- [project_structure.md](project_structure.md) - Project structure

## 🐛 Known Issues

### Drag & Drop
- Custom model với `moveRow()` để tránh mất dòng
- Chi tiết: [BAO_CAO_DRAG_DROP.md](BAO_CAO_DRAG_DROP.md)

### Game Compatibility
- Một số game chặn DirectInput
- Một số game chặn screen capture
- Test trước khi sử dụng

## 📄 License

MIT License

## 👤 Author

MonSoft - AutoKey Development Team

---

**Version**: 1.0  
**Created**: 2024-12-01  
**Last Updated**: 2024-12-01

