# Hợp đồng 3: Danh sách sự kiện (Events) & Dòng `end` — v1.1

Khớp **PRD Phase 2 (TICKET-02) — Mục 4.4 & 4.5** (mở rộng từ v1.0).

## 1. Vỏ event

- Ở chế độ độc lập (`gather`/`quan`): `{"type":"event","tick":k,"phase":"gather"|"quan","name":...,"data":...}`.
- Ở chế độ `day`: có thêm trường `"day": 1..5`.
- Event đổi pha đầu Ngày 1 (`day_start`, `day_plan`, `phase_start`) phát tại `tick: 0` trước snapshot tick 0.
- Khi đổi pha (`gather_end`, `quan_end`, `shop_end`), event kết thúc mang **pha cũ**, ngay sau đó là `phase_start` (hoặc `day_start → day_plan → phase_start`) mang **pha mới** cùng tick, rồi snapshot pha mới có `phase_tick: 0`.

## 2. Sự kiện v1.0 (giữ nguyên)
- `gather`: `node_regrown`, `dive`, `surface`, `oxygen_empty`, `choke`, `faint` (`cause: "choke"`), `gather`, `hold_full`, `fish_caught`, `gather_end`.
- `quan`: `dish_ready`, `cook_started`, `dish_picked`, `served`, `paid`, `customer_left`, `quan_end`, `customer_arrived`, `no_dish`.

## 3. Sự kiện mới ở v1.1

| `name` | Pha | `data` | Điều kiện phát |
|---|---|---|---|
| `monster_hit` | `gather` | `{"monster_id": str, "hp": int, "lost": [kind, ...], "pos": [x, d]}` | Quái chạm người chơi (`≤ 1.5 m`, `d ≥ 10`, `invuln_ticks == 0`): `-1` Máu, bỏ `floor(len(hold)/2)` theo LIFO, đặt bất tử `90` tick, quái vào `recoil` `60` bước. |
| `faint` (mở rộng) | `gather` | `{"cause": "monster", "lost": [kind, ...], "hp": 0}` | `hp` về `0` sau `monster_hit`; `lost` là **phần giỏ còn lại** theo LIFO; tiếp ngay bằng `gather_end(reason:"fainted", items:{})`. |
| `fish_spawned` | `gather` | `{"id": str, "kind": str, "pos": [x, d]}` | Tại `phase_tick = 360·k` (`k ≥ 1`), sau khi cá bơi, dưới trần `12` đàn và có điểm sinh cách mọi đàn sống `> 1 m`. |
| `day_start` | `gather` (`day`) | `{}` | Mở đầu mỗi Ngày (`tick: 0` cho Ngày 1; cùng tick `shop_end` cho Ngày kế). |
| `day_plan` | `gather` (`day`) | `{"dishes": {...}, "ingredients": {...}}` | Ngay sau `day_start`, công bố thực đơn & tổng nguyên liệu Ngày đó. |
| `phase_start` | `gather` / `quan` / `shop` | `{}` | Bắt đầu mỗi pha trong `day`. |
| `paused` / `resumed` | mọi pha | `{}` | Cạnh lên nút `pause` vào/thoát tạm dừng. |
| `bought` | `shop` | `{"upgrade": str, "level": int, "price": int, "money": int}` | Mua thành công cấp kế tiếp (`oxygen`/`hp`); trừ `money`, giữ nguyên `earned`. |
| `buy_failed` | `shop` | `{"action": str, "reason": "funds"\|"max_level"\|"out_of_stock"\|"unknown"}` | Lệnh `buy` thất bại (không đủ tiền, đã tối đa, hoặc không hỗ trợ). |
| `shop_end` | `shop` | `{"reason": "done"\|"time"}` | Đóng Shop bằng `shop_done` (ưu tiên ở bước cuối) hoặc tự đóng sau `600` tick. |

## 4. Thứ tự xử lý một bước (v1.1 §4.5)
1. **Pause:** xét cạnh `pause` trước mọi xử lý gameplay.
2. **Gather:** đồng hồ/cooldown/bất tử/hồi nút → bơi/oxy/ngạt → cập nhật quái theo `id` & tối đa 1 hit → `interact` (bến trước hái) → `catch` (vị trí cá trước khi bơi) → xét hết giờ → nếu còn giờ: cá bơi theo `id`, rồi sinh cá theo lịch `360·k`.
3. **Quán:** giữ nguyên thứ tự v1.0; trong `day` lọc menu theo `day_plan.dishes` trước khi lọc tồn khả dụng.
4. **Shop:** giảm timer → xử lý 1 `buy` → xét `shop_done` → xét hết giờ (`600` tick). Đóng Shop tăng `days_completed`, nếu chưa đủ `--days` thì sao `upgrades → active_upgrades` và dựng Ngày mới ngay tick đó.

## 5. Dòng `end`
- Độc lập (`gather`/`quan`): giữ nguyên v1.0.
- Chế độ `day`: thêm `"days_completed": int`; `reason` là `"days_complete"` khi đóng đủ `--days` Shop, hoặc `"tick_limit"`.
