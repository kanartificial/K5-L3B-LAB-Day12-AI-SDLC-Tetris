# Lý Hà Trân Trân (TranHa161) — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm:**
  - P1–P2 (QA): ma trận truy vết, `check_determinism.py` (`083eef3`); 30 test hộp đen v1.1, `smoke_p2.py` (`788ed64`); chơi thử UI 5 Ngày (`39f260b`).
  - P3: bật v1.2, sửa 3 lỗi tích hợp, `test_contract_p3.py` (`0b13736`).
  - P4: `bench`, `soak`, cảnh báo, tương phản cao, Release (`9c1885e`).
- **Đã giúp:** @KimY22-it và @kanartificial (lỗi bàn giao kho, `0b13736`); @ThuThaoVuong (sửa pause/màn hình UI, `053261f`).
- **Đã review:** chạy smoke 2 tiến trình trên `cdf840e`, `c4393f6`, tìm ra lỗi bàn giao kho.
- **AI sai:** test lát Quán bỏ qua `read_inventory` nên vẫn xanh; tôi xác minh test mới fail trên code cũ. AI viết `== "1.3"` đúng lỗi vừa ghi retro, tôi bắt được khi đọc diff.
- **Bài học:** test từng lát xanh chưa phải tích hợp đúng; smoke đầu-cuối phải chạy sớm và đọc lại mọi diff AI viết.
