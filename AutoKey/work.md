# Work Plan: 3D Game Optimization & Large File Handling

## Mục tiêu
Record/Playback mượt cho game 3D + xử lý file lớn (100k+ events) không lag

---

## Hạng mục 1: Relative Mouse Delta cho 3D ⏳

### Tasks
- [ ] Tạo `utils/mouse_backend.py` với SendInput relative delta
- [ ] Implement auto-detect 2D/3D mode (cursor lock, raw input, clipcursor)
- [ ] Add Force UI / Force 3D options
- [ ] Fixed tick ≥240Hz playback (configurable)
- [ ] Coalesce delta khi trễ

### Files
- `utils/mouse_backend.py` (NEW)
- `core/recorder.py` (MODIFY)
- `core/player.py` (MODIFY)
- `ui/mouse_dialog.py` (ADD OPTIONS)

### Test
- [ ] Test trong game 3D: spin 360°
- [ ] Micro-flick: sai lệch góc ≤±10%
- [ ] No stutter/jitter

---

## Hạng mục 2: High-Precision Scheduler ⏳

### Tasks
- [ ] Tạo `utils/scheduler.py`
- [ ] sleep-then-spin với busy_margin_ms (default 2ms)
- [ ] Drift logging mỗi giây
- [ ] Configurable từ settings

### Files
- `utils/scheduler.py` (NEW)
- `core/player.py` (MODIFY)
- `ui/settings_dialog.py` (ADD TAB)

### Test
- [ ] 120s playback: drift ≤120ms (≤1ms/s)
- [ ] Log drift: tổng, max, coalesce count

---

## Hạng mục 3: Throttle & Resample Recording ⏳

### Tasks
- [ ] Record delta (dx,dy) + perf_counter timestamp
- [ ] Throttle: |dx|+|dy| ≥5px OR ≥8ms
- [ ] Resample về fixed tick (≥240Hz)
- [ ] Key press: down + duration + up (no spam)

### Files
- `core/recorder.py` (MAJOR MODIFY)

### Test
- [ ] Record 60s game → check event count
- [ ] Replay: smooth camera movement

---

## Hạng mục 4: New File Format (AKM v2) ⏳

### Tasks
- [ ] Tạo `utils/akm_format.py`
- [ ] Header JSON: version, tick_hz, profile, offsets
- [ ] Events: MessagePack/JSONL + gzip/zstd
- [ ] Type mapping: byte codes
- [ ] Timestamp: int64 microseconds
- [ ] Index keyframes mỗi 5000 events

### Files
- `utils/akm_format.py` (NEW)
- `ui/main_window.py` (MODIFY save/load)

### Test
- [ ] Save 100k events → file size
- [ ] Load speed < 1s
- [ ] Export/Import JSON cũ vẫn work

---

## Hạng mục 5: Streaming I/O Player ⏳

### Tasks
- [ ] Đọc file theo chunk (1-5MB)
- [ ] Parse streaming vào queue
- [ ] Backpressure control
- [ ] Seek với index keyframes

### Files
- `core/player.py` (MAJOR REFACTOR)
- `utils/stream_reader.py` (NEW)

### Test
- [ ] Play 100k events: RAM < 150MB
- [ ] Seek to middle: < 0.5s

---

## Hạng mục 6: UI Virtualization ⏳

### Tasks
- [ ] List virtualized: batch 500-1000
- [ ] Background import với progress
- [ ] Search/filter không quét full sync

### Files
- `ui/main_window.py` (MAJOR REFACTOR)
- `ui/virtual_table.py` (NEW)

### Test
- [ ] 100k events: UI không freeze
- [ ] Scroll ≥60 FPS
- [ ] Search responsive

---

## Hạng mục 7: Config & Compatibility ⏳

### Tasks
- [ ] Auto-detect file format (.json vs .akm)
- [ ] Legacy file streaming read
- [ ] Save As convert old→new
- [ ] Settings expose: tick_hz, busy_margin, thresholds, gain

### Files
- `ui/settings_dialog.py` (NEW TAB)
- `utils/config.py` (NEW)

### Test
- [ ] Load old .json → works
- [ ] Save As .akm → converts
- [ ] Settings persist

---

## Hạng mục 8: Performance Benchmarks ⏳

### Tiêu chí (BẮT BUỘC ĐẠT)
- [ ] 100k events: mở < 1s
- [ ] 100k events: RAM < +150MB
- [ ] UI scroll ≥60 FPS
- [ ] 120s play: drift ≤120ms
- [ ] 3D spin 360°: góc ±5-10%
- [ ] No stutter

### Files
- `tests/benchmark.py` (NEW)
- `README.md` (UPDATE)

---

## Current Status

**Đang làm:** Hạng mục 1 - Relative Mouse Delta

**Next:** Test H1 → H2 → Test H2 → ...

**Backup:** Created at start
