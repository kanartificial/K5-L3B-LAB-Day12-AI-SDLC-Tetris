# Kiểm chứng Phase 3 — phần Quán

| Yêu cầu TICKET-03 | Kiểm chứng | Kết quả |
|---|---|---|
| Kho cá thể Quán, hao tươi, phát `spoiled` đúng tick và theo ID | [Test lát Quán](../proof/phase-3/quan.md) | Đạt trong runner với kho đã nạp |
| Giữ theo ID, thay phần giữ bị ươn, đơn thiếu hàng tiếp tục chờ | [Test lát Quán](../proof/phase-3/quan.md) | Đạt |
| Chốt giá lúc nấu, tính boa theo giá đã chốt | [Test lát Quán](../proof/phase-3/quan.md) | Đạt |
| Hồi quy v1.1 trong lúc ghép v1.2 | [Unittest](../proof/phase-3/regression-v11/regression.md) · [Smoke kho](../proof/phase-3/regression-v11/integration.md) · [Smoke day](../proof/phase-3/regression-v11/day.md) · [Tất định](../proof/phase-3/regression-v11/determinism.md) | 95/95 test, 15/15 ca tất định, smoke đạt |
| Bàn giao kho cá thể qua file, `day` và Shop trên manifest v1.2 | [Điểm ghép](../proof/phase-3/quan.md#bàn-giao-tích-hợp) | Chờ ghép adapter, Gather và runner |
