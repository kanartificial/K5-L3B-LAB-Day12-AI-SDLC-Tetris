# Hợp đồng 3: Danh sách sự kiện (Events) & Thứ tự bước — v1.2

Khớp **PRD Phase 3 (TICKET-03) — Mục 1** (mở rộng từ v1.1).

## 1. Sự kiện mới & Thay đổi payload ở v1.2

| `name` | Pha | `data` (v1.2) | Quy tắc |
|---|---|---|---|
| `spoiled` *(mới)* | `gather` / `quan` | `{"item_id": str, "kind": str, "location": "hold"\|"stock"}` | Phát **đúng 1 lần** khi `fresh` đi từ `≥ 30` xuống `< 30` (so trước làm tròn). Nhiều cá thể vượt ngưỡng cùng tick → phát theo `id`. |
| `monster_hit` *(đổi)* | `gather` | `{"monster_id", "hp", "lost": [{"id","kind","fresh"}, ...], "pos"}` | `lost` là mảng cá thể theo thứ tự bỏ **LIFO**. |
| `faint` *(đổi)* | `gather` | `{"cause": "choke"\|"monster", "lost": [{"id","kind","fresh"}, ...], "hp": 0}` | `lost` là mảng cá thể phần giỏ còn lại theo **LIFO**. |
| `gather_end` *(đổi)* | `gather` | `{"reason", "inventory": {"items": [{"id","kind","fresh"}, ...]}}` | `inventory.items` sắp theo `id` (ngất là `[]`). |
| `cook_started` *(đổi)* | `quan` | `{"stove_id", "order_id", "dish_id", "items": [{"id","kind","fresh"}, ...], "base_price": int}` | `items` là mảng cá thể đã dùng, sắp theo `(kind, id)`; `base_price = floor(giá niêm yết × avg_fresh / 100)`. |

## 2. Thứ tự xử lý một bước (v1.2)
1. **Pause:** xét cạnh `pause` trước; khi đang pause dừng mọi đồng hồ, timer và **dừng hao tươi**.
2. **Gather:** đồng hồ, cooldown, bất tử, hồi nút **và hao tươi hàng có sẵn** (phát `spoiled` theo `id`) → bơi, oxy, ngạt → quái/hit → `interact` (bến trước hái) → `catch` → xét hết giờ → cá bơi & sinh.
3. **Quán:** đồng hồ & timer → **hao tươi kho thô, phát hết `spoiled` theo `id`, rồi mới xử lý các đơn có phần giữ vừa ươn** (theo `order_tick` rồi `table_id`: nhả toàn bộ & thử giữ lại đúng 1 lần lấy tươi nhất hòa `id`; không đủ → `unfulfillable`) → bếp chín → di chuyển & tối đa 1 `interact` → thanh toán, kiên nhẫn/đóng ca → lượt khách mới.
4. **Shop:** không hao tươi; giữ nguyên thứ tự `buy` → `shop_done` → hết giờ (`600` tick).
