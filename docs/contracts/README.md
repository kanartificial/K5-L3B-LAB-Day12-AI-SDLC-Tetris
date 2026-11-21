# Hợp đồng tích hợp — Nhóm Tetris (Phase 1 / Contract v1.0)

> Khớp [PRD Phase 1](../prd-phase-1.md) (Test Contract v1.0) và [game.contract.json](../../game.contract.json).
> Người giữ contract: **Integrator** (xem [TEAM.md](../../TEAM.md)).

## Mục lục hợp đồng

1. [**Schema file kho (`gather` → `quan`)**](inventory.md) — định dạng JSON, kiểm lỗi, ghi nguyên tử, smoke test 2 tiến trình.
   - File kho mẫu hợp lệ: [`inventory.sample.json`](inventory.sample.json)
2. [**Giao diện `sim/*` ↔ `client/ui`**](sim-ui.md) — snapshot UI được đọc, lệnh UI gửi vào (`Session` & HTTP API của `chonoi.live`), yêu cầu HUD tối thiểu.
3. [**Danh sách sự kiện & dòng `end` (Events)**](events.md) — toàn bộ sự kiện `gather` và `quan`, schema `data`, bên phát/nghe, thứ tự xử lý và quy tắc tất định.

## Nguyên tắc thay đổi hợp đồng

- **Khóa contract sau kickoff:** Không tự ý sửa các file trong `docs/contracts/`, `game.contract.json` hoặc schema kho khi chưa báo cả nhóm.
- **Khi cần đổi (Phase 2+):** Thảo luận và thống nhất trước với cả nhóm (đặc biệt các module bị ảnh hưởng: `sim/gather`, `sim/quan`, `client/ui`, `qa`), cập nhật contract đồng bộ và ghi lại lý do vào `docs/adr/` hoặc commit message.
- **Nguồn sự thật cho số liệu:** Mọi thông số gameplay chỉ đọc từ [`game.contract.json`](../../game.contract.json), không hard-code trong `sim/*` hay `client/ui`.
