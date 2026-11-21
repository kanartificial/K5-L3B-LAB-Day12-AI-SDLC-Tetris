# Ma trận truy vết Phase 2 — TICKET-02 · Test Contract v1.1

> QA: TranHa161 · Mã AC theo [docs/plan/phase-2.md](../plan/phase-2.md) · Hạn tag `phase-2`: 1:55 · **Cập nhật cột Kết quả trên đúng commit gắn tag.**
> Chạy lại:
> - `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` (Windows: `"tests;."`). `tests/test_contract_p2.py` (30 test) tự skip khi `contract_version` còn `1.0`; tên test mang mã AC (`test_p2_0X_...`).
> - `python3 tools/smoke_p2.py all` (ghi `docs/proof/phase-2/{integration,day,regression}.md`)
> - `python3 tools/check_determinism.py --proof docs/proof/phase-2`

| AC (plan) | Yêu cầu kiểm (TICKET-02) | Cách kiểm chứng | Bằng chứng | Kết quả (commit `…`) |
|---|---|---|---|---|
| AC-P2-01 | Contract v1.1: `contract_version:"1.1"`, số chuẩn mục 1.1–1.3, 6 nguyên liệu/6 món, N1–N6, B1–B2, T1–T4, `gather.monsters`, `day_plan` D1–D5 (ingredients = công thức × suất), `shop.upgrades`. Khung: `--mode day --days 1..5` (sai miền/sai mode → 2), scenario day (cấm `quan.stock`/`quan.reputation`, `0 ≤ money ≤ earned`), scenario ví dụ của ticket chạy được | `test_p2_01_*`, `test_p2_01_cli_*` | [regression.log](../proof/phase-2/regression.log) | Chưa đạt: contract còn `1.0` |
| AC-P2-02 | Cá: 8 đàn đầu ca ở 8 điểm khác nhau, bơi trong x∈[4,96] và dải độ sâu theo loài, `fish_spawned`, trần 12, phụ thuộc seed, `random_fish:false` thì đứng yên | `test_p2_02_*` | [regression.log](../proof/phase-2/regression.log) | Chưa đạt |
| AC-P2-03 | Cá Sấu: chỉ M1 ở Ngày 1, M2 từ Ngày 3; chạm → −1 Máu, bỏ floor(n/2) theo LIFO, bất tử 90 tick; ngất do quái thì mất giỏ, `cause:"monster"` | `test_p2_03_*`, `test_p2_05_day_five_days...` (M2 Ngày 3) | [regression.log](../proof/phase-2/regression.log) | Chưa đạt |
| AC-P2-04 | Quán 2 bếp/4 bàn, khách lúc 120 + 900·k vào bàn trống id nhỏ nhất, quán chạy riêng dùng cả 6 món, kho nhận `ca_keo`/`keo_neo` | `test_p2_04_*` | [regression.log](../proof/phase-2/regression.log) | Chưa đạt |
| AC-P2-05 · day | `day_start → day_plan → phase_start(gather)` ở tick 0; gather → quan → shop; ngất vẫn mở quán cùng tick; D1–D5 đúng; end `days_complete` + `days_completed`; 1 Ngày ≤ 22.200 tick và ≤ 20 s | `test_p2_05_day_*` + `smoke_p2.py day` | [day.md](../proof/phase-2/day.md) | Chưa đạt: mode day chưa bật |
| AC-P2-05 · shop | Mua oxygen 200 → `bought` money 0; thiếu tiền → `buy_failed funds`; lệnh lạ → `unknown`; giữ earned; `shop_done` → `shop_end done`; tự đóng sau 600 tick → `time`; cấp hiện ngay, áp dụng từ Ngày sau (oxy 2.700 tick) | `test_p2_05_shop_*` | [regression.log](../proof/phase-2/regression.log) | Chưa đạt |
| AC-P2-05 · pause | `paused`/`resumed`, snapshot `state:"paused"`, gameplay và timer đứng yên | `test_p2_05_pause_*` | [regression.log](../proof/phase-2/regression.log) | Chưa đạt |
| AC-P2-06 | Menu, pause menu, DayIntro/EveningIntro/DayResult/Summary, HUD sáng/quán (chữ ≥ 18 px ở 1280×720), ≥ 30 FPS | Chơi thử `python3 -m chonoi.live --mode day`, chụp màn hình + đo FPS | `docs/proof/phase-2/ui/` (chưa có) | Chưa kiểm |
| AC-P2-07 · smoke | Phút 20: `gather --inventory-out` → `quan --inventory`, stock tick 0 = kho bàn giao | `smoke_p2.py integration` | [integration.md](../proof/phase-2/integration.md), [integration/](../proof/phase-2/integration/) | Một phần (10:30, `ece548f`, số v1.0): bàn giao kho ĐẠT; khách gọi món CHƯA ĐẠT (`sim/quan` còn TODO). **Chạy lại với số chuẩn v1.1.** |
| AC-P2-07 · regression | Regression P1 với số chuẩn; test cũ phải sửa thì ghi lý do | `smoke_p2.py regression` + `check_determinism.py` | [regression.md](../proof/phase-2/regression.md) | Một phần: 72 test, chỉ fail `test_template_is_rejected` (đã biết từ P1); 30 test P2 đang skip |
| AC-P2-07 · bàn giao | clarify, ai-usage-log, retro (phút 45–50), tag `phase-2` trỏ commit bàn giao trên main | Đọc lại file + `git ls-remote --tags origin` | — | Chưa |

## Test cũ cần đổi vì luật mới (ghi lý do)
- Khi đổi sang số chuẩn v1.1: `test_gather_snapshot_has_gather_fields` trong `tests/test_smoke_p1.py` đang kiểm `len(s["fish"]) == 6`, còn v1.1 đầu ca có **8** đàn. Test này cần đổi thành 8; lý do: TICKET-02 mục 1.1 "Đầu ca 8 đàn". Chưa sửa, chờ bật v1.1.
- `tests/test_gather_p1.py` (của lát gather) có thể lệch khi cá bơi/sinh và có M1: fixture cần cá đứng yên thì dùng `random_fish: false` (plan mục 4).
- `test_team_check.test_template_is_rejected`: xem verification Phase 1, ghi chú 1.

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: *(điền lúc gắn tag)*
- Điều cần chỉnh cho phase sau:
