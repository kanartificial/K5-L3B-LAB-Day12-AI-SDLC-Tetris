"""Tiện ích test: chạy headless, đọc JSONL, dựng fixture, so sánh có dung sai."""

import json
import math
import os
import shlex
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return path


def frames(*fr):
    return {"frames": list(fr)}


def headless_cmd():
    """Lệnh headless khai trong game.contract.json — test chạy qua đây nên dùng được với MỌI ngôn ngữ."""
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        command = shlex.split(json.load(f)["headless_cmd"])
    # Windows có thể ánh xạ python3 vào Microsoft Store dù Python đã cài.
    if os.name == "nt" and command == ["python3", "-m", "chonoi.headless"]:
        command[0] = sys.executable
    return command


def run_headless(*args, cwd=ROOT):
    """Chạy `<headless_cmd> <args>`; trả (mã thoát, stderr)."""
    p = subprocess.run([*headless_cmd(), *args], cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stderr


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def snapshots(rows):
    return [r for r in rows if r["type"] == "snapshot"]


def events(rows, name=None):
    return [r for r in rows if r["type"] == "event" and (name is None or r["name"] == name)]


def close(a, b, tol=0.1):
    return abs(a - b) <= tol


def dist(p, q):
    return math.dist(p, q)


class Workdir:
    """Thư mục tạm tự dọn: with Workdir() as w: w.path('x.json')."""

    def __enter__(self):
        self._d = tempfile.TemporaryDirectory()
        return self

    def __exit__(self, *a):
        self._d.cleanup()

    def path(self, name):
        return os.path.join(self._d.name, name)


# ---------------------------------------------------------------- Contract v1.2: kho cá thể
def inst(*kinds, start=1, fresh=100):
    """Dựng hold/stock v1.2 từ danh sách kind: I<start>, I<start+1>… theo thứ tự (mặc định fresh 100)."""
    return [{"id": f"I{start + i}", "kind": k, "fresh": fresh} for i, k in enumerate(kinds)]


def kinds_of(items):
    """Mảng cá thể -> mảng kind (giữ thứ tự) để so luật P1/P2 vốn tính theo kind."""
    return [it["kind"] for it in items]


def counts(payload):
    """{"items":[cá thể]} hoặc mảng cá thể -> {kind: số lượng} sắp theo kind (dạng kho đếm cũ)."""
    items = payload["items"] if isinstance(payload, dict) else payload
    out = {}
    for it in items:
        out[it["kind"]] = out.get(it["kind"], 0) + 1
    return {k: out[k] for k in sorted(out)}


def ids_of(items):
    return [it["id"] for it in items]
