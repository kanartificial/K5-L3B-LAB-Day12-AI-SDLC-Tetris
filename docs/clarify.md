# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 10:15 | `tests/test_team_check.py::test_template_is_rejected` đọc trực tiếp `TEAM.md` ở gốc repo nên báo FAIL sau khi nhóm điền danh sách thành viên thật. Xử lý thế nào để lệnh test 1 dòng xanh? | Tách chuỗi `TEMPLATE` mẫu vào trong `tests/test_team_check.py` để vẫn kiểm tra việc từ chối template, đồng thời thêm `test_repo_team_md_is_valid` xác nhận `TEAM.md` thật của nhóm khớp `team_size` trong `game.contract.json`. Ghi rõ lý do trong commit. | Cả nhóm / QA |
| 2 | 2026-11-21 10:38 | Chế độ chơi nối 2 buổi trên 1 cổng (`chonoi/play_campaign.py`) có ảnh hưởng tới Test Contract v1.0 ở headless không? | Không: `play_campaign.py` chỉ dùng cho chế độ chơi trực tiếp trên trình duyệt, tắt hoàn toàn ở `chonoi.headless`, và dùng nguyên `read_inventory`/`write_inventory` theo Contract G. Ghi vào mục "Sáng tạo của nhóm" trong `README.md`. | Cả nhóm |
| 3 | 2026-11-21 10:44 | `QuanSim.snapshot()["player"]` ở starter chỉ xuất `{"pos": self.pos}`, trong khi PRD-0 mục D/E khai `quan.player` gồm `{pos, vel}`. | Bổ sung `"vel": list(self.vel)` vào `QuanSim.snapshot()["player"]` để khớp chính xác Test Contract v1.0 mục D & E. | Integrator (`@kanartificial`) |
