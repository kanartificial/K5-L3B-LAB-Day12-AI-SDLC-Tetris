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
| `AC-P1-01` | Kickoff: hoàn thiện `TEAM.md` (đủ vai quy trình & người dự phòng), cập nhật `team` trong `game.contract.json`, chốt `docs/contracts/` + `inventory.sample.json` | Cả nhóm (`@kanartificial` chốt contract) | PRD-0 | Đã xong contract; cần chốt tên nhóm & vai còn trống |
| `AC-P1-02` | **Lát 1 (`sim/gather`):** bơi, chặn biên, `dive`/`surface`, oxy tiêu/hồi, `oxygen_empty`, `choke` (`t+59`), `faint` mất giỏ LIFO + kho rỗng (`chonoi/sim/gather.py`) | Khổng Ngọc Anh (`@kanartificial`) | `AC-P1-01` | **Xong** (`f020f68`) |
| `AC-P1-03` | **Lát 2 (`sim/gather`):** hái nút mặt nước + `node_regrown`, bắt cá + cooldown (`t+L`), `hold_full`, cập bến ưu tiên trước hái, ghi kho 1 lần + `tests/test_gather_p1.py` | Khổng Ngọc Anh (`@kanartificial`) | `AC-P1-02` | **Xong** (`f020f68`) |
| `AC-P1-04` | **Lát 3 (`sim/quan`):** khách theo lịch (`customer_arrived`/`no_dish`), giữ chỗ nguyên liệu (`reserved`), kiên nhẫn, khách bỏ đi (`customer_left`) + uy tín, kiểm mâu thuẫn fixture quán (`chonoi/sim/quan.py`, `chonoi/scenario.py`) | Võ Thị Kim Ý (`@KimY22-it`) | `AC-P1-01` (dùng `inventory.sample.json`) | Đang làm |
| `AC-P1-05` | **Lát 4 (`sim/quan`):** `interact` theo `(khoảng cách, bếp trước bàn, id)`, bếp nấu → chín (`cook_started`/`dish_ready`), bưng (`dish_picked`), phục vụ (`served`), trả tiền (`paid`) + boa + uy tín, hết ca (`quan_end`) | Võ Thị Kim Ý (`@KimY22-it`) | `AC-P1-04` | Chờ Lát 3 |
| `AC-P1-06` | **Giao diện & HUD (`client/ui`):** hoàn thiện hiển thị 2 buổi & HUD tối thiểu trên `chonoi/web/index.html` theo `docs/contracts/sim-ui.md` (thời gian, oxy, Máu, giỏ; kho khả dụng, món gọi, kiên nhẫn, bếp, món trên tay, tiền, uy tín) | Vương Thu Thảo (`@ThuThaoVuong`, QA Lead) | `AC-P1-01` (đọc snapshot từ `GET /state`) | Đang làm |
| `AC-P1-07` | **QA, tích hợp & bàn giao:** viết test hộp đen `quan` + smoke 2 tiến trình, chạy kiểm chứng trên `main`, lưu `docs/proof/phase-1/`, điền `docs/verification/phase-1.md`, cập nhật `README.md` (≤ 3 lệnh chạy), `docs/{clarify,standup,ai-usage-log,retro}.md`, `docs/members/<handle>.md`, đẩy tag `phase-1` | Lý Hà Trân Trân (`@TranHa161`) + Vương Thu Thảo (`@ThuThaoVuong`) + cả nhóm | `AC-P1-03`, `AC-P1-05`, `AC-P1-06` | Chờ tích hợp |

## 3. Mốc phối hợp (60 phút)
- **0–15 phút:** Chốt `TEAM.md`, `game.contract.json`, `docs/contracts/` → triển khai song song `sim/gather`, `sim/quan`, `client/ui`, kịch bản test `qa`.
- **Phút 20–30:** Rà tiến độ Lát 3–4 (`sim/quan`); `@kanartificial` (đã xong `sim/gather`) hỗ trợ ghép `quan` / `scenario.py` nếu cần; thử chạy xuất file kho thật trước phút 25; standup 2–3 phút ghi vào `docs/standup.md`.
- **Phút 45–55:** Gộp toàn bộ vào `main`, chạy smoke 2 tiến trình + test hộp đen + chơi thử `chonoi.live`, lưu bằng chứng `docs/proof/phase-1/` và hoàn thiện `docs/verification/phase-1.md`.
- **Phút 55–60:** Kiểm tra DoD (commit đủ 4 thành viên, `README.md`, ghi chép tối thiểu) và đẩy tag `phase-1`.

## 4. Rủi ro & hướng xử lý
- **Lát 3–4 (`sim/quan`) nhiều ca biên** (giữ chỗ nguyên liệu, dọn món dở khi khách rời, kiểm mâu thuẫn fixture trả mã `2`): ưu tiên làm chuẩn thứ tự bước mục F trước; nếu vướng quá 10 phút, `@kanartificial` sang pair/hỗ trợ ngay.
- **Lệch trường snapshot/event giữa `sim/quan` và `client/ui`:** bám chặt `docs/contracts/sim-ui.md` và `docs/contracts/events.md`; UI tự bỏ qua trường chưa có và tính kho khả dụng = `stock - tổng reserved`.
- **Test mẫu `tests/test_team_check.py::test_template_is_rejected` fail** do `TEAM.md` đã điền tên nhóm thật: ghi nhận trong `docs/clarify.md` / `docs/verification/phase-1.md` và thống nhất cách xử lý với QA Lead trước khi gắn tag.
- **Thiếu commit cá nhân hoặc quên ghi chép tối thiểu trước hạn 1:00:** mỗi thành viên tự commit trực tiếp phần việc của mình (tối thiểu 1–2 commit có nội dung ngay trong Phase 1) và dành 10 phút cuối chốt `docs/verification/phase-1.md`, `docs/ai-usage-log.md`, `docs/members/<handle>.md`.
