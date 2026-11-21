# Hợp đồng 1: File kho cá thể (`gather` → `quan` & `day`) — v1.2

Khớp **PRD Phase 3 (TICKET-03) — Mục 1**, [ADR-0001](../adr/0001-item-instance-inventory.md) và [`chonoi/inventory.py`](../../chonoi/inventory.py).

## 1. Schema JSON (Breaking Change ở v1.2)

File UTF-8 JSON chỉ gồm **đúng 1 khóa gốc** `"items"` là **mảng cá thể** sắp theo `id`:

```json
{"items":[{"id":"I1","kind":"ca_linh","fresh":100},{"id":"I2","kind":"ca_loc","fresh":97.5}]}
```

- Kho rỗng hợp lệ: `{"items":[]}`.
- File mẫu chuẩn v1.2: [`inventory.v12.sample.json`](inventory.v12.sample.json).

### Ràng buộc dữ liệu

| Trường | Kiểu | Ràng buộc |
|---|---|---|
| gốc | `object` | Chỉ có đúng khóa `"items"`. |
| `items` | `array` | Ở v1.2 phải là mảng cá thể; **file kho đếm (`{"items":{"ca_loc":1}}`) bị từ chối với mã thoát `2`**. |
| `items[].id` | `string` | Chuỗi khác rỗng, duy nhất trong toàn bộ nơi chứa; cấp `I1, I2, …` tăng đơn điệu xuyên pha và xuyên Ngày. |
| `items[].kind` | `string` | 6 ID nguyên liệu chuẩn: `ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo`. |
| `items[].fresh` | `number` | Số hữu hạn trong `[0, 100]`. Xuất đủ độ chính xác để đọc lại không lệch giá trị và nhánh tại ngưỡng `30`. |

## 2. Quy tắc độ tươi & bàn giao

- **Số học chính xác:** Lưu nội bộ bằng `Fraction` (chuẩn hóa lưới `240` đơn vị/điểm tươi):
  - Hàng mới bắt/hái: `fresh = 100`, bắt đầu hao từ bước sau.
  - `gather`: giảm `0.5/s` (`2/240 = 1/120` mỗi tick), kẹp đáy `0`, dừng khi `pause`.
  - `quan`: giảm `0.25/s` (`1/240` mỗi tick) kể cả hàng đang giữ chỗ, kẹp đáy `0`, dừng khi `pause`.
  - `shop`: hàng thô dư **không hao tươi** trong Shop.
  - Ươn: `fresh < 30` (so trước khi làm tròn); vẫn chiếm ô/kho, không dùng nấu.
- **Độc lập (`gather --inventory-out` → `quan --inventory`):**
  - Ghi nguyên tử 1 lần khi `gather_end` (ngất ghi `{"items":[]}`); chạm `--ticks` giữ nguyên đường dẫn đích.
  - Kho quán nhận nguyên số lượng, `id` và độ tươi, kể cả hàng ươn; trần `hold_capacity` không áp lên kho quán.
- **Vòng ngày (`--mode day`):**
  - Bàn giao trong cùng tick chuyển pha, không hao thêm; ca quán chạy từ bước sau.
  - `IdAllocator` cho họ `I` duy trì xuyên pha và xuyên Ngày; mẫu `gather.hold` giữ nguyên `id` ở Ngày 1 và cấp `id` mới theo thứ tự ở Ngày kế.
