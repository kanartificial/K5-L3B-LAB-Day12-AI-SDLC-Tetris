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

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
