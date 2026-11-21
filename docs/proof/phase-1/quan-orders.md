# Phase 1 — Vòng đời đơn Quán

## Chạy lại luồng chính

Tạo `quan-scenario.json` và `quan-inputs.json` với nội dung tương ứng:

```json
{"quan":{"player":{"pos":[2,8]},"tables":[{"id":"T1","pos":[3,8]}]}}
```

```json
{"frames":[{"tick":120,"interact":true},{"tick":121,"interact":false},{"tick":480,"interact":true},{"tick":481,"interact":false,"move":[1,0]},{"tick":496,"move":[0,0]},{"tick":500,"interact":true}]}
```

```powershell
python -m chonoi.headless --mode quan --seed 1 --inventory docs/contracts/inventory.sample.json --scenario quan-scenario.json --inputs quan-inputs.json --ticks 1101 --snapshot-every 1 --out quan.jsonl
```

## Kết quả đã kiểm

- JSONL ghi `customer_arrived` ở tick 120, `cook_started` ở 121, `dish_ready` rồi `dish_picked` cùng tick 481, `served` ở 501 và `paid` ở 1101. Kho mất một cá lóc khi nấu. Khi phục vụ, timer ăn còn đủ 600 tick. Sau thanh toán, bàn trống, tiền 72 và uy tín 3.2. Hai lần chạy cho cùng kết quả từng byte.
- Kiểm qua `Session`: phục vụ được khi kiên nhẫn vừa về 0 và khi hết ca. Đóng ca ngay sau phục vụ phát `served → paid → quan_end`. Khách vừa ăn xong đúng tick đóng ca trả với lý do `finished_eating`.
- Khách hết kiên nhẫn bị dọn món trên tay và uy tín giảm còn 2.5. Đóng ca dọn món đang nấu của khách chờ và uy tín giữ ở 3. Món vừa chín có `ready_ticks = 0`, bước sau mới tăng. Bếp đang nấu thắng hòa khoảng cách với bàn và lượt tương tác kết thúc tại bếp. Boa đúng ngưỡng và uy tín được kẹp ở 5.
- Unittest trên Windows bằng Python 3.13, dùng trình Python hiện tại cho các tiến trình headless vì `python3` trỏ vào alias Microsoft Store. 31/32 đạt. `test_template_is_rejected` vẫn lỗi vì `TEAM.md` của nhóm đã điền.

## Test hồi quy

```powershell
$env:PYTHONPATH = 'tests;.'
python -m unittest discover -s tests -p test_quan_p1.py -v
```

Sau khi thêm `test_quan_p1.py`, cả 6 test Quán đạt. Toàn bộ suite đạt 37/38 khi dùng Python 3.13 cho các tiến trình headless trên Windows. Test `test_template_is_rejected` vẫn lỗi như trên.

Đã chạy lại sau khi sửa `tests/helpers.py` để lệnh starter dùng Python hiện tại trên Windows. Lệnh kiểm Quán ở trên đạt 6/6 và suite đầy đủ đạt 37/38.
