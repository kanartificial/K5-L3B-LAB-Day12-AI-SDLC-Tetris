# Thử từ clone sạch (AC-P4-04)

- Commit: `9c1885e` · Windows 11, Git Bash, Python 3.15.0, không cài thêm gói nào.
- Clone từ repo cục bộ vào thư mục trống. `git status --porcelain --ignored` = 0 dòng trước khi chạy, nên không có file bị ignore hay file tạm nào mang theo.
- Ba lệnh lấy nguyên văn từ README. Lệnh thứ 3 chạy nền (`--port 8791` để không đụng cổng 8000 đang bận), rồi gọi HTTP để chắc chắn giao diện đã lên.

```text
$ git clone <repo> K5-L3B-LAB-Day12-AI-SDLC-Tetris
exit=0
$ cd K5-L3B-LAB-Day12-AI-SDLC-Tetris
HEAD=9c1885e · untracked/ignored trước khi chạy: 0
$ python3 -m chonoi.live --mode day   (python trên Windows)
GET /       -> HTTP 200 · <title>Chợ Nổi — v1.0.0
GET /state  -> HTTP 200 · mode day phase gather day 1 error None
Mở trình duyệt tại http://127.0.0.1:8791/  (chế độ day, seed 1). Ctrl+C để dừng.
```

Chạy test ngay trong bản clone sạch: `PYTHONPATH="tests;." python -m unittest discover -s tests`, kết quả **Ran 129 tests · OK**.

Giới hạn: nhóm không có máy macOS hoặc Linux để thử trực tiếp. Lệnh chỉ dùng thư viện chuẩn Python. Khác biệt duy nhất trên Windows là gọi `python` thay cho `python3`.
