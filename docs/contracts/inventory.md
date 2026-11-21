# Hợp đồng 1: File kho (`gather` → `quan` & `day`) — v1.1

Khớp **PRD Phase 2 (TICKET-02) — Mục 1, 2 & 4.1** và triển khai chuẩn tại [`chonoi/inventory.py`](../../chonoi/inventory.py).

## 1. Schema JSON

File UTF-8 JSON chỉ gồm **đúng 1 khóa gốc** `"items"`:

```json
{"items":{"bong_sung":2,"ca_loc":1}}
```

- Kho rỗng hợp lệ: `{"items":{}}`.
- File mẫu: [`inventory.sample.json`](inventory.sample.json).

### Ràng buộc dữ liệu (v1.1 — 6 nguyên liệu)

| Trường | Kiểu | Ràng buộc |
|---|---|---|
| gốc | `object` | Chỉ được có đúng khóa `"items"`. |
| `items` | `object` | Map `kind -> count`. |
| `kind` | `string` | 6 ID nguyên liệu chuẩn: `ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo`. |
| `count` | `int` | Số nguyên `>= 0` (từ chối `bool`, `float`, `string`, số âm → mã thoát `2`). |

### Thực đơn chuẩn (6 món)

| `dish_id` | Tên món | Công thức (`recipe`) | Nấu | Giá |
|---|---|---|---|---|
| `ca_loc_nuong_trui` | Cá lóc nướng trui | `{"ca_loc": 1}` | 6 s | 60 |
| `goi_bong_sung` | Gỏi bông súng | `{"bong_sung": 2}` | 4 s | 40 |
| `lau_ca_linh_dien_dien` | Lẩu cá linh bông điên điển | `{"ca_linh": 3, "bong_dien_dien": 1}` | 10 s | 120 |
| `canh_chua_ca_loc` | Canh chua cá lóc bông điên điển | `{"ca_loc": 1, "bong_dien_dien": 1}` | 8 s | 90 |
| `ca_keo_nuong` | Cá kèo nướng muối ớt | `{"ca_keo": 2}` | 6 s | 70 |
| `lau_mam` | Lẩu mắm miền Tây | `{"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}` | 12 s | 200 |

## 2. Quy tắc bàn giao kho

- **Chế độ độc lập (`gather --inventory-out` → `quan --inventory`):** giữ nguyên v1.0 (ghi đúng 1 lần khi có `gather_end`, nguyên tử qua file tạm, ngất ghi rỗng, chạm `--ticks` không ghi).
- **Chế độ `--mode day`:**
  - Cấm dùng `--inventory` và `--inventory-out` (trả mã `2`).
  - Cấm khai `quan.stock` và `quan.reputation` trong scenario `day` (trả mã `2`); dùng `gather.hold` để dựng hàng.
  - Khi `gather_end` xảy ra (kể cả `fainted`), `DaySession` bàn giao `gather.inventory_items()` trực tiếp trong bộ nhớ sang `QuanSim` theo đúng schema đếm v1.0.
  - Kho dư sau ca tối hiển thị trong snapshot Shop (`stock`) và bị bỏ sau khi Shop đóng.
