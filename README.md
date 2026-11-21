# Quán Ăn Chợ Nổi — Nhóm Tetris · v1.0.0

> Game 2D nhỏ chạy trên trình duyệt. Buổi sáng Út Sen **lặn bắt cá, hái rau** trên sông Chín Khúc (`gather`). Buổi tối **mở quán** phục vụ khách trên nhà bè Má Tư (`quan`). Cuối ngày ghé **Shop** mua nâng cấp. Nguyên liệu có **độ tươi** và ươn dần theo thời gian.
> Lab Day 12 · AI SDLC · 4 phase · Test Contract **v1.3** (gameplay theo v1.2).

## Chạy từ clone sạch (3 lệnh, macOS / Linux)

```bash
git clone https://github.com/kanartificial/K5-L3B-LAB-Day12-AI-SDLC-Tetris.git
cd K5-L3B-LAB-Day12-AI-SDLC-Tetris
python3 -m chonoi.live --mode day
```

Mở trình duyệt tại **http://127.0.0.1:8000/**, bấm **CHƠI**. Dừng server bằng `Ctrl+C`.
Không cần cài thư viện: chỉ dùng thư viện chuẩn Python. Bản đóng gói `.zip` ở [GitHub Release v1.0.0](https://github.com/kanartificial/K5-L3B-LAB-Day12-AI-SDLC-Tetris/releases/tag/v1.0.0) chạy bằng `python3 -m chonoi.live --mode day` sau khi giải nén.

Các chế độ khác: `--mode gather` (chỉ buổi sáng) · `--mode quan` (chỉ buổi tối) · `--days 1..5` · `--seed N` · `--port N`.

## Yêu cầu môi trường

| Thành phần | Yêu cầu | Dùng cho |
|---|---|---|
| Python | **3.10 trở lên** (không cần `pip install`) | game, test, headless, soak, bench |
| Trình duyệt | Chrome / Chromium / Edge / Firefox / Safari bản mới | chơi |
| Chrome / Chromium / Edge | bất kỳ bản mới (Chromium headless) | chỉ cho **bench** |
| Node.js ≥ 22 | tùy chọn | chỉ cho script chơi thử UI tự động (`tools/playtest_warnings.py`) |

Trên Windows dùng `python` thay cho `python3`. Khi chạy test dùng `PYTHONPATH="tests;."` thay cho `tests:.`.

## Điều khiển

| Phím | Buổi sáng (`gather`) | Buổi tối (`quan`) |
|---|---|---|
| `WASD` / mũi tên | bơi (lên/xuống = nổi/lặn) | đi lại trong quán |
| `E` | cập bến · hái rau trên mặt nước | nấu ở bếp · nhấc món chín · phục vụ ở bàn |
| `Space` | bắt đàn cá khi đang lặn | — |
| `Esc` / `P` | tạm dừng / tiếp tục | tạm dừng / tiếp tục |
| `R` | chơi lại từ đầu | chơi lại từ đầu |
| `H` | **bật/tắt tương phản cao** (nhớ lựa chọn) | như bên trái |

Shop: bấm **MUA** (Bình oxy / Áo phao) rồi **ĐÓNG SHOP**. Shop tự đóng sau 10 s.

**Cảnh báo** (chữ + biểu tượng, cả ở chế độ tương phản cao): `🐊 THỦY QUÁI GẦN!` khi Cá Sấu cách < 12 m (kèm ô “!” trên con Cá Sấu) · `🫧 SẮP HẾT OXY` khi đang lặn và oxy < 25 % · `😠 KHÁCH SẮP GIẬN: Tn` khi khách còn < 25 % kiên nhẫn (kèm ô “!” và chữ “SẮP GIẬN” ở bàn).

**Điểm:** `score = earned + 100 × floor(reputation)`. Giá món chốt lúc bắt đầu nấu: `floor(giá niêm yết × trung bình độ tươi / 100)`. Boa `floor(giá × 0.2)` khi phục vụ lúc khách còn ≥ 50 % kiên nhẫn. Nguyên liệu có độ tươi < 30 là **ươn**, vẫn chiếm chỗ nhưng không nấu được.

## Lệnh cho người phát triển / chấm

```bash
# Test toàn bộ (P1–P4)
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v

# Headless theo Test Contract (JSONL), 2 tiến trình nối qua file kho cá thể
python3 -m chonoi.headless --mode gather --seed 42 --ticks 600 --out gather.jsonl --inventory-out catch.json
python3 -m chonoi.headless --mode quan   --seed 42 --ticks 600 --out quan.jsonl --inventory catch.json
python3 -m chonoi.headless --mode day --days 5 --seed 1 --ticks 111000 --out day.jsonl

# Benchmark có render (bench_cmd) — cần Chrome/Chromium/Edge; --browser PATH hoặc CHROME_PATH nếu không tự tìm thấy
python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

# Soak headless 10 Ngày trong một tiến trình bằng bot tất định (soak_cmd)
python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

# QA: smoke + tất định + chơi thử cảnh báo
python3 tools/smoke_p3.py all
python3 tools/check_determinism.py --proof docs/proof/phase-4
python3 tools/playtest_warnings.py
```

Lệnh được khai trong [game.contract.json](game.contract.json): `run_cmd`, `headless_cmd`, `bench_cmd`, `soak_cmd`.

## Kết quả đo (commit phát hành)

Xem [docs/verification/phase-4.md](docs/verification/phase-4.md) và [docs/proof/phase-4/](docs/proof/phase-4/): bench 1280×720, soak 10 Ngày, regression P1–P3, chơi thử 3 cảnh báo ở chế độ tương phản cao.

## Sáng tạo của nhóm

- **Chế độ chơi nối tiếp 2 buổi trên 1 cổng trình duyệt** (`python3 -m chonoi.play_campaign`): kết thúc buổi sáng thì đọc file kho vừa xuất và chuyển thẳng sang buổi tối trên cùng cổng. Nằm riêng ở [chonoi/play_campaign.py](chonoi/play_campaign.py), **tắt hoàn toàn ở headless**, dùng nguyên `read_inventory`/`write_inventory` theo [hợp đồng kho](docs/contracts/inventory.md).
- **Chế độ tương phản cao và cảnh báo có biểu tượng** chỉ nằm ở client (`chonoi/web/index.html`), không chạm luật hay JSONL.
- Bằng chứng lõi vẫn đúng: toàn bộ test P1–P4, `tools/smoke_p3.py all` và `tools/check_determinism.py` đều đạt trên commit phát hành ([phase-4.md](docs/verification/phase-4.md)).

Mở rộng (`leaderboard`, phụ đề SFX, `current`, `reservations`): **không làm** (nhóm 4 người không bắt buộc). `extensions` để trống.

## Giới hạn đã biết

- Kiểm clone sạch và bench chạy trên Windows 11 (Git Bash, Python 3.15, Chrome 157 headless). Nhóm không có máy macOS/Linux để thử trực tiếp. Lệnh và mã chỉ dùng thư viện chuẩn, đường dẫn trình duyệt có sẵn cho macOS/Linux.
- Bench headless bị giới hạn bởi vsync của Chrome (~60 FPS). Viewport bên trong cửa sổ 1280×720 nhỏ hơn một chút do khung cửa sổ.
- Không có âm thanh (nên không có phụ đề SFX). Hình vẽ bằng canvas, không có tài sản ngoài.
- Bot soak chơi đơn giản (hái rau / bắt cá nông, nấu theo thứ tự đơn), chỉ để chạy dài và kiểm không crash, không phải AI chơi tối ưu.

## Tài liệu dự án

- [TEAM.md](TEAM.md) · [AGENTS.md](AGENTS.md) · [CHANGELOG.md](CHANGELOG.md) · [CREDITS.md](CREDITS.md) · [LICENSE](LICENSE) · [Release notes v1.0.0](docs/release-notes-v1.0.0.md)
- Hợp đồng tích hợp: [docs/contracts/](docs/contracts/README.md) · ADR: [docs/adr/](docs/adr/)
- Kế hoạch: [docs/plan/](docs/plan/) · Kiểm chứng: [docs/verification/](docs/verification/) · Bằng chứng: [docs/proof/](docs/proof/)
- Ghi chép nhóm: [docs/clarify.md](docs/clarify.md), [docs/standup.md](docs/standup.md), [docs/ai-usage-log.md](docs/ai-usage-log.md), [docs/retro.md](docs/retro.md), [docs/members/](docs/members/)
- Khung kỹ thuật starter: [docs/STARTER.md](docs/STARTER.md)
