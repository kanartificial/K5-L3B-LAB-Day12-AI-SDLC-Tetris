# Changelog

Ghi theo từng phase. Phiên bản phát hành **v1.0.0** = Phase 4 (Test Contract v1.3).

## [v1.0.0 — Phase 4: Phát hành] (Contract v1.3) — 2026-11-21

### Contract v1.3
- `contract_version: "1.3"`. Khai ở gốc `game.contract.json`: `bench_cmd: "python3 -m chonoi.bench"`, `soak_cmd: "python3 -m chonoi.soak"`, `extensions: []`.
- **Gameplay, tuning, kho và JSONL giữ nguyên v1.2.** `is_v12()` nhận cả `"1.2"` và `"1.3"`. Không có breaking change cho fixture hay file kho.

### Mới
- **Benchmark có render** (`chonoi/bench.py`): mở Chrome/Chromium/Edge headless ở cửa sổ 1280×720 trên cảnh buổi sáng lõi (độ tươi, cá bơi, Cá Sấu, Út Sen đứng yên ở bến), làm nóng 3 s rồi đo. Xuất `avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`.
- **Soak headless** (`chonoi/soak.py` + bot tất định `chonoi/bot.py`): chạy N Ngày trong một tiến trình (gather → quan → shop), xuất `days`, `days_completed`, `crashes`, `results[]`, `duration_s`.
- **Cảnh báo dễ nhận biết** (UI): `🫧 SẮP HẾT OXY` khi oxy < 25 % lúc lặn (trước đây chỉ báo khi đã hết), `🐊 THỦY QUÁI GẦN!` kèm ô “!” trên Cá Sấu, `😠 KHÁCH SẮP GIẬN` mới thêm (banner + ô “!” + chữ ở bàn).
- **Chế độ tương phản cao**: phím `H`, nút “TƯƠNG PHẢN CAO” hoặc `?hc=1`. Nhớ lựa chọn trong trình duyệt.
- `?play=1` vào thẳng cảnh, bỏ menu (dùng cho bench / chơi thử tự động).
- README hướng dẫn chạy từ clone sạch bằng 3 lệnh. Thêm LICENSE (MIT cho phần nhóm viết) và CREDITS đầy đủ. Thêm release notes.

### Sửa
- `day` crash ở **Ngày 6** (`KeyError 6`): kế hoạch D1–D5 nay lặp ở Ngày 6–10 (`DaySession._plan`). Headless `--days` vẫn giới hạn 1..5 theo Test Contract.
- `chonoi.live` không còn in traceback `ConnectionResetError` khi người chơi đóng tab.

### Test & công cụ
- `tests/test_contract_p4.py` (10 test): manifest v1.3, soak qua `soak_cmd` (6 Ngày, lặp kế hoạch, tất định, mã 2), công thức avg / 1% low, chạy thật `bench_cmd` (skip khi máy không có Chrome).
- `tools/playtest_warnings.py` + `tools/ui_warnings.mjs`: chơi thử tự động 3 cảnh báo ở chế độ thường và tương phản cao qua Chrome DevTools Protocol, chụp ảnh.
- Điều kiện chạy test P2/P3 và tool nhận `1.3` (dạng `in (...)`, không dùng `==`, theo hành động retro P3).

---

## [v1.2 — Phase 3: Change Request “Mùa Nước Nổi”] — 2026-11-21

### Breaking Changes (khi bật `contract_version: "1.2"`)
- **Kho đếm → Kho cá thể (`inventory` / `hold` / `stock`):**
  - Schema cũ (`v1.0`/`v1.1`): `{"items":{"ca_loc":1,"bong_sung":2}}`, `gather.hold: ["ca_loc"]`, `quan.stock: {"ca_loc":1}`.
  - Schema mới (`v1.2`): `{"items":[{"id":"I1","kind":"ca_loc","fresh":100},{"id":"I2","kind":"bong_sung","fresh":97.5}]}`, `gather.hold` và `quan.stock` là mảng cá thể `{id, kind, fresh}`. Kho rỗng là `{"items":[]}`.
  - File kho đếm hoặc schema sai ở v1.2 trả **mã thoát `2`**.
- **Giữ chỗ theo lượng → Giữ chỗ theo `id`:**
  - `customers[].reserved` đổi từ map `{kind: count}` sang mảng `id` cá thể `["I1", ...]`.
- **Sự kiện & trường dữ liệu thay đổi:**
  - Thêm event `spoiled` (`{"item_id", "kind", "location": "hold"|"stock"}`) phát đúng 1 lần theo `id` khi `fresh` đi từ `>= 30` xuống `< 30`.
  - `monster_hit.data.lost` và `faint.data.lost` đổi từ mảng `kind` sang mảng cá thể `{id, kind, fresh}` theo thứ tự LIFO.
  - `cook_started.data.items` đổi sang mảng cá thể sắp theo `(kind, id)`.
  - `base_price` chốt theo độ tươi trung bình khi bắt đầu nấu: `floor(giá niêm yết × trung bình fresh / 100)`.
- **Cấu hình mới trong `game.contract.json`:** thêm `tuning.freshness = {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}`.

### Hướng dẫn cập nhật fixture cũ (`v1.1 → v1.2`)
1. File kho (`--inventory`): đổi `{"items":{"ca_loc":1}}` → `{"items":[{"id":"I1","kind":"ca_loc","fresh":100}]}`.
2. Scenario `gather.hold`: đổi `["ca_loc","bong_sung"]` → `[{"id":"I1","kind":"ca_loc","fresh":100},{"id":"I2","kind":"bong_sung","fresh":100}]`.
3. Scenario `quan.stock`: đổi `{"ca_loc":1}` → `[{"id":"I1","kind":"ca_loc","fresh":100}]`.
4. Scenario `quan.customers[].reserved`: đổi `{"ca_loc":1}` → `["I1"]` (hoặc bỏ trống để tự cấp theo tươi nhất rồi `id` nhỏ).

### Trạng thái tích hợp
- **Đã bật `contract_version: "1.2"` trên `main`.** Adapter (`chonoi/inventory.py`, `scenario.py`, `contract.py`, `headless.py`, `live.py`), Gather, Quán, `runner.py` và `shop.py` cùng chạy schema cá thể (ADR-0001).
- `QuanSim` nhận `contract_version` và chỉ bật độ tươi ở v1.2. Trước đây nó bật theo sự có mặt của `tuning.freshness`, nên khi manifest còn 1.1 thì `main` đỏ 18 test.

### Sửa lỗi tích hợp khi bật v1.2
- Quán từ chối file kho v1.2 hợp lệ (và `day` có hàng thoát mã 2) do `fresh` dạng `Fraction` từ adapter. `_load_fresh_stock` nay nhận `Fraction`.
- `day` crash khi chuyển quán → Shop vì Shop nhận list id thay vì cá thể. Nay truyền `sort_by_id(stock.values())`.

### Test & công cụ
- Thêm `tests/test_contract_p3.py` (14 test hộp đen qua CLI): ví dụ ngưỡng 30, smoke bàn giao 2 tiến trình, round-trip file sát ngưỡng, mã 2, giữ nguyên đích khi chạm `--ticks`, giá theo tươi, giữ lại / `unfulfillable`, `day` → Shop → Ngày 2.
- Thêm `tools/smoke_p3.py` (`threshold | integration | reject | day | regression | all`), ghi bằng chứng vào `docs/proof/phase-3/`.
- `tools/check_determinism.py` chọn fixture theo `contract_version` và thêm kịch bản `day_hold_handoff`. `stock` v1.2 phải sắp theo id. Snapshot đầu được phép đứng sau các event tick 0 (thứ tự `day` từ P2).
- `tools/smoke_p2.py day` chấp nhận cả 1.1 và 1.2.
- **Test cũ đổi theo luật mới:** fixture P1/P2 chuyển sang kho cá thể và vẫn so theo kind/số lượng. 2 test thanh toán đổi giá 60 → 59 (giá theo tươi). `test_contract_p2` chạy ở cả 1.1/1.2 (trước đó tự skip 32 test). Chi tiết lý do ở `docs/verification/phase-3.md`.

---

## [v1.1 — Phase 2: Một ngày ở chợ nổi] — 2026-11-21
- Nâng bộ số chuẩn v1.1: 6 nguyên liệu (`+ca_keo`, `+keo_neo`), 6 món, `N1–N6`, `B1–B2`, `T1–T4`.
- Thêm đàn cá bơi (`1.5 m/s`, đổi hướng tick 120, phản xạ mép/góc) và sinh theo lịch `360·k` (trần 12).
- Thêm Cá Sấu Năm Chèo (`M1` Ngày 1+, `M2` Ngày 3+), bất tử `90` tick, rơi `floor(hold/2)` LIFO.
- Thêm `--mode day --days 1..5`, `day_plan` D1–D5, `ShopSim` (`oxygen`/`hp`), `pause`/`resumed` ở cả 3 mode.

## [v1.0 — Phase 1] — 2026-11-21
- Ra mắt vòng chơi lõi 2 buổi `gather` & `quan` nối nhau qua file kho đếm JSON nguyên tử.
