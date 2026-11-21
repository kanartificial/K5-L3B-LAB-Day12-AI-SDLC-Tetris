"""QA Phase 3 — smoke Contract v1.2 (độ tươi + kho cá thể), lưu bằng chứng vào docs/proof/phase-3/.

  python3 tools/smoke_p3.py threshold     # ví dụ TICKET-03: hold fresh 30, 1 bước -> spoiled tick 1
  python3 tools/smoke_p3.py integration   # smoke bàn giao file: fresh 100 cập bến frame 0 -> quan --ticks 0
  python3 tools/smoke_p3.py reject        # kho đếm / sai schema -> mã 2
  python3 tools/smoke_p3.py day           # day --days 1 có hàng (bàn giao cùng tick, Shop không hao) + --days 1|5 chuẩn
  python3 tools/smoke_p3.py regression    # chạy lại toàn bộ unittest (P1 + P2 + P3)
  python3 tools/smoke_p3.py all [--proof DIR]   # mặc định docs/proof/phase-3/

Hộp đen: chỉ dùng headless_cmd trong game.contract.json. Mã thoát 0 = đạt hết, 1 = có mục chưa đạt.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smoke_p2 as base  # noqa: E402  (dùng lại headless/report/regression của Phase 2)

ROOT = base.ROOT
base.PROOF = PROOF = os.path.join(ROOT, "docs", "proof", "phase-3")
TOL = 0.01


def _dir(name):
    d = os.path.join(PROOF, name)
    os.makedirs(d, exist_ok=True)
    return d


def threshold():
    d = _dir("threshold")
    sc = base.dump(os.path.join(d, "gather.scenario.json"),
                   {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}], "random_fish": False, "monsters": []}})
    out = os.path.join(d, "gather.jsonl")
    code, err, _, cmd = base.headless("--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", sc, "--out", out)
    checks = [("gather exit 0", code == 0, err[-200:])]
    if code == 0:
        want = {"type": "event", "tick": 1, "phase": "gather", "name": "spoiled",
                "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"}}
        got = [r for r in base.jsonl(out) if r.get("name") == "spoiled"]
        checks.append(("đúng 1 dòng spoiled khớp nguyên văn ticket", got == [want], json.dumps(got, ensure_ascii=False)))
    return base.report("threshold.md", "Smoke ngưỡng ươn 30 (ví dụ TICKET-03)", checks, [cmd])


def integration():
    d = _dir("integration")
    sc = base.dump(os.path.join(d, "gather.scenario.json"),
                   {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}], "random_fish": False, "monsters": []}})
    inp = base.dump(os.path.join(d, "gather.inputs.json"), {"frames": [{"tick": 0, "interact": True}]})
    inv = os.path.join(d, "inventory.json")
    g_out, q_out = os.path.join(d, "gather.jsonl"), os.path.join(d, "quan.jsonl")
    if os.path.exists(inv):
        os.remove(inv)
    checks, cmds = [], []
    code, err, _, cmd = base.headless("--mode", "gather", "--seed", "1", "--ticks", "600", "--scenario", sc, "--inputs", inp,
                                      "--inventory-out", inv, "--out", g_out)
    cmds.append(cmd)
    checks.append(("gather exit 0", code == 0, err[-200:]))
    saved = json.load(open(inv, encoding="utf-8")) if os.path.exists(inv) else None
    items = (saved or {}).get("items") or []
    expect = 100 - 0.5 / 60
    checks.append(("file kho đúng schema v1.2, I1 ca_linh hao đúng 1 bước giỏ",
                   isinstance(saved, dict) and list(saved) == ["items"] and len(items) == 1
                   and (items[0]["id"], items[0]["kind"]) == ("I1", "ca_linh") and abs(items[0]["fresh"] - expect) < 1e-9,
                   f"kho = {saved} · kỳ vọng fresh {expect!r}"))
    if code == 0:
        end = [r for r in base.jsonl(g_out) if r.get("name") == "gather_end"]
        ok = (bool(end) and end[0]["tick"] == 1 and end[0]["data"]["reason"] == "docked"
              and [(i["id"], i["kind"]) for i in end[0]["data"]["inventory"]["items"]] == [(i["id"], i["kind"]) for i in items]
              and all(abs(a["fresh"] - b["fresh"]) <= TOL for a, b in zip(end[0]["data"]["inventory"]["items"], items)))
        checks.append(("gather_end(docked) tick 1, inventory cùng schema với file", ok,
                       json.dumps(end[0]["data"] if end else None, ensure_ascii=False)))
    if saved is not None:
        code, err, _, cmd = base.headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv, "--out", q_out)
        cmds.append(cmd)
        checks.append(("quan --inventory --ticks 0 exit 0", code == 0, err[-200:]))
        if code == 0:
            s0 = next(r for r in base.jsonl(q_out) if r["type"] == "snapshot")
            stock = s0.get("stock") or []
            ok = ([(i["id"], i["kind"]) for i in stock] == [(i["id"], i["kind"]) for i in items]
                  and all(abs(a["fresh"] - b["fresh"]) <= TOL for a, b in zip(stock, items)))
            checks.append(("snapshot quán tick 0: id, kind, fresh khớp file (±0.01)", s0["tick"] == 0 and ok,
                           f"stock = {stock}"))
    return base.report("integration.md", "Smoke bàn giao kho cá thể gather → file → quan (v1.2)", checks, cmds)


def reject():
    d = _dir("reject")
    checks, cmds = [], []
    cases = (
        ("kho đếm v1.1", {"items": {"ca_linh": 1}}),
        ("id trùng", {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, {"id": "I1", "kind": "ca_loc", "fresh": 90}]}),
        ("kind lạ", {"items": [{"id": "I1", "kind": "ca_hong", "fresh": 100}]}),
        ("fresh ngoài miền", {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 101}]}),
        ("id rỗng", {"items": [{"id": "", "kind": "ca_linh", "fresh": 100}]}),
    )
    for i, (what, obj) in enumerate(cases):
        p = base.dump(os.path.join(d, f"bad{i}.json"), obj)
        out = os.path.join(d, f"bad{i}.jsonl")
        if os.path.exists(out):
            os.remove(out)
        code, err, _, cmd = base.headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", p, "--out", out)
        cmds.append(cmd)
        checks.append((f"{what} → mã 2, không ghi output", code == 2 and not os.path.exists(out), err[-160:]))
    return base.report("reject.md", "Smoke từ chối kho sai schema (v1.2)", checks, cmds)


def day():
    d = _dir("day")
    sc = base.dump(os.path.join(d, "day.scenario.json"),
                   {"gather": {"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100},
                                        {"id": "I2", "kind": "bong_sung", "fresh": 100}], "random_fish": False}})
    inp = base.dump(os.path.join(d, "day.inputs.json"), {"frames": [{"tick": 0, "interact": True}]})
    out = os.path.join(d, "day_hold.jsonl")
    code, err, sec, cmd = base.headless("--mode", "day", "--days", "2", "--seed", "1", "--ticks", str(base.DAY_MAX_TICKS * 2),
                                        "--scenario", sc, "--inputs", inp, "--snapshot-every", "1", "--out", out)
    checks = [("day --days 2 có hàng exit 0", code == 0, err[-200:])]
    if code == 0:
        rows = base.jsonl(out)
        snaps = [r for r in rows if r["type"] == "snapshot"]
        end = [r for r in rows if r.get("name") == "gather_end"][0]
        q0 = next(s for s in snaps if s["phase"] == "quan")
        g_items = end["data"]["inventory"]["items"]
        ok = (q0["tick"] == end["tick"] and [i["id"] for i in q0["stock"]] == [i["id"] for i in g_items]
              and all(abs(a["fresh"] - b["fresh"]) <= TOL for a, b in zip(q0["stock"], g_items)))
        checks.append(("bàn giao cùng tick, không hao thêm (gather_end.inventory = stock quán đầu)", ok,
                       f"tick {end['tick']} · {g_items} → {q0['stock']}"))
        shop = [s for s in snaps if s["phase"] == "shop" and s.get("day") == 1]
        fresh_set = {json.dumps(s["stock"]) for s in shop}
        checks.append(("Shop nhận mảng cá thể và không hao tươi", bool(shop) and len(fresh_set) == 1 and shop[0]["stock"],
                       f"{len(shop)} snapshot shop · stock = {shop[0]['stock'] if shop else None}"))
        d2 = next((s for s in snaps if s.get("day") == 2 and s["phase"] == "gather"), None)
        checks.append(("Ngày 2 cấp id mới tăng tiếp (I3, I4) với fresh 100",
                       d2 is not None and [(i["id"], i["fresh"]) for i in d2["hold"]] == [("I3", 100), ("I4", 100)],
                       f"hold D2 = {d2['hold'] if d2 else None}"))
        spoiled = [r for r in rows if r.get("name") == "spoiled"]
        checks.append(("có event spoiled ở kho/giỏ khi hàng ươn", bool(spoiled),
                       "; ".join(f"t{r['tick']} {r['data']['item_id']}@{r['data']['location']}" for r in spoiled[:6])))
        checks.append(("end: days_complete, 2 Ngày", rows[-1].get("reason") == "days_complete"
                       and rows[-1].get("days_completed") == 2, json.dumps(rows[-1], ensure_ascii=False)[:200]))
    r1 = base.report("day_hold.md", "Smoke day v1.2 có hàng: gather → quan → Shop → Ngày 2", checks, [cmd])
    r2 = base.day()  # --days 1 / --days 5 chuẩn (thời gian, D1–D5) -> docs/proof/phase-3/day.md
    return r1 and r2


def main():
    global PROOF
    args = sys.argv[1:]
    if "--proof" in args:  # ghi bằng chứng vào thư mục khác (vd docs/proof/phase-4/smoke)
        i = args.index("--proof")
        base.PROOF = PROOF = os.path.abspath(args[i + 1])
        del args[i:i + 2]
    what = args[0] if args else "all"
    steps = {"threshold": [threshold], "integration": [integration], "reject": [reject], "day": [day],
             "regression": [base.regression],
             "all": [threshold, integration, reject, day, base.regression]}[what]
    results = [s() for s in steps]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
