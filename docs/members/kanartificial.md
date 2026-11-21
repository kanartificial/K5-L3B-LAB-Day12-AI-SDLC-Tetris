# kanartificial — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Thiết lập `TEAM.md` (`2ec6272`) và cập nhật `game.contract.json` (`team: "tetris"`).
  - Soạn bộ hợp đồng tích hợp `docs/contracts/{README,inventory,sim-ui,events}.md` (`78bf8a3`).
  - Triển khai trọn vẹn Lát 1 & Lát 2 `chonoi/sim/gather.py` (bơi, biên, `dive`/`surface`, oxy, `choke` `t+59`, `faint` LIFO, hái nút, `node_regrown`, bắt cá + cooldown `t+L`, `hold_full`, cập bến, xuất kho) cùng 10 test hộp đen `tests/test_gather_p1.py` (`f020f68`).
  - Lập kế hoạch `docs/plan/phase-1.md` (`ece548f`), `docs/plan/phase-2.md` (`a2634c6`), bổ sung `tests/test_integration_p1.py` và bằng chứng `docs/proof/phase-1/{gather,integration}.md`.
- **Tôi đã review (kèm link):** Rà tích hợp `chonoi/sim/quan.py` (`8ad8880`) và `chonoi/play_campaign.py` (`2df9c22`) so với Test Contract v1.0; phát hiện thiếu `vel` trong `QuanSim.snapshot()["player"]` và bổ sung.
- **AI sai ở đâu và tôi phát hiện thế nào:** Khi viết test `test_gather_p1.py`, AI tạo dư một biến `inp` ghi đè ngay sau đó; rà lại code trước khi commit và bỏ đoạn thừa. Ngoài ra kiểm tra thực tế phát hiện `test_template_is_rejected` fail do đọc `TEAM.md` đã điền.
- **Điều tôi học được:** Chốt sớm contract (schema kho, snapshot, event) và viết test hộp đen ngay theo từng ca biên giúp 4 module ghép lại gần như không lỗi.
