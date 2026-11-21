"""QA: kiểm tất định & định dạng JSONL theo docs/contracts/events.md §5 (CON-02).

Hộp đen: chỉ chạy `headless_cmd` trong game.contract.json, nên dùng được với mọi ngôn ngữ.
Mỗi kịch bản chạy 2 lần cùng seed/đầu vào → so JSONL và file kho từng byte, rồi kiểm:
  - đúng 1 dòng `end` và là dòng cuối; snapshot đầu ở tick 0;
  - mảng thực thể (nodes, fish, stoves, tables, customers, stock v1.2) sắp theo id (F2 trước F10);
  - số thực có ≤ 3 chữ số thập phân, không có -0.0;
  - đổi seed vẫn chạy được (exit 0).

Chạy:   python3 tools/check_determinism.py [--seeds 1,7,42] [--ticks 600] [--proof docs/proof/phase-1]
Mã thoát: 0 = đạt hết, 1 = có lỗi.
"""

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTITY_KEYS = ("nodes", "fish", "stoves", "tables", "customers", "stock")  # hold giữ thứ tự vào giỏ (LIFO)
_TAIL = re.compile(r"^(.*?)(\d+)$")


def id_key(ident):
    m = _TAIL.match(ident)
    return (m.group(1), int(m.group(2)), ident) if m else (ident, -1, ident)


def headless_cmd():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        command = shlex.split(json.load(f)["headless_cmd"])
    if os.name == "nt" and command == ["python3", "-m", "chonoi.headless"]:
        command[0] = sys.executable
    return command


def v12():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f).get("contract_version") == "1.2"


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return path


def scenarios(tmp):
    """(tên, mode, đối số thêm, có ghi kho không). Đầu vào trộn di chuyển + nút để phủ nhiều nhánh luật."""
    gin = write_json(os.path.join(tmp, "g_in.json"), {"frames": [
        {"tick": 0, "move": [1, 1]}, {"tick": 40, "move": [1, 0], "catch": True}, {"tick": 41, "catch": False},
        {"tick": 90, "move": [0, -1], "interact": True}, {"tick": 91, "interact": False},
        {"tick": 200, "move": [-1, 0]}, {"tick": 400, "move": [0, 0], "interact": True}]})
    qin = write_json(os.path.join(tmp, "q_in.json"), {"frames": [
        {"tick": 0, "move": [1, 0]}, {"tick": 30, "interact": True}, {"tick": 31, "interact": False},
        {"tick": 60, "move": [0, 1]}, {"tick": 120, "move": [0, 0], "interact": True}]})
    kinds_inv = ["bong_sung", "bong_sung", "ca_loc", "ca_linh", "ca_linh", "ca_linh"]
    kinds_dock = ["ca_loc", "bong_sung", "bong_sung"]
    if v12():
        # Contract v1.2: kho cá thể; trộn độ tươi để phủ nhánh ươn/giữ lại/giá theo tươi.
        inv_obj = {"items": [{"id": f"I{i + 1}", "kind": k, "fresh": f}
                             for i, (k, f) in enumerate(zip(kinds_inv, (100, 30, 75.5, 30.25, 100, 60)))]}
        hold = [{"id": f"I{i + 1}", "kind": k, "fresh": 100} for i, k in enumerate(kinds_dock)]
    else:
        inv_obj = {"items": {"bong_sung": 2, "ca_loc": 1, "ca_linh": 3}}
        hold = kinds_dock
    inv = write_json(os.path.join(tmp, "inv_in.json"), inv_obj)
    dock = write_json(os.path.join(tmp, "dock_sc.json"), {"gather": {"hold": hold}})
    dock_in = write_json(os.path.join(tmp, "dock_in.json"), {"frames": [{"tick": 0, "interact": True}]})
    extra_cases = []
    if v12():
        extra_cases.append(("day_hold_handoff", "day", ["--scenario", dock, "--inputs", dock_in, "--snapshot-every", "600"], False))
    return extra_cases + [
        ("gather_idle", "gather", [], False),
        ("gather_inputs", "gather", ["--inputs", gin, "--snapshot-every", "10"], False),
        ("gather_dock_inventory", "gather", ["--scenario", dock, "--inputs", dock_in], True),
        ("quan_idle", "quan", [], False),
        ("quan_inventory_inputs", "quan", ["--inventory", inv, "--inputs", qin, "--snapshot-every", "10"], False),
    ]


def run(mode, seed, ticks, extra, out, inv_out=None):
    args = [*headless_cmd(), "--mode", mode, "--seed", str(seed), "--ticks", str(ticks), "--out", out, *extra]
    if inv_out:
        args += ["--inventory-out", inv_out]
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, p.stderr.strip()


def read_bytes(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()


def check_floats(v, where, errs):
    if isinstance(v, float):
        if v == 0 and str(v).startswith("-"):
            errs.append(f"{where}: có -0.0")
        if round(v, 3) != v:
            errs.append(f"{where}: {v} quá 3 chữ số thập phân")
    elif isinstance(v, dict):
        for k, x in v.items():
            check_floats(x, f"{where}.{k}", errs)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            check_floats(x, f"{where}[{i}]", errs)


def check_format(raw):
    errs = []
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if not rows:
        return ["JSONL rỗng"]
    # `day` (từ P2) phát day_start/day_plan/phase_start ở tick 0 trước snapshot đầu -> chỉ cho phép event tick 0 đứng trước.
    first = next((i for i, r in enumerate(rows) if r.get("type") == "snapshot"), None)
    if first is None or rows[first].get("tick") != 0 or any(
            r.get("type") != "event" or r.get("tick") != 0 for r in rows[:first]):
        errs.append("snapshot đầu không ở tick 0 (trước nó chỉ được có event tick 0)")
    ends = [i for i, r in enumerate(rows) if r.get("type") == "end"]
    if ends != [len(rows) - 1]:
        errs.append(f"dòng `end` phải có đúng 1 và ở cuối (thấy ở {ends})")
    last_tick = -1
    for i, r in enumerate(rows):
        t = r.get("tick")
        if isinstance(t, int):
            if t < last_tick:
                errs.append(f"dòng {i + 1}: tick giảm {last_tick} → {t}")
            last_tick = t
        check_floats(r, f"dòng {i + 1}", errs)
        if r.get("type") == "snapshot":
            for k in ENTITY_KEYS:
                arr = r.get(k)
                if isinstance(arr, list) and arr and all(isinstance(e, dict) and "id" in e for e in arr):
                    ids = [e["id"] for e in arr]
                    if ids != sorted(ids, key=id_key):
                        errs.append(f"dòng {i + 1} (tick {t}): `{k}` chưa sắp theo id: {ids}")
    return errs[:20]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", default="1,7,42")
    ap.add_argument("--ticks", type=int, default=600)
    ap.add_argument("--proof", help="thư mục lưu báo cáo + JSONL mẫu (vd docs/proof/phase-1)")
    a = ap.parse_args()
    seeds = [int(s) for s in a.seeds.split(",")]

    lines, failed = [], 0
    with tempfile.TemporaryDirectory() as tmp:
        for name, mode, extra, writes_inv in scenarios(tmp):
            ticks = {"gather_dock_inventory": 1, "day_hold_handoff": 22200}.get(name, a.ticks)
            for seed in seeds:
                outs, invs, problems = [], [], []
                for i in (1, 2):
                    out = os.path.join(tmp, f"{name}_s{seed}_{i}.jsonl")
                    inv = os.path.join(tmp, f"{name}_s{seed}_{i}.inv.json") if writes_inv else None
                    code, err = run(mode, seed, ticks, extra, out, inv)
                    if code != 0:
                        problems.append(f"lần {i} exit {code}: {err[-300:]}")
                    outs.append(read_bytes(out))
                    invs.append(read_bytes(inv) if inv else None)
                if not problems:
                    if outs[0] != outs[1]:
                        problems.append("JSONL 2 lần chạy KHÁC nhau")
                    if invs[0] != invs[1]:
                        problems.append("file kho 2 lần chạy KHÁC nhau")
                    if writes_inv and invs[0] is None:
                        problems.append("không ghi file kho dù cập bến")
                    problems += check_format(outs[0])
                digest = hashlib.sha256(outs[0] or b"").hexdigest()[:12]
                status = "ĐẠT" if not problems else "CHƯA ĐẠT"
                failed += bool(problems)
                lines.append(f"| {name} | {mode} | {seed} | {ticks} | `{digest}` | {status} | {'; '.join(problems)} |")
                if a.proof and seed == seeds[0] and outs[0]:
                    os.makedirs(a.proof, exist_ok=True)
                    with open(os.path.join(a.proof, f"{name}_seed{seed}.jsonl"), "wb") as f:
                        f.write(outs[0])

    header = ["# Kiểm tất định & định dạng JSONL (CON-02, events.md §5)", "",
              f"Lệnh: `python3 tools/check_determinism.py --seeds {a.seeds} --ticks {a.ticks}`", "",
              "| Kịch bản | Mode | Seed | Ticks | sha256 JSONL | Kết quả | Ghi chú |", "|---|---|---|---|---|---|---|"]
    report = "\n".join(header + lines + ["", f"**Tổng:** {len(lines) - failed}/{len(lines)} đạt."]) + "\n"
    sys.stdout.buffer.write(report.encode("utf-8"))
    if a.proof:
        os.makedirs(a.proof, exist_ok=True)
        with open(os.path.join(a.proof, "determinism.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(report)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
