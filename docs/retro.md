# Retro nhóm

## Phase 2 (nhanh)
> Bản nháp do QA (@TranHa161) viết từ bằng chứng trong repo; cả nhóm đọc lại và sửa trước khi gắn tag `phase-2`.

- Điều tốt:
  - Viết test trước: 30 test hộp đen v1.1 (`tests/test_contract_p2.py`) có sẵn từ đầu phase, tự bật khi Integrator nâng contract lên 1.1 → lõi backend xanh **88/88**, 1 Ngày headless **1.3 s** (≤ 20 s), tất định byte-cho-byte.
  - Smoke tích hợp phút 20 và regression chạy bằng 1 lệnh (`tools/smoke_p2.py`), bằng chứng tự ghi vào `docs/proof/phase-2/`.
  - Cả 4 người đều đã có ≥ 3 commit gắn tài khoản của mình.
- Điều tệ:
  - Tag `phase-1` đẩy trễ hạn 1:00 vì cả nhóm chuyển sang Phase 2 mà không ai chốt tag.
  - UI chỉ được chơi thử thật ở cuối phase: lúc đó mới thấy nút Tiếp tục không bỏ được pause, EveningIntro/DayResult không bao giờ hiện, phím W/S đảo ngược ở quán khi chạy `day`. Test headless xanh nhưng không bắt được lỗi luồng màn hình.
  - Nhiều người cùng sửa `README.md` và `docs/verification/*.md` khi chưa pull → pull bị chặn, mất thời gian gỡ.
- 1 hành động cho Phase 3: trước mỗi lần đẩy thay đổi UI, chạy chơi thử tự động `docs/proof/phase-2/ui/ui_drive.mjs` + `unittest` và dán kết quả vào commit. **Người nhận:** @ThuThaoVuong (UI), @TranHa161 kiểm lại. Integrator @kanartificial đặt nhắc gắn tag 5 phút trước mỗi hạn.

## Phase 3 (nhanh): rút ra từ lần đổi kho đếm → kho cá thể
> Chốt ngày 2026-11-21, trước khi gắn tag `phase-3`. Bằng chứng: `docs/verification/phase-3.md`, `docs/proof/phase-3/`.

- **Rà hành động Phase 2** (chạy `ui_drive.mjs` + `unittest` trước khi đẩy UI): **chưa làm**. Hai commit `update ui phase 3` (`8c05158`, `94f2328`) không có kết quả chơi thử tự động đi kèm, và `docs/proof/phase-3/` chưa có ảnh/log UI. Lý do: phase chỉ có 35 phút, UI đẩy song song với lúc ghép backend. Nhắc gắn tag thì có: tag `phase-3` được đẩy kèm bằng chứng của đúng commit gắn tag.
- **Điều tốt:**
  - Chốt schema và thứ tự tích hợp ngay từ đầu (`docs/plan/phase-3.md`, ADR-0001). Dùng số học chính xác 240 đơn vị/điểm tươi (`Fraction`), nên không lệch float ở ngưỡng 30 hay ở phép `floor` giá. Round-trip file sát ngưỡng ươn đúng tick 119.
  - Mỗi lát có test v1.2 riêng (`test_gather_p3` 10 test, `test_quan_p3` 7 test) viết trong lúc manifest còn 1.1.
  - Khi bật 1.2, toàn bộ luật P1/P2 vẫn giữ nhờ migrate fixture bằng helper (`inst`/`counts`) thay vì viết lại test. Kết quả: 119/119 test, smoke 29/29, tất định 18/18.
- **Điều tệ:**
  - Test lát xanh nhưng **lần ghép đầu vẫn hỏng**: Quán nhận `fresh` kiểu `int/float`, adapter trả `Fraction`, nên Quán từ chối chính file kho Gather vừa ghi. Lỗi chỉ lộ khi chạy smoke 2 tiến trình thật, mà mốc smoke phút 20 đã bị bỏ qua.
  - Quán bật v1.2 theo `tuning.freshness` thay vì `contract_version`, nên `main` đỏ 18/105 test ngay cả khi manifest còn 1.1. Commit lên `main` khi chưa chạy đủ test, trái `AGENTS.md`.
  - `test_contract_p2` chỉ chạy khi version đúng `"1.1"`, nên lên 1.2 thì regression P2 lặng lẽ skip 32 test. Điều kiện skip theo `==` che mất regression.
  - Đóng góp Phase 3 dồn vào 1–2 commit lớn mỗi người (`git shortlog phase-2..`: kanartificial 1, KimY22-it 1, ThuThaoVuong 1 (+1 merge), TranHa161: commit tích hợp + QA). Khó đọc lại và khó review trước khi đẩy.
- **Một lần AI sai và cách phát hiện:** test lát Quán do AI viết truyền `fresh` dạng số nguyên thẳng vào runner, bỏ qua `read_inventory`. Test xanh nhưng không phản ánh đường bàn giao thật. QA phát hiện bằng smoke ticket (`gather --inventory-out` → `quan --inventory --ticks 0`), sau đó viết test hồi quy và xác nhận test fail 5/14 trên HEAD cũ.
- **1 hành động cho Phase 4:** `python tools/smoke_p3.py integration day` phải đạt trên `main` trước khi bắt đầu việc tiếp. Mọi điều kiện skip theo version phải viết dạng `>=`/`in (...)`, không dùng `==`. Mỗi lát đẩy commit nhỏ kèm kết quả test trong mô tả. **Người nhận:** @TranHa161 (QA) chạy smoke và chặn tag nếu đỏ. Integrator @kanartificial từ chối merge khi commit không ghi kết quả test. @ThuThaoVuong đính ảnh hoặc log `ui_drive` cho mỗi commit UI.

## Phase 4 (cuối): phát hành v1.0.0
> Điều phối retro: @TranHa161. Viết từ bằng chứng trong repo (git log, `docs/proof/`, `docs/verification/`). Mỗi người đọc lại và bổ sung phần của mình trong `docs/members/`.

### Rà lại hành động đã chốt
| Hành động | Chốt ở | Đã làm? | Bằng chứng / vì sao |
|---|---|---|---|
| Chạy chơi thử UI tự động + `unittest` trước khi đẩy thay đổi UI, dán kết quả vào commit (@ThuThaoVuong, @TranHa161 kiểm lại) | P2 | **P3: không. P4: có, nhưng do QA làm** | P3: hai commit `update ui phase 3` không kèm log `ui_drive`. P4: thay đổi UI (cảnh báo, tương phản cao) nằm trong `9c1885e` kèm `tools/playtest_warnings.py`, 4/4 ca có ảnh. Người làm là QA chứ không phải chủ module UI, nên thói quen vẫn chưa thành của người viết UI. |
| Nhắc gắn tag 5 phút trước hạn (@kanartificial) | P2 | Có | Tag `phase-2`, `phase-3` đã đẩy, mỗi tag kèm bằng chứng của đúng commit đó. |
| Smoke tích hợp phải đạt trên `main` trước việc tiếp; QA chặn tag nếu đỏ | P3 | Có | `tools/smoke_p3.py all` 29/29 và tất định 18/18 trên `9c1885e`, trước khi gắn `phase-4`. |
| Điều kiện skip theo version viết `>=` / `in (...)`, không dùng `==` | P3 | Có, sau một lần trượt | P2/P3 đổi sang `in (...)`. Test P4 mới viết bị AI viết lại thành `== "1.3"`. Phát hiện khi viết chính retro này và đã đổi sang `>= (1, 3)`. |
| Commit nhỏ kèm kết quả test; Integrator từ chối merge khi thiếu | P3 | **Chưa đều** | Commit của QA ghi kết quả test trong mô tả. Các commit `update ai log`, `update file md` (P4) không ghi gì và vẫn vào `main`, vì nhóm đẩy thẳng `main` nên không có bước chặn. |

### Điều làm tốt
- Mỗi phase có ma trận AC → bằng chứng → kết quả gắn với commit cụ thể (`docs/verification/phase-1..4.md`). Bằng chứng tự sinh bằng script, không chép tay.
- Test hộp đen viết trước theo ticket (P2: 30 test, P3: 14, P4: 10) và chạy qua `headless_cmd` / `bench_cmd` / `soak_cmd`, nên đổi nội bộ không làm vỡ hợp đồng. Cả repo hiện có 129 test, 0 skip.
- Hai lần đổi contract lớn (1.1 → 1.2 kho cá thể, 1.2 → 1.3) đều giữ được regression P1–P3 nhờ migrate fixture bằng helper thay vì viết lại test.
- Tất định byte-cho-byte suốt 4 phase. Soak 10 Ngày cho kết quả giống hệt nhau giữa hai lần chạy.

### Điều cần sửa
- Đóng góp lệch: commit không merge theo người là TranHa161 10, kanartificial 9, ThuThaoVuong 4, KimY22-it 3. Việc tích hợp và QA dồn vào một người, nên khi người đó vắng thì không ai chạy smoke.
- Lỗi tích hợp chỉ lộ ở cuối phase (P3: Quán từ chối `fresh` dạng `Fraction`, Shop nhận id). Chơi thử UI thật cũng chỉ làm ở cuối (P2).
- Đẩy thẳng `main` không có review. `main` từng đỏ 18 test (P3) mà không ai biết cho tới lúc QA kiểm.
- Đo token chưa đều: chỉ @kanartificial ghi số token, các dòng khác ghi “chưa đo”.

### Một lỗi AI đã mắc và cách nhóm xác minh
Ở P3, test lát Quán do AI viết truyền `fresh` dạng số nguyên thẳng vào runner, bỏ qua `read_inventory`. Test xanh nhưng đường bàn giao thật thì hỏng. Nhóm xác minh bằng smoke hai tiến trình đúng ví dụ ticket (`gather --inventory-out` → `quan --inventory --ticks 0`), sau đó viết test hồi quy và chạy trên commit cũ để chắc test **fail 5/14 trước khi sửa**. Ở P4 thì AI lặp lại lỗi `== "1.3"` mà retro vừa cấm, và chỉ được phát hiện khi người đọc lại diff.

### Nếu làm lại / hành động tiếp theo
1. Chạy smoke đầu-cuối (2 tiến trình + `day`) từ **phút đầu** của mỗi phase, coi đó là “test đỏ” cần làm xanh, không để tới cuối. Người nhận: QA.
2. Làm theo nhánh ngắn + PR, mỗi PR cần một người khác chạy `contract-verify` rồi mới merge. Người nhận: Integrator.
3. Người viết UI tự chạy `tools/playtest_warnings.py` / `ui_drive.mjs` trước khi đẩy, không chờ QA. Người nhận: @ThuThaoVuong.
4. Mỗi lần dùng AI ghi token ước tính và chỗ AI sai vào `docs/ai-usage-log.md` ngay lúc làm. Người nhận: cả nhóm.
