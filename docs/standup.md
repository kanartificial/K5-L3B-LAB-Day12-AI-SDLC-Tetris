# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| Phase 1 | Khổng Ngọc Anh (`@kanartificial`) | Chốt `docs/contracts/`, xong Lát 1–2 `sim/gather` + 10 test `test_gather_p1.py`, viết `plan/phase-1.md` & `plan/phase-2.md`, bổ sung `test_integration_p1.py`, `vel` trong `QuanSim`, đổi `team: "tetris"` | Chốt merge & đẩy tag `phase-1`, sang `AC-P2-01` nâng Contract v1.1 | Không |
| Phase 1 | Võ Thị Kim Ý (`@KimY22-it`) | Xong Lát 3–4 `sim/quan` + 6 test `test_quan_p1.py` + proof `quan-arrivals.md`, `quan-orders.md` | Bổ sung kiểm mâu thuẫn fixture quán và nâng `quan` lên 2 bếp/4 bàn/6 món ở Phase 2 | Alias `python3` trên Windows (đã xử lý ở `tests/helpers.py`) |
| Phase 1 | Vương Thu Thảo (`@ThuThaoVuong`) | Cập nhật `chonoi/web/index.html` (UI/HUD 2 buổi) và thêm `chonoi/play_campaign.py` | Nâng cấp Menu, màn chuyển pha, Pause & HUD v1.1 ở Phase 2 | Không |
| Phase 1 | Lý Hà Trân Trân (`@TranHa161`) | Viết `tools/check_determinism.py` (15/15 đạt), điền ma trận truy vết Phase 1 & lưu `docs/proof/phase-1/{determinism.md,unittest.log}`, chuẩn bị `tests/test_contract_p2.py` (30 test v1.1) và `tools/smoke_p2.py` | Chạy lại kiểm chứng toàn bộ trên commit bàn giao Phase 1 và dẫn test hộp đen + regression Phase 2 | `test_template_is_rejected` & `"team"` trong `game.contract.json` (đã chốt xử lý cùng Integrator) |
