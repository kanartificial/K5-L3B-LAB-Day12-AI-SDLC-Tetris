# Võ Thị Kim Ý (@KimY22-it) — phản tư cá nhân

- **Phần tôi làm.** Tôi phụ trách Mở Quán. Phase 1, tôi triển khai vòng đời đơn hàng (`8ad8880`). Phase 2, tôi kiểm đơn theo kế hoạch Ngày và kho bàn giao (`99ddcde`). Phase 3, tôi triển khai độ tươi nguyên liệu và giá món (`cdf840e`).
- **Tôi đã hỗ trợ ai.** Tôi hỗ trợ QA kiểm các lỗi chỉ xuất hiện khi chuyển từ Lặn & Hái sang Mở Quán bằng bài kiểm headless trong `99ddcde`. Kết quả tích hợp được ghi trong [ma trận kiểm chứng Phase 2](../verification/phase-2.md).
- **AI sai ở đâu.** Codex ban đầu giả định kiểm kho lúc đọc tham số CLI là đủ. Khi đối chiếu luồng `day`, tôi thấy kho thực tế chỉ có sau khi Gather kết thúc, nên kiểm đơn phải diễn ra lúc mở ca Quán. [Nhật ký AI](../ai-usage-log.md)
- **Điều tôi học được.** Tôi cần kiểm bằng dữ liệu đi qua đúng đường bàn giao và chạy hồi quy tích hợp trước khi gộp, kể cả khi test Quán đã đạt.
