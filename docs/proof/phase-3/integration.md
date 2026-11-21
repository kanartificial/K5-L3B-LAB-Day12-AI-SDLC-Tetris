# Smoke bàn giao kho cá thể gather → file → quan (v1.2)

- Commit: `0b13736 (+ thay đổi chưa commit)` · contract_version `1.2`
- Thời điểm: 2026-11-21 12:38:04

| Kiểm | Kết quả | Chi tiết |
|---|---|---|
| gather exit 0 | ĐẠT |  |
| file kho đúng schema v1.2, I1 ca_linh hao đúng 1 bước giỏ | ĐẠT | kho = {'items': [{'id': 'I1', 'kind': 'ca_linh', 'fresh': 99.99166666666666}]} · kỳ vọng fresh 99.99166666666666 |
| gather_end(docked) tick 1, inventory cùng schema với file | ĐẠT | {"reason": "docked", "inventory": {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 99.992}]}} |
| quan --inventory --ticks 0 exit 0 | ĐẠT |  |
| snapshot quán tick 0: id, kind, fresh khớp file (±0.01) | ĐẠT | stock = [{'id': 'I1', 'kind': 'ca_linh', 'fresh': 99.992}] |

Lệnh đã chạy:

- `python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --scenario docs/proof/phase-3/integration/gather.scenario.json --inputs docs/proof/phase-3/integration/gather.inputs.json --inventory-out docs/proof/phase-3/integration/inventory.json --out docs/proof/phase-3/integration/gather.jsonl`
- `python3 -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory docs/proof/phase-3/integration/inventory.json --out docs/proof/phase-3/integration/quan.jsonl`
