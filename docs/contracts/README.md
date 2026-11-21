# Hợp đồng tích hợp — Nhóm Tetris (Phase 2 / Contract v1.1)

> Khớp [PRD Phase 2 (TICKET-02)](../prd-phase-2.md) (Test Contract v1.1) và [game.contract.json](../../game.contract.json).
> Người giữ contract: **Integrator (`@kanartificial`)** (xem [TEAM.md](../../TEAM.md)).

## Mục lục hợp đồng

1. [**Schema file kho (`gather` → `quan`)**](inventory.md) — mở rộng lên 6 nguyên liệu & 6 món chuẩn, ghi nguyên tử, smoke test 2 tiến trình + truyền trong bộ nhớ ở `--mode day`.
   - File kho mẫu hợp lệ: [`inventory.sample.json`](inventory.sample.json)
2. [**Giao diện `sim/*` ↔ `client/ui`**](sim-ui.md) — snapshot v1.1 (`monsters[]`, `day`, `day_plan`, `upgrades`, `active_upgrades`, `phase: "shop"`, `state: "paused"`), lệnh mới (`pause`, `shop_done`, `buy`), và yêu cầu Menu/Pause/HUD v1.1.
3. [**Danh sách sự kiện & dòng `end` (Events)**](events.md) — toàn bộ sự kiện v1.0 + v1.1 (`monster_hit`, `fish_spawned`, `faint(cause:"monster")`, `day_start`, `day_plan`, `phase_start`, `paused`, `resumed`, `bought`, `buy_failed`, `shop_end`), thứ tự xử lý mục 4.5 và `days_completed`.

## Lịch sử đổi hợp đồng
- **v1.0 → v1.1 (Phase 2):** Áp dụng bộ số chuẩn TICKET-02: thêm 2 nguyên liệu (`ca_keo`, `keo_neo`), 3 món mới, nút `N5`/`N6`, 8 đàn cá bơi/sinh (trần 12), Cá Sấu Năm Chèo (`M1`, `M2`), 2 bếp (`B1–B2`), 4 bàn (`T1–T4`), chế độ `--mode day --days 1..5`, Shop nâng cấp `oxygen`/`hp`, và `pause`/`resumed` ở cả 3 mode.

## Nguyên tắc thay đổi hợp đồng

- **Khóa contract:** Không tự ý sửa `docs/contracts/`, `game.contract.json` hoặc schema kho khi chưa báo cả nhóm.
- **Nguồn sự thật cho số liệu:** Mọi thông số gameplay chỉ đọc từ [`game.contract.json`](../../game.contract.json), không hard-code trong `sim/*` hay `client/ui`.
