# Smoke tích hợp gather → kho → quan (phút 20)

- Commit: `957e58c (+ thay đổi chưa commit)` · contract_version `1.1`
- Thời điểm: 2026-11-21 11:09:00

| Kiểm | Kết quả | Chi tiết |
|---|---|---|
| gather chạy exit 0 | ĐẠT |  |
| file kho ghi đúng giỏ | ĐẠT | kho = {'items': {'bong_dien_dien': 1, 'bong_sung': 2, 'ca_linh': 3, 'ca_loc': 1}} |
| gather_end.reason = docked, inventory = file kho | ĐẠT | {'reason': 'docked', 'inventory': {'items': {'bong_dien_dien': 1, 'bong_sung': 2, 'ca_linh': 3, 'ca_loc': 1}}} |
| quan đọc kho exit 0 | ĐẠT |  |
| snapshot quan tick 0: stock = kho bàn giao | ĐẠT | stock = {'bong_dien_dien': 1, 'bong_sung': 2, 'ca_linh': 3, 'ca_loc': 1} |
| có khách gọi món từ kho bàn giao (≤ 300 tick) | ĐẠT | [{'order_id': 'C1', 'table_id': 'T1', 'dish_id': 'goi_bong_sung'}] |

Lệnh đã chạy:

- `python3 -m chonoi.headless --mode gather --seed 42 --ticks 60 --scenario docs/proof/phase-2/integration/gather.scenario.json --inputs docs/proof/phase-2/integration/gather.inputs.json --inventory-out docs/proof/phase-2/integration/inventory.json --out docs/proof/phase-2/integration/gather.jsonl`
- `python3 -m chonoi.headless --mode quan --seed 42 --ticks 300 --inventory docs/proof/phase-2/integration/inventory.json --out docs/proof/phase-2/integration/quan.jsonl`
