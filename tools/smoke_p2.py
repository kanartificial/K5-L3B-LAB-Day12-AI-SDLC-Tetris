"""QA Phase 2 — smoke tích hợp + smoke day + regression P1, lưu bằng chứng vào docs/proof/phase-2/.

  python3 tools/smoke_p2.py integration   # phút 20: gather --inventory-out → quan --inventory, đối chiếu stock tick 0
  python3 tools/smoke_p2.py day           # phút 35: day --days 1 và --days 5 (thời gian, reason, D1–D5)
  python3 tools/smoke_p2.py regression    # phút 35: chạy lại test P1 + P2
  python3 tools/smoke_p2.py all

Hộp đen: chỉ dùng headless_cmd trong game.contract.json. Mã thoát 0 = đạt hết, 1 = có mục chưa đạt.
"""

import json
import os
import shlex
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROOF = os.path.join(ROOT, "docs", "proof", "phase-2")
DAY_MAX_TICKS = 22200


def contract():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)


def headless(*args):
    base = shlex.split(contract()["headless_cmd"])
    cmd = [*base, *args]
    if os.name == "nt" and base == ["python3", "-m", "chonoi.headless"]:
        cmd[0] = sys.executable
    t0 = time.monotonic()
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    shown = " ".join([base[0], *(rel(c) if os.path.isabs(c) else c for c in cmd[1:])])
    return p.returncode, p.stderr.strip(), time.monotonic() - t0, shown


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def dump(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False)
    return path


def git_head():
    p = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True)
    return p.stdout.strip() + (" (+ thay đổi chưa commit)" if dirty.stdout.strip() else "")


def header(title):
    c = contract()
    return [f"# {title}", "", f"- Commit: `{git_head()}` · contract_version `{c.get('contract_version')}`",
            f"- Thời điểm: {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]


def integration():
    d = os.path.join(PROOF, "integration")
    os.makedirs(d, exist_ok=True)
    hold = ["ca_loc", "bong_sung", "bong_sung", "ca_linh", "ca_linh", "ca_linh", "bong_dien_dien"]
    sc = dump(os.path.join(d, "gather.scenario.json"), {"gather": {"hold": hold}})
    inp = dump(os.path.join(d, "gather.inputs.json"), {"frames": [{"tick": 0, "interact": True}]})
    inv = os.path.join(d, "inventory.json")
    g_out, q_out = os.path.join(d, "gather.jsonl"), os.path.join(d, "quan.jsonl")
    if os.path.exists(inv):
        os.remove(inv)
    checks, cmds = [], []
    code, err, _, cmd = headless("--mode", "gather", "--seed", "42", "--ticks", "60", "--scenario", sc, "--inputs", inp,
                                 "--inventory-out", inv, "--out", g_out)
    cmds.append(cmd)
    checks.append(("gather chạy exit 0", code == 0, err[-200:]))
    expected = {}
    for k in hold:
        expected[k] = expected.get(k, 0) + 1
    saved = json.load(open(inv, encoding="utf-8")) if os.path.exists(inv) else None
    checks.append(("file kho ghi đúng giỏ", saved == {"items": expected}, f"kho = {saved}"))
    if code == 0:
        end = [r for r in jsonl(g_out) if r.get("name") == "gather_end"]
        checks.append(("gather_end.reason = docked, inventory = file kho",
                       bool(end) and end[0]["data"]["reason"] == "docked" and end[0]["data"]["inventory"] == saved,
                       f"{end[0]['data'] if end else 'không có gather_end'}"))
    if saved is not None:
        code, err, _, cmd = headless("--mode", "quan", "--seed", "42", "--ticks", "300", "--inventory", inv, "--out", q_out)
        cmds.append(cmd)
        checks.append(("quan đọc kho exit 0", code == 0, err[-200:]))
        if code == 0:
            rows = jsonl(q_out)
            s0 = next(r for r in rows if r["type"] == "snapshot")
            checks.append(("snapshot quan tick 0: stock = kho bàn giao", s0["tick"] == 0 and s0.get("stock") == saved["items"],
                           f"stock = {s0.get('stock')}"))
            arr = [r for r in rows if r.get("name") == "customer_arrived"]
            checks.append(("có khách gọi món từ kho bàn giao (≤ 300 tick)", bool(arr), f"{[a['data'] for a in arr]}"))
    return report("integration.md", "Smoke tích hợp gather → kho → quan (phút 20)", checks, cmds)


def day():
    checks, cmds = [], []
    if contract().get("contract_version") not in ("1.1", "1.2", "1.3"):
        checks.append(("contract_version ≥ 1.1", False, "còn 1.0 — mode day chưa bật"))
        return report("day.md", "Smoke mode day", checks, cmds)
    for days in (1, 5):
        out = os.path.join(PROOF, f"day{days}.jsonl")
        code, err, sec, cmd = headless("--mode", "day", "--days", str(days), "--seed", "1",
                                       "--ticks", str(DAY_MAX_TICKS * days), "--out", out)
        cmds.append(cmd)
        checks.append((f"--days {days} exit 0", code == 0, err[-200:]))
        if code != 0:
            continue
        rows = jsonl(out)
        end = rows[-1]
        checks.append((f"--days {days}: end reason days_complete, days_completed = {days}",
                       end.get("reason") == "days_complete" and end.get("days_completed") == days,
                       f"end = {json.dumps(end, ensure_ascii=False)}"))
        if days == 1:
            checks.append(("1 Ngày ≤ 20 s", sec <= 20, f"{sec:.1f} s"))
            checks.append(("1 Ngày ≤ 22.200 tick", end.get("sim_tick", end.get("ticks", 0)) <= DAY_MAX_TICKS,
                           f"sim_tick = {end.get('sim_tick')}"))
        plans = [r for r in rows if r.get("name") == "day_plan"]
        checks.append((f"--days {days}: công bố day_plan Ngày 1..{days}", [p.get("day") for p in plans] == list(range(1, days + 1)),
                       "; ".join(f"D{p.get('day')}: {p['data']['dishes']}" for p in plans)))
        phases = [r["phase"] for r in rows if r.get("name") == "phase_start"]
        checks.append((f"--days {days}: pha gather → quan → shop lặp lại", phases == ["gather", "quan", "shop"] * days,
                       " → ".join(phases)))
    return report("day.md", "Smoke mode day (phút 35)", checks, cmds)


def regression():
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(["tests", "."]), PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, env=env,
                       capture_output=True, text=True, encoding="utf-8")
    log = os.path.join(PROOF, "regression.log")
    os.makedirs(PROOF, exist_ok=True)
    with open(log, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# commit {git_head()}\n$ PYTHONPATH=tests{os.pathsep}. python3 -m unittest discover -s tests -v\n")
        f.write(p.stderr)
    tail = [l for l in p.stderr.splitlines() if l.startswith(("Ran ", "OK", "FAILED"))]
    fails = [l for l in p.stderr.splitlines() if l.startswith(("FAIL:", "ERROR:"))]
    checks = [("toàn bộ test (P1 + P2) xanh", p.returncode == 0, " · ".join(tail) + (" · " + "; ".join(fails) if fails else ""))]
    return report("regression.md", "Regression P1 + test P2", checks, [f"log đầy đủ: {rel(log)}"])


def report(name, title, checks, cmds):
    os.makedirs(PROOF, exist_ok=True)
    lines = header(title) + ["| Kiểm | Kết quả | Chi tiết |", "|---|---|---|"]
    for what, ok, detail in checks:
        lines.append(f"| {what} | {'ĐẠT' if ok else 'CHƯA ĐẠT'} | {str(detail).replace('|', '/')} |")
    lines += ["", "Lệnh đã chạy:", ""] + [f"- `{c}`" for c in cmds]
    text = "\n".join(lines) + "\n"
    with open(os.path.join(PROOF, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    sys.stdout.buffer.write(text.encode("utf-8") + b"\n")
    return all(ok for _, ok, _ in checks)


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = {"integration": [integration], "day": [day], "regression": [regression],
             "all": [integration, day, regression]}[what]
    results = [s() for s in steps]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
