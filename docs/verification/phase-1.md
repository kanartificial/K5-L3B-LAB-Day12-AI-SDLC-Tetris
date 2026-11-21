# Ma trận truy vết Phase 1

> QA: TranHa161 · Commit kiểm: `520f488` (gather v1 + quan order lifecycle) · Ngày: 2026-11-21 · Lần kiểm đầu: `78bf8a3`
> Mã AC lấy theo test công khai `tests/test_smoke_p1.py` (PRD-0). **Khi PRD-0 mở trên lab board, đối chiếu lại và bổ sung AC còn thiếu.**
> Chạy lại: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` (Windows: `PYTHONPATH="tests;."`) · `python3 tools/check_determinism.py --proof docs/proof/phase-1`

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| CON-01 `--ticks 0` → snapshot tick 0 đầu, đúng 1 dòng `end` ở cuối (gather + quan) | `test_con_01_ticks_zero_and_end_line`; `check_determinism.py` kiểm lại cho mọi kịch bản | [unittest.log](../proof/phase-1/unittest.log), [determinism.md](../proof/phase-1/determinism.md) | Đạt |
| Snapshot gather có đủ trường (pos xuất phát [2,0], oxy, máu, `at_surface`, `hold_capacity` từ contract, 6 cá, nút trên mặt nước) | `test_gather_snapshot_has_gather_fields` | [unittest.log](../proof/phase-1/unittest.log) | Đạt |
| CON-02 Tất định byte-cho-byte (JSONL + file kho) | `test_con_02_deterministic_bytes` + `check_determinism.py`: 5 kịch bản × 3 seed (1, 7, 42) × 2 lần chạy, so byte | [determinism.md](../proof/phase-1/determinism.md), JSONL mẫu `*_seed1.jsonl` | Đạt (15/15) |
| §5 Định dạng: mảng thực thể sắp theo id, số thực ≤ 3 chữ số, không có -0.0, tick không giảm | `check_determinism.py` (`check_format`) | [determinism.md](../proof/phase-1/determinism.md) | Đạt |
| CON-03 Đầu vào sai → exit 2, **không** ghi output (tick trùng, `--ticks -1`, nút lạ `jump`/`attack`) | `test_con_03_bad_input_exit_2` | [unittest.log](../proof/phase-1/unittest.log) | Đạt |
| CON-03 Mode cũ/tương lai (`river`, `day`) và scenario cũ bị từ chối | `test_con_03_old_and_future_modes_rejected` | [unittest.log](../proof/phase-1/unittest.log) | Đạt |
| Scenario ngoài miền (ra biên, nút không ở mặt nước, id trùng, giỏ vượt sức chứa, khóa lạ) → exit 2 | `test_scenario_out_of_domain_exit_2` | [unittest.log](../proof/phase-1/unittest.log) | Đạt |
| Scenario sai khối mode / fixture quan không hợp lệ → exit 2; fixture hợp lệ → exit 0 | `test_khoi_sai_mode_exit_2`, `test_quan_fixture_khong_hop_le_exit_2`, `test_quan_player_vel_hop_le` | [unittest.log](../proof/phase-1/unittest.log) | Đạt |
| MOVE-01 Tốc độ bơi = `swim_speed` sau ramp (ngang, xuống, chéo không nhanh hơn) | `test_move_01_swim_speed_after_ramp` | [unittest.log](../proof/phase-1/unittest.log) | Đạt |
| MOVE-01 Đảo hướng chạm vận tốc đích trong ≤ `ramp_max_ticks` | `test_move_ramp_doi_huong_trong_tran` | [unittest.log](../proof/phase-1/unittest.log) | Đạt |
| MOVE-02 `heading_deg` dương là đi xuống (90° khi lặn thẳng) | `test_move_02_heading_positive_is_down` | [unittest.log](../proof/phase-1/unittest.log) | Đạt |
| MOVE-03 Chặn 4 mép vùng nước (x 0..100, d 0..30), vận tốc về 0 ở mép | `test_move_03_edge_clamp`, `test_move_mep_vel_ve_0` | [unittest.log](../proof/phase-1/unittest.log) | Đạt |
| Hết giờ → `gather_end` reason `time`, giữ nguyên giỏ vào kho | `test_time_ends_gather_and_keeps_hold` | [unittest.log](../proof/phase-1/unittest.log) | Đạt |
| INV-01 Cập bến ghi kho; quan đọc đúng `stock` | `test_inv_01_gather_writes_inventory_quan_reads_it`; kịch bản `gather_dock_inventory` (kho giống nhau byte) | [unittest.log](../proof/phase-1/unittest.log), [gather_dock_inventory_seed1.jsonl](../proof/phase-1/gather_dock_inventory_seed1.jsonl) | Đạt |
| INV-01 Hết `--ticks` trước khi cập bến → không ghi kho, reason `tick_limit` | `test_inv_01_not_written_when_tick_limit_first` | [unittest.log](../proof/phase-1/unittest.log) | Đạt |
| Kho sai schema / xung đột với scenario / cờ kho sai mode → exit 2 | `test_inv_bad_schema_exit_2`, `test_inventory_and_scenario_stock_conflict`, `test_inventory_flags_mode_mismatch_exit_2` | [unittest.log](../proof/phase-1/unittest.log) | Đạt |
| Luật gather (lát 1–2): dive/surface, oxy tiêu/hồi, `oxygen_empty`, `choke` t+59, ngất mất giỏ LIFO + kho rỗng, hái + mọc lại, bắt cá + cooldown, `hold_full`, cập bến trước hái | `tests/test_gather_p1.py` (@kanartificial) | [unittest.log](../proof/phase-1/unittest.log) | Đạt |
| Luật quán (lát 3–4): khách theo lịch + giữ nguyên liệu, `no_dish`, nấu → chín → bưng → phục vụ → trả tiền + boa, khách rời chỉ trừ uy tín khi hết kiên nhẫn, phục vụ ở tick đóng ca | `tests/test_quan_p1.py` (@KimY22-it) | [unittest.log](../proof/phase-1/unittest.log), [quan-arrivals.md](../proof/phase-1/quan-arrivals.md), [quan-orders.md](../proof/phase-1/quan-orders.md) | Đạt |
| Smoke 2 tiến trình gather → kho → quan có khách gọi món từ kho bàn giao | `tools/smoke_p2.py integration` | [../proof/phase-2/integration.md](../proof/phase-2/integration.md) | Đạt |
| TEAM.md hợp lệ, `team_size` = 4 | `tools/check_team.py`; `test_team_check` | [unittest.log](../proof/phase-1/unittest.log) | Đạt cho TEAM.md của nhóm. Riêng `test_template_is_rejected` **FAIL**, xem ghi chú 1 |

## Ghi chú QA
1. `test_team_check.test_template_is_rejected` chờ `TEAM.md` vẫn là template, nên fail sau khi nhóm điền TEAM.md thật là **đúng kỳ vọng**, không phải lỗi luật. Chưa sửa test; cần báo nhóm và quyết định (xóa test hoặc cho nó đọc template riêng), sau đó ghi lý do vào commit.
2. Đổi seed (1/7/42) cho **cùng một** JSONL: hiện luật chưa dùng `Streams`. Khi thêm yếu tố ngẫu nhiên (cá bơi, khách đến…) phải chạy lại `check_determinism.py` và kiểm seed khác thì output khác.
3. Trên Windows, lệnh test trong AGENTS.md (`PYTHONPATH=tests:.`) báo `No module named 'helpers'`; phải dùng `PYTHONPATH="tests;."`.
4. `game.contract.json` vẫn còn `"team": "ten-nhom"`, nên đổi thành `Tetris` (cần báo cả nhóm vì đây là file khóa).

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: trên `520f488`: 47/48 test chạy xanh (30 test P2 skip), 15/15 kiểm tất định đạt, smoke 2 tiến trình đạt. Test fail duy nhất là test template của TEAM.md (ghi chú 1). Chưa có toàn văn PRD-0 trong repo để đối chiếu từng AC. HUD/UI Phase 1 chưa có bằng chứng ảnh chụp.
- Tag `phase-1` gắn **trễ** (sau hạn 1:00) do quên trong lúc chuyển sang Phase 2.
- Điều cần chỉnh cho phase sau: lấy PRD-0/PRD-1 từ lab board để bổ sung AC còn thiếu; viết test riêng cho từng luật mới (oxy, ngạt, hái, bắt cá, quán) ngay khi các module `sim/*` đẩy code; chạy `check_determinism.py` trước mỗi lần gắn tag.
