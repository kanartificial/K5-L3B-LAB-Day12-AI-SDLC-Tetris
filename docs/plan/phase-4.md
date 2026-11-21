# Kế hoạch Phase 4 — Phát hành v1.0.0 (≤ 1 trang)

> Tham chiếu: `TICKET-04` · [TEAM.md](../../TEAM.md) · [Hợp đồng tích hợp](../contracts/README.md) · [Retro](../retro.md) · Thời lượng: **30 phút (2:30–3:00)** · Contract **v1.3** · Hạn tag `phase-4` & GitHub Release `v1.0.0`: **3:00**.
> Phạm vi nhóm 4 người: **100% Lõi v1.3 + Soak headless 10 Ngày + Đóng gói/Release + Retro & Phản tư cá nhân** (mở rộng `leaderboard` / phụ đề SFX không bắt buộc với nhóm 4 người; chỉ làm nếu lõi & Release đã xanh sớm).
> Cổng vào từ Retro P3: chạy `python3 tools/smoke_p3.py integration day` xanh trên `main` trước khi ghép việc mới; không dùng `==` để skip test theo version; mọi commit ghi kết quả test (commit UI đính ảnh/log chơi thử).

## 1. Phân vai Phase 4 & Phân công AC

| Vai quy trình | Thành viên | AC phụ trách | Phạm vi & Đầu ra chính | Phụ thuộc |
|---|---|---|---|---|
| **Release / Integrator** + **Soak** | Khổng Ngọc Anh (`@kanartificial`) | `AC-P4-01`, `AC-P4-03`, `AC-P4-06` | Nâng `game.contract.json` → `contract_version: "1.3"`, khai `bench_cmd` & `soak_cmd` ở gốc (giữ gameplay/tuning/kho/JSONL v1.2); cài `soak_cmd` (`--seed 7 --days 10 --out soak.json`, lặp `day_plan` D1–D5 ở Ngày 6–10, nối suốt tiền/uy tín/nâng cấp/số Ngày/`id` cá thể, `days_completed == days`, `crashes == 0`, lặp lại được ở trường gameplay); rà `CHANGELOG.md` theo từng phase, viết Release notes `v1.0.0`, kiểm commit bàn giao, gắn tag `phase-4` & công bố GitHub Release `v1.0.0`. | TICKET-04; `AC-P4-06` phụ thuộc `AC-P4-01` → `AC-P4-05`, `AC-P4-07` |
| **UI Cảnh báo & Benchmark** | Vương Thu Thảo (`@ThuThaoVuong`) | `AC-P4-02`, `AC-P4-04` | Cài `bench_cmd` (`--seed 42 --duration 30 --out bench.json`): cảnh sáng lõi (độ tươi, cá bơi, Cá Sấu Năm Chèo, hiệu ứng mặc định, Út Sen đứng yên ở bến), cửa sổ `1280×720`, làm nóng 3 s + đo 30 s, xuất đúng 5 trường (`avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`), lưu `bench.json` vào `docs/proof/phase-4/`. Thêm chữ/biểu tượng cảnh báo rõ cho **thủy quái gần**, **oxy sắp hết**, **khách sắp giận** và **chế độ tương phản cao** trong `chonoi/web/index.html`; chơi thử cả 3 cảnh báo ở chế độ tương phản cao & lưu bằng chứng. | `AC-P4-01` |
| **Đóng gói** | Võ Thị Kim Ý (`@KimY22-it`) | `AC-P4-05` | Cập nhật `README.md` (yêu cầu môi trường, chạy bản có giao diện từ clone sạch ≤ 3 lệnh trên Linux/macOS, điều khiển, lệnh test, headless, benchmark, soak, mục “Sáng tạo của nhóm”); bổ sung `LICENSE` và rà `CREDITS.md`; tạo gói phát hành đính kèm Release `v1.0.0`; thử chạy trực tiếp từ **clone sạch** và lưu log bằng chứng vào `docs/proof/phase-4/`. | `AC-P4-01`, `AC-P4-02`, `AC-P4-04` |
| **Bench / QA** + **Điều phối Retro** | Lý Hà Trân Trân (`@TranHa161`) + cả nhóm | `AC-P4-07` | Chạy regression P1–P3 + test mới v1.3 (`bench_cmd`, `soak_cmd` 10 Ngày + tính lặp, `check_determinism.py --proof docs/proof/phase-4`), lập ma trận `AC-P4-xx → bằng chứng → kết quả trên commit bàn giao` trong `docs/verification/phase-4.md`. Điều phối Retro cuối trong `docs/retro.md` (mở đầu bằng rà hành động đã chốt ở **Retro P2** & P3, nêu 1 lỗi AI & cách xác minh, tổng hợp bằng chứng đóng góp), đôn đốc đủ 4 file `docs/members/<handle>.md` (≤ 200 từ, dẫn commit/bằng chứng), cập nhật `docs/clarify.md` & `docs/ai-usage-log.md`. | `AC-P4-01` → `AC-P4-05` |

## 2. Ma trận AC-P4 dự kiến & Tiêu chí nghiệm thu

| AC | Tiêu chí đạt (khớp DoD TICKET-04) | Bằng chứng lưu tại |
|---|---|---|
| `AC-P4-01` | `game.contract.json` có `contract_version: "1.3"`, khai `bench_cmd`, `soak_cmd` ở gốc; toàn bộ test kiểm version không skip ngầm regression P1–P3. | `game.contract.json`, `docs/proof/phase-4/` |
| `AC-P4-02` | `<bench_cmd> --seed 42 --duration 30 --out bench.json` chạy được cảnh sáng chuẩn `1280×720` (3 s làm nóng + 30 s đo), xuất đúng 5 trường JSON (báo cáo so mốc `avg ≥ 60 FPS`, `1% low ≥ 30 FPS`, `load ≤ 10 s`). | `docs/proof/phase-4/bench.json` (+ log chạy trên commit nộp) |
| `AC-P4-03` | `<soak_cmd> --seed 7 --days 10 --out soak.json` chạy 10 Ngày liên tục 1 tiến trình (`day_plan` lặp Ngày 6–10), `days_completed == 10`, `crashes == 0`, kết quả gameplay lặp lại được giữa 2 lần chạy. | `docs/proof/phase-4/soak.json` (+ log kiểm lặp) |
| `AC-P4-04` | Có chữ hoặc biểu tượng cho 3 cảnh báo (thủy quái gần, oxy sắp hết, khách sắp giận) + chế độ tương phản cao hoạt động và đã chơi thử cả 3 cảnh báo ở chế độ đó. | `chonoi/web/index.html`, ảnh/log trong `docs/proof/phase-4/` |
| `AC-P4-05` | Từ clone sạch chạy bản có giao diện theo `README.md` trong ≤ 3 lệnh (Linux/macOS); đủ yêu cầu môi trường, điều khiển, test, headless, benchmark; `LICENSE` & `CREDITS.md` đầy đủ; có gói phát hành đính kèm Release. | `README.md`, `LICENSE`, `CREDITS.md`, `docs/proof/phase-4/clean_clone.log` |
| `AC-P4-06` | `CHANGELOG.md` đủ các phase, Release notes `v1.0.0` (điểm mới, cách chạy, giới hạn đã biết); tag `phase-4` và GitHub Release `v1.0.0` cùng trỏ tới 1 commit bàn giao trên `main` chậm nhất **3:00**. | `CHANGELOG.md`, GitHub tag `phase-4` & Release `v1.0.0` |
| `AC-P4-07` | Regression P1–P3 + determinism xanh trên commit bàn giao; `docs/verification/phase-4.md` khớp commit; `docs/retro.md` đã rà hành động P2 + lỗi AI; đủ 4 file `docs/members/<handle>.md` (≤ 200 từ); cập nhật `docs/clarify.md`, `docs/ai-usage-log.md`. | `docs/verification/phase-4.md`, `docs/retro.md`, `docs/members/*.md` |

## 3. Lịch 30 phút (2:30–3:00)

- **0–5 phút (2:30–2:35):** Chạy cổng vào `smoke_p3.py integration day` trên `main`; chốt `contract_version: "1.3"` và chữ ký CLI của `bench_cmd` & `soak_cmd` (`AC-P4-01`).
- **5–15 phút (2:35–2:45):** Làm song song:
  - `@ThuThaoVuong`: `bench_cmd` (`1280×720`, làm nóng 3 s, đo 30 s) + 3 cảnh báo chữ/biểu tượng & chế độ tương phản cao.
  - `@kanartificial`: `soak_cmd` 10 Ngày (bot/input tất định, lặp `day_plan` D1–D5) + rà `CHANGELOG.md`.
  - `@KimY22-it`: cập nhật `README.md`, tạo `LICENSE`, rà `CREDITS.md`, chuẩn bị đóng gói & chạy thử từ clone sạch.
  - `@TranHa161`: viết test v1.3 (`bench_cmd`, `soak_cmd`, regression version), dựng khung `docs/verification/phase-4.md`.
- **15–25 phút (2:45–2:55):**
  - **Phút 20 (2:50 — Standup 2 phút):** Rà vướng mắc, điều người đã xong sang hỗ trợ; pair chạy smoke + `bench_cmd` + `soak_cmd` + regression P1–P3 trên bản tích hợp.
  - Cả nhóm hoàn tất **Retro cuối** (`docs/retro.md`, mở đầu bằng rà hành động P2) và **4 phản tư cá nhân** (`docs/members/<handle>.md`, ≤ 200 từ, dẫn commit/bằng chứng), cập nhật `docs/clarify.md` & `docs/ai-usage-log.md`.
- **25–30 phút (2:55–3:00):** Đóng băng code ở phút 25; chạy lại bộ kiểm chứng cuối trên **đúng commit bàn giao** trên `main`, đối chiếu toàn bộ artifact trong `docs/proof/phase-4/` & `docs/verification/phase-4.md`; đẩy tag **`phase-4`** và công bố GitHub Release **`v1.0.0`** (đính kèm bản đóng gói + release notes) chậm nhất **3:00**. Chuẩn bị checklist Demo 4 mục sau 3:00.

## 4. Rủi ro chính & Hướng xử lý

- **Regression P1–P3 bị skip ngầm khi lên `"1.3"`** (bài học Retro P3): rà mọi điều kiện kiểm `contract_version` trong `tests/` và `tools/` chuyển sang `>=` / tập phiên bản hợp lệ; xác nhận số test chạy không giảm.
- **Sai công thức hoặc môi trường đo `bench_cmd`:** bám đúng `p1_low_fps = 1 / mean(max(1, ceil(0.01 * frames)) khung chậm nhất tính theo giây)`, tách rõ 3 s làm nóng trước khi ghi `frames`/`measured_s`, đo đúng `load_ms` từ lúc khởi chạy tới khung đầu tiên của cảnh đo `1280×720`.
- **Soak 10 Ngày lỗi chu kỳ hoặc mất trạng thái xuyên Ngày:** dùng `day_plan[(day - 1) % 5]` cho Ngày 6–10, giữ nguyên bộ cấp `id` cá thể, tiền, tổng thu, uy tín và cấp nâng cấp xuyên suốt; khi so tính lặp bỏ trường `duration_s`.
- **Trễ hạn tag `phase-4` & Release `v1.0.0` (3:00):** đặt mốc đóng băng code ở **2:55** (phút 25); không gộp thêm tính năng mở rộng nếu lõi/đóng gói/retro chưa hoàn tất.
