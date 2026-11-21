# Kiểm tất định & định dạng JSONL (CON-02, events.md §5)

Lệnh: `python3 tools/check_determinism.py --seeds 1,7,42 --ticks 600`

| Kịch bản | Mode | Seed | Ticks | sha256 JSONL | Kết quả | Ghi chú |
|---|---|---|---|---|---|---|
| gather_idle | gather | 1 | 600 | `ad96e510e22a` | ĐẠT |  |
| gather_idle | gather | 7 | 600 | `b3b26a21c2ec` | ĐẠT |  |
| gather_idle | gather | 42 | 600 | `f0c523bb7938` | ĐẠT |  |
| gather_inputs | gather | 1 | 600 | `00cc166e3d38` | ĐẠT |  |
| gather_inputs | gather | 7 | 600 | `a2a866292892` | ĐẠT |  |
| gather_inputs | gather | 42 | 600 | `0f8971679ae5` | ĐẠT |  |
| gather_dock_inventory | gather | 1 | 1 | `dd3aa3e30724` | ĐẠT |  |
| gather_dock_inventory | gather | 7 | 1 | `838ef8cde610` | ĐẠT |  |
| gather_dock_inventory | gather | 42 | 1 | `e8c4d88b1372` | ĐẠT |  |
| quan_idle | quan | 1 | 600 | `0e83d0f0672e` | ĐẠT |  |
| quan_idle | quan | 7 | 600 | `0e83d0f0672e` | ĐẠT |  |
| quan_idle | quan | 42 | 600 | `0e83d0f0672e` | ĐẠT |  |
| quan_inventory_inputs | quan | 1 | 600 | `e0c6aeaa8077` | ĐẠT |  |
| quan_inventory_inputs | quan | 7 | 600 | `e0c6aeaa8077` | ĐẠT |  |
| quan_inventory_inputs | quan | 42 | 600 | `870fcb0f78ff` | ĐẠT |  |

**Tổng:** 15/15 đạt.
