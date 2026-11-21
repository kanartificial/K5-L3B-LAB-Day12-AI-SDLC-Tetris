---
name: contract-verify
description: Chạy toàn bộ test hộp đen, smoke tích hợp v1.1 và kiểm tất định trước khi commit hoặc gắn tag phase.
---

# Skill: `contract-verify`

Dùng trước mỗi lần đẩy lên `main` hoặc gắn tag `phase-n`.

## Các bước thực hiện
1. Chạy toàn bộ test hộp đen + unit:
   - Linux/macOS: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
   - Windows/Git Bash: `PYTHONPATH="tests;." python -m unittest discover -s tests -v`
2. Chạy smoke Phase 2 (tích hợp `gather → quan`, `--mode day --days 1|5`, regression):
   - `python3 tools/smoke_p2.py all`
3. Chạy kiểm tất định byte-cho-byte & định dạng JSONL:
   - `python3 tools/check_determinism.py --proof docs/proof/phase-2`
4. Đối chiếu kết quả và cập nhật trung thực vào `docs/verification/phase-n.md` trước khi gắn tag.
