# Kiểm chứng lát Quán — TICKET-03

Chạy từ thư mục gốc với Python đã cài:

```powershell
$env:PYTHONPATH = 'tests;.'
python -m unittest discover -s tests -p test_quan_p3.py -v
```

Kết quả trên Windows với Python 3.13: **7/7 đạt**. Test gọi runner ghi JSONL với tuning độ tươi và kho cá thể được truyền trực tiếp sau bước nạp kho.

- Snapshot tick 0 giữ ID, loại và độ tươi, kể cả hàng ươn đã có sẵn. Đúng 30 tại một tick, xuống dưới 30 ở tick sau, phát `spoiled` đúng một lần. Cùng tick sắp theo ID trước `cook_started`.
- Phần giữ tường minh phải đúng công thức, chưa ươn và không dùng chung giữa các đơn. Phần giữ mặc định chọn theo thứ tự đơn, ưu tiên độ tươi rồi ID. Phần giữ vừa ươn được thay trước khi nấu. Nếu thiếu hàng, đơn chuyển `unfulfillable` và khách chờ đến khi kiên nhẫn cạn.
- Gỏi giá 40 với hai cá thể ban đầu 90 và 60 hao tươi trước tương tác. Trung bình lúc nấu thấp hơn 75, chốt giá 29, boa 5. Bếp, sự kiện nấu và phục vụ dùng giá đã chốt.

## Bàn giao tích hợp

- Giữ manifest v1.1 khi các lát đang ghép. Khi adapter và Gather sẵn sàng, truyền kho cá thể `[{id,kind,fresh}]` vào `QuanSim` cùng `tuning.freshness`. Hàng đang giữ ở fixture Quán là mảng ID trong `customers[].reserved`.
- Runner sang Shop lấy kho thực thể từ `QuanSim.stock_snapshot()`. HUD đọc kho cá thể từ snapshot Quán. Sau khi bật v1.2, chạy smoke thật qua cả hai tiến trình và mode `day`.
