"""QA Phase 3 — test hộp đen tích hợp theo TICKET-03 / Test Contract v1.2 (chạy qua headless_cmd).

Bổ sung cho test lát (`test_gather_p3.py`, `test_quan_p3.py`): kiểm bàn giao kho cá thể giữa HAI tiến trình
(gather -> file -> quan) và trong `--mode day` (gather -> quan -> Shop -> Ngày kế), đúng các ví dụ của ticket.
Hai lỗi tích hợp lúc ghép (quán từ chối file kho v1.2 hợp lệ; Shop nhận id thay vì cá thể) được giữ ở đây làm hồi quy.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_contract_p3 -v   (Windows: "tests;.")
"""

import json
import math
import os
import unittest
from fractions import Fraction

from helpers import ROOT, Workdir, events, frames, ids_of, inst, read_jsonl, run_headless, snapshots, write_json

TOL = 0.01  # dung sai quan sát độ tươi theo ticket


def contract():
    with open(f"{ROOT}/game.contract.json", encoding="utf-8") as f:
        return json.load(f)


V12 = contract().get("contract_version") == "1.2"
need_v12 = unittest.skipUnless(V12, "chờ contract_version 1.2 (Phase 3)")
DOCK = frames({"tick": 0, "interact": True})


def run_ok(test, *args):
    code, err = run_headless(*args)
    test.assertEqual(code, 0, err)


@need_v12
class ContractV12(unittest.TestCase):
    def test_p3_01_manifest_version_and_freshness(self):
        c = contract()
        self.assertEqual(c["contract_version"], "1.2")
        self.assertEqual(c["tuning"]["freshness"],
                         {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30})

    def test_p3_01_counted_or_invalid_inventory_exit_2_for_quan_and_day_paths(self):
        bad_files = (
            {"items": {"ca_linh": 1}},  # kho đếm v1.1
            {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, {"id": "I1", "kind": "ca_loc", "fresh": 90}]},
            {"items": [{"id": "I1", "kind": "ca_hong", "fresh": 100}]},
            {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100.5}]},
            {"items": [{"id": "", "kind": "ca_linh", "fresh": 100}]},
            {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 50, "x": 1}]},
        )
        with Workdir() as w:
            for bad in bad_files:
                p = write_json(w.path("inv.json"), bad)
                out = w.path("q.jsonl")
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", p, "--out", out)
                self.assertEqual(code, 2, bad)
                self.assertFalse(os.path.exists(out), "mã 2 không được ghi output")

    def test_p3_01_empty_inventory_is_items_array(self):
        with Workdir() as w:
            p = write_json(w.path("inv.json"), {"items": []})
            run_ok(self, "--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", p, "--out", w.path("q.jsonl"))
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"], [])


@need_v12
class TicketExamples(unittest.TestCase):
    def test_p3_02_ticket_threshold_example_spoils_at_tick_1(self):
        """Ví dụ nguyên văn TICKET-03: hold fresh 30, một bước không input -> spoiled tick 1."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
                                                           "random_fish": False, "monsters": []}})
            run_ok(self, "--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", sc, "--out", w.path("g.jsonl"))
            spoiled = events(read_jsonl(w.path("g.jsonl")), "spoiled")
            self.assertEqual(spoiled, [{"type": "event", "tick": 1, "phase": "gather", "name": "spoiled",
                                        "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"}}])

    def test_p3_06_two_process_file_handoff_smoke(self):
        """Smoke bàn giao TICKET-03: fresh 100, cập bến frame 0 -> file -> quan --ticks 0 khớp id/kind/fresh."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}],
                                                           "random_fish": False, "monsters": []}})
            inp = write_json(w.path("in.json"), DOCK)
            inv = w.path("inv.json")
            run_ok(self, "--mode", "gather", "--seed", "1", "--ticks", "600", "--scenario", sc, "--inputs", inp,
                   "--inventory-out", inv, "--out", w.path("g.jsonl"))
            with open(inv, encoding="utf-8") as f:
                saved = json.load(f)
            # Hao đúng một bước ở giỏ: 100 - 0.5/60
            self.assertEqual(list(saved), ["items"])
            self.assertEqual(ids_of(saved["items"]), ["I1"])
            self.assertAlmostEqual(saved["items"][0]["fresh"], 100 - 0.5 / 60, delta=1e-9)
            end = events(read_jsonl(w.path("g.jsonl")), "gather_end")[0]
            self.assertEqual((end["tick"], end["data"]["reason"]), (1, "docked"))
            self.assertAlmostEqual(end["data"]["inventory"]["items"][0]["fresh"], saved["items"][0]["fresh"], delta=TOL)

            run_ok(self, "--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv, "--out", w.path("q.jsonl"))
            stock = snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"]
            self.assertEqual([(i["id"], i["kind"]) for i in stock], [("I1", "ca_linh")])
            self.assertAlmostEqual(stock[0]["fresh"], saved["items"][0]["fresh"], delta=TOL)

    def test_p3_06_file_roundtrip_keeps_threshold_branch(self):
        """Ghi file ở trạng thái sát ngưỡng rồi đọc lại: nhánh ươn ở quán phải đúng tick (không lệch do làm tròn)."""
        # Giỏ fresh 30.5: hao 2/240 mỗi tick -> sau 1 bước còn 30.5 - 1/120 (>= 30, chưa ươn).
        # Ở quán hao 1/240 mỗi tick: cần thêm (0.5 - 1/120) * 240 = 118 tick để chạm đúng 30, ươn ở tick 119.
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 30.5}],
                                                           "random_fish": False, "monsters": []}})
            inv = w.path("inv.json")
            run_ok(self, "--mode", "gather", "--seed", "1", "--ticks", "5", "--scenario", sc,
                   "--inputs", write_json(w.path("in.json"), DOCK), "--inventory-out", inv, "--out", w.path("g.jsonl"))
            self.assertEqual(events(read_jsonl(w.path("g.jsonl")), "spoiled"), [])
            q_sc = write_json(w.path("q.json"), {"quan": {"random_customers": False}})
            run_ok(self, "--mode", "quan", "--seed", "1", "--ticks", "200", "--inventory", inv, "--scenario", q_sc,
                   "--out", w.path("q.jsonl"))
            spoiled = events(read_jsonl(w.path("q.jsonl")), "spoiled")
            self.assertEqual([(e["tick"], e["data"]) for e in spoiled],
                             [(119, {"item_id": "I1", "kind": "ca_loc", "location": "stock"})])

    def test_p3_06_tick_limit_before_gather_end_keeps_destination(self):
        with Workdir() as w:
            inv = w.path("inv.json")
            with open(inv, "w", encoding="utf-8") as f:
                f.write("cũ")
            run_ok(self, "--mode", "gather", "--seed", "1", "--ticks", "3", "--inventory-out", inv, "--out", w.path("g.jsonl"))
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(f.read(), "cũ")
            self.assertEqual([n for n in os.listdir(os.path.dirname(inv)) if n not in ("inv.json", "g.jsonl")], [],
                             "không để lại file tạm")

    def test_p3_06_faint_writes_empty_item_array(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "hold": inst("ca_loc", "bong_sung"), "random_fish": False, "monsters": [],
                "player": {"pos": [20, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1}}})
            inv = w.path("inv.json")
            run_ok(self, "--mode", "gather", "--seed", "1", "--ticks", "5", "--scenario", sc,
                   "--inventory-out", inv, "--out", w.path("g.jsonl"))
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})
            faint = events(read_jsonl(w.path("g.jsonl")), "faint")[0]
            self.assertEqual(ids_of(faint["data"]["lost"]), ["I2", "I1"], "lost theo thứ tự bỏ LIFO")


@need_v12
class QuanFreshnessCli(unittest.TestCase):
    STOVE = None

    def quan(self, w, stock, customers, ticks, interact_at=None, **extra):
        t = contract()["tuning"]["quan"]
        sc = {"stock": stock, "customers": customers, "random_customers": False, **extra}
        if interact_at is not None:
            sc["player"] = {"pos": t["stoves"][0]["pos"]}
        args = ["--mode", "quan", "--seed", "1", "--ticks", str(ticks), "--snapshot-every", "1",
                "--scenario", write_json(w.path("q.json"), {"quan": sc}), "--out", w.path("q.jsonl")]
        if interact_at is not None:
            args += ["--inputs", write_json(w.path("qi.json"), frames({"tick": interact_at, "interact": True}))]
        run_ok(self, *args)
        rows = read_jsonl(w.path("q.jsonl"))
        return events(rows), {r["tick"]: r for r in snapshots(rows)}

    @staticmethod
    def order(**kw):
        base = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "waiting",
                "order_status": "reserved", "order_tick": 0}
        base.update(kw)
        return base

    def test_p3_03_price_locked_at_cook_from_average_freshness(self):
        """fresh 50 -> nấu ở tick 1 sau một lần hao: floor(60 × (50 − 1/240) / 100) = 29."""
        with Workdir() as w:
            log, _ = self.quan(w, [{"id": "I7", "kind": "ca_loc", "fresh": 50}], [self.order(reserved=["I7"])], 1, 0)
            cook = events_named(log, "cook_started")[0]
            self.assertEqual(cook["tick"], 1)
            self.assertEqual(cook["data"]["base_price"], math.floor(60 * (Fraction(50) - Fraction(1, 240)) / 100))
            self.assertEqual(cook["data"]["base_price"], 29)
            self.assertEqual([(i["id"], i["kind"]) for i in cook["data"]["items"]], [("I7", "ca_loc")])

    def test_p3_03_spoiled_reservation_is_replaced_once_with_freshest(self):
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 30}, {"id": "I2", "kind": "ca_loc", "fresh": 60},
                 {"id": "I3", "kind": "ca_loc", "fresh": 80}]
        with Workdir() as w:
            log, snap = self.quan(w, stock, [self.order(reserved=["I1"])], 1)
            self.assertEqual([(e["tick"], e["name"], e["data"]["item_id"]) for e in log],
                             [(1, "spoiled", "I1")])
            self.assertEqual(snap[1]["customers"][0]["reserved"], ["I3"], "giữ lại cá thể tươi nhất")
            self.assertEqual(snap[1]["customers"][0]["order_status"], "reserved")
            self.assertEqual(ids_of(snap[1]["stock"]), ["I1", "I2", "I3"], "hàng ươn vẫn chiếm chỗ trong kho")

    def test_p3_03_no_replacement_becomes_unfulfillable_and_waits(self):
        with Workdir() as w:
            log, snap = self.quan(w, [{"id": "I1", "kind": "ca_loc", "fresh": 30}],
                                  [self.order(reserved=["I1"], patience_ticks_left=3)], 3)
            self.assertEqual([(e["tick"], e["name"]) for e in log], [(1, "spoiled"), (3, "customer_left")])
            self.assertEqual(snap[1]["customers"][0]["order_status"], "unfulfillable")
            self.assertEqual(snap[1]["customers"][0]["reserved"], [])
            self.assertEqual(log[1]["data"]["reason"], "patience")


@need_v12
class DayHandoffV12(unittest.TestCase):
    def day(self, w, days, ticks, hold):
        sc = write_json(w.path("d.json"), {"gather": {"hold": hold, "random_fish": False}})
        run_ok(self, "--mode", "day", "--days", str(days), "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
               "--inputs", write_json(w.path("di.json"), DOCK), "--snapshot-every", "1", "--out", w.path("d.jsonl"))
        return read_jsonl(w.path("d.jsonl"))

    def test_p3_04_same_tick_handoff_no_extra_decay_then_quan_decay(self):
        with Workdir() as w:
            rows = self.day(w, 1, 3, inst("ca_loc", "bong_sung"))
            end = events(rows, "gather_end")[0]
            self.assertEqual(end["tick"], 1)
            snaps = {r["tick"]: r for r in snapshots(rows)}
            first_quan = snaps[1]
            self.assertEqual(first_quan["phase"], "quan")
            gather_fresh = {i["id"]: i["fresh"] for i in end["data"]["inventory"]["items"]}
            self.assertEqual(ids_of(first_quan["stock"]), ["I1", "I2"], "Ngày 1 giữ nguyên id mẫu")
            for it in first_quan["stock"]:
                self.assertAlmostEqual(it["fresh"], gather_fresh[it["id"]], delta=TOL, msg="không hao thêm lúc bàn giao")
            # Ca quán chạy từ bước sau với 0.25/s
            for it in snaps[3]["stock"]:
                self.assertAlmostEqual(it["fresh"], 100 - 2 / 240 - 2 / 240, delta=TOL)

    def test_p3_04_quan_to_shop_carries_item_instances_without_decay(self):
        """Hồi quy: Shop phải nhận mảng cá thể từ kho quán (trước đây nhận id chuỗi và crash)."""
        with Workdir() as w:
            rows = self.day(w, 1, 30000, inst("ca_linh"))
            shop = [s for s in snapshots(rows) if s["phase"] == "shop"]
            self.assertTrue(shop)
            self.assertEqual(ids_of(shop[0]["stock"]), ["I1"])
            self.assertEqual({it["fresh"] for s in shop for it in s["stock"]}, {shop[0]["stock"][0]["fresh"]},
                             "hàng thô ở Shop không hao tươi")
            # 1 bước giỏ (2/240) + 10800 bước quán (1/240)
            self.assertAlmostEqual(shop[0]["stock"][0]["fresh"], 100 - (2 + 10800) / 240, delta=TOL)
            self.assertEqual(rows[-1]["reason"], "days_complete")

    def test_p3_04_ids_keep_increasing_across_days(self):
        with Workdir() as w:
            rows = self.day(w, 2, 30000 * 2, inst("ca_linh", "ca_loc"))
            d2 = [s for s in snapshots(rows) if s.get("day") == 2 and s["phase"] == "gather"][0]
            self.assertEqual(ids_of(d2["hold"]), ["I3", "I4"], "Ngày kế cấp id mới theo thứ tự mảng")
            self.assertEqual([it["fresh"] for it in d2["hold"]], [100, 100])
            self.assertEqual(rows[-1]["days_completed"], 2)


def events_named(log, name):
    return [e for e in log if e["name"] == name]


if __name__ == "__main__":
    unittest.main()
