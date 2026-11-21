# Hợp đồng tích hợp — Nhóm Tetris (Phase 3 / Contract v1.2)

> Khớp [PRD Phase 3 (TICKET-03)](../prd-phase-3.md) (Test Contract v1.2), [ADR-0001](../adr/0001-item-instance-inventory.md) và [game.contract.json](../../game.contract.json).
> Người giữ contract: **Integrator (`@kanartificial`)** (xem [TEAM.md](../../TEAM.md)).

## Mục lục hợp đồng

1. [**Schema file kho cá thể (`gather` → `quan` & `day`)**](inventory.md) — `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}`, độ chính xác ngưỡng `30`, từ chối kho đếm mã `2` ở v1.2.
   - File mẫu v1.2: [`inventory.v12.sample.json`](inventory.v12.sample.json) *(mẫu v1.1 cũ: [`inventory.sample.json`](inventory.sample.json))*
2. [**Giao diện `sim/*` ↔ `client/ui`**](sim-ui.md) — snapshot v1.2 (`hold[]`, `stock[]` mảng cá thể, `customers[].reserved[]` mảng `id`), yêu cầu HUD hiển thị độ tươi / hàng ươn.
3. [**Danh sách sự kiện & dòng `end` (Events)**](events.md) — sự kiện mới `spoiled`, `lost` & `cook_started.items` mảng cá thể, thứ tự xử lý tick v1.2.

## Lịch sử đổi hợp đồng
- **v1.2 → v1.3 (Phase 4, không breaking):** thêm `bench_cmd`, `soak_cmd`, `extensions: []` ở gốc manifest. Gameplay, tuning, kho cá thể và JSONL giữ nguyên v1.2 (`is_v12()` nhận `1.2` và `1.3`). Soak lặp kế hoạch D1–D5 ở Ngày 6+.
- **v1.1 → v1.2 (Phase 3 — Breaking Change, xem `CHANGELOG.md` & `ADR-0001`):** Đổi kho đếm sang kho cá thể `{id, kind, fresh}` với `tuning.freshness` (`100`, `0.5/s`, `0.25/s`, `< 30`), giữ chỗ theo `id` (nhả & thử giữ lại 1 lần khi ươn → `unfulfillable`), chốt giá theo độ tươi trung bình. Hỗ trợ song song `1.1`/`1.2` theo `contract_version` trong lúc tích hợp rồi bật `"1.2"` khi cả `gather` và `quan` sẵn sàng.
- **v1.0 → v1.1 (Phase 2):** Số chuẩn TICKET-02 (6 nguyên liệu, 6 món, `N1–N6`, cá bơi/sinh, Cá Sấu `M1`/`M2`, `B1–B2`, `T1–T4`, `--mode day`, Shop, `pause`).
