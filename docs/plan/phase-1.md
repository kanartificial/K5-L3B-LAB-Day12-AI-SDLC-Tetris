# Kế hoạch Phase 1 (≤ 1 trang)

> Tham chiếu: [PRD Phase 1](../prd-phase-1.md) · [TEAM.md](../../TEAM.md) · [Hợp đồng tích hợp](../contracts/README.md) · Hạn tag `phase-1`: **1:00**.

## 1. Mục tiêu
Hoàn thiện trọn vẹn phạm vi lõi Phase 1 của **Quán Ăn Chợ Nổi** đúng Test Contract v1.0:
- Chơi được cả 2 buổi **Lặn & Hái (`gather`)** và **Mở Quán (`quan`)** kèm HUD tối thiểu đọc được.
- Nối 2 tiến trình headless qua file kho JSON nguyên tử (`gather --inventory-out` → `quan --inventory`), tất định từng byte.
- Đủ test hộp đen chạy bằng 1 lệnh, bằng chứng thật tại `docs/proof/phase-1/`, ma trận truy vết `docs/verification/phase-1.md`, tài liệu nhóm và đẩy tag `phase-1` trên `main`.

## 2. Phân công đầu việc / người / phụ thuộc

| AC | Đầu việc & phạm vi | Người phụ trách | Phụ thuộc | Trạng thái |
|---|---|---|---|---|
| `AC-P1-01` | Kickoff: `TEAM.md`, cập nhật `team: "tetris"` trong `game.contract.json`, chốt `docs/contracts/` + `inventory.sample.json` | Cả nhóm (`@kanartificial` Integrator) | PRD-0 | **Xong** (`2ec6272`, `78bf8a3`; chỉ còn vài ô dự phòng trong `TEAM.md`) |
| `AC-P1-02` | **Lát 1 (`sim/gather`):** bơi, chặn biên, `dive`/`surface`, oxy tiêu/hồi, `oxygen_empty`, `choke` (`t+59`), `faint` mất giỏ LIFO + kho rỗng (`chonoi/sim/gather.py`) | Khổng Ngọc Anh (`@kanartificial`) | `AC-P1-01` | **Xong** (`f020f68`) |
| `AC-P1-03` | **Lát 2 (`sim/gather`):** hái nút mặt nước + `node_regrown`, bắt cá + cooldown (`t+L`), `hold_full`, cập bến ưu tiên trước hái, ghi kho 1 lần + `tests/test_gather_p1.py` | Khổng Ngọc Anh (`@kanartificial`) | `AC-P1-02` | **Xong** (`f020f68`) |
| `AC-P1-04` | **Lát 3 (`sim/quan`):** khách theo lịch (`customer_arrived`/`no_dish`), giữ chỗ nguyên liệu (`reserved`), kiên nhẫn, khách bỏ đi (`customer_left`) + uy tín (`chonoi/sim/quan.py`, `chonoi/scenario.py`) | Võ Thị Kim Ý (`@KimY22-it`) | `AC-P1-01` (dùng `inventory.sample.json`) | **Xong luật lõi** (`8ad8880`; kiểm fixture nâng cao trong `scenario.py` nối sang P2) |
| `AC-P1-05` | **Lát 4 (`sim/quan`):** `interact` theo `(khoảng cách, bếp trước bàn, id)`, bếp nấu → chín (`cook_started`/`dish_ready`), bưng (`dish_picked`), phục vụ (`served`), trả tiền (`paid`) + boa + uy tín, hết ca (`quan_end`) | Võ Thị Kim Ý (`@KimY22-it`) | `AC-P1-04` | **Xong** (`8ad8880`) |
| `AC-P1-06` | **Giao diện & HUD (`client/ui`):** hiển thị 2 buổi & HUD tối thiểu trên `chonoi/web/index.html` theo `docs/contracts/sim-ui.md` + `chonoi/play_campaign.py` | Vương Thu Thảo (`@ThuThaoVuong`, QA Lead) | `AC-P1-01` (đọc snapshot từ `GET /state`) | **Xong** (`2df9c22`) |
| `AC-P1-07` | **QA, tích hợp & bàn giao:** `tools/check_determinism.py` (15/15), `tests/test_integration_p1.py`, smoke 2 tiến trình, `docs/proof/phase-1/`, `docs/verification/phase-1.md`, `README.md`, ghi chép tối thiểu và đẩy tag `phase-1` | Lý Hà Trân Trân (`@TranHa161`) + Vương Thu Thảo (`@ThuThaoVuong`) + cả nhóm | `AC-P1-03`, `AC-P1-05`, `AC-P1-06` | **Đã tích hợp — sẵn sàng gắn tag `phase-1`** |

## 3. Mốc phối hợp (60 phút)
- **0–15 phút:** Chốt `TEAM.md`, `game.contract.json`, `docs/contracts/` → triển khai song song 4 module.
- **Phút 20–35:** Hoàn thiện `sim/gather`, `sim/quan`, `client/ui`, `tools/check_determinism.py`; ghi standup (`docs/standup.md`).
- **Phút 45–60:** Gộp toàn bộ vào `main`, chạy smoke 2 tiến trình + kiểm tất định + test 1 lệnh, hoàn thiện `docs/verification/phase-1.md`, `README.md` và đẩy tag `phase-1`.

## 4. Rủi ro & hướng xử lý đã áp dụng
- **Lát 3–4 (`sim/quan`) nhiều ca biên:** tách kiểm thử riêng (`test_quan_p1.py`), rà chéo và bổ sung `vel` trong `QuanSim.snapshot()["player"]`; phần kiểm mâu thuẫn fixture nâng cao trong `scenario.py` ghi nhận trung thực để hoàn thiện cùng v1.1.
- **Lệnh test trên Windows khác Linux (`;` vs `:`):** đã xử lý alias `python` trong `tests/helpers.py` và ghi chú trong `AGENTS.md`.
- **`test_team_check.py::test_template_is_rejected` fail sau khi điền `TEAM.md`:** đã tách chuỗi `TEMPLATE` riêng và thêm `test_repo_team_md_is_valid`, ghi lý do rõ trong `docs/clarify.md`.
