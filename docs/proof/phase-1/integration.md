# Phase 1 — Bằng chứng tích hợp 2 tiến trình & Toàn bộ test suite

## 1. Smoke test hộp đen 2 tiến trình (PRD-0 mục G)

Fixture `dock.json`: `{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}`
Input `dock-inputs.json`: `{"frames":[{"tick":0,"interact":true}]}`

```bash
python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather.jsonl --inventory-out catch.json
python3 -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl
```

### Đầu ra thật

**`catch.json`:**
```json
{"items":{"bong_sung":2,"ca_loc":1}}
```

**Dòng `gather_end` và `end` trong `gather.jsonl`:**
```json
{"type":"event","tick":1,"phase":"gather","name":"gather_end","data":{"reason":"docked","inventory":{"items":{"bong_sung":2,"ca_loc":1}}}}
{"type":"end","ticks":1,"sim_tick":1,"mode":"gather","state":"finished","reason":"docked","money":0,"earned":0,"reputation":3.0,"score":300}
```

**Snapshot tick 0 trong `quan.jsonl`:**
```json
{"type":"snapshot","tick":0,"sim_tick":0,"mode":"quan","phase":"quan","phase_tick":0,"state":"playing","time_left_ticks":10800,"money":0,"earned":0,"reputation":3.0,"score":300,"player":{"pos":[8,5],"vel":[0.0,0.0]},"stock":{"bong_sung":2,"ca_loc":1},"hand":null,"stoves":[{"id":"B1","pos":[2,8],"state":"idle","dish":null,"cook_ticks_left":0,"ready_ticks":0}],"tables":[{"id":"T1","pos":[9,2],"customer_id":null}],"customers":[]}
```

→ `stock` của `quan` tại tick `0` khớp chính xác `{"bong_sung":2,"ca_loc":1}` trong `catch.json`, và `quan.player` có đủ `pos` và `vel`.

## 2. Toàn bộ bộ test chạy bằng 1 lệnh

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

Kết quả chạy trên Linux (Python 3.14):
- `test_gather_p1.py`: 10/10 ok
- `test_integration_p1.py`: 2/2 ok (luồng bắt cá → kho → nấu/phục vụ/trả tiền & luồng ngất → kho rỗng → `no_dish`)
- `test_live.py`: 1/1 ok
- `test_python_starter_units.py`: 7/7 ok
- `test_quan_p1.py`: 6/6 ok
- `test_smoke_p1.py`: 20/20 ok
- `test_team_check.py`: 5/5 ok *(đã tách mẫu `TEMPLATE` khỏi `TEAM.md` thật và thêm `test_repo_team_md_is_valid`, xem ghi chú trong `docs/clarify.md`)*

**Tổng kết:** `Ran 51 tests in 7.680s — OK`.
