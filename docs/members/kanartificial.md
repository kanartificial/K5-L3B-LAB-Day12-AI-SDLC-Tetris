# kanartificial — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm:**
  - **Phase 1:** Thiết lập `TEAM.md` (`2ec6272`), chốt `docs/contracts/` v1.0 (`78bf8a3`), triển khai Lát 1–2 `chonoi/sim/gather.py` + `tests/test_gather_p1.py` (`f020f68`), kế hoạch P1/P2 (`ece548f`, `a2634c6`), `tests/test_integration_p1.py`, `README.md`, bằng chứng Phase 1 (`6f0fdcc`) và gắn tag `phase-1`.
  - **Phase 2:** Nâng Contract v1.1 (`game.contract.json`, `chonoi/{contract,inventory,inputs,scenario,headless,live}.py`, `docs/contracts/`), cá bơi/sinh + Cá Sấu Năm Chèo (`chonoi/sim/gather.py`), `ShopSim` + `DaySession` + `pause` (`chonoi/sim/shop.py`, `chonoi/runner.py`), `tests/test_gather_p2.py`, cập nhật `AGENTS.md` và 2 skill nhóm trong `.agents/skills/`.
- **Tôi đã review:** Rà `chonoi/sim/quan.py` (`8ad8880`), `chonoi/play_campaign.py` (`2df9c22`) và `tests/test_contract_p2.py` (`957e58c`); bổ sung `vel` và `allowed_dishes` cho `QuanSim`.
- **AI sai ở đâu và tôi phát hiện thế nào:** Ở Phase 1, AI tạo dư một biến `inp` ghi đè trong test và gặp lỗi `test_template_is_rejected` khi `TEAM.md` đã điền thật; rà code và tách `TEMPLATE` riêng. Ở Phase 2, kiểm kỹ tick snapshot cho thấy cần chụp snapshot khi `bought` để không bỏ lỡ nâng cấp vừa mua trước `shop_done`.
- **Điều tôi học được:** Test-first bằng `test_contract_p2.py` và chốt contract sớm giúp cả nhóm ghép 86/86 test xanh ngay lần chạy đầu.
