# <github-handle> — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  - Hoàn thiện và sửa UI `chonoi/web/index.html` (Phase 1): dựng giao diện cơ bản cho game, có tương tác giữa các nhân vật
  - Nâng cấp UI cho Phase 2: thêm HUD oxy/máu/giỏ, cảnh báo hết hơi & thủy quái, DayIntro, Pause, Shop.
  - Commit: `2df9c22`, `a7c30ac`

- Tôi đã review (kèm link):
  - Review hợp đồng `docs/contracts/sim-ui.md` và logic interact ở `quan.py` để khớp snapshot.
  - Kiểm tra luồng chuyển pha và input LiveInputs.
  - Review: `2df9c22`, `a7c30ac`

- AI sai ở đâu và tôi phát hiện thế nào:
  - AI viết UI giả định `stove.dish` và `hand` luôn là string. Thực tế sim trả object `{dish_id, order_id, ...}`. Khi nhấn E bắt đầu nấu → `.slice` trên object → crash render, nhân vật biến mất. Phát hiện bằng Console F12 (TypeError) + đọc `quan.py` `_interact_stove`.

- Điều tôi học được:
  - UI chỉ được đọc snapshot, không được giả định kiểu dữ liệu. Luôn kiểm tra `typeof` trước khi dùng method của string. Nên bọc `render()` trong try/catch để một lỗi vẽ không làm chết cả vòng game.