# Smoke ngưỡng ươn 30 (ví dụ TICKET-03)

- Commit: `9c1885e` · contract_version `1.3`
- Thời điểm: 2026-11-21 14:17:52

| Kiểm | Kết quả | Chi tiết |
|---|---|---|
| gather exit 0 | ĐẠT |  |
| đúng 1 dòng spoiled khớp nguyên văn ticket | ĐẠT | [{"type": "event", "tick": 1, "phase": "gather", "name": "spoiled", "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"}}] |

Lệnh đã chạy:

- `python3 -m chonoi.headless --mode gather --seed 1 --ticks 1 --scenario docs/proof/phase-4/smoke/threshold/gather.scenario.json --out docs/proof/phase-4/smoke/threshold/gather.jsonl`
