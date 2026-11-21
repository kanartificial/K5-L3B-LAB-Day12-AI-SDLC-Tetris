# Hợp đồng 2: Giao diện `sim/*` ↔ `client/ui` — v1.2

Khớp **PRD Phase 3 (TICKET-03) — Mục 1** (kế thừa toàn bộ v1.1).

## 1. Thay đổi Snapshot từ v1.1 → v1.2
- **`gather.hold`:** mảng cá thể `[{"id": "I1", "kind": "ca_linh", "fresh": 99.5}, ...]` theo **thứ tự nhặt** (mới nhất cuối mảng, LIFO khi rơi/ngất).
- **`quan.stock` và `shop.stock`:** mảng cá thể `[{"id": "I1", "kind": "ca_linh", "fresh": 82.25}, ...]` sắp theo `id` (bao gồm cả hàng ươn `fresh < 30`).
- **`quan.customers[].reserved`:** mảng `id` cá thể đang giữ `["I1", "I4"]` (thay cho map đếm).
- **`quan.customers[].order_status`:** giữ `"reserved" | "assigned" | "unfulfillable" | "served"` (`unfulfillable` kích hoạt khi cá thể giữ bị ươn và thử giữ lại không đủ).
- **Lệnh đầu vào (`inputs` / `POST /input`):** giữ nguyên v1.1 (`move`, `interact`, `catch`, `pause`, `shop_done`, `buy`, `attack`, `photo`).

## 2. Yêu cầu HUD bổ sung ở Phase 3 (v1.2)
- Ở cả **buổi sáng (`gather`)** và **buổi tối (`quan`)**, HUD phải cho người chơi đọc được **độ tươi** (`fresh`) hoặc nhận ra ngay **hàng ươn** (`fresh < 30`) bằng số, thanh màu, nhãn hoặc biểu tượng.
- Khi đọc `stock` ở `quan`, UI nên hỗ trợ cả `Array` (v1.2) lẫn `Object` (v1.1) trong lúc chuyển đổi để không bị vỡ giao diện.
