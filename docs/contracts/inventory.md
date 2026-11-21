# Hợp đồng 1: File kho (`gather` → `quan`) — v1.0

Khớp **PRD Phase 1 — Mục 5 & Mục G** và triển khai chuẩn tại [`chonoi/inventory.py`](../../chonoi/inventory.py).

## 1. Schema JSON

File UTF-8 JSON chỉ gồm **đúng 1 khóa gốc** `"items"`:

```json
{"items":{"bong_sung":2,"ca_loc":1}}
```

- Kho rỗng hợp lệ: `{"items":{}}`.
- File mẫu chuẩn để `sim/quan` và `qa` dùng ngay khi làm song song: [`inventory.sample.json`](inventory.sample.json).

### Ràng buộc dữ liệu (Phase 1)

| Trường | Kiểu | Ràng buộc |
|---|---|---|
| gốc | `object` | Chỉ được có đúng khóa `"items"` (không khóa thừa, không thiếu). |
| `items` | `object` | Map `kind -> count`. |
| `kind` | `string` | Chỉ chấp nhận 4 ID nguyên liệu Phase 1: `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`. |
| `count` | `int` | Số nguyên `>= 0` (không chấp nhận `bool`, `float`, `string`, số âm). |

### Công thức món tiêu thụ từ kho (Phase 1)

| `dish_id` | Tên món | Công thức (`recipe`) |
|---|---|---|
| `ca_loc_nuong_trui` | Cá lóc nướng trui | `{"ca_loc": 1}` |
| `goi_bong_sung` | Gỏi bông súng | `{"bong_sung": 2}` |
| `lau_ca_linh_dien_dien` | Lẩu cá linh bông điên điển | `{"ca_linh": 3, "bong_dien_dien": 1}` |

## 2. Quy tắc bên ghi (`sim/gather` + `runner`)

- Chỉ ghi khi chạy `--mode gather --inventory-out <path>` **và** buổi sáng kết thúc bằng `gather_end` (`reason` là `docked`, `time`, hoặc `fainted`).
- Ghi **đúng 1 lần** sau khi `gather_end` xảy ra; nội dung `{"items": ...}` phải khớp hoàn toàn với `data.inventory` trong event `gather_end`:
  - `docked` / `time`: tổng hợp số lượng từ `hold` hiện còn trong giỏ.
  - `fainted`: giỏ bị mất hết (LIFO), ghi kho rỗng `{"items":{}}`.
- Nếu dừng sớm do chạm `--ticks` (`reason: "tick_limit"`) mà chưa có `gather_end`: **không tạo và không ghi đè** file đích.
- Bỏ tất cả khóa có số lượng `0`; sắp khóa `kind` theo thứ tự chữ cái (Unicode) và xuất JSON gọn `separators=(",", ":")` kết thúc bằng `\n` để **ổn định từng byte**.
- **Ghi nguyên tử:** ghi ra file tạm trong cùng thư mục đích rồi `os.replace()` sang đường dẫn đích sau khi ghi xong.

## 3. Quy tắc bên đọc (`sim/quan` + CLI)

- Chỉ hợp lệ với `--mode quan --inventory <path>` (truyền `--inventory` cho `gather` hoặc `--inventory-out` cho `quan` → thoát mã `2`).
- Không được khai đồng thời `--inventory` và `scenario.quan.stock` → thoát mã `2`.
- Từ chối ngay lúc khởi tạo (trước khi ghi JSONL) với **mã thoát `2`** và chẩn đoán qua `stderr` nếu:
  - File không đọc được / sai JSON / có khóa gốc khác `"items"`.
  - Có `kind` lạ ngoài danh sách Phase 1.
  - Có giá trị âm, không phải số nguyên, hoặc là `boolean`.
- Khóa `kind` vắng mặt được hiểu là `0`. Khóa bằng `0` bị bỏ qua khi nạp vào `stock`.
- **Trần giỏ (`hold_capacity`) không áp lên kho quán.**
- Khi chạy `quan` độc lập không có cả `--inventory` lẫn `scenario.quan.stock`: `stock` khởi tạo là `{}` (rỗng).

## 4. Smoke test tích hợp 2 tiến trình (Contract G)

Tạo `dock.json` với `{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}` và `dock-inputs.json` với `{"frames":[{"tick":0,"interact":true}]}`:

```bash
python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather.jsonl --inventory-out catch.json
python3 -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl
```

Kỳ vọng:
- `catch.json` có nội dung `{"items":{"bong_sung":2,"ca_loc":1}}`.
- Snapshot tick `0` trong `quan.jsonl` có `"stock":{"bong_sung":2,"ca_loc":1}`.
