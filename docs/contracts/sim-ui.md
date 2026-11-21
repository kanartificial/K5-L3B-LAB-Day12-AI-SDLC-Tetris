# Hợp đồng 2: Giao diện `sim/*` ↔ `client/ui` — v1.0

Khớp **PRD Phase 1 — Mục 2, C, D, E** và khung starter tại [`chonoi/runner.py`](../../chonoi/runner.py), [`chonoi/live.py`](../../chonoi/live.py), [`chonoi/inputs.py`](../../chonoi/inputs.py).

## 1. Nguyên tắc phân tách

- **Một nguồn sự thật cho luật chơi:** Cả `headless` và `client/ui` (`chonoi.live`) chạy chung một lớp sim (`GatherSim` / `QuanSim`) thông qua `runner.Session` ở 60 tick/s.
- **UI chỉ ĐỌC snapshot và GỬI lệnh input:** `client/ui` không đọc/sửa biến nội bộ của `sim/*`, không tính lại luật chơi, không dùng đồng hồ/RNG của UI làm ảnh hưởng tới `Streams` của sim.
- **Sáng tạo giao diện/âm thanh:** Hiệu ứng, hình ảnh, thoại, âm thanh nằm hoàn toàn ở `client/ui` (tắt ở headless). Khi thiếu trường tùy chọn, UI tự bỏ qua để không vỡ khi các lát đang phát triển song song.

## 2. Lệnh đầu vào (`client/ui` → `sim/*`)

### Điều khiển gợi ý trên bàn phím

| Phím | Lệnh gửi vào sim | Tác dụng |
|---|---|---|
| `WASD` / phím mũi tên | `move: [a, b]` | Bơi (`gather`: `[x, d]`, `+d` là lặn xuống) / Đi (`quan`: `[x, z]`, `+z` là hướng bắc). Mỗi thành phần trong `[-1, 1]`, tự chuẩn hóa nếu độ dài `> 1`. |
| `E` | `interact: bool` | Cạnh lên (`false -> true`): cập bến hoặc hái nút (`gather`); nấu / bưng / phục vụ (`quan`). |
| `Space` | `catch: bool` | Cạnh lên (`false -> true`): bắt đàn cá khi lặn (`gather`); bỏ qua ở `quan`. |
| `R` | `POST /restart` | Khởi động lại lượt chơi trên live UI (không phải input của headless). |

### HTTP API của `chonoi.live` (`chonoi/live.py` ↔ `chonoi/web/index.html`)

| Endpoint | Request | Response |
|---|---|---|
| `GET /state` | — | JSON snapshot hiện tại (xem mục 3) + các trường live bổ sung: `meta` (`tuning[mode]`), `events` (tối đa 40 event gần nhất), `finished` (`bool`), `reason` (`string\|null`), `error` (`string\|null`). |
| `POST /input` | `{"move":[a,b], "interact":bool, "catch":bool}` (chỉ cần gửi trường thay đổi) | `200 {"ok":true}` hoặc `400 {"error":"..."}`. `LiveInputs` ghi nhớ cạnh lên giữa 2 tick để không mất thao tác bấm nhanh. |
| `POST /restart` | rỗng | `200 {"ok":true}` — reset `Session` về tick 0 cùng `seed` và `scenario`. |

### Python API nội bộ (`runner.Session`)

- `sess.step(inp: InputState) -> list[dict]`: chạy 1 tick, trả về danh sách dòng event có `tick = k + 1`.
- `sess.snapshot() -> dict`: trả về snapshot hoàn chỉnh (trường chung + trường riêng của `mode`).
- `sess.end_row() -> dict`: trả về dòng `end`.
- `sess.write_inventory_if_done(path)`: ghi file kho 1 lần nếu `mode == "gather"` và `sess.done`.

## 3. Trạng thái UI được đọc (`sim/*` → `client/ui`: Snapshot)

### 3.1. Trường chung (mọi `mode`)

```json
{
  "type": "snapshot",
  "tick": 0,
  "sim_tick": 0,
  "mode": "gather",
  "phase": "gather",
  "phase_tick": 0,
  "state": "playing",
  "time_left_ticks": 10800,
  "money": 0,
  "earned": 0,
  "reputation": 3.0,
  "score": 300
}
```

- `state`: `"playing"` hoặc `"finished"`.
- `score`: `earned + tuning.score.reputation_multiplier * floor(reputation)` (`earned + 100 * floor(reputation)`).

### 3.2. Trường riêng của `gather`

```json
{
  "player": {
    "pos": [2.0, 0.0],
    "vel": [0.0, 0.0],
    "heading_deg": 0.0,
    "oxygen_ticks": 1800,
    "oxygen_max_ticks": 1800,
    "hp": 3,
    "hp_max": 3,
    "zero_oxy_ticks": 0,
    "invuln_ticks": 0,
    "catch_cd_ticks": 0,
    "at_surface": true
  },
  "hold": ["ca_loc", "bong_sung"],
  "hold_count": 2,
  "hold_capacity": 12,
  "nodes": [
    {"id": "N1", "pos": [12.0, 0.0], "kind": "bong_dien_dien", "ready": true, "regrow_ticks": 0}
  ],
  "fish": [
    {"id": "F1", "pos": [15.0, 5.0], "kind": "ca_linh", "heading_deg": 0}
  ]
}
```

- `nodes[]`, `fish[]` luôn sắp theo `ids.sort_by_id`.
- `hold` giữ đúng thứ tự nhặt (mới nhất ở cuối mảng, bỏ theo LIFO khi ngất).
- `nodes[].ready` bằng `regrow_ticks == 0`.
- Lưu ý tọa độ: mặt cắt nhìn ngang `[x, d]`, `x ∈ [0, 100]` sang phải, `d ∈ [0, 30]` hướng xuống (`d = 0` là mặt nước, `d <= surface_depth` là `at_surface`).

### 3.3. Trường riêng của `quan`

```json
{
  "player": {
    "pos": [8.0, 5.0],
    "vel": [0.0, 0.0]
  },
  "stock": {"bong_sung": 2, "ca_loc": 1},
  "hand": null,
  "stoves": [
    {"id": "B1", "pos": [2.0, 8.0], "state": "idle", "dish": null, "cook_ticks_left": 0, "ready_ticks": 0}
  ],
  "tables": [
    {"id": "T1", "pos": [9.0, 2.0], "customer_id": "C1"}
  ],
  "customers": [
    {
      "id": "C1",
      "table_id": "T1",
      "dish_id": "ca_loc_nuong_trui",
      "order_tick": 120,
      "state": "waiting",
      "patience_ticks_left": 3600,
      "eat_ticks_left": 0,
      "order_status": "reserved",
      "reserved": {"ca_loc": 1},
      "base_price": 60,
      "tip": 0
    }
  ]
}
```

- `stock`: tồn vật lý hiện có (đã gồm phần đang được khách `reserved`), chỉ chứa khóa có số lượng `> 0`, sắp theo `kind`. **Kho khả dụng** để hiển thị trên HUD = `stock[k] - sum(c.reserved.get(k, 0) for c in customers)`.
- `hand` và `stoves[].dish`: `null` hoặc payload món `{"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}`.
- `stoves[].state`: `"idle"` | `"cooking"` | `"ready"`.
- `customers[]`: chỉ liệt kê khách **còn ngồi**, sắp theo `ids.sort_by_id`.
  - `state`: `"waiting"` | `"eating"`.
  - `order_status`: `"reserved"` | `"assigned"` | `"unfulfillable"` | `"served"`.
- `tables[].customer_id`: `id` khách đang ngồi hoặc `null` nếu bàn trống.
- Lưu ý tọa độ: nhìn từ trên xuống `[x, z]`, `x ∈ [0, 16]` hướng đông, `z ∈ [0, 10]` hướng bắc (lưu ý đảo trục Y khi vẽ lên HTML Canvas nếu gốc Canvas ở góc trên-trái).

## 4. Yêu cầu HUD tối thiểu (PRD mục 2)

- **Buổi sáng (`gather`):** thời gian còn lại (`time_left_ticks / 60`), thanh oxy (`oxygen_ticks / oxygen_max_ticks`), Máu (`hp / hp_max`), giỏ (`hold_count / hold_capacity` + danh sách nguyên liệu trong `hold`).
- **Buổi tối (`quan`):** thời gian còn lại, kho khả dụng (tồn trừ giữ chỗ), món khách gọi (`customers[].dish_id`), thanh kiên nhẫn (`patience_ticks_left`), trạng thái bếp (`stoves[].state`, `cook_ticks_left`), món trên tay (`hand`), tiền (`money` / `earned`) và uy tín (`reputation`).
