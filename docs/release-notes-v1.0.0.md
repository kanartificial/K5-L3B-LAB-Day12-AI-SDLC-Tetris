# Quán Ăn Chợ Nổi v1.0.0 — Nhóm Tetris

Bản phát hành đầu tiên. Cả vòng chơi một Ngày đã đủ: buổi sáng Út Sen lặn bắt cá, hái rau trên sông, buổi tối mở quán bán cho khách, cuối ngày ghé Shop mua nâng cấp. Có 5 Ngày với kế hoạch món khác nhau.

## Điểm mới
- **Vòng chơi 5 Ngày** (`--mode day`): Lặn & Hái → Mở Quán → Shop, tiền, uy tín và nâng cấp được giữ qua các Ngày.
- **Độ tươi nguyên liệu:** cá và rau ươn dần (0.5 điểm/s trong giỏ, 0.25 điểm/s trong kho quán). Hàng dưới 30 điểm là ươn, không nấu được. Giá món tính theo độ tươi trung bình lúc bắt đầu nấu.
- **Sông có sự sống:** đàn cá bơi và sinh thêm, Cá Sấu Năm Chèo tuần tra vùng sâu (thêm một con từ Ngày 3).
- **Quán 2 bếp, 4 bàn, 6 món**, khách có kiên nhẫn, phục vụ nhanh thì được boa.
- **Cảnh báo dễ nhận biết:** thủy quái gần, oxy sắp hết, khách sắp giận. Mỗi cảnh báo có chữ kèm biểu tượng.
- **Chế độ tương phản cao:** nhấn `H`.
- Cho người chấm và người phát triển: chạy headless theo Test Contract (JSONL), benchmark có render, soak nhiều Ngày.

## Cách chạy
Cần **Python 3.10 trở lên** (không phải cài thêm gì) và một trình duyệt.

```bash
# Từ bản .zip đính kèm: giải nén rồi vào thư mục
python3 -m chonoi.live --mode day
# Mở http://127.0.0.1:8000/ và bấm CHƠI
```

Hoặc từ repo: `git clone …` → `cd K5-L3B-LAB-Day12-AI-SDLC-Tetris` → `python3 -m chonoi.live --mode day`.

| Phím | Tác dụng |
|---|---|
| WASD / mũi tên | bơi / đi lại |
| E | cập bến, hái rau, nấu, nhấc món, phục vụ |
| Space | bắt cá |
| Esc / P | tạm dừng |
| R | chơi lại |
| H | tương phản cao |

Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` · Bench: `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json` (cần Chrome/Chromium/Edge) · Soak: `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`.

## Kết quả kiểm trên commit phát hành
Xem [docs/verification/phase-4.md](verification/phase-4.md): toàn bộ test đạt, bench 1280×720, soak 10 Ngày không crash, chơi thử 3 cảnh báo ở chế độ tương phản cao.

## Giới hạn đã biết
- Chỉ kiểm trực tiếp trên Windows 11. Nhóm không có máy macOS/Linux để thử, dù code chỉ dùng thư viện chuẩn Python.
- Không có âm thanh.
- Bench headless bị khóa khoảng 60 FPS theo vsync của Chrome.
- Bot của lệnh soak chơi đơn giản, chỉ dùng để kiểm chạy dài không crash.
- Chưa làm các phần mở rộng: bảng xếp hạng, phụ đề SFX, dòng nước lũ, khách đặt trước.

Giấy phép: MIT cho phần nhóm viết, xem `LICENSE` và `CREDITS.md`.
