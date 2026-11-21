# Chơi thử 3 cảnh báo — thường & tương phản cao (AC-P4-03)

- Commit: `9c1885e` · trình duyệt `chrome.exe` headless · viewport 1280×720 · 4.2 s
- Lệnh: `python3 tools/playtest_warnings.py`

| Ca | Tương phản cao | Banner hiện (chữ + biểu tượng) | Kết quả | Ảnh |
|---|---|---|---|---|
| gather-normal | tắt | `warnOxy`: 🫧 SẮP HẾT OXY (6s) — NỔI LÊN!; `warnMonster`: 🐊 THỦY QUÁI GẦN! | ĐẠT | [gather-normal.png](gather-normal.png) |
| quan-normal | tắt | `warnAngry`: 😠 KHÁCH SẮP GIẬN: T1 | ĐẠT | [quan-normal.png](quan-normal.png) |
| gather-hc | bật | `warnOxy`: 🫧 SẮP HẾT OXY (4s) — NỔI LÊN!; `warnMonster`: 🐊 THỦY QUÁI GẦN! | ĐẠT | [gather-hc.png](gather-hc.png) |
| quan-hc | bật | `warnAngry`: 😠 KHÁCH SẮP GIẬN: T1 | ĐẠT | [quan-hc.png](quan-hc.png) |

Ngoài banner, canvas vẽ ô “!” trên Cá Sấu khi ở gần (< 12 m) và ô “!” + chữ “SẮP GIẬN” ở bàn có khách
còn < 25 % kiên nhẫn. Chế độ tương phản cao đổi nền đen, chữ/viền vàng, tăng tương phản canvas (phím `H`).
