# Credits

## Mã nguồn
- **Khung starter Lab Day 12 — Quán Ăn Chợ Nổi** (headless, contract, inventory, runner, live, client mẫu): tác giả lab, commit `08f4b7f`, `932cd94`, `59c6011`. Dùng theo điều khoản của khóa học (xem `docs/clarify.md`).
- **Phần nhóm Tetris viết** (luật `sim/*`, kho cá thể v1.2, `day`/Shop, UI, bench, soak, test, tool QA): giấy phép MIT, xem [LICENSE](LICENSE).

## Tài sản (asset)
Đã rà toàn repo cho bản v1.0.0: **không dùng tài sản ngoài**.

| Loại | Nguồn | Giấy phép |
|---|---|---|
| Hình (nhân vật, cá, Cá Sấu, rau, bếp, bàn, nền) | Vẽ bằng code canvas trong `chonoi/web/index.html` | MIT (của nhóm) |
| Biểu tượng cảnh báo 🐊 🫧 😠 | Ký tự emoji Unicode, hiển thị bằng font hệ điều hành của người chơi | không đóng gói font |
| Font chữ | `system-ui` / `monospace` của hệ điều hành | không đóng gói font |
| Âm thanh / nhạc | Không có | — |

## Công cụ AI đã dùng
Chi tiết từng lần dùng, token ước tính và chỗ AI sai: [docs/ai-usage-log.md](docs/ai-usage-log.md).

| Công cụ / model | Người dùng | Việc chính |
|---|---|---|
| Antigravity CLI (Gemini 4 Neon) | @kanartificial | hợp đồng tích hợp, `sim/gather`, khung v1.1/v1.2, adapter kho cá thể |
| Codex | @KimY22-it | `sim/quan` P2–P3 (kiểm fixture, độ tươi, giữ chỗ, giá) |
| Grok (xAI) | @ThuThaoVuong | UI `chonoi/web/index.html` P1–P3 |
| Claude Code (Claude Opus 5.5) | @TranHa161 | QA (test hộp đen, smoke, tất định), tích hợp v1.2, bench/soak/cảnh báo/tương phản cao P4 |

## Công cụ khác
Python thư viện chuẩn · Chrome headless + Chrome DevTools Protocol (bench, chơi thử UI tự động) · Node.js (script CDP).
