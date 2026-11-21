# Khổng Ngọc Anh (kanartificial) — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm:**
  - **P1:** Chốt `TEAM.md` (`2ec6272`), hợp đồng v1.0 (`78bf8a3`), `sim/gather` + `test_gather_p1` (`f020f68`), kế hoạch P1–P2 (`ece548f`, `a2634c6`), tích hợp P1 (`6f0fdcc`).
  - **P2 (`32d1921`):** Contract v1.1, cá bơi/sinh, Cá Sấu, `ShopSim`/`DaySession`/`pause`, `test_gather_p2`, `AGENTS.md` và 2 skill nhóm.
  - **P3 (`c4393f6`):** ADR-0001 kho cá thể, hợp đồng v1.2, adapter `inventory`/`scenario`, độ tươi chính xác 240 đơn vị (`gather`, `runner`, `shop`), `test_gather_p3`, kế hoạch P3.
  - **P4:** Kế hoạch phát hành v1.0.0 (`docs/plan/phase-4.md`) và rà DoD bàn giao.
- **Đã giúp & review:** Rà `sim/quan` (`8ad8880`, `2955c18`), `play_campaign` (`2df9c22`), `test_contract_p2` (`957e58c`); hỗ trợ `@KimY22-it`, `@ThuThaoVuong` khớp hợp đồng kho/snapshot.
- **AI sai ở đâu & phát hiện:** P1: AI để dư biến `inp` và làm vỡ `test_template_is_rejected`, phát hiện qua unittest. P3: adapter trả `fresh` kiểu `Fraction` nhưng thiếu smoke 2 tiến trình với `QuanSim`, gây lỗi bàn giao mà `@TranHa161` (`0b13736`) bắt ra.
- **Bài học:** Chốt contract sớm giúp ghép nhanh, nhưng cần commit nhỏ và chạy smoke đầu-cuối ngay khi đổi schema thay vì chỉ tin test lát.
