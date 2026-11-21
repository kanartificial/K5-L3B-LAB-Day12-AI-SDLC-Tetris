# Kế hoạch Phase 2 (≤ 1 trang)

> Tham chiếu: [PRD Phase 2 (TICKET-02)](../prd-phase-2.md) · [TEAM.md](../../TEAM.md) · [Hợp đồng tích hợp](../contracts/README.md) · Thời lượng: **55 phút (1:00–1:55)** · Hạn tag `phase-2`: **1:55**.
> Phạm vi nhóm 4 người: **tập trung 100% Lõi v1.1** (không bắt buộc mở rộng; chỉ làm thêm nếu lõi xong sớm và xanh test).

## 1. Mục tiêu
Nâng cấp lên **Test Contract v1.1** với bộ số chuẩn và chơi trọn vòng ngày (`--mode day --days 1..5`):
- `gather`: 6 nút (`N1–N6`), 3 loài cá (`ca_linh`, `ca_loc`, `ca_keo`) bơi & sinh theo lịch (`8` ban đầu, trần `12`), **Cá Sấu Năm Chèo** (`M1` Ngày 1+, `M2` Ngày 3+), bất tử `90` tick, rơi `floor(hold/2)` LIFO khi chạm, ngạt xuyên bất tử.
- `quan`: 2 bếp (`B1–B2`), 4 bàn (`T1–T4`), 6 món theo dữ liệu, lọc theo `day_plan.dishes` khi chạy `day`.
- `day` + `Shop` + `pause`: vòng `gather → quan → shop → Ngày kế` (D1–D5), mua nâng cấp `oxygen`/`hp` có hiệu lực từ Ngày kế, tạm dừng (`pause`/`resumed`) đóng băng `sim_tick`/`phase_tick`/timer ở cả 3 mode.
- UI đầy đủ Menu, màn chuyển pha (`DayIntro`, `EveningIntro`, `DayResult`, `Summary`), Pause (`Esc`/`P`) và HUD v1.1 (`≥ 18px` ở 1280×720, `≥ 30 FPS`). Headless 1 Ngày chạy `≤ 20 s`.

## 2. Phân công đầu việc / người / phụ thuộc

| AC | Đầu việc & phạm vi | Người phụ trách | Phụ thuộc |
|---|---|---|---|
| `AC-P2-01` | **Nâng Contract v1.1 & dữ liệu chuẩn:** cập nhật `game.contract.json` (`contract_version: "1.1"`, số chuẩn mục 1–2, `day_plan` D1–D5, `shop`, `gather.monsters`), cập nhật `chonoi/{contract,inventory,inputs,scenario,headless}.py` (6 nguyên liệu, `--mode day --days`, nút `pause`/`shop_done`/`buy`, schema scenario v1.1) và đồng bộ `docs/contracts/` | Khổng Ngọc Anh (`@kanartificial`) + chốt cùng cả nhóm (0–5') | TICKET-02 |
| `AC-P2-02` | **Lát 1 (`sim/gather` — Cá bơi & sinh):** thêm `N5/N6` (`keo_neo`), 8 đàn ban đầu ở 8 điểm khác nhau, cá bơi `1.5 m/s` theo dải độ sâu từng loài, đổi hướng theo seed ở bước bơi `120, 240…`, phản xạ mép/góc, sinh cá tại `phase_tick = 360·k` (trọng số 40/30/30, cách `> 1m`, trần 12, `fish_spawned`) | Khổng Ngọc Anh (`@kanartificial`) | `AC-P2-01` |
| `AC-P2-03` | **Lát 2 (`sim/gather` — Cá Sấu, Máu & ngất):** `M1`/`M2` theo Ngày, `patrol` (1.0 m/s) ↔ `chase` (3.0 m/s, vào `d ≥ 10 & ≤ 10m`, ra `> 16m` hoặc `d < 10`), chạm `≤ 1.5m` ở `d ≥ 10` khi hết bất tử → `-1` Máu, bỏ `floor(len/2)` LIFO, `invuln = 90`, `recoil` 60 bước (`2/60 m`), `monster_hit`, `faint(cause:"monster")`, đúng thứ tự bước mục 4.5 | Khổng Ngọc Anh (`@kanartificial`) | `AC-P2-02` |
| `AC-P2-04` | **Lát 3 (`sim/quan` — 2 bếp, 4 bàn, 6 món & kế hoạch ngày):** mở rộng `B1–B2`, `T1–T4`, 6 món & 6 nguyên liệu đọc từ `tuning`; trong `day` lọc menu theo `day_plan.dishes` trước khi lọc kho khả dụng; kiểm mâu thuẫn scenario quán v1.1 (`quan.stock`/`quan.reputation` cấm trong `day`) | Võ Thị Kim Ý (`@KimY22-it`) | `AC-P2-01` |
| `AC-P2-05` | **Lát 4 (`runner` / `day` / `Shop` / `pause`):** luồng `--mode day --days 1..5`, đổi pha cùng tick (`day_start → day_plan → phase_start(gather)` → `gather_end + phase_start(quan)` → `quan_end + phase_start(shop)`), Shop (`buy` trước `shop_done`, `bought`/`buy_failed`/`shop_end`, tự đóng 600 tick, áp `upgrades → active_upgrades` đầu Ngày kế), `pause`/`resumed` cả 3 mode, dòng `end` có `days_completed` & `days_complete` | Võ Thị Kim Ý (`@KimY22-it`) + Khổng Ngọc Anh (`@kanartificial`) phối hợp | `AC-P2-01`, `AC-P2-04` |
| `AC-P2-06` | **Menu, Pause & HUD v1.1 (`client/ui`):** Menu chính (Chơi/Thoát), màn `DayIntro` (4s/nhấn phím), `EveningIntro`, `DayResult`, `Summary`, Pause (`Esc`/`P` làm mờ nền), HUD sáng đầy đủ (oxy < 25%, giờ ≤ 30s, độ sâu, giỏ, danh sách cần lấy, hồi bắt, cảnh báo “Thủy quái!” viền tím & “Hết hơi!”), HUD quán (2 bếp, 4 bàn + kiên nhẫn < 25%, kho khả dụng), chữ ≥ 18px ở 1280×720, ≥ 30 FPS | Vương Thu Thảo (`@ThuThaoVuong`, QA Lead) | `AC-P2-01`, `AC-P2-05` (dùng snapshot mẫu trước) |
| `AC-P2-07` | **Kiểm chứng, Regression & bàn giao `phase-2`:** smoke phút 20 (`docs/proof/phase-2/integration.*`), viết test hộp đen cá bơi/sinh, Cá Sấu, 6 món, `day --days 1..5`, Shop nâng cấp, `pause`, đo thời gian 1 Ngày ≤ 20s; chạy regression P1 (ghi rõ lý do các test P1 cập nhật theo số chuẩn v1.1); hoàn thiện `docs/verification/phase-2.md`, `docs/{clarify,standup,ai-usage-log,retro}.md` và gắn tag `phase-2` trên `main` | Lý Hà Trân Trân (`@TranHa161`) + Vương Thu Thảo (`@ThuThaoVuong`) + cả nhóm | `AC-P2-02` → `AC-P2-06` |

## 3. Lịch phối hợp (55 phút)
- **0–5 phút:** Chốt diff Contract v1.1 (`AC-P2-01`), chia rõ ranh giới file (`gather.py`, `quan.py`, `day/shop/runner`, `web/index.html`, `tests/`).
- **5–20 phút:** Build song song 4 lát; chốt `game.contract.json` v1.1 sớm nhất có thể để cả nhóm kéo về dùng chung.
- **Phút 20 (Checkpoint bắt buộc):** Chạy smoke tích hợp `gather --inventory-out → quan --inventory` với số chuẩn v1.1, lưu `docs/proof/phase-2/integration.*`; standup 2–3 phút (`docs/standup.md`), điều người xong sang lát trễ (ưu tiên hỗ trợ `day`/Shop nếu vướng).
- **20–35 phút:** Ghép hoàn chỉnh luồng `day` + Shop + `pause` + HUD v1.1 trên `main`.
- **35–45 phút:** Chạy smoke `day --days 1` & nhiều Ngày (kiểm nâng cấp `oxygen`/`hp` từ Ngày 2, `M2` từ Ngày 3), chạy regression P1, đo tốc độ ≤ 20s/Ngày, lưu `docs/proof/phase-2/` và điền `docs/verification/phase-2.md`.
- **45–55 phút:** Retro nhanh vào `docs/retro.md`, cập nhật `docs/ai-usage-log.md` & `docs/clarify.md`, rà DoD và đẩy tag `phase-2` chậm nhất **1:55**.

## 4. Rủi ro & hướng xử lý
- **Đụng file khung chung (`chonoi/{headless,inputs,scenario,runner,contract}.py`):** chốt gọn phần nâng khung v1.1 ngay trong `AC-P2-01` (5–10 phút đầu) rồi push lên `main` để 4 bạn cùng pull, tránh conflict lớn về sau.
- **Test P1 cũ lệch do đổi số chuẩn v1.1** (`fish_initial` từ mảng 6 đàn thành số `8` đàn bơi/sinh, thêm `M1`, `N5/N6`, 6 món): chạy sớm regression P1 với `random_fish: false` ở fixture cần cá đứng yên, và ghi rõ lý do cập nhật test trong commit & `docs/verification/phase-2.md`.
- **Thứ tự xử lý tick phức tạp trong `gather` & `day`** (bắt cá trước khi cá bơi, ngạt đi trước hit, `phase_start` cùng tick đổi pha, `buy` trước `shop_done`, `pause` đóng băng `sim_tick`/`phase_tick`): bám sát mục 4.5 của `docs/prd-phase-2.md` và viết test biên từng trường hợp ngay trong quá trình code.
- **Hiệu năng 1 Ngày (`≤ 22.200` tick trong `≤ 20 s`):** hạn chế cấp phát/sort dư thừa trong vòng tick và tránh ghi snapshot quá dày ở test hiệu năng.
