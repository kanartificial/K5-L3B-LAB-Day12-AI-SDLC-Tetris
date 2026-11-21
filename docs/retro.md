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

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
