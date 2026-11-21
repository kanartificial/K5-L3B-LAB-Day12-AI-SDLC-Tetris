# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | `@kanartificial` | Antigravity CLI (Gemini 4 Neon) | Soạn bộ hợp đồng tích hợp `docs/contracts/{README,inventory,sim-ui,events}.md` từ PRD-0 | ~15k token | Không phát hiện sai; đã đối chiếu trực tiếp với `chonoi/inventory.py` và `chonoi/live.py`. |
| Phase 1 | `@kanartificial` | Antigravity CLI (Gemini 4 Neon) | Hoàn thiện Lát 1 & Lát 2 `chonoi/sim/gather.py` và 10 test hộp đen `tests/test_gather_p1.py` | ~25k token | AI từng viết dư một block `inp = write_json(...)` bị ghi đè ngay sau đó trong `test_catch_fish_tiebreak_cooldown_and_remove`; đã tự rà và bỏ trước khi commit. |
| Phase 1 | `@kanartificial` | Antigravity CLI (Gemini 4 Neon) | Viết `docs/plan/phase-1.md`, `docs/plan/phase-2.md`, `tests/test_integration_p1.py`, `docs/proof/phase-1/*`, `docs/verification/phase-1.md`, `README.md` | ~22k token | Phát hiện `QuanSim.snapshot()["player"]` thiếu trường `vel` và `test_template_is_rejected` fail khi `TEAM.md` đã điền tên thật; đã sửa và ghi rõ lý do trong `docs/clarify.md`. |
