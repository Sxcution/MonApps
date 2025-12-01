# Auto Detect - Hướng dẫn sử dụng

## Cách mở Auto Detect

1. Click chuột phải vào bất kỳ dòng nào trong bảng Macro
2. Chọn **"Auto Detect"** trong menu (giữa Keyboard Action và Image)

```
Menu hiển thị:
┌─────────────────────┐
│ Mouse Action        │
│ Keyboard Action     │
│ Auto Detect        │  ← CHỌN CÁI NÀY
├─────────────────────┤
│ Image              ►│
│   Detect image [I]  │
├─────────────────────┤
│ Text               ►│
│   Search Text [T]   │
└─────────────────────┘
```

## Giao diện Dialog

### Tab 1: Hình Ảnh (Mặc định)

```
┌────────────────────────────────────────────────────────────────────┐
│  Auto Detect - Phát hiện tự động                            [✖]    │
├────────────────────────────────────────────────────────────────────┤
│  Auto Detect cho phép quét liên tục nhiều ảnh/text và thực        │
│  hiện hành động tương ứng khi tìm thấy.                            │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  Hình Ảnh  │  Text  │                                        │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │  Thêm nhiều ảnh để quét. Khi tìm thấy ảnh nào, hệ thống    │  │
│  │  sẽ thực hiện hành động tương ứng.                          │  │
│  │                                                              │  │
│  │  ┌─────────────────────────────────────────────────────┐   │  │
│  │  │         + Thêm Ảnh                                   │   │  │
│  │  └─────────────────────────────────────────────────────┘   │  │
│  │                                                              │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Ảnh #1                            [✖ Xóa]           │  │  │
│  │  │  ┌─────────┐  Vùng Tìm: [toàn màn hình ▼] [Define]  │  │
│  │  │  │   ???   │  Độ dung sai: [0 / 255]        [Test]   │  │
│  │  │  │         │  Hành động: [Press Key      ▼]          │  │
│  │  │  │150x150  │  Tham số:   [A                       ]  │  │
│  │  │  └─────────┘  ☑ Grayscale  ☑ Multi-scale            │  │
│  │  │  [Nhập Ảnh]   Status: ✅ Tìm thấy: 100, 200         │  │
│  │  │  [Cắt Ảnh]                                           │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │                                                              │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Ảnh #2                            [✖ Xóa]           │  │  │
│  │  │  ┌─────────┐  Vùng Tìm: [vùng tùy chỉnh ▼] [Define] │  │
│  │  │  │ [IMG]   │  Độ dung sai: [10 / 255]       [Test]   │  │
│  │  │  │         │  Hành động: [Click chuột trái ▼]        │  │
│  │  │  │150x150  │  ☐ Grayscale  ☑ Multi-scale            │  │
│  │  │  └─────────┘  Status:                                 │  │
│  │  │  [Nhập Ảnh]                                           │  │
│  │  │  [Cắt Ảnh]                                            │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ Cài đặt chung: ─────────────────────────────────────────┐  │
│  │  Quét lại mỗi:         [200 ▲▼] ms                       │  │
│  │  Thời gian chờ tối đa: [65535 ▲▼] giây                   │  │
│  │  Nếu hết thời gian chờ: [Tiếp theo  ▼]                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│                                        [ OK ]  [ Hủy ]          │
└──────────────────────────────────────────────────────────────────┘
```

## Các thành phần chính

### 1. Button "Thêm Ảnh"
- Màu xanh dương đậm (#0078D4)
- Thêm 1 item ảnh mới vào danh sách
- Mỗi item có index riêng (Ảnh #1, #2, #3...)

### 2. Mỗi Item Ảnh bao gồm:

#### a) Header
- **Label**: "Ảnh #X" (màu xanh dương)
- **Button Xóa**: Nút đỏ "✖ Xóa" (ẩn nếu chỉ còn 1 ảnh)

#### b) Image Preview (Trái)
- Khung 150x150 pixel
- Hiển thị ảnh đã chọn hoặc placeholder "?"
- 2 button bên dưới:
  - **Nhập Ảnh**: Load từ file (PNG/JPG/BMP)
  - **Cắt Ảnh**: Capture từ màn hình bằng Snipping Tool

#### c) Options (Phải)
1. **Vùng Tìm kiếm**:
   - Dropdown: toàn màn hình / cửa sổ đang focus / vùng tùy chỉnh
   - Button **Define**: Hiện khi chọn "cửa sổ đang focus" hoặc "vùng tùy chỉnh"

2. **Độ dung sai**:
   - SpinBox 0-255
   - Giá trị càng cao = tolerant hơn với sai khác màu sắc

3. **Button Test**:
   - Test tìm ảnh ngay lập tức
   - Hiển thị kết quả: "✅ Tìm thấy: x, y" hoặc "❌ Không tìm thấy!"

4. **Hành động**:
   - Dropdown:
     - Không làm gì
     - Press Key (hiện input cho key: A, D, F...)
     - Click chuột trái
     - Click chuột phải
     - Hold chuột trái (hiện input cho duration ms: 1000)

5. **Tham số**:
   - Input field (ẩn mặc định)
   - Hiện khi chọn "Press Key" hoặc "Hold chuột trái"
   - Nhập key (A, D, F) hoặc duration (1000)

6. **Checkboxes**:
   - **Grayscale**: Tìm ở chế độ đen trắng (nhanh hơn)
   - **Multi-scale**: Tìm ở nhiều tỉ lệ (chậm hơn nhưng chính xác)

7. **Status Label**:
   - Hiển thị kết quả test
   - Màu: xanh (thành công), đỏ (thất bại), xanh dương (đang tìm)

### 3. Cài đặt chung

- **Quét lại mỗi**: Khoảng thời gian giữa các lần quét (ms)
  - Mặc định: 200ms
  - Min: 50ms, Max: 10000ms
  - Giá trị thấp = quét nhanh hơn = CPU cao hơn

- **Thời gian chờ tối đa**: Thời gian tối đa chờ trước khi timeout (giây)
  - Mặc định: 65535 giây (~18 giờ)
  - Min: 1s, Max: 999999s

- **Nếu hết thời gian chờ**: Hành động khi timeout
  - Tiếp theo: Chạy step tiếp theo
  - Bắt đầu: Quay về step đầu tiên
  - Kết thúc: Dừng macro

## Workflow sử dụng

### Bước 1: Thêm ảnh đầu tiên
1. Click **"+ Thêm Ảnh"** (đã có sẵn 1 item mặc định)
2. Click **"Nhập Ảnh"** để chọn file hoặc **"Cắt Ảnh"** để capture
3. Chọn vùng tìm kiếm
4. Điều chỉnh độ dung sai nếu cần
5. Chọn hành động khi tìm thấy
6. Click **"Test"** để thử

### Bước 2: Thêm ảnh thứ 2, 3, 4...
1. Click **"+ Thêm Ảnh"** để thêm item mới
2. Lặp lại như Bước 1
3. Có thể xóa item bằng button **"✖ Xóa"**

### Bước 3: Cấu hình chung
1. Điều chỉnh **"Quét lại mỗi"** (nhanh = 50-100ms, chậm = 500-1000ms)
2. Đặt **"Thời gian chờ tối đa"**
3. Chọn hành động khi timeout

### Bước 4: Lưu
1. Click **"OK"** để lưu
2. Event xuất hiện trong bảng Macro với text: **"Auto Detect (X ảnh)"**

## Ví dụ thực tế: Game Câu Cá

### Mô tả tình huống:
```
1. Màn hình game hiển thị thanh thể lực (HP bar)
2. Khi thể lực giảm → Cần giữ chuột 1 giây
3. Nút "A" xuất hiện → Cần nhấn phím A
4. Nút "D" xuất hiện → Cần nhấn phím D  
5. UI phần thưởng xuất hiện → Nhấn phím F
```

### Cấu hình:

#### Ảnh #1: Thanh thể lực (Đầy)
- **Nhập Ảnh**: Chụp ảnh thanh HP đầy
- **Vùng Tìm**: Vùng tùy chỉnh (chỉ vùng thanh HP)
- **Hành động**: Không làm gì (chỉ detect)

#### Ảnh #2: Thanh thể lực (Giảm)
- **Nhập Ảnh**: Chụp ảnh thanh HP giảm
- **Vùng Tìm**: Vùng tùy chỉnh (cùng vùng)
- **Hành động**: Hold chuột trái
- **Tham số**: 1000 (1 giây)

#### Ảnh #3: Button "A"
- **Nhập Ảnh**: Chụp nút A trên game
- **Vùng Tìm**: Toàn màn hình
- **Hành động**: Press Key
- **Tham số**: A

#### Ảnh #4: Button "D"
- **Nhập Ảnh**: Chụp nút D trên game
- **Vùng Tìm**: Toàn màn hình
- **Hành động**: Press Key
- **Tham số**: D

#### Ảnh #5: UI Phần thưởng
- **Nhập Ảnh**: Chụp nút nhận thưởng
- **Vùng Tìm**: Toàn màn hình
- **Hành động**: Press Key
- **Tham số**: F

#### Cài đặt chung:
- **Quét lại mỗi**: 100ms (quét nhanh)
- **Thời gian chờ tối đa**: 300 giây (5 phút)
- **Nếu hết thời gian**: Tiếp theo

### Kết quả:
Macro sẽ quét liên tục 5 ảnh trên mỗi 100ms. Khi tìm thấy bất kỳ ảnh nào, sẽ thực hiện hành động tương ứng ngay lập tức và tiếp tục quét.

## Tips & Tricks

### 1. Tối ưu tốc độ quét
- Sử dụng **Vùng tùy chỉnh** thay vì toàn màn hình
- Bật **Grayscale** nếu ảnh không cần màu sắc
- Tăng **Quét lại mỗi** lên 200-500ms nếu không cần phản ứng nhanh

### 2. Tăng độ chính xác
- Giảm **Độ dung sai** xuống 0-10 cho ảnh rõ nét
- Tắt **Grayscale** nếu ảnh cần màu sắc
- Bật **Multi-scale** nếu ảnh có thể thay đổi kích thước

### 3. Debug
- Sử dụng button **Test** để kiểm tra từng ảnh
- Quan sát status label: "✅ Tìm thấy" hay "❌ Không tìm thấy"
- Nếu không tìm thấy:
  - Tăng độ dung sai
  - Bật Grayscale
  - Bật Multi-scale
  - Chụp lại ảnh rõ hơn

### 4. Thứ tự ảnh quan trọng
- Ảnh được quét theo thứ tự từ trên xuống
- Đặt ảnh ưu tiên cao ở đầu danh sách
- Ví dụ: Nút "Emergency Stop" nên ở vị trí đầu tiên

### 5. Tránh spam action
- Không đặt **Quét lại mỗi** quá thấp (< 50ms)
- Nếu cần delay giữa các action, thêm step "Wait" vào macro

## Phím tắt

- **Enter**: OK (lưu cấu hình)
- **Esc**: Hủy
- **Tab**: Di chuyển giữa các controls

## Lưu ý quan trọng

⚠️ **Performance**:
- Quét nhiều ảnh = CPU cao
- Khuyến nghị tối đa 5-10 ảnh
- Sử dụng vùng tùy chỉnh để giảm tải

⚠️ **Accuracy**:
- Ảnh càng rõ nét = tìm càng chính xác
- Nên capture ảnh trong điều kiện tương tự (độ sáng, resolution)

⚠️ **Game Compatibility**:
- Một số game chặn screen capture
- Một số game chặn DirectInput
- Test trước khi sử dụng cho tác vụ quan trọng

## Troubleshooting

### Không tìm thấy ảnh:
1. Tăng độ dung sai lên 20-30
2. Bật Grayscale
3. Bật Multi-scale
4. Chụp lại ảnh trong game
5. Kiểm tra vùng tìm kiếm có đúng không

### CPU quá cao:
1. Giảm số lượng ảnh
2. Tăng "Quét lại mỗi" lên 300-500ms
3. Sử dụng vùng tùy chỉnh thay vì toàn màn hình
4. Bật Grayscale

### Hành động không thực hiện:
1. Kiểm tra hành động đã chọn đúng chưa
2. Kiểm tra tham số (key, duration) đã nhập đúng chưa
3. Xem log playback (nút "!" trên toolbar)
4. Chạy lại với quyền Admin

## Tab Text (Sắp tới)

Tab Text sẽ có chức năng tương tự nhưng dùng OCR để tìm text trên màn hình.

**Tính năng dự kiến:**
- Quét nhiều text query
- Fuzzy matching
- Nhiều ngôn ngữ (Tiếng Việt, English, Chinese...)
- Hành động tương tự (click, press key...)

---

**Version**: 1.0  
**Created**: 2025-12-01  
**Author**: AutoKey Development Team

