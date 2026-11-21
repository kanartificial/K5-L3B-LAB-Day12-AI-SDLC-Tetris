# Phase 1 — Khách đến và giữ nguyên liệu

```powershell
python -m chonoi.headless --mode quan --seed 1 --inventory docs/contracts/inventory.sample.json --ticks 1020 --snapshot-every 1 --out quan.jsonl
python -m chonoi.headless --mode quan --seed 1 --ticks 1020 --snapshot-every 1 --out quan-empty.jsonl
```

Đã chạy bằng Python 3.13 trên Windows.

- Kho mẫu, seed 1: tick 119 chưa có khách. Tick 120 có `customer_arrived` cho `C1` tại `T1`, gọi `ca_loc_nuong_trui`. Đơn giữ `{"ca_loc":1}`, tồn vật lý giữ nguyên. Kiên nhẫn từ 3600 ở tick 120 xuống 3599 ở tick 121.
- Chạy lại cùng đầu vào cho JSONL giống từng byte. Bàn vẫn có khách tại tick 1020 nên bỏ lượt đến.
- Kho rỗng phát `no_dish` ở tick 120 và 1020. Scenario hết ca ở tick 120 chỉ phát `quan_end`. Scenario có `random_customers: false` bỏ qua lịch khách.
- Unittest: 31/32 đạt khi dùng Python 3.13 thay cho alias `python3` trong tiến trình test. Test `test_template_is_rejected` còn lỗi vì đọc `TEAM.md` đã điền và kỳ vọng dữ liệu mẫu bị từ chối.
