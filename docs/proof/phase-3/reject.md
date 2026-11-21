# Smoke từ chối kho sai schema (v1.2)

- Commit: `94f2328 (+ thay đổi chưa commit)` · contract_version `1.2`
- Thời điểm: 2026-11-21 12:35:20

| Kiểm | Kết quả | Chi tiết |
|---|---|---|
| kho đếm v1.1 → mã 2, không ghi output | ĐẠT | đầu vào sai: items ở contract v1.2 phải là mảng cá thể (từ chối kho đếm) |
| id trùng → mã 2, không ghi output | ĐẠT | đầu vào sai: id cá thể trùng: I1 |
| kind lạ → mã 2, không ghi output | ĐẠT | đầu vào sai: nguyên liệu lạ: ca_hong |
| fresh ngoài miền → mã 2, không ghi output | ĐẠT | đầu vào sai: fresh phải trong [0, 100], đang là 101 |
| id rỗng → mã 2, không ghi output | ĐẠT | đầu vào sai: items[0].id phải là chuỗi khác rỗng |

Lệnh đã chạy:

- `python3 -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory docs/proof/phase-3/reject/bad0.json --out docs/proof/phase-3/reject/bad0.jsonl`
- `python3 -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory docs/proof/phase-3/reject/bad1.json --out docs/proof/phase-3/reject/bad1.jsonl`
- `python3 -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory docs/proof/phase-3/reject/bad2.json --out docs/proof/phase-3/reject/bad2.jsonl`
- `python3 -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory docs/proof/phase-3/reject/bad3.json --out docs/proof/phase-3/reject/bad3.jsonl`
- `python3 -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory docs/proof/phase-3/reject/bad4.json --out docs/proof/phase-3/reject/bad4.jsonl`
