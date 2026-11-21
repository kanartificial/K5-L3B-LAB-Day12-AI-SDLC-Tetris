# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| `AC-P1-01` | Kiểm `TEAM.md`, `game.contract.json` (`team: "tetris"`, `team_size: 4`), `docs/contracts/` + `inventory.sample.json`, chạy `test_team_check.py` | [integration.md](../proof/phase-1/integration.md) · [contracts/README.md](../contracts/README.md) | **Đạt một phần** (`game.contract.json` & contracts đạt; `TEAM.md` còn trống vài ô cột vai quy trình/dự phòng) |
| `AC-P1-02` | Chạy test hộp đen Lát 1 (`test_gather_p1.py`: bơi, biên, `dive`/`surface`, oxy, `oxygen_empty`, `choke` `t+59`, `faint` LIFO) | [gather.md](../proof/phase-1/gather.md) | **Đạt** |
| `AC-P1-03` | Chạy test hộp đen Lát 2 (`test_gather_p1.py` & `test_smoke_p1.py`: hái mặt nước, `node_regrown`, bắt cá + cooldown `t+L`, `hold_full`, cập bến, ghi kho nguyên tử) | [gather.md](../proof/phase-1/gather.md) · [integration.md](../proof/phase-1/integration.md) | **Đạt** |
| `AC-P1-04` | Chạy `test_quan_p1.py` & chạy headless kiểm lịch khách, giữ chỗ, `no_dish`, kiên nhẫn, bỏ đi | [quan-arrivals.md](../proof/phase-1/quan-arrivals.md) | **Đạt một phần** (luật lõi đạt; `chonoi/scenario.py` chưa bổ sung hết các ca kiểm mâu thuẫn fixture quán nâng cao) |
| `AC-P1-05` | Chạy `test_quan_p1.py` & `test_integration_p1.py` kiểm `interact`, nấu → chín → bưng → phục vụ → trả tiền + boa + uy tín + đóng ca | [quan-orders.md](../proof/phase-1/quan-orders.md) · [integration.md](../proof/phase-1/integration.md) | **Đạt** |
| `AC-P1-06` | Chơi thử trực tiếp `python3 -m chonoi.live --mode gather\|quan` và chạy `test_live.py` kiểm `GET /state`, `POST /input`, `POST /restart` | [integration.md](../proof/phase-1/integration.md) (`test_live.py`) | **Đạt** |
| `AC-P1-07` | Chạy smoke 2 tiến trình (`gather --inventory-out` → `quan --inventory`) và toàn bộ 51 test bằng 1 lệnh; kiểm `README.md` và ghi chép tối thiểu | [integration.md](../proof/phase-1/integration.md) | **Đạt một phần** (51/51 test & smoke 2 tiến trình đạt; cần hoàn tất commit cá nhân của `@TranHa161` và file phản tư các thành viên còn lại) |

## Đánh giá ngắn
- **Yêu cầu đạt:** Toàn bộ luật lõi `gather` (Lát 1–2), `quan` (Lát 3–4), UI chơi 2 buổi, hợp đồng kho + smoke test 2 tiến trình, bộ 51 test hộp đen/unit chạy bằng 1 lệnh (`OK`).
- **Yêu cầu chưa trọn vẹn (ghi trung thực):** Kiểm tra mâu thuẫn fixture quán nâng cao trong `chonoi/scenario.py` còn TODO cho bước tiếp theo; tại thời điểm tổng hợp bằng chứng, `@TranHa161` chưa có commit trực tiếp trên `main` và một số ô vai quy trình trong `TEAM.md` còn trống.
- **Điều cần chỉnh cho Phase 2:** Chốt sớm khung Contract v1.1 trong 5–10 phút đầu để 4 bạn cùng pull, đảm bảo mọi thành viên commit đều đặn và bổ sung kiểm fixture v1.1 ngay khi code `day`/`quan`.
