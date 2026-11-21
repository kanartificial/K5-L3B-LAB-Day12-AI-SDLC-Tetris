# Kiểm chứng Phase 3 — TICKET-03 “Mùa Nước Nổi” (Contract v1.2)

> Manifest `game.contract.json`: `contract_version: "1.2"`, `tuning.freshness = {initial 100, gather_decay_per_s 0.5, quan_decay_per_s 0.25, spoiled_below 30}`.
> Phạm vi nhóm 4 người: **Lõi độ tươi + kho cá thể**. Không làm mở rộng (`current`, `reservations`), không khai `extensions`.
> Mã AC theo [docs/plan/phase-3.md](../plan/phase-3.md). Bằng chứng nằm trong [docs/proof/phase-3/](../proof/phase-3/).

## Lệnh tái lập (chạy ở commit gắn tag `phase-3`)

```bash
PYTHONPATH="tests;." python -m unittest discover -s tests -v        # Linux/macOS: tests:.
python tools/smoke_p3.py all                                       # ngưỡng, bàn giao file, mã 2, day, regression
python tools/check_determinism.py --proof docs/proof/phase-3       # 6 kịch bản × 3 seed × 2 lần, so byte
```

## AC-P3-xx → bằng chứng → kết quả

| AC | Yêu cầu TICKET-03 | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P3-01 | `contract_version "1.2"` + `freshness`. File kho `{"items":[{id,kind,fresh}]}`, rỗng `{"items":[]}`. Kho đếm, kind lạ, id trùng/rỗng, fresh ngoài [0,100] → mã 2, không ghi output | `test_contract_p3.ContractV12` (3 test) · `test_gather_p3.AdapterAndSchemaV12` · [reject.md](../proof/phase-3/reject.md) (5/5) | ĐẠT |
| AC-P3-02 | Gather: hàng mới fresh 100, hao 0.5/s từ bước sau, pause dừng hao, `spoiled` đúng 1 lần theo id khi qua ngưỡng, id `I1…` theo thứ tự vào giỏ, `lost` cá thể LIFO, ngất ghi kho rỗng, chạm `--ticks` trước `gather_end` thì giữ nguyên đích | Ví dụ ticket fresh 30 → `spoiled` tick 1: [threshold.md](../proof/phase-3/threshold.md) · `test_gather_p3` (10 test) · `test_contract_p3.TicketExamples` | ĐẠT |
| AC-P3-03 | Quán: kho giữ cả hàng ươn, hao 0.25/s kể cả hàng đang giữ, `spoiled` theo id trước khi xử lý giữ chỗ, giữ theo id (tươi nhất rồi id), nhả rồi thử giữ lại đúng 1 lần → `unfulfillable` và khách chờ tới hạn, `base_price = floor(giá × avg fresh / 100)` lúc nấu, boa tính trên giá đã chốt, `cook_started.items` sắp theo (kind, id) | `test_quan_p3` (7 test) · `test_contract_p3.QuanFreshnessCli` (fresh 50 → giá 29, giữ lại I3, `unfulfillable` → `customer_left` theo patience) · [quan.md](../proof/phase-3/quan.md) | ĐẠT |
| AC-P3-04 | `day`: Ngày 1 giữ id mẫu, Ngày kế cấp id mới tăng tiếp, bàn giao cùng tick không hao thêm, quán chạy từ bước sau, Shop nhận cá thể và không hao | [day_hold.md](../proof/phase-3/day_hold.md) (6/6) · [day.md](../proof/phase-3/day.md) (`--days 1` 1.4 s, `--days 5` D1–D5) · `test_contract_p3.DayHandoffV12` (3 test) | ĐẠT |
| AC-P3-05 | HUD cho người chơi đọc độ tươi / nhận ra hàng ươn | `chonoi/web/index.html`: màu theo `freshColor`, nhãn “Ươn: n”, trạng thái “Giỏ n (ươn k)”, thông báo `spoiled: "Ươn!"`. `test_live` đạt | ĐẠT (kiểm thủ công UI: @ThuThaoVuong) |
| AC-P3-06 | Smoke 2 tiến trình theo ticket (fresh 100, cập bến frame 0 → `quan --inventory --ticks 0`, so id/kind/fresh), regression P1–P2 còn hiệu lực, tất định | [integration.md](../proof/phase-3/integration.md) (5/5) · [regression.md](../proof/phase-3/regression.md) (119/119, 0 skip) · [determinism.md](../proof/phase-3/determinism.md) (18/18) | ĐẠT |

## Lỗi tích hợp tìm thấy khi bật v1.2 (đã sửa, có test hồi quy)

| # | Triệu chứng | Nguyên nhân | Sửa | Test giữ lỗi |
|---|---|---|---|---|
| 1 | Ở manifest 1.1, `main` đỏ 18/105 test: quán báo `kho Quán v1.2 phải là mảng cá thể` | `QuanSim` bật độ tươi khi manifest có `tuning.freshness`, còn gather/runner dựa vào `contract_version` | `QuanSim(contract_version=…)`, chỉ bật khi `is_v12`. Runner truyền version cho cả `quan` độc lập và `day` | toàn bộ bộ P1/P2 |
| 2 | Quán trả mã 2 với chính file kho v1.2 mà gather vừa ghi; `day` có hàng cũng thoát mã 2 | `read_inventory` và bàn giao trong `day` đưa `fresh` sang dạng `Fraction`, còn `_load_fresh_stock` chỉ nhận `int/float` | Nhận thêm `Fraction` và giữ nguyên giá trị chính xác | `test_p3_06_two_process_file_handoff_smoke`, `test_p3_06_file_roundtrip_keeps_threshold_branch` |
| 3 | `day` crash `TypeError` khi chuyển quán → Shop | `list(QuanSim.stock)` ở v1.2 trả về list các id vì `stock` là dict theo id | Shop nhận `sort_by_id(stock.values())` | `test_p3_04_quan_to_shop_carries_item_instances_without_decay` |

Trên HEAD trước khi sửa (`94f2328`, chỉ bật 1.2), `test_contract_p3` fail 5/14 test. Sau khi sửa, đạt 14/14.

## Test cũ bị thay bởi luật v1.2 (lý do)

Luật P1/P2 tính theo **kind và số lượng** vẫn còn hiệu lực, nên test giữ nguyên ý nghĩa và chỉ đổi fixture/assert sang schema cá thể (helper `inst`, `kinds_of`, `counts`, `ids_of` trong `tests/helpers.py`):

- **Fixture** `gather.hold`, `quan.stock` và file `--inventory` đổi từ mảng kind / map đếm sang mảng `{id,kind,fresh}`. Kho rỗng `{}` đổi thành `[]`. Áp dụng cho `test_gather_p1`, `test_gather_p2`, `test_quan_p1`, `test_integration_p1`, `test_smoke_p1`, `test_contract_p2`.
- **`lost`** (`monster_hit`/`faint`) là cá thể LIFO: so kind như cũ và thêm so id (`I3, I2, I1`).
- **`reserved`** đổi từ map đếm sang mảng id (`["I1"]`). **`cook_started.items`** là cá thể.
- **Giá:** `test_cook_pick_serve_and_pay` và `test_gather_catch_and_harvest_flows_into_quan_service_and_payment` đổi giá niêm yết 60 thành giá theo tươi `floor(60 × (100 − 121/240) / 100) = 59`, boa `floor(59 × 0.2) = 11` ([THAY THẾ] Giá niêm yết → giá theo tươi).
- **Các test “mã 2”** trước đây có thể đạt nhầm vì sai schema (giỏ vượt sức chứa, kho sai, `stock` xung đột, mode sai) nay dùng fixture v1.2 hợp lệ, để mã 2 đến đúng từ lỗi mà test định kiểm.
- **`test_contract_p2`:** trước chỉ chạy khi version đúng `"1.1"` (sang 1.2 thì 32 test tự skip). Nay chạy ở cả `1.1` và `1.2`, nên regression P2 vẫn có hiệu lực.

## Ngoài phạm vi / chưa làm
- Mở rộng `current` và `reservations`: không làm (nhóm 4 người không bắt buộc). `extensions` để trống.
- Chợ Chú Sáu / bán hàng: game không có, nên luật “hàng mua nhập fresh 100” và “bán cá thể tươi nhất” không áp dụng.
