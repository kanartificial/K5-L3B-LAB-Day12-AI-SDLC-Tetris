# Kế hoạch Phase 3 — Change Request “Mùa Nước Nổi” (≤ 1 trang)

> Tham chiếu: [PRD Phase 3 (TICKET-03)](../prd-phase-3.md) · [TEAM.md](../../TEAM.md) · [Hợp đồng tích hợp](../contracts/README.md) · Thời lượng: **35 phút (1:55–2:30)** · Hạn tag `phase-3`: **2:30**.
> Phạm vi nhóm 4 người: **100% Lõi v1.2 (Độ tươi & Kho cá thể)** — không bắt buộc mở rộng (`current` / `reservations`).

## 1. Quyết định đổi schema & Thứ tự tích hợp giữ `main` chạy được
- **Breaking change schema kho (`v1.1 → v1.2`):** Đổi `{"items":{"ca_loc":1}}` (kho đếm) sang `{"items":[{"id":"I1","kind":"ca_loc","fresh":100}]}` (kho cá thể, sắp theo `id`). Ở `contract_version: "1.2"`, mọi file kho đếm trả mã thoát `2`.
- **Biểu diễn số học chính xác độ tươi:** Dùng số hữu tỷ / số nguyên `fresh_units` với hệ số **`240` đơn vị = 1 điểm tươi** (`100` → `24000`, ngưỡng ươn `30` → `7200`): `gather` trừ đúng `2` đơn vị/tick (`0.5/s`), `quan` trừ đúng `1` đơn vị/tick (`0.25/s`), dùng `Fraction`/số nguyên cho các fixture bất kỳ để so `< 30` và tính `floor(price × avg_fresh / 100)` không sai số dấu phẩy động.
- **Thứ tự tích hợp an toàn (không làm đỏ `main`):**
  1. **Bước 1 (0–7'):** Chốt `docs/contracts/` v1.2, `chonoi/inventory.py` hỗ trợ chọn schema theo `contract_version` (giữ `game.contract.json` ở `"1.1"` trong lúc 4 nhánh code song song).
  2. **Bước 2 (7–20'):** Song song hoàn thiện `sim/gather`, `sim/quan`, `runner/shop`, `client/ui`, và test v1.2 (tự skip khi chưa bật `"1.2"`).
  3. **Bước 3 (20–25'):** Gộp `gather` + `quan` + `runner` + `scenario`, **bật `contract_version: "1.2"`** trong `game.contract.json` cùng cập nhật fixture/test P1–P2, chạy smoke bàn giao file + `day` ngay trên `main`.

## 2. Phân tích tác động (Impact Analysis)

| Module | File cần đổi | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|
| **Adapter & Contract** (`AC-P3-01`) | `game.contract.json` (`1.2` + `freshness`), `chonoi/{contract,inventory,scenario}.py`, `docs/contracts/*`, `CHANGELOG.md` | Đổi: `test_smoke_p1.py` (`Integration`), `test_contract_p2.py` (`QuanP2`, `DayCli`), `test_python_starter_units.py` · Thêm: test từ chối kho đếm mã `2` & scenario v1.2 | Khổng Ngọc Anh (`@kanartificial`, Integrator) |
| **Lặn & Hái** (`AC-P3-02`) | `chonoi/sim/gather.py` | Đổi: `test_gather_p1.py`, `test_gather_p2.py`, `test_contract_p2.py` (`hold`/`lost` mảng cá thể) · Thêm: test `fresh=30 → spoiled` tick 1, hao `0.5/s`, `I1/I2…`, LIFO | Khổng Ngọc Anh (`@kanartificial`) |
| **Mở Quán** (`AC-P3-03`) | `chonoi/sim/quan.py` | Đổi: `test_quan_p1.py`, `test_integration_p1.py` (`stock`/`reserved`/`items`/`base_price` theo tươi) · Thêm: test `spoiled` kho, nhả & thử giữ lại 1 lần → `unfulfillable`, giá `floor(giá × avg_fresh / 100)` + boa | Võ Thị Kim Ý (`@KimY22-it`) |
| **Vòng ngày & Shop** (`AC-P3-04`) | `chonoi/runner.py`, `chonoi/sim/shop.py` | Đổi: `test_contract_p2.py` (`DayLoop`, `ShopP2`, `DOCK_NOW` dùng mảng cá thể) · Thêm: test `id` cá thể tăng xuyên pha/Ngày, Shop không hao tươi, Ngày 2 cấp `id` mới | Khổng Ngọc Anh (`@kanartificial`) + Võ Thị Kim Ý (`@KimY22-it`) |
| **HUD / UI** (`AC-P3-05`) | `chonoi/web/index.html` | Giữ: `test_live.py` · Kiểm thủ công: đọc `hold`/`stock` mảng cá thể, hiển thị độ tươi & cảnh báo hàng ươn (`fresh < 30`) | Vương Thu Thảo (`@ThuThaoVuong`, QA Lead) |
| **QA & Bàn giao** (`AC-P3-06`) | `tests/test_contract_p3.py`, `tools/smoke_p2.py` / `tools/smoke_p3.py`, `tools/check_determinism.py`, `docs/verification/phase-3.md`, `docs/proof/phase-3/` | Thêm bộ test hộp đen v1.2 (ngưỡng 30, giữ lại khi ươn, chốt giá, bàn giao file & `day`, kho đếm → mã `2`); chạy regression P1–P2 có ghi lý do đổi test | Lý Hà Trân Trân (`@TranHa161`) + Vương Thu Thảo (`@ThuThaoVuong`) |

## 3. Phân công AC & Phụ thuộc

| AC | Phạm vi nghiệm thu | Người phụ trách | Phụ thuộc |
|---|---|---|---|
| `AC-P3-01` | Contract `1.2`, `freshness`, schema kho cá thể (`items[]`), từ chối kho đếm mã `2`, kiểm scenario v1.2, cập nhật `docs/contracts/` & `CHANGELOG.md` | `@kanartificial` | TICKET-03 |
| `AC-P3-02` | `gather`: `fresh=100` mới lấy, hao `0.5/s` đầu bước (dừng khi `pause`), `spoiled` tick 1 khi `fresh=30`, `I1…` theo thứ tự vào giỏ, `lost` LIFO mảng cá thể | `@kanartificial` | `AC-P3-01` |
| `AC-P3-03` | `quan`: `stock` mảng cá thể (giữ cả hàng ươn), hao `0.25/s`, `spoiled` theo `id` trước xử lý giữ chỗ, giữ theo `id` (tươi nhất hòa `id`), nhả & thử giữ lại 1 lần → `unfulfillable`, `base_price` theo tươi + boa, `cook_started.items` sắp `(kind, id)` | `@KimY22-it` | `AC-P3-01` |
| `AC-P3-04` | `day` & `shop`: cấp `id` xuyên pha/Ngày (Ngày 1 giữ `id` mẫu, Ngày kế cấp mới), bàn giao cùng tick không hao thêm, Shop không hao tươi | `@kanartificial` + `@KimY22-it` | `AC-P3-02`, `AC-P3-03` |
| `AC-P3-05` | HUD sáng & tối hiển thị độ tươi và nhận diện rõ hàng ươn (`fresh < 30`) | `@ThuThaoVuong` | `AC-P3-01` |
| `AC-P3-06` | Smoke file kho (`fresh:100` cập bến tick 0 → `quan --ticks 0`) & `day`, regression P1–P2 xanh (ghi lý do đổi test), `check_determinism.py`, `docs/proof/phase-3/`, `docs/verification/phase-3.md`, `docs/{clarify,ai-usage-log,retro}.md`, tag `phase-3` | `@TranHa161` + cả nhóm | `AC-P3-01` → `AC-P3-05` |

## 4. Lịch 35 phút & Rủi ro
- **0–7 phút:** Chốt tác động + hợp đồng v1.2 + adapter kho cá thể (`AC-P3-01`).
- **7–20 phút:** Song song `gather`, `quan`, `day/shop`, `HUD`, `test_contract_p3.py`.
- **Phút 20 (Checkpoint):** Ghép nhánh & chạy smoke bàn giao file kho cá thể; standup 2 phút hỗ trợ lát chậm.
- **20–32 phút:** Bật `contract_version: "1.2"`, cập nhật regression P1–P2 có ghi lý do, chạy `smoke` + `check_determinism.py`, hoàn thiện `CHANGELOG.md`, `docs/verification/phase-3.md`, `docs/retro.md`.
- **32–35 phút:** Dự phòng, kiểm DoD và đẩy tag **`phase-3`** chậm nhất **2:30**.
- **Rủi ro chính:** Sai số float ở ngưỡng `30` và `floor(price × avg_fresh / 100)` → giải quyết triệt để bằng số học chính xác (`240` đơn vị / điểm tươi hoặc `Fraction`); lệch `id` xuyên Ngày → dùng một bộ cấp `item_ids` chung trong `DaySession` truyền qua mọi pha; test cũ P1–P2 vỡ hàng loạt do schema kho đếm → rà theo bảng tác động mục 2 và ghi rõ lý do từng test sửa trong `CHANGELOG.md` & `docs/verification/phase-3.md`.
