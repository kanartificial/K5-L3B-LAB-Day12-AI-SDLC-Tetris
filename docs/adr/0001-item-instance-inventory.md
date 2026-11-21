# ADR-0001: Chuyển đổi từ kho đếm sang kho cá thể có độ tươi (Contract v1.2)

- **Ngày:** 2026-11-21
- **Trạng thái:** Đã thống nhất (Phase 3 — TICKET-03)
- **Người đề xuất:** Khổng Ngọc Anh (`@kanartificial`, Integrator)

## Bối cảnh
TICKET-03 (Change Request *Mùa Nước Nổi*) thay thế schema kho đếm (`{"items":{"ca_loc":1}}`) bằng kho cá thể có ID duy nhất và độ tươi (`{"items":[{"id":"I1","kind":"ca_loc","fresh":100}]}`), kèm quy tắc hao tươi (`0.5/s` ở `gather`, `0.25/s` ở `quan`), ngưỡng ươn `< 30`, giữ chỗ theo `id`, và chốt giá theo độ tươi trung bình.

Thay đổi này mang tính **breaking change** ảnh hưởng đồng thời tới 4 module (`inventory/scenario`, `sim/gather`, `sim/quan`, `client/ui`) và toàn bộ test P1–P2.

## Quyết định
1. **Biểu diễn số học chính xác (`Fraction` + lưới 240 đơn vị/điểm):**
   - Trong `chonoi/inventory.py`, mọi độ tươi được lưu nội bộ bằng `fractions.Fraction`.
   - `gather` trừ đúng `1/120` (`2/240`) mỗi tick, `quan` trừ đúng `1/240` mỗi tick.
   - Khi đọc lại từ JSON, số thực nằm trong sai số `<= 1e-9` quanh bội số `1/240` được khôi phục chính xác về `Fraction(u, 240)` để so ngưỡng `< 30` và tính `floor(price * avg_fresh / 100)` không bao giờ lệch vì sai số float.
2. **Chiến lược tích hợp song song giữ `main` luôn xanh:**
   - Adapter (`inventory.py`, `scenario.py`, `contract.py`, `runner.py`, `headless.py`, `live.py`), `sim/gather.py` và `sim/shop.py` chọn schema theo `contract_version` (`"1.1"` vs `"1.2"`).
   - Giữ `game.contract.json` ở `"1.1"` (đã bổ sung khối `tuning.freshness`) trong lúc `@KimY22-it` hoàn thiện `sim/quan.py` (`AC-P3-03`) và `@ThuThaoVuong` hoàn thiện HUD (`AC-P3-05`), nhờ đó `main` luôn pass 100% test.
   - Ngay khi `sim/quan.py` hỗ trợ kho cá thể, bật `"contract_version": "1.2"` trong `game.contract.json`; từ thời điểm đó file kho đếm trả mã thoát `2`.
3. **Cấp ID cá thể xuyên pha & xuyên Ngày:**
   - `DaySession` giữ duy nhất một `self.item_ids = IdAllocator()` truyền qua mọi pha và mọi Ngày (`I1, I2, …` tăng đơn điệu không cấp lại).

## Hệ quả
- **Tích cực:** `main` không bao giờ vỡ trong giai đoạn chuyển đổi; độ chính xác tại ngưỡng `30` và phép `floor` đạt tuyệt đối; `gather` + adapter + `shop` được kiểm thử độc lập ở v1.2 ngay qua `tests/test_gather_p3.py`.
- **Chi phí:** Sau khi bật `"contract_version": "1.2"`, cần cập nhật các fixture kho đếm cũ trong test hồi quy P1–P2 sang kho cá thể và ghi lý do vào `CHANGELOG.md` & `docs/verification/phase-3.md`.
