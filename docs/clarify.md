# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 21/11 (P1) | `test_team_check.test_template_is_rejected` fail vì TEAM.md đã điền thật: xóa test hay cho nó đọc template riêng? | Giả định: đây là test của repo mẫu, fail là đúng kỳ vọng; chưa sửa test | Chờ nhóm (QA nêu) |
| 2 | 21/11 (P1) | `game.contract.json` vẫn ghi `"team": "ten-nhom"`: đổi thành `Tetris`? | Giả định: đổi; file khóa nên chờ Integrator | Integrator |
| 3 | 21/11 (P2) | TICKET-02 nhắc "AC-P2-xx" nhưng không liệt kê mã | Đã rõ: dùng mã AC-P2-01…07 trong `docs/plan/phase-2.md`; verification và test đã đổi theo | Nhóm (plan) |
| 4 | 21/11 (P2) | `day_plan` và `shop` đặt trong `tuning` hay ở gốc manifest? | Test chấp nhận cả hai; đề xuất đặt trong `tuning` cạnh `menu` | Hỏi PO / Integrator |
| 5 | 21/11 (P2) | `--mode day` đi kèm `--inventory`/`--inventory-out` thì sao? | Giả định: mã 2 ("hai cờ file kho vẫn dành cho hai mode độc lập") | Hỏi PO |
| 6 | 21/11 (P2) | Pause: `--ticks` đếm tick ngoài (gồm cả bước pause) hay `sim_tick`? | Giả định: tick ngoài, vì "bước vào pause chỉ tăng tick ngoài" | Hỏi PO |
| 7 | 21/11 (P2) | `fish_initial` đổi từ mảng thành số 8: bỏ danh sách vị trí cố định cũ? | Giả định: đúng, vị trí đầu ca chọn theo seed từ các điểm sinh | Hỏi PO |
