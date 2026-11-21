# Hợp đồng 3: Danh sách sự kiện (Events) & Dòng `end` — v1.0

Khớp **PRD Phase 1 — Mục E & Mục F**.

## 1. Cấu trúc chung của một dòng event trong JSONL

```json
{"type":"event","tick":1,"phase":"gather","name":"gather","data":{"node_id":"N1","kind":"bong_dien_dien","amount":1}}
```

- Bước `k` đọc input ở `tick = k`, biến trạng thái `k → k+1` và mọi event phát ra trong bước đó mang `"tick": k + 1`.
- Trong cùng 1 tick: ghi **các event theo đúng thứ tự xử lý** trước, rồi mới ghi **snapshot** (nếu tick chia hết cho `--snapshot-every` hoặc gameplay kết thúc).
- Trong `chonoi.live`, `GET /state` trả kèm danh sách `events` gần nhất dùng đúng cấu trúc dòng event này để `client/ui` kích hoạt hiệu ứng/âm thanh/thông báo.

## 2. Sự kiện buổi sáng (`phase: "gather"`)

**Bên phát:** `sim/gather` (`GatherSim.step`) · **Bên nghe:** `runner` (JSONL), `client/ui` (hiệu ứng/HUD/âm thanh), `qa` (kiểm chứng).

| Thứ tự trong bước | `name` | `data` | Điều kiện phát |
|---|---|---|---|
| 1. Đồng hồ & nút | `node_regrown` | `{"node_id": str}` | `regrow_ticks` giảm từ `1` về `0` (duyệt theo `id`); nút có thể hái ngay trong bước này. |
| 2. Bơi & biên nước | `dive` | `{"pos": [x, d]}` | Đầu bước ở mặt nước (`d <= surface_depth`), cuối bước dưới nước (`d > surface_depth`). `pos` là tọa độ sau di chuyển. |
| 2. Bơi & biên nước | `surface` | `{"pos": [x, d]}` | Đầu bước dưới nước, cuối bước ở mặt nước. `pos` là tọa độ sau di chuyển. |
| 2. Oxy & ngạt | `oxygen_empty` | `{"oxygen_ticks": 0}` | `oxygen_ticks` vừa giảm từ `> 0` xuống `0`. |
| 2. Oxy & ngạt | `choke` | `{"hp": int}` | Ở dưới nước với `oxygen_ticks == 0` đủ `choke_interval_ticks` (60) bước → trừ 1 Máu; `hp` là giá trị sau khi trừ. |
| 2. Oxy & ngạt | `faint` | `{"cause": "choke", "lost": [kind, ...], "hp": 0}` | Sau `choke`, `hp == 0`. `lost` là mảng `kind` bị bỏ theo thứ tự **LIFO** (nhặt sau bỏ trước). |
| 2 / 3 / 5. Kết thúc | `gather_end` | `{"reason": "time"\|"docked"\|"fainted", "inventory": {"items": {...}}}` | Kết thúc buổi sáng (`fainted` dừng ngay ở bước 2 với kho rỗng; `docked` dừng ngay ở bước 3; `time` ở bước 5). |
| 3. `interact` (hái) | `gather` | `{"node_id": str, "kind": str, "amount": int}` | Ngoài bến, ở mặt nước, chọn nút `ready` gần nhất trong `interact_radius` (hòa theo `id`), giỏ còn đủ chỗ (`node_yield`). |
| 3 / 4. Giỏ đầy | `hold_full` | `{"action": "gather"\|"catch", "node_id"\|"fish_id": str, "required": int, "free": int}` | Hái (`action:"gather"`, khóa `"node_id"`) hoặc bắt cá (`action:"catch"`, khóa `"fish_id"`) khi `free < required`. Giữ nguyên nút/đàn cá và cooldown. |
| 4. `catch` (bắt cá) | `fish_caught` | `{"fish_id": str, "kind": str, "yield": int}` | `catch_cd_ticks == 0`, đang dưới nước, chọn đàn gần nhất trong `catch_radius` (hòa theo `id`), giỏ đủ chỗ cho toàn bộ `yield`. |

## 3. Sự kiện buổi tối (`phase: "quan"`)

**Bên phát:** `sim/quan` (`QuanSim.step`) · **Bên nghe:** `runner` (JSONL), `client/ui` (hiệu ứng/HUD/âm thanh), `qa` (kiểm chứng).

| Thứ tự trong bước | `name` | `data` | Điều kiện phát |
|---|---|---|---|
| 2. Bếp nấu xong | `dish_ready` | `{"stove_id": str, "order_id": str, "dish_id": str}` | Duyệt bếp theo `id`: bếp `cooking` có `cook_ticks_left` về `0` → chuyển `ready` với `ready_ticks = 0`. |
| 3. `interact` bếp `idle` | `cook_started` | `{"stove_id": str, "order_id": str, "dish_id": str, "items": [kind, ...], "base_price": int}` | Chọn bếp `idle` lấy đơn `reserved` cũ nhất theo `(order_tick, table_id)`, tiêu nguyên liệu giữ. `items` là mảng `kind` đã sắp theo `kind`. |
| 3. `interact` bếp `ready` | `dish_picked` | `{"stove_id": str, "order_id": str, "dish_id": str}` | Tay đang trống (`hand is None`), nhấc món khỏi bếp `ready`, bếp về `idle`. |
| 3. `interact` bàn | `served` | `{"order_id": str, "table_id": str, "dish_id": str, "patience_ticks_left": int, "base_price": int, "tip": int}` | Giao đúng `order_id` trên tay cho khách đang `waiting`; chốt `tip = floor(base_price * tip_rate)` nếu tỷ lệ kiên nhẫn sau bước 1 `>= tip_min_patience_ratio`, ngược lại `0`. |
| 4. Thanh toán | `paid` | `{"order_id": str, "table_id": str, "base_price": int, "tip": int, "amount": int, "reason": "finished_eating"\|"closing"}` | Duyệt theo `table_id`: khách ăn xong (`finished_eating`) hoặc hết ca khi đang ăn (`closing`). `amount = base_price + tip`. Nếu `tip > 0`, cộng `tip_reputation` và kẹp `[reputation_min, reputation_max]`. |
| 4. Khách rời | `customer_left` | `{"order_id": str, "table_id": str, "reason": "patience"\|"closing", "reputation": float}` | Duyệt theo `table_id`: hết kiên nhẫn khi còn giờ (`patience`, đổi uy tín theo `left_reputation_delta`) hoặc hết ca khi còn chờ (`closing`, không trừ uy tín). Nhả phần giữ, bỏ món dở trên bếp/tay. |
| 4. Kết thúc ca | `quan_end` | `{"reason": "time", "money": int, "earned": int, "shift_earned": int, "reputation": float}` | Sau khi dọn hết khách ở bước hết giờ (`time_left_ticks == 0`). |
| 5. Khách mới | `customer_arrived` | `{"order_id": str, "table_id": str, "dish_id": str}` | Còn giờ, đúng lịch khách (`phase_tick == first_customer_tick` hoặc lặp mỗi `customer_interval_s * 60`), có bàn trống (`id` nhỏ nhất) và có ít nhất 1 món đủ kho khả dụng. |
| 5. Hết món | `no_dish` | `{}` | Đúng lịch khách và có bàn trống, nhưng không món nào trong 3 món đủ nguyên liệu khả dụng. |

## 4. Dòng `end` (luôn là dòng cuối của JSONL)

```json
{"type":"end","ticks":10800,"sim_tick":10800,"mode":"quan","state":"finished","reason":"time","money":72,"earned":72,"reputation":3.2,"score":372}
```

- `state`: `"finished"` nếu kết thúc do luật gameplay, `"playing"` nếu dừng do chạm `--ticks`.
- `reason`:
  - `gather`: `"time"` | `"docked"` | `"fainted"` | `"tick_limit"`.
  - `quan`: `"time"` | `"tick_limit"`.
  - Nếu gameplay kết thúc đúng bước cuối được cấp (`ticks`), **ưu tiên lý do gameplay**.

## 5. Quy tắc tất định & định dạng (bắt buộc cho QA và `sim/*`)

- **Sắp thứ tự:** mảng thực thể (`nodes`, `fish`, `stoves`, `tables`, `customers`) sắp theo `ids.sort_by_id`; `hold` theo thứ tự nhặt; `lost` theo LIFO; `cook_started.items` sắp theo `kind`; ứng viên món trong `quan` duyệt theo mã Unicode trước khi chọn đều bằng `Streams`.
- **Làm tròn khi xuất:** số thực làm tròn 3 chữ số thập phân ở bước ghi JSONL (`chonoi/jsonl.py`); mọi phép so bán kính, tính giá, tính boa dùng giá trị chính xác trước khi định dạng.
- **Tất định byte-cho-byte:** cùng seed, đầu vào, tham số và bản chạy phải ra JSONL và file kho giống nhau từng byte.
