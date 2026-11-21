# Smoke mode day (phút 35)

- Commit: `32d1921 (+ thay đổi chưa commit)` · contract_version `1.1`
- Thời điểm: 2026-11-21 11:25:30

| Kiểm | Kết quả | Chi tiết |
|---|---|---|
| --days 1 exit 0 | ĐẠT |  |
| --days 1: end reason days_complete, days_completed = 1 | ĐẠT | end = {"type": "end", "ticks": 22200, "sim_tick": 22200, "mode": "day", "state": "finished", "reason": "days_complete", "days_completed": 1, "money": 0, "earned": 0, "reputation": 3.0, "score": 300} |
| 1 Ngày ≤ 20 s | ĐẠT | 0.6 s |
| 1 Ngày ≤ 22.200 tick | ĐẠT | sim_tick = 22200 |
| --days 1: công bố day_plan Ngày 1..1 | ĐẠT | D1: {'ca_loc_nuong_trui': 3, 'goi_bong_sung': 3} |
| --days 1: pha gather → quan → shop lặp lại | ĐẠT | gather → quan → shop |
| --days 5 exit 0 | ĐẠT |  |
| --days 5: end reason days_complete, days_completed = 5 | ĐẠT | end = {"type": "end", "ticks": 111000, "sim_tick": 111000, "mode": "day", "state": "finished", "reason": "days_complete", "days_completed": 5, "money": 0, "earned": 0, "reputation": 3.0, "score": 300} |
| --days 5: công bố day_plan Ngày 1..5 | ĐẠT | D1: {'ca_loc_nuong_trui': 3, 'goi_bong_sung': 3}; D2: {'ca_loc_nuong_trui': 2, 'lau_ca_linh_dien_dien': 2}; D3: {'goi_bong_sung': 2, 'canh_chua_ca_loc': 2, 'ca_keo_nuong': 2}; D4: {'lau_mam': 1, 'ca_loc_nuong_trui': 2, 'goi_bong_sung': 1}; D5: {'lau_mam': 1, 'lau_ca_linh_dien_dien': 1, 'ca_loc_nuong_trui': 1} |
| --days 5: pha gather → quan → shop lặp lại | ĐẠT | gather → quan → shop → gather → quan → shop → gather → quan → shop → gather → quan → shop → gather → quan → shop |

Lệnh đã chạy:

- `python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out docs/proof/phase-2/day1.jsonl`
- `python3 -m chonoi.headless --mode day --days 5 --seed 1 --ticks 111000 --out docs/proof/phase-2/day5.jsonl`
