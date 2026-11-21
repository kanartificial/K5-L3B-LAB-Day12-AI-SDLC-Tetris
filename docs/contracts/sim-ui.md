# Hợp đồng 2: Giao diện `sim/*` ↔ `client/ui` — v1.1

Khớp **PRD Phase 2 (TICKET-02) — Mục 2 & 4.2–4.4** và [`chonoi/runner.py`](../../chonoi/runner.py), [`chonoi/inputs.py`](../../chonoi/inputs.py), [`chonoi/live.py`](../../chonoi/live.py).

## 1. Lệnh đầu vào (`client/ui` / `inputs.json` → `sim/*`)

| Trường | Kiểu | Tác dụng |
|---|---|---|
| `move` | `[a, b]` trong `[-1, 1]` | Bơi (`gather`: `[x, d]`) / đi (`quan`: `[x, z]`), chuẩn hóa nếu độ dài `> 1`. |
| `interact` | `bool` (cạnh lên) | Cập bến/hái (`gather`); nấu/nhấc/phục vụ (`quan`). |
| `catch` | `bool` (cạnh lên) | Bắt đàn cá dưới nước (`gather`). |
| `pause` | `bool` (cạnh lên) | Tạm dừng / tiếp tục ở cả 3 mode (`gather`, `quan`, `day`). Bước vào `pause` chỉ tăng `tick` ngoài và đóng băng `sim_tick`, `phase_tick`, timer; cạnh lên kế phát `resumed` và chạy gameplay ngay bước đó. |
| `shop_done` | `bool` (cạnh lên) | Đóng Shop sớm trong pha `shop`. |
| `buy` | `string` khác rỗng (1-shot) | Chỉ chạy tại đúng frame khai báo (không kế thừa): `"oxygen"`, `"hp"` (hoặc mở rộng). Xử lý trước `shop_done`. |
| `attack`, `photo` | `bool` (cạnh lên) | Dành cho mở rộng `weapon`/`ca_ho`; bị bỏ qua khi mở rộng chưa bật. |

> Giữ nút qua đổi pha không tạo cạnh lên mới. Nút đúng kiểu nhưng sai pha bị bỏ qua.

## 2. Snapshot UI được đọc

### 2.1. Trường chung (mọi pha)
- `type: "snapshot"`, `tick`, `sim_tick`, `mode` (`"gather"|"quan"|"day"`), `phase` (`"gather"|"quan"|"shop"`), `phase_tick`, `state` (`"playing"|"paused"|"finished"`), `time_left_ticks`, `money`, `earned`, `reputation`, `score`.
- Riêng `--mode day`, mọi snapshot đều có thêm:
  - `day`: số Ngày hiện tại (`1..5`).
  - `day_plan`: `{"dishes": {...}, "ingredients": {...}}`.
  - `upgrades`: cấp nâng cấp **đã mua** (cập nhật ngay khi mua trong Shop).
  - `active_upgrades`: cấp nâng cấp **đang áp dụng** (sao từ `upgrades` khi bắt đầu Ngày mới).

### 2.2. Trường bổ sung v1.1 theo từng pha
- **`gather`:**
  - `player`: gồm `invuln_ticks`, `oxygen_max_ticks` & `hp_max` theo `active_upgrades`.
  - `nodes[]`: 6 nút `N1–N6` (`bong_dien_dien`, `bong_sung`, `keo_neo`).
  - `fish[]`: bổ sung `age_ticks` (số bước bơi đã qua).
  - `monsters[]`: mảng sắp theo `id`, mỗi phần tử `{id, kind, pos, waypoints, target_idx, state, state_ticks_left, recoil_dir}` (`M1` từ Ngày 1, `M2` từ Ngày 3).
- **`quan`:**
  - `player`: `{pos, vel}`.
  - `stoves[]`: `B1`, `B2`. `tables[]`: `T1–T4`.
  - Trong `day`, khách chỉ gọi món thuộc `day_plan.dishes` còn đủ kho khả dụng.
- **`shop`:**
  - `stock`: kho dư từ ca tối.
  - `time_left_ticks`: đếm ngược từ `600` về `0`.

## 3. Yêu cầu Menu, Pause & HUD tối thiểu (v1.1)
- Menu chính (**Chơi**, **Thoát**); màn chuyển pha (`DayIntro` 4s/nhấn phím, `EveningIntro`, `DayResult`, `Summary`); Pause (`Esc`/`P`, làm mờ nền, **Tiếp tục** / **Về menu**).
- **HUD sáng:** Máu, oxy (`< 25%` đổi màu/nhấp nháy), thời gian (`≤ 30 s` đổi màu), độ sâu, giỏ theo loại, danh sách cần lấy (`đã lấy / cần`), hồi bắt, gợi ý hái/cập bến, cảnh báo *"Thủy quái!"* (viền tím) và *"Hết hơi!"*.
- **HUD quán:** đồng hồ ca, tiền ca, uy tín, món & kiên nhẫn tại 4 bàn (`< 25%` đổi màu), tiến độ 2 bếp, món trên tay, kho khả dụng. Chữ không chân `≥ 18 px` ở `1280×720`, trung bình `≥ 30 FPS`.
