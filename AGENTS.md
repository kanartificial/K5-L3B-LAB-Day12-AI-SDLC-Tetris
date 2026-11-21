# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm Tetris

> Cập nhật qua các phase: **Phase 1 (v1.0)** → **Phase 2 (v1.1: cá bơi/sinh, Cá Sấu, 2 bếp/4 bàn/6 món, `--mode day`, Shop, `pause`)**.

## Lệnh
- Test toàn bộ: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` (Windows/Git Bash: `PYTHONPATH="tests;."`)
- Smoke Phase 2 (QA): `python3 tools/smoke_p2.py all` — chạy smoke tích hợp 2 tiến trình, `--mode day --days 1|5` và regression; ghi bằng chứng vào `docs/proof/phase-2/`.
- Smoke Phase 3 (QA, Contract v1.2): `python3 tools/smoke_p3.py all` — ngưỡng ươn 30, bàn giao kho cá thể 2 tiến trình, kho đếm → mã 2, `day` có hàng (→ Shop → Ngày 2), regression; ghi vào `docs/proof/phase-3/`.
- Kiểm tất định (QA): `python3 tools/check_determinism.py --proof docs/proof/phase-3` — chạy 2 lần cùng seed, so byte JSONL + kho, kiểm sắp id / làm tròn; chạy trước khi gắn tag.
- Headless: `python3 -m chonoi.headless --mode gather|quan|day [--days 1..5] --seed 1 --ticks 600 --out out.jsonl`
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather|quan|day` (WASD/mũi tên, `E`, `Space`, `Esc`/`P`, `R`)

## Cấu trúc & quy ước
- Khung đã nâng lên Contract v1.1: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa ngoài phạm vi lát của mình; khi đổi contract phải báo cả nhóm và cập nhật `docs/contracts/`.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py`, `chonoi/sim/shop.py`.
- **Số liệu chỉ đọc từ `game.contract.json` (`tuning`)**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm.
- Không làm hỏng nhánh chính: trước khi đẩy, chạy đủ test + smoke + determinism.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; nếu test cũ lệch vì đổi luật phase mới (vd v1.0 → v1.1) phải ghi rõ lý do trong commit và `docs/verification/phase-n.md`.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase (`docs/prd-phase-n.md`), kế hoạch (`docs/plan/phase-n.md`) và hợp đồng (`docs/contracts/`) trước khi code.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem `README.md`, mục "Sáng tạo của nhóm").

## Skills / hooks của nhóm
- `contract-verify` (`.agents/skills/contract-verify/SKILL.md`): dùng trước mỗi lần đẩy lên `main` hoặc gắn tag phase để chạy đủ unittest, `tools/smoke_p2.py all` và `tools/check_determinism.py`.
- `phase-slice-delivery` (`.agents/skills/phase-slice-delivery/SKILL.md`): dùng khi triển khai một lát gameplay mới để bám sát Contract, không hard-code số liệu, viết test hộp đen ca biên và cập nhật nhật ký AI.
