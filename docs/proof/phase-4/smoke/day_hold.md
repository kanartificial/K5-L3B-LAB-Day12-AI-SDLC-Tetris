# Smoke day v1.2 có hàng: gather → quan → Shop → Ngày 2

- Commit: `9c1885e` · contract_version `1.3`
- Thời điểm: 2026-11-21 14:17:59

| Kiểm | Kết quả | Chi tiết |
|---|---|---|
| day --days 2 có hàng exit 0 | ĐẠT |  |
| bàn giao cùng tick, không hao thêm (gather_end.inventory = stock quán đầu) | ĐẠT | tick 1 · [{'id': 'I1', 'kind': 'ca_loc', 'fresh': 99.992}, {'id': 'I2', 'kind': 'bong_sung', 'fresh': 99.992}] → [{'id': 'I1', 'kind': 'ca_loc', 'fresh': 99.992}, {'id': 'I2', 'kind': 'bong_sung', 'fresh': 99.992}] |
| Shop nhận mảng cá thể và không hao tươi | ĐẠT | 600 snapshot shop · stock = [{'id': 'I1', 'kind': 'ca_loc', 'fresh': 54.992}, {'id': 'I2', 'kind': 'bong_sung', 'fresh': 54.992}] |
| Ngày 2 cấp id mới tăng tiếp (I3, I4) với fresh 100 | ĐẠT | hold D2 = [{'id': 'I3', 'kind': 'ca_loc', 'fresh': 100}, {'id': 'I4', 'kind': 'bong_sung', 'fresh': 100}] |
| có event spoiled ở kho/giỏ khi hàng ươn | ĐẠT | t19802 I3@hold; t19802 I4@hold |
| end: days_complete, 2 Ngày | ĐẠT | {"type": "end", "ticks": 33601, "sim_tick": 33601, "mode": "day", "state": "finished", "reason": "days_complete", "days_completed": 2, "money": 0, "earned": 0, "reputation": 2.0, "score": 200} |

Lệnh đã chạy:

- `python3 -m chonoi.headless --mode day --days 2 --seed 1 --ticks 44400 --scenario docs/proof/phase-4/smoke/day/day.scenario.json --inputs docs/proof/phase-4/smoke/day/day.inputs.json --snapshot-every 1 --out docs/proof/phase-4/smoke/day/day_hold.jsonl`
