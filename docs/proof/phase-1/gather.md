# Phase 1 — Bằng chứng buổi sáng (`gather`: Lát 1 & Lát 2)

## Lệnh kiểm thử hộp đen

```bash
PYTHONPATH=tests:. python3 -m unittest tests/test_gather_p1.py -v
```

## Kết quả thực tế (Python 3.14, Linux)

- **10/10 test PASS** trong `tests/test_gather_p1.py`:
  1. `test_dive_and_surface_events_and_oxygen_drain_refill`: phát `dive` khi lặn qua `d = 0.5`, trừ `1` oxy/tick khi dưới nước, phát `surface` và hồi `+6` oxy/tick khi lên mặt nước.
  2. `test_oxygen_empty_and_choke_at_t_plus_59`: chạm oxy `0` ở tick `t = 2` phát `oxygen_empty`; ở dưới nước liên tục bị `choke` (`hp: 2`) đúng ở tick `t + 59 = 61`.
  3. `test_surface_on_would_be_choke_tick_prevents_choke`: nổi lên đúng tick `zero_oxy_ticks = 59` → hồi oxy, reset ngạt, không mất Máu.
  4. `test_faint_loses_hold_lifo_writes_empty_inventory_and_stops_step`: `hp` về `0` phát `choke → faint (lost LIFO) → gather_end(fainted, items={})`, ghi kho rỗng, dừng bước trước cả `docked`/`time`.
  5. `test_harvest_boundary_tiebreak_regrow_and_immediate_reharvest`: hái đúng mép bán kính `2.0 m`, hòa theo `id` (`N2` thắng `N10`), nút mọc lại sau `1200` tick phát `node_regrown` trước `gather` và hái ngay được.
  6. `test_harvest_hold_full_and_underwater_ignored`: giỏ đầy phát `hold_full` và giữ nút `ready`; dưới nước không hái được.
  7. `test_catch_fish_tiebreak_cooldown_and_remove`: bắt cá dưới nước hòa theo `id` (`F2` thắng `F10`), xóa đàn, lấy đủ `yield`, cooldown `L = 30` chặn ở `t + L - 1` và dùng lại đúng từ `t + L`.
  8. `test_catch_hold_full_does_not_try_other_fish_and_keeps_cooldown`: thiếu chỗ cho đàn gần nhất phát `hold_full`, giữ đàn & cooldown `0`, không thử đàn thứ hai.
  9. `test_catch_at_surface_or_empty_range_no_event_no_cooldown`: ở mặt nước (`d = 0.5`) hoặc không có cá trong tầm không phát event và không đặt hồi chiêu.
  10. `test_dock_precedes_harvest_and_last_tick_actions_saved_to_inventory`: cập bến xét trước hái (đúng mép `3 m`); hái/bắt hợp lệ ở bước cuối ca vẫn được ghi vào file kho khi `gather_end(time)`.
