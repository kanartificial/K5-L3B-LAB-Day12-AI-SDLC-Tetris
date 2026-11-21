# Kiểm chứng Phase 4 — TICKET-04 “Phát hành v1.0.0” (Contract v1.3)

> Commit đo: **`9c1885e`** (code + tài liệu phát hành), gồm bench, soak, smoke, tất định, chơi thử UI và clone sạch. Tag `phase-4` và Release `v1.0.0` trỏ vào commit kế tiếp trên `main`. Commit đó **không đổi code trong `chonoi/`, `tools/` hay `game.contract.json`**. Nó chỉ thêm bằng chứng và tài liệu, và đổi điều kiện bật trong `tests/test_contract_p4.py` sang `>= (1, 3)`. `regression.log` được chạy lại trên đúng cây của commit gắn tag (129/129).
> Máy đo: Windows 11, Python 3.15.0, Chrome 157 (headless), Node 26. Bằng chứng: [docs/proof/phase-4/](../proof/phase-4/).
> Nhóm 4 người: không làm mở rộng (`leaderboard`, phụ đề SFX). `extensions: []`.

## Lệnh tái lập

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v                 # Windows: "tests;."
python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json             # bench_cmd
python3 -m chonoi.soak --seed 7 --days 10 --out soak.json                    # soak_cmd
python3 tools/smoke_p3.py all --proof docs/proof/phase-4/smoke
python3 tools/check_determinism.py --proof docs/proof/phase-4/determinism
python3 tools/playtest_warnings.py                                           # cần Chrome + Node ≥ 22
```

## AC-P4-xx → bằng chứng → kết quả

| AC | Yêu cầu TICKET-04 | Bằng chứng | Kết quả |
|---|---|---|---|
| AC-P4-01 | Contract v1.3: `contract_version "1.3"`, `bench_cmd`, `soak_cmd` ở gốc. Gameplay, tuning, kho, JSONL theo v1.2 | [game.contract.json](../../game.contract.json) · `test_contract_p4.ManifestV13` · toàn bộ test P1–P3 chạy ở 1.3 | ĐẠT |
| AC-P4-02 | **Bench có render**: `bench_cmd --seed 42 --duration 30 --out bench.json`, cảnh buổi sáng lõi (độ tươi, cá bơi, Cá Sấu, hiệu ứng mặc định), Út Sen đứng yên ở bến, cửa sổ 1280×720, làm nóng 3 s rồi đo 30 s, 5 trường JSON | [bench.json](../proof/phase-4/bench.json): `{"avg_fps": 59.89, "p1_low_fps": 54.01, "frames": 1797, "measured_s": 30.007, "load_ms": 1162}` · [bench.meta.json](../proof/phase-4/bench.meta.json) · `test_contract_p4.BenchFormula` (công thức 1% low) + `BenchRun` (chạy thật) | ĐẠT (lệnh chạy, `bench.json` đúng 5 trường). Mốc báo cáo: avg ≥ 60 **chưa đạt, 59.89**: Chrome headless khóa vsync ~60 Hz nên khung đo luôn ≈ 16.7 ms · 1% low 54.0 ≥ 30 đạt · load 1.16 s ≤ 10 s đạt |
| AC-P4-03 | **Soak**: `soak_cmd --seed 7 --days 10 --out soak.json`, 1 tiến trình, gather → quan → shop mỗi Ngày, D1–D5 lặp ở Ngày 6–10, tiền / thu / uy tín / nâng cấp / id đi xuyên suốt | [soak.json](../proof/phase-4/soak.json): `days 10, days_completed 10, crashes 0`, Ngày 10 `earned 1880, reputation 5, score 2380`, 14.0 s. Chạy lần 2 giống hệt (bỏ `duration_s`) · `test_contract_p4.SoakV13` (6 Ngày, lặp kế hoạch, tất định, mã 2) | ĐẠT |
| AC-P4-04 | **Cảnh báo dễ nhận biết** (thủy quái gần, oxy sắp hết, khách sắp giận) bằng chữ hoặc biểu tượng. **Chế độ tương phản cao**, chơi thử cả 3 cảnh báo ở chế độ đó | [ui/report.md](../proof/phase-4/ui/report.md): 4/4 ca (thường + tương phản cao), ảnh [gather-hc.png](../proof/phase-4/ui/gather-hc.png), [quan-hc.png](../proof/phase-4/ui/quan-hc.png) | ĐẠT |
| AC-P4-05 | **Clone sạch ≤ 3 lệnh** chạy bản có giao diện. README ghi yêu cầu môi trường, điều khiển, lệnh test, headless, bench | [clean-clone.md](../proof/phase-4/clean-clone.md): 3 lệnh, HTTP 200 trang + `/state`, 129/129 test trong bản clone · [README.md](../../README.md) | ĐẠT (thử trên Windows; chưa có máy macOS/Linux, xem giới hạn) |
| AC-P4-06 | **Regression P1–P3** còn hiệu lực | [regression.log](../proof/phase-4/regression.log): 129/129 OK, 0 skip · [smoke/](../proof/phase-4/smoke/) 29/29 · [determinism/determinism.md](../proof/phase-4/determinism/determinism.md) 18/18 | ĐẠT |
| AC-P4-07 | **Phát hành**: CHANGELOG theo phase, release notes, LICENSE, CREDITS, bản đóng gói ở GitHub Release v1.0.0. Tag `phase-4` và Release cùng trỏ một commit trên `main` | [CHANGELOG.md](../../CHANGELOG.md) · [release-notes-v1.0.0.md](../release-notes-v1.0.0.md) · [LICENSE](../../LICENSE) · [CREDITS.md](../../CREDITS.md) · Release v1.0.0 kèm `chonoi-v1.0.0.zip` (`git archive` của commit gắn tag) | ĐẠT khi tag và Release đã đẩy (xem mục cuối) |
| AC-P4-08 | Quy trình: retro rà hành động P2 + P3, phản tư cá nhân đủ người, clarify, nhật ký AI | [retro.md](../retro.md) · [members/](../members/) · [clarify.md](../clarify.md) #15–18 · [ai-usage-log.md](../ai-usage-log.md) | Một phần: thiếu `members/KimY22-it.md` (người đó tự viết) |

## Ghi chú đo
- Bench chạy Chrome **headless**. Tốc độ khung bị khóa theo vsync khoảng 60 Hz, nên `avg_fps` ≈ 59.9 là trần của môi trường đo, không phải giới hạn của game. Muốn đo không khóa thì chạy `--headed` trên máy có màn hình.
- Cửa sổ trình duyệt là 1280×720 đúng theo ticket. Viewport bên trong đo được 1262×624, do khung cửa sổ của Chrome headless (ghi trong `bench.meta.json`, clarify #15).
- `load_ms` tính từ lúc tiến trình bench bắt đầu đến khung hình đầu tiên có snapshot của cảnh đo, gồm cả thời gian khởi động Chrome.

## Thay đổi so với test cũ
- Không có test P1–P3 nào đổi kỳ vọng. Chỉ đổi điều kiện bật test: `test_contract_p2` và `test_contract_p3` nhận `"1.3"` dạng `in (...)`, `test_contract_p4` so phiên bản `>= (1, 3)`. Lý do: v1.3 giữ nguyên luật v1.2, và retro P3 đã cấm dùng `==` vì từng làm regression bị skip.

## Tag & Release
- `phase-4` và GitHub Release `v1.0.0` cùng trỏ commit bàn giao trên `main`, ngay sau `9c1885e`. Asset `chonoi-v1.0.0.zip` được tạo bằng `git archive` từ chính commit đó.
