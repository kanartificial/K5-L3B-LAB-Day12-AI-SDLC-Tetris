# Kiểm tất định & định dạng JSONL (CON-02, events.md §5)

Lệnh: `python3 tools/check_determinism.py --seeds 1,7,42 --ticks 600`

| Kịch bản | Mode | Seed | Ticks | sha256 JSONL | Kết quả | Ghi chú |
|---|---|---|---|---|---|---|
| gather_idle | gather | 1 | 600 | `72c30e63f0ca` | ĐẠT |  |
| gather_idle | gather | 7 | 600 | `72c30e63f0ca` | ĐẠT |  |
| gather_idle | gather | 42 | 600 | `72c30e63f0ca` | ĐẠT |  |
| gather_inputs | gather | 1 | 600 | `29c0e25a20b3` | ĐẠT |  |
| gather_inputs | gather | 7 | 600 | `29c0e25a20b3` | ĐẠT |  |
| gather_inputs | gather | 42 | 600 | `29c0e25a20b3` | ĐẠT |  |
| gather_dock_inventory | gather | 1 | 1 | `6bc3a907bb1c` | ĐẠT |  |
| gather_dock_inventory | gather | 7 | 1 | `6bc3a907bb1c` | ĐẠT |  |
| gather_dock_inventory | gather | 42 | 1 | `6bc3a907bb1c` | ĐẠT |  |
| quan_idle | quan | 1 | 600 | `5af637b8e5a5` | ĐẠT |  |
| quan_idle | quan | 7 | 600 | `5af637b8e5a5` | ĐẠT |  |
| quan_idle | quan | 42 | 600 | `5af637b8e5a5` | ĐẠT |  |
| quan_inventory_inputs | quan | 1 | 600 | `c3fb5fcce24c` | ĐẠT |  |
| quan_inventory_inputs | quan | 7 | 600 | `c3fb5fcce24c` | ĐẠT |  |
| quan_inventory_inputs | quan | 42 | 600 | `2e2fe2b5cf2c` | ĐẠT |  |

**Tổng:** 15/15 đạt.
