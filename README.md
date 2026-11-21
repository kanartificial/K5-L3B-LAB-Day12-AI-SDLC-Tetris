# Day 12 — AI SDLC: Quán Ăn Chợ Nổi (Nhóm Tetris)

> **Nhóm Tetris (4 thành viên)** · Xây game 2D **Quán Ăn Chợ Nổi** qua 4 phase: buổi sáng Út Sen lặn bắt cá, hái rau trên sông Chín Khúc (`gather`); buổi tối mở quán phục vụ khách trên nhà bè Má Tư (`quan`).

## Chạy nhanh từ clone sạch (≤ 3 lệnh, Linux / macOS)

```bash
git clone https://github.com/kanartificial/K5-L3B-LAB-Day12-AI-SDLC-Tetris.git && cd K5-L3B-LAB-Day12-AI-SDLC-Tetris
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v        # chạy toàn bộ test bằng 1 lệnh
python3 -m chonoi.live --mode gather                                # chơi thử buổi sáng trên trình duyệt (hoặc --mode quan)
```

Chạy **headless** theo Test Contract v1.0 (nối 2 tiến trình qua file kho):

```bash
python3 -m chonoi.headless --mode gather --seed 42 --ticks 600 --out gather.jsonl --inventory-out catch.json
python3 -m chonoi.headless --mode quan   --seed 42 --inventory catch.json --ticks 600 --out quan.jsonl
```

## Điều khiển & Cách tính điểm

- **Điều khiển:**
  - `WASD` / **Phím mũi tên**: bơi (`gather`) / di chuyển (`quan`)
  - `E` (`interact`): cập bến hoặc hái rau ở mặt nước (`gather`); nấu / nhấc món / phục vụ (`quan`)
  - `Space` (`catch`): bắt đàn cá khi đang lặn (`gather`)
  - `R`: chơi lại từ đầu (trên bản trình duyệt `chonoi.live`)
- **Cách tính điểm:**
  `score = earned + 100 × floor(reputation)`
  - `earned`: tổng thu (nghìn đồng), gồm tiền món (`base_price`) và tiền boa (`floor(base_price × 0.2)` khi phục vụ lúc còn ≥ 50% kiên nhẫn).
  - `reputation`: uy tín đầu lượt `3.0` (kẹp `[0, 5]`), `+0.2` khi thu boa dương, `-0.5` khi khách hết kiên nhẫn bỏ đi.

## Sáng tạo của nhóm

- **Chế độ chơi nối tiếp 2 buổi trên 1 cổng trình duyệt (`python3 -m chonoi.play_campaign`):** tự mở `gather` tại `http://127.0.0.1:8000/`, khi kết thúc buổi sáng sẽ đọc file kho vừa xuất và chuyển thẳng sang màn `quan` trên cùng một cổng mà người chơi không phải đổi lệnh thủ công.
- **Đảm bảo giữ đúng lõi & Test Contract:** chế độ này nằm riêng tại [chonoi/play_campaign.py](chonoi/play_campaign.py), **tắt hoàn toàn ở chế độ headless** (`chonoi.headless`) và tái sử dụng nguyên `read_inventory`/`write_inventory` theo [hợp đồng kho](docs/contracts/inventory.md). Toàn bộ **51/51 test hộp đen & unit** đều đạt (xem [docs/proof/phase-1/integration.md](docs/proof/phase-1/integration.md)).

## Tài liệu dự án

- [TEAM.md](TEAM.md) · [AGENTS.md](AGENTS.md) · [game.contract.json](game.contract.json)
- Hợp đồng tích hợp: [docs/contracts/README.md](docs/contracts/README.md) ([inventory.md](docs/contracts/inventory.md), [sim-ui.md](docs/contracts/sim-ui.md), [events.md](docs/contracts/events.md), [inventory.sample.json](docs/contracts/inventory.sample.json))
- Kế hoạch & kiểm chứng: [docs/plan/phase-1.md](docs/plan/phase-1.md), [docs/plan/phase-2.md](docs/plan/phase-2.md), [docs/verification/phase-1.md](docs/verification/phase-1.md), [docs/proof/phase-1/](docs/proof/phase-1/)
- Ghi chép nhóm: [docs/clarify.md](docs/clarify.md), [docs/standup.md](docs/standup.md), [docs/ai-usage-log.md](docs/ai-usage-log.md), [docs/retro.md](docs/retro.md), [docs/members/](docs/members/)
- Chi tiết khung kỹ thuật starter: [docs/STARTER.md](docs/STARTER.md)
