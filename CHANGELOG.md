# Changelog

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
- Đã hoàn thiện adapter chọn schema theo `contract_version` (`chonoi/inventory.py`, `scenario.py`, `contract.py`, `headless.py`, `live.py`), độ tươi & cá thể trong `chonoi/sim/gather.py`, `chonoi/sim/shop.py`, `chonoi/runner.py` và 10 test v1.2 trong `tests/test_gather_p3.py` (ADR-0001).
- Giữ `contract_version: "1.1"` trên `main` cho đến khi `chonoi/sim/quan.py` (`AC-P3-03`) hoàn tất để `main` luôn xanh.

---

## [v1.1 — Phase 2: Một ngày ở chợ nổi] — 2026-11-21
- Nâng bộ số chuẩn v1.1: 6 nguyên liệu (`+ca_keo`, `+keo_neo`), 6 món, `N1–N6`, `B1–B2`, `T1–T4`.
- Thêm đàn cá bơi (`1.5 m/s`, đổi hướng tick 120, phản xạ mép/góc) và sinh theo lịch `360·k` (trần 12).
- Thêm Cá Sấu Năm Chèo (`M1` Ngày 1+, `M2` Ngày 3+), bất tử `90` tick, rơi `floor(hold/2)` LIFO.
- Thêm `--mode day --days 1..5`, `day_plan` D1–D5, `ShopSim` (`oxygen`/`hp`), `pause`/`resumed` ở cả 3 mode.

## [v1.0 — Phase 1] — 2026-11-21
- Ra mắt vòng chơi lõi 2 buổi `gather` & `quan` nối nhau qua file kho đếm JSON nguyên tử.
