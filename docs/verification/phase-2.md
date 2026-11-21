# Ma trận truy vết Phase 2 — TICKET-02 · Test Contract v1.1

> QA: `@TranHa161` · Integrator: `@kanartificial` · Mã AC theo [docs/plan/phase-2.md](../plan/phase-2.md) · Hạn tag `phase-2`: 1:55
> Chạy lại:
> - `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` (Windows: `"tests;."`)
> - `python3 tools/smoke_p2.py all` (ghi `docs/proof/phase-2/{integration,day,regression}.md`)
> - `python3 tools/check_determinism.py --proof docs/proof/phase-2`

| AC (plan) | Yêu cầu kiểm (TICKET-02) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| `AC-P2-01` | Contract v1.1: `contract_version:"1.1"`, số chuẩn mục 1.1–1.3, 6 nguyên liệu/6 món, `N1–N6`, `B1–B2`, `T1–T4`, `gather.monsters`, `day_plan` D1–D5, `shop.upgrades`; CLI `--mode day --days 1..5`, kiểm scenario `day` | `test_p2_01_*`, `test_p2_01_cli_*` | [regression.log](../proof/phase-2/regression.log) · [contracts/README.md](../contracts/README.md) | **Đạt** |
| `AC-P2-02` | Cá: 8 đàn đầu ca ở 8 điểm khác nhau, bơi `1.5 m/s` trong `x ∈ [4,96]` và dải độ sâu loài, đổi hướng bước 120, phản xạ mép/góc, bắt trước khi bơi, `fish_spawned`, trần 12, phụ thuộc seed, `random_fish:false` đứng yên | `test_p2_02_*`, `tests/test_gather_p2.py` | [regression.log](../proof/phase-2/regression.log) · [determinism.md](../proof/phase-2/determinism.md) | **Đạt** |
| `AC-P2-03` | Cá Sấu: `M1` Ngày 1, `M2` từ Ngày 3; `patrol`/`chase`/`recoil` 60 tick; chạm → `-1` Máu, bỏ `floor(n/2)` LIFO, bất tử 90 tick; ngất `cause:"monster"`; ngạt xuyên bất tử | `test_p2_03_*`, `tests/test_gather_p2.py` | [regression.log](../proof/phase-2/regression.log) | **Đạt** |
| `AC-P2-04` | Quán 2 bếp/4 bàn, khách lúc `120 + 900·k` vào bàn trống `id` nhỏ nhất, quán độc lập dùng cả 6 món, kho nhận `ca_keo`/`keo_neo`, lọc `day_plan.dishes` trong `day` | `test_p2_04_*` | [regression.log](../proof/phase-2/regression.log) | **Đạt** |
| `AC-P2-05 · day` | `day_start → day_plan → phase_start(gather)` ở tick 0; `gather → quan → shop`; ngất vẫn mở quán cùng tick; D1–D5 đúng; `end` `days_complete` + `days_completed`; 1 Ngày ≤ 22.200 tick & ≤ 20 s | `test_p2_05_day_*` + `smoke_p2.py day` | [day.md](../proof/phase-2/day.md) (**1.3 s / Ngày**) | **Đạt** |
| `AC-P2-05 · shop` | Mua `oxygen`/`hp` → `bought`, giữ `earned`; thiếu tiền → `funds`, hết cấp → `max_level`, lạ → `unknown`; `shop_done` → `done`, 600 tick → `time`; cấp hiện ngay, áp dụng từ Ngày sau | `test_p2_05_shop_*`, `tests/test_gather_p2.py` | [regression.log](../proof/phase-2/regression.log) | **Đạt** |
| `AC-P2-05 · pause` | `paused`/`resumed`, snapshot `state:"paused"`, gameplay và timer đứng yên ở cả 3 mode | `test_p2_05_pause_*` | [regression.log](../proof/phase-2/regression.log) | **Đạt** |
| `AC-P2-06` | Menu, pause menu, `DayIntro`/`EveningIntro`/`DayResult`/`Summary`, HUD sáng/quán (chữ ≥ 18 px ở 1280×720), ≥ 30 FPS | Chơi thử `python3 -m chonoi.live --mode day`, chụp màn hình + đo FPS | `docs/proof/phase-2/ui/` (chờ `client/ui`) | **Chưa kiểm** *(backend `chonoi.live --mode day` đã sẵn sàng; chờ `@ThuThaoVuong` hoàn thiện UI)* |
| `AC-P2-07 · smoke` | Phút 20: `gather --inventory-out` → `quan --inventory`, `stock` tick 0 = kho bàn giao, có khách gọi món | `smoke_p2.py integration` | [integration.md](../proof/phase-2/integration.md) | **Đạt (6/6)** |
| `AC-P2-07 · regression` | Regression P1 + toàn bộ test P2 với số chuẩn v1.1 + kiểm tất định byte-cho-byte | `smoke_p2.py regression` + `check_determinism.py` | [regression.md](../proof/phase-2/regression.md) · [determinism.md](../proof/phase-2/determinism.md) | **Đạt (86/86 test OK, 15/15 determinism)** |
| `AC-P2-07 · bàn giao` | `clarify`, `ai-usage-log`, `retro` (phút 45–50), `AGENTS.md` + 2 skill, đẩy tag `phase-2` trên `main` | Đọc lại file + `git ls-remote --tags origin` | `AGENTS.md`, `.agents/skills/` | **Đang hoàn tất** *(chờ `client/ui` + retro nhóm trước khi gắn tag `phase-2`)* |

## Test cũ đã cập nhật vì luật mới (ghi lý do)
1. `tests/test_smoke_p1.py::test_gather_snapshot_has_gather_fields`: đọc số lượng đàn cá ban đầu từ `tuning.gather.fish_initial` (`8` ở v1.1 thay vì hard-code `6` của v1.0; lý do: TICKET-02 §1.1 *"Đầu ca 8 đàn"*).
2. `tests/test_smoke_p1.py::test_con_03_old_and_future_modes_rejected`: đổi `"day"` thành `"night"` vì `--mode day` đã chính thức mở ở Contract v1.1 (TICKET-02 §4.1); vẫn từ chối `"river"` và mode lạ.
3. `tests/test_smoke_p1.py::test_con_03_bad_input_exit_2` & `tests/test_python_starter_units.py`: ở v1.1 §4.2, `attack`/`photo`/`pause`/`shop_done` là nút boolean hợp lệ (bỏ qua nếu sai pha hoặc mở rộng chưa bật), còn nút lạ (`jump`, `fly`) vẫn thoát mã `2`.
4. `tests/test_quan_p1.py::test_cook_pick_serve_and_pay` & `tests/test_integration_p1.py`: ở v1.1 có 4 bàn (`T1–T4`), nên tại tick `1020` khi bàn `T2–T4` còn trống mà kho đã hết sẽ phát thêm `no_dish`; test lọc sự kiện vòng đời đơn `C1` (`e["name"] != "no_dish"`).

## Đánh giá ngắn
- **Đạt:** Toàn bộ lõi backend/headless Contract v1.1 (`AC-P2-01` → `AC-P2-05`, `AC-P2-07` smoke/regression/determinism) đã xanh **86/86 test**, 1 Ngày chạy trong **1.3 s** (≤ 20 s), 5 Ngày chạy trơn tru, tất định **15/15** (seed khác cho output khác ở `gather`). Đã bổ sung `chonoi.live --mode day` và 2 skill nhóm trong `.agents/skills/`.
- **Chưa xong:** `AC-P2-06` (Menu, màn chuyển pha, Pause & HUD v1.1 trên `chonoi/web/index.html`) và mục retro nhanh Phase 2 (`docs/retro.md`) trước khi đẩy tag `phase-2`.
