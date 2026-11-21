"""QA Phase 4 (AC-P4-03): chơi thử tự động 3 cảnh báo ở chế độ thường và tương phản cao.

    python3 tools/playtest_warnings.py [--browser PATH] [--proof docs/proof/phase-4/ui]

Dựng 2 server `chonoi.live` trong tiến trình (cổng ngẫu nhiên) với scenario gây cảnh báo:
  - gather: Út Sen lặn ở d = 22 m, oxy còn 400/1800 tick (< 25 %), cách Cá Sấu M1 < 12 m → oxy sắp hết + thủy quái gần
  - quan:   khách C1 ở T1 còn 700/3600 tick kiên nhẫn (< 25 %) → khách sắp giận
rồi gọi `tools/ui_warnings.mjs` (Chrome DevTools Protocol) mở `?play=1[&hc=1]`, kiểm banner hiện trong DOM, chụp ảnh.
Ghi `report.md` + ảnh vào thư mục proof. Mã thoát 0 khi mọi ca đạt.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from chonoi.bench import find_browser  # noqa: E402
from chonoi.contract import load_contract  # noqa: E402
from chonoi.live import LiveGame, LiveServer  # noqa: E402
from chonoi.scenario import load_scenario  # noqa: E402

GATHER = {"gather": {"player": {"pos": [56, 22], "oxygen_ticks": 400}, "random_fish": False}}
QUAN = {"quan": {"random_customers": False,
                 "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 90}],
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "waiting",
                                "order_status": "reserved", "order_tick": 0, "patience_ticks_left": 700,
                                "reserved": ["I1"]}]}}


def serve(mode, scenario, tmp, contract):
    path = os.path.join(tmp, f"{mode}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(scenario, f)
    version = contract["contract_version"]
    sc = load_scenario(path, mode, contract["tuning"], contract_version=version)
    srv = LiveServer(LiveGame(mode, contract["tuning"], sc, 1, contract_version=version), port=0)
    srv.start()
    return srv


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--browser")
    ap.add_argument("--proof", default=os.path.join(ROOT, "docs", "proof", "phase-4", "ui"))
    a = ap.parse_args(argv)
    exe = find_browser(a.browser)
    if exe is None:
        print("không tìm thấy Chrome/Chromium/Edge", file=sys.stderr)
        return 1
    os.makedirs(a.proof, exist_ok=True)
    contract = load_contract()
    with tempfile.TemporaryDirectory() as tmp:
        cases = []
        servers = []
        try:
            for hc in (False, True):
                # mỗi ca một server mới để trạng thái (oxy, kiên nhẫn) bắt đầu lại từ scenario
                g = serve("gather", GATHER, tmp, contract)
                q = serve("quan", QUAN, tmp, contract)
                servers += [g, q]
                suffix = "&hc=1" if hc else "&hc=0"
                tag = "hc" if hc else "normal"
                cases.append({"name": f"gather-{tag}", "url": f"{g.url}?play=1{suffix}",
                              "expect": ["warnOxy", "warnMonster"], "hc": hc})
                cases.append({"name": f"quan-{tag}", "url": f"{q.url}?play=1{suffix}",
                              "expect": ["warnAngry"], "hc": hc})
            cases_path = os.path.join(tmp, "cases.json")
            with open(cases_path, "w", encoding="utf-8") as f:
                json.dump(cases, f)
            t0 = time.monotonic()
            p = subprocess.run(["node", os.path.join(ROOT, "tools", "ui_warnings.mjs"), exe, a.proof, cases_path],
                               capture_output=True, text=True, encoding="utf-8", timeout=180)
            elapsed = time.monotonic() - t0
        finally:
            for s in servers:
                s.stop()
    if p.returncode != 0:
        print(p.stderr, file=sys.stderr)
        return 1
    results = json.loads(p.stdout.strip().splitlines()[-1])
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    lines = ["# Chơi thử 3 cảnh báo — thường & tương phản cao (AC-P4-03)", "",
             f"- Commit: `{head}` · trình duyệt `{os.path.basename(exe)}` headless · viewport 1280×720 · {elapsed:.1f} s",
             "- Lệnh: `python3 tools/playtest_warnings.py`", "",
             "| Ca | Tương phản cao | Banner hiện (chữ + biểu tượng) | Kết quả | Ảnh |", "|---|---|---|---|---|"]
    for r in results:
        vis = "; ".join(f"`{k}`: {v}" for k, v in (r.get("visible") or {}).items() if v)
        lines.append(f"| {r['name']} | {'bật' if r['hc'] else 'tắt'} | {vis or '—'} | "
                     f"{'ĐẠT' if r['ok'] else 'CHƯA ĐẠT'} | [{r['screenshot']}]({r['screenshot']}) |")
    lines += ["", "Ngoài banner, canvas vẽ ô “!” trên Cá Sấu khi ở gần (< 12 m) và ô “!” + chữ “SẮP GIẬN” ở bàn có khách",
              "còn < 25 % kiên nhẫn. Chế độ tương phản cao đổi nền đen, chữ/viền vàng, tăng tương phản canvas (phím `H`)."]
    text = "\n".join(lines) + "\n"
    with open(os.path.join(a.proof, "report.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    sys.stdout.buffer.write(text.encode("utf-8"))
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
