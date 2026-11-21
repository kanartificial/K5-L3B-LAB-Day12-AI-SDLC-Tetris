# Ma trận truy vết Phase 1

> QA: `@TranHa161` · Integrator: `@kanartificial` · Ngày: 2026-11-21
> Chạy lại: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` (Windows: `PYTHONPATH="tests;."`) · `python3 tools/check_determinism.py --proof docs/proof/phase-1`

## 1. Tổng hợp theo AC kế hoạch (`AC-P1-01` → `AC-P1-07`)

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| `AC-P1-01` | Kiểm `TEAM.md`, `game.contract.json` (`team: "tetris"`, `team_size: 4`), `docs/contracts/` + `inventory.sample.json`, chạy `test_team_check.py` | [integration.md](../proof/phase-1/integration.md) · [contracts/README.md](../contracts/README.md) | **Đạt một phần** (`game.contract.json`, contracts & `test_team_check` đạt; `TEAM.md` còn trống vài ô cột dự phòng) |
| `AC-P1-02` | Chạy test hộp đen Lát 1 (`test_gather_p1.py`: bơi, biên, `dive`/`surface`, oxy, `oxygen_empty`, `choke` `t+59`, `faint` LIFO) | [gather.md](../proof/phase-1/gather.md) · [unittest.log](../proof/phase-1/unittest.log) | **Đạt** |
| `AC-P1-03` | Chạy test hộp đen Lát 2 (`test_gather_p1.py`, `test_smoke_p1.py`, `check_determinism.py`: hái mặt nước, `node_regrown`, bắt cá + cooldown `t+L`, `hold_full`, cập bến, ghi kho nguyên tử) | [gather.md](../proof/phase-1/gather.md) · [determinism.md](../proof/phase-1/determinism.md) | **Đạt** |
| `AC-P1-04` | Chạy `test_quan_p1.py` & chạy headless kiểm lịch khách, giữ chỗ, `no_dish`, kiên nhẫn, bỏ đi | [quan-arrivals.md](../proof/phase-1/quan-arrivals.md) · [unittest.log](../proof/phase-1/unittest.log) | **Đạt một phần** (luật lõi đạt; `chonoi/scenario.py` chưa bổ sung hết các ca kiểm mâu thuẫn fixture quán nâng cao) |
| `AC-P1-05` | Chạy `test_quan_p1.py` & `test_integration_p1.py` kiểm `interact`, nấu → chín → bưng → phục vụ → trả tiền + boa + uy tín + đóng ca | [quan-orders.md](../proof/phase-1/quan-orders.md) · [integration.md](../proof/phase-1/integration.md) | **Đạt** |
| `AC-P1-06` | Chơi thử trực tiếp `python3 -m chonoi.live --mode gather\|quan` và chạy `test_live.py` kiểm `GET /state`, `POST /input`, `POST /restart` | [integration.md](../proof/phase-1/integration.md) (`test_live.py`) | **Đạt** *(chưa đính ảnh chụp màn hình HUD)* |
| `AC-P1-07` | Smoke 2 tiến trình (`gather --inventory-out` → `quan --inventory`), `check_determinism.py` (15/15), toàn bộ unit/smoke test bằng 1 lệnh, `README.md`, ghi chép tối thiểu | [integration.md](../proof/phase-1/integration.md) · [determinism.md](../proof/phase-1/determinism.md) · [../proof/phase-2/integration.md](../proof/phase-2/integration.md) | **Đạt** *(tag `phase-1` gắn sau mốc 1:00; đã đủ commit của cả 4 thành viên)* |

## 2. Chi tiết kiểm chứng Test Contract v1.0 (QA)

| Hạng mục / Contract | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| CON-01 `--ticks 0` → snapshot tick 0 đầu, đúng 1 dòng `end` ở cuối (gather + quan) | `test_con_01_ticks_zero_and_end_line`; `check_determinism.py` | [unittest.log](../proof/phase-1/unittest.log), [determinism.md](../proof/phase-1/determinism.md) | Đạt |
| Snapshot gather có đủ trường (pos `[2,0]`, oxy, máu, `at_surface`, `hold_capacity`, 6 cá, nút `d = 0`) | `test_gather_snapshot_has_gather_fields` | [unittest.log](../proof/phase-1/unittest.log) | Đạt |
| CON-02 Tất định byte-cho-byte (JSONL + file kho) | `test_con_02_deterministic_bytes` + `check_determinism.py` (5 kịch bản × 3 seed × 2 lần) | [determinism.md](../proof/phase-1/determinism.md) | Đạt (15/15) |
| §5 Định dạng: sắp thực thể theo `id`, số thực ≤ 3 chữ số, không `-0.0`, tick không giảm | `check_determinism.py` (`check_format`) | [determinism.md](../proof/phase-1/determinism.md) | Đạt |
| CON-03 Đầu vào sai / mode lạ / scenario ngoài miền / sai khối → exit `2`, không ghi output | `test_con_03_*`, `test_scenario_out_of_domain_exit_2`, `ScenarioModes` | [unittest.log](../proof/phase-1/unittest.log) | Đạt |
| MOVE-01..03 Tốc độ bơi, ramp đảo hướng, `heading_deg`, chặn 4 mép & vận tốc về 0 | `test_move_*` trong `test_smoke_p1.py` | [unittest.log](../proof/phase-1/unittest.log) | Đạt |
| INV-01 Cập bến / hết giờ ghi kho 1 lần, chạm `--ticks` không ghi kho, quan đọc đúng `stock` | `test_inv_*`, `test_time_ends_gather_and_keeps_hold`, `test_integration_p1.py`, `tools/smoke_p2.py integration` | [integration.md](../proof/phase-1/integration.md), [../proof/phase-2/integration.md](../proof/phase-2/integration.md) | Đạt |
| `TEAM.md` hợp lệ, `team_size = 4` | `tools/check_team.py`; `tests/test_team_check.py` | [integration.md](../proof/phase-1/integration.md) | Đạt *(5/5 test sau khi tách `TEMPLATE` riêng và thêm `test_repo_team_md_is_valid`, xem `docs/clarify.md` #1)* |

## 3. Ghi chú QA & Đánh giá ngắn
- **Yêu cầu đạt:** Toàn bộ luật lõi `gather` (Lát 1–2), `quan` (Lát 3–4, đã bổ sung `vel` trong snapshot), UI chơi 2 buổi, hợp đồng kho + smoke 2 tiến trình, kiểm tất định `15/15`, và toàn bộ test suite P1 chạy xanh bằng 1 lệnh (`tests/test_contract_p2.py` tự skip khi `contract_version` còn `1.0`).
- **Yêu cầu chưa trọn vẹn (ghi trung thực):**
  - Kiểm mâu thuẫn fixture quán nâng cao trong `chonoi/scenario.py` còn TODO, sẽ hoàn thiện cùng Contract v1.1.
  - HUD/UI Phase 1 chưa đính ảnh chụp màn hình trong `docs/proof/phase-1/`.
  - Tag `phase-1` gắn trễ hơn hạn 1:00 do chuyển gấp sang Phase 2; ghi nhận trung thực.
- **Lưu ý môi trường:** Trên Windows dùng `PYTHONPATH="tests;."` thay cho `:` (đã ghi chú trong `AGENTS.md`).
- **Điều cần chỉnh cho Phase 2:** Chốt khung Contract v1.1 sớm trong 5–10 phút đầu để 4 bạn cùng pull; chạy lại `check_determinism.py` (kể cả kiểm seed khác cho cá bơi/khách đến) trước khi gắn tag `phase-2`.
