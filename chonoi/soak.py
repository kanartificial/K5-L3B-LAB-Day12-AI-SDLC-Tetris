"""Soak headless (Contract v1.3 · `soak_cmd`): chạy N Ngày liên tục trong MỘT tiến trình bằng bot tất định.

    python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Mỗi Ngày đi qua gather → quan → shop. Kế hoạch D1–D5 lặp ở Ngày 6–10. Tiền, tổng thu, uy tín, cấp nâng cấp,
số Ngày và id cá thể đi xuyên suốt nhờ dùng chung một `DaySession`. Không ghi JSONL, không ghi bảng xếp hạng.

soak.json: {"days", "days_completed", "crashes", "results": [{day, earned, reputation, score}], "duration_s"}.
`results[]` chụp lúc Shop đóng. `duration_s` là thời gian thực (bỏ qua khi so tất định).
Mã thoát: 0 khi days_completed = days và crashes = 0; 1 khi có crash / chưa đủ Ngày; 2 khi đối số sai.
"""

import argparse
import json
import math
import os
import sys
import tempfile
import time
import traceback

from .bot import SoakBot
from .contract import load_contract
from .errors import BadInput
from .runner import DaySession

# 1 Ngày ≤ 22.200 tick (gather 10.800 + quan 10.800 + shop 600). Dư gấp đôi để bắt kẹt vòng lặp.
MAX_TICKS_PER_DAY = 2 * 22200


def soak(seed: int, days: int, contract=None) -> dict:
    c = contract or load_contract()
    tuning = c["tuning"]
    mult = tuning["score"]["reputation_multiplier"]
    t0 = time.monotonic()
    results, crashes, error = [], 0, None
    sess = None
    try:
        sess = DaySession(tuning, None, seed, days=days, contract_version=c.get("contract_version", "1.3"))
        bot = SoakBot(tuning)
        limit = MAX_TICKS_PER_DAY * days
        while not sess.done and sess.tick < limit:
            rows = sess.step(bot.act(sess.snapshot()))
            for r in rows:
                if r.get("name") == "shop_end":
                    results.append({
                        "day": r["day"], "earned": sess.earned, "reputation": round(sess.reputation, 3),
                        "score": sess.earned + mult * math.floor(sess.reputation),
                    })
        if not sess.done:
            error = f"chưa xong sau {limit} tick (kẹt vòng lặp?)"
    except Exception:  # soak phải báo crash thay vì chết im lặng
        crashes += 1
        error = traceback.format_exc(limit=-3)
    out = {
        "days": days,
        "days_completed": sess.days_completed if sess is not None else 0,
        "crashes": crashes,
        "results": results,
        "duration_s": round(time.monotonic() - t0, 3),
    }
    if error:
        out["error"] = error
    return out


def _write_atomic(path, obj):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def _int(name, lo):
    def conv(v):
        try:
            n = int(v)
        except ValueError:
            raise argparse.ArgumentTypeError(f"--{name} phải là số nguyên")
        if n < lo:
            raise argparse.ArgumentTypeError(f"--{name} phải ≥ {lo}")
        return n
    return conv


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="chonoi.soak", description="Soak headless N Ngày bằng bot tất định.")
    ap.add_argument("--seed", type=_int("seed", -2**63), required=True)
    ap.add_argument("--days", type=_int("days", 1), required=True)
    ap.add_argument("--out", required=True)
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        res = soak(a.seed, a.days)
    except BadInput as e:
        print(f"đầu vào sai: {e}", file=sys.stderr)
        return 2
    _write_atomic(a.out, res)
    if res.get("error"):
        print(res["error"], file=sys.stderr)
    ok = res["days_completed"] == res["days"] and res["crashes"] == 0
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
