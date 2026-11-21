# Kiểm tất định & định dạng JSONL (CON-02, events.md §5)

Lệnh: `python3 tools/check_determinism.py --seeds 1,7,42 --ticks 600`

| Kịch bản | Mode | Seed | Ticks | sha256 JSONL | Kết quả | Ghi chú |
|---|---|---|---|---|---|---|
| day_hold_handoff | day | 1 | 22200 | `e2724a6c2a2c` | ĐẠT |  |
| day_hold_handoff | day | 7 | 22200 | `9a8b950223b4` | ĐẠT |  |
| day_hold_handoff | day | 42 | 22200 | `bf89961a8da8` | ĐẠT |  |
| gather_idle | gather | 1 | 600 | `ad96e510e22a` | ĐẠT |  |
| gather_idle | gather | 7 | 600 | `b3b26a21c2ec` | ĐẠT |  |
| gather_idle | gather | 42 | 600 | `f0c523bb7938` | ĐẠT |  |
| gather_inputs | gather | 1 | 600 | `27a4c19f102d` | ĐẠT |  |
| gather_inputs | gather | 7 | 600 | `5a9ffa1bbc5e` | ĐẠT |  |
| gather_inputs | gather | 42 | 600 | `482357693741` | ĐẠT |  |
| gather_dock_inventory | gather | 1 | 1 | `2673e5649872` | ĐẠT |  |
| gather_dock_inventory | gather | 7 | 1 | `5127dce942a8` | ĐẠT |  |
| gather_dock_inventory | gather | 42 | 1 | `799862e5e203` | ĐẠT |  |
| quan_idle | quan | 1 | 600 | `ed33bd0baecf` | ĐẠT |  |
| quan_idle | quan | 7 | 600 | `ed33bd0baecf` | ĐẠT |  |
| quan_idle | quan | 42 | 600 | `ed33bd0baecf` | ĐẠT |  |
| quan_inventory_inputs | quan | 1 | 600 | `4deb0cad4699` | ĐẠT |  |
| quan_inventory_inputs | quan | 7 | 600 | `4deb0cad4699` | ĐẠT |  |
| quan_inventory_inputs | quan | 42 | 600 | `4deb0cad4699` | ĐẠT |  |

**Tổng:** 18/18 đạt.
