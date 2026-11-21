---
name: phase-slice-delivery
description: Quy trình triển khai một lát gameplay đúng Test Contract, không hard-code số liệu, không vỡ tính tất định và ghi bằng chứng.
---

# Skill: `phase-slice-delivery`

Dùng khi bắt đầu code một lát mới (`sim/gather`, `sim/quan`, `sim/shop`, `runner`, hoặc `client/ui`).

## Quy trình bắt buộc
1. Đọc đúng PRD phase (`docs/prd-phase-n.md`), kế hoạch (`docs/plan/phase-n.md`) và hợp đồng trong `docs/contracts/`.
2. Chỉ đọc số liệu từ `game.contract.json` (`tuning`); mọi ngẫu nhiên đi qua `chonoi.rng.Streams`; mọi thực thể sắp bằng `chonoi.ids.sort_by_id` và cấp ID bằng `IdAllocator`.
3. Tuân thủ chính xác thứ tự xử lý trong một bước (PRD mục F / mục 4.5).
4. Viết test hộp đen qua `headless_cmd` phủ mọi ca biên (giới hạn bán kính, hòa `id`, cooldown `t+L`, mất giỏ LIFO, `pause`, đổi pha cùng tick).
5. Cập nhật `docs/ai-usage-log.md` và `docs/clarify.md` (nếu có giả định mới) rồi chạy skill `contract-verify`.
