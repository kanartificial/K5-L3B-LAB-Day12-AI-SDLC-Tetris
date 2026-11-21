"""QA Phase 2 — test hộp đen theo TICKET-02 / Test Contract v1.1 (viết trước, test-first).

Tự SKIP khi game.contract.json còn contract_version "1.0", để không làm đỏ main lúc các lát đang làm.
Khi Integrator nâng lên "1.1", toàn bộ test này bật lên và là tiêu chí nghiệm thu AC-P2-01…05
theo docs/plan/phase-2.md (xem docs/verification/phase-2.md). Số liệu chuẩn lấy nguyên văn từ TICKET-02 mục 1–2.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_contract_p2 -v   (Windows: "tests;.")
"""

import json
import math
import time
import unittest
from pathlib import Path

from helpers import ROOT, Workdir, counts, events, frames, ids_of, inst, kinds_of, read_jsonl, run_headless, snapshots, write_json


def contract():
    with open(f"{ROOT}/game.contract.json", encoding="utf-8") as f:
        return json.load(f)


# v1.2 vẫn giữ toàn bộ luật P2 còn hiệu lực -> regression chạy ở cả 1.1 và 1.2.
V11 = contract().get("contract_version") in ("1.1", "1.2")
need_v11 = unittest.skipUnless(V11, "chờ contract_version 1.1 (Phase 2)")


def tuning():
    return contract()["tuning"]


def section(name):
    """day_plan / shop: ticket không nói rõ nằm trong tuning hay ở gốc manifest → chấp nhận cả hai (xem clarify)."""
    c = contract()
    return c["tuning"].get(name, c.get(name))


MENU = {
    "ca_loc_nuong_trui": ({"ca_loc": 1}, 6, 60),
    "goi_bong_sung": ({"bong_sung": 2}, 4, 40),
    "lau_ca_linh_dien_dien": ({"ca_linh": 3, "bong_dien_dien": 1}, 10, 120),
    "canh_chua_ca_loc": ({"ca_loc": 1, "bong_dien_dien": 1}, 8, 90),
    "ca_keo_nuong": ({"ca_keo": 2}, 6, 70),
    "lau_mam": ({"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, 12, 200),
}
PLAN = {
    1: ({"ca_loc_nuong_trui": 3, "goi_bong_sung": 3}, {"ca_loc": 3, "bong_sung": 6}),
    2: ({"ca_loc_nuong_trui": 2, "lau_ca_linh_dien_dien": 2}, {"ca_loc": 2, "ca_linh": 6, "bong_dien_dien": 2}),
    3: ({"goi_bong_sung": 2, "canh_chua_ca_loc": 2, "ca_keo_nuong": 2},
        {"bong_sung": 4, "ca_loc": 2, "bong_dien_dien": 2, "ca_keo": 4}),
    4: ({"lau_mam": 1, "ca_loc_nuong_trui": 2, "goi_bong_sung": 1},
        {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1, "ca_loc": 2, "bong_sung": 2}),
    5: ({"lau_mam": 1, "lau_ca_linh_dien_dien": 1, "ca_loc_nuong_trui": 1},
        {"ca_linh": 5, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 2, "ca_loc": 1}),
}
DAY_MAX_TICKS = 22200
FISH_DEPTHS = {"ca_linh": (3, 12), "ca_loc": (8, 20), "ca_keo": (22, 28)}


def run_ok(test, *args):
    code, err = run_headless(*args)
    test.assertEqual(code, 0, err)


# ---------------------------------------------------------------- AC-P2-01 contract v1.1 & số liệu chuẩn
@need_v11
class StandardData(unittest.TestCase):
    def test_p2_01_gather_constants(self):
        g = tuning()["gather"]
        self.assertEqual((g["duration_s"], g["swim_speed"], g["ramp_max_ticks"], g["surface_depth"]), (180, 4.0, 6, 0.5))
        self.assertEqual((g["oxygen_max_s"], g["oxygen_refill_per_tick"], g["choke_interval_ticks"], g["hp_max"]), (30, 6, 60, 3))
        self.assertEqual((g["hold_capacity"], g["interact_radius"], g["regrow_s"], g["catch_radius"], g["catch_cooldown_s"]),
                         (12, 2.0, 20, 2.0, 0.5))
        self.assertEqual(g["fish_yield"], {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2})
        for key in ("fish_speed", "fish_turn_ticks", "fish_max", "fish_spawn_ticks", "fish_spawn_clearance", "fish_x",
                    "fish_depths", "fish_spawn_x", "fish_spawn_depths", "fish_weights"):
            self.assertIn(key, g)
        self.assertEqual((g["fish_speed"], g["fish_turn_ticks"], g["fish_max"], g["fish_spawn_ticks"]), (1.5, 120, 12, 360))
        self.assertEqual(g["fish_x"], [4, 96])
        self.assertEqual(sorted(g["fish_spawn_x"]), [15, 30, 45, 60, 75, 90])
        self.assertEqual(g["fish_initial"], 8)

    def test_p2_01_nodes_n1_n6(self):
        nodes = {n["id"]: (n["kind"], n["pos"]) for n in tuning()["gather"]["nodes"]}
        self.assertEqual(nodes, {"N1": ("bong_dien_dien", [12, 0]), "N2": ("bong_dien_dien", [28, 0]),
                                 "N3": ("bong_sung", [44, 0]), "N4": ("bong_sung", [60, 0]),
                                 "N5": ("keo_neo", [76, 0]), "N6": ("keo_neo", [90, 0])})

    def test_p2_01_menu_six_dishes_as_data(self):
        menu = tuning()["menu"]
        self.assertEqual(set(menu), set(MENU))
        for dish, (recipe, cook, price) in MENU.items():
            self.assertEqual((menu[dish]["recipe"], menu[dish]["cook_s"], menu[dish]["price"]), (recipe, cook, price), dish)

    def test_p2_01_quan_layout(self):
        q = tuning()["quan"]
        self.assertEqual({s["id"]: s["pos"] for s in q["stoves"]}, {"B1": [2, 8], "B2": [5, 8]})
        self.assertEqual({t["id"]: t["pos"] for t in q["tables"]}, {"T1": [9, 2], "T2": [13, 2], "T3": [9, 6], "T4": [13, 6]})
        self.assertEqual((q["first_customer_tick"], q["customer_interval_s"], q["patience_s"], q["eat_s"]), (120, 15, 60, 10))
        self.assertIsNone(q["burn_s"])

    def test_p2_01_monsters(self):
        m = tuning()["gather"]["monsters"]
        self.assertEqual((m["invuln_ticks"], m["loss_ratio"]), (90, 0.5))
        for key in ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "depths", "hit_radius",
                    "recoil_ticks", "recoil_dist"):
            self.assertIn(key, m["species"]["ca_sau"])
        sp = m["species"]["ca_sau"]
        self.assertEqual((sp["patrol_speed"], sp["chase_speed"], sp["detect_radius"], sp["exit_radius"], sp["hit_radius"],
                          sp["recoil_ticks"]), (1.0, 3.0, 10, 16, 1.5, 60))
        self.assertEqual(sp["depths"], [10, 30])
        spawns = {s["id"]: s for s in m["spawns"]}
        self.assertEqual(spawns["M1"]["pos"], [60, 24])
        self.assertEqual(spawns["M1"]["waypoints"], [[60, 24], [64, 24]])
        self.assertEqual(spawns["M2"]["waypoints"], [[85, 18], [89, 18]])
        self.assertEqual((spawns["M1"]["from_day"], spawns["M2"]["from_day"]), (1, 3))

    def test_p2_01_day_plan_matches_ticket_and_recipes(self):
        plan = section("day_plan")
        self.assertEqual(len(plan), 5)
        menu = tuning()["menu"]
        for entry in plan:
            dishes, ingredients = PLAN[entry["day"]]
            self.assertEqual(entry["dishes"], dishes, entry["day"])
            self.assertEqual(entry["ingredients"], ingredients, entry["day"])
            total = {}
            for dish, n in entry["dishes"].items():
                for kind, k in menu[dish]["recipe"].items():
                    total[kind] = total.get(kind, 0) + k * n
            self.assertEqual(entry["ingredients"], total, f"D{entry['day']}: ingredients phải = tổng công thức × suất")

    def test_p2_01_shop_upgrades(self):
        shop = section("shop")
        self.assertEqual(shop["max_ticks"], 600)
        self.assertEqual([(u["level"], u["price"], u["oxygen_max_s"]) for u in shop["upgrades"]["oxygen"]], [(1, 200, 45), (2, 400, 60)])
        self.assertEqual([(u["level"], u["price"], u["hp_max"]) for u in shop["upgrades"]["hp"]], [(1, 250, 4), (2, 500, 5)])


# ---------------------------------------------------------------- AC-P2-02 cá bơi / sinh
@need_v11
class FishP2(unittest.TestCase):
    def test_p2_02_initial_8_schools_distinct_spawn_points(self):
        with Workdir() as w:
            run_ok(self, "--mode", "gather", "--seed", "3", "--ticks", "0", "--out", w.path("g.jsonl"))
            s = snapshots(read_jsonl(w.path("g.jsonl")))[0]
            self.assertEqual(len(s["fish"]), 8)
            self.assertEqual(len({tuple(f["pos"]) for f in s["fish"]}), 8)
            self.assertEqual(len(s["nodes"]), 6)

    def test_p2_02_fish_stay_in_species_band_spawn_on_schedule_cap_12(self):
        with Workdir() as w:
            run_ok(self, "--mode", "gather", "--seed", "5", "--ticks", "4000", "--snapshot-every", "10",
                   "--out", w.path("g.jsonl"))
            rows = read_jsonl(w.path("g.jsonl"))
            for s in snapshots(rows):
                self.assertLessEqual(len(s["fish"]), 12)
                for f in s["fish"]:
                    lo, hi = FISH_DEPTHS[f["kind"]]
                    self.assertTrue(4 - 1e-6 <= f["pos"][0] <= 96 + 1e-6, (s["tick"], f))
                    self.assertTrue(lo - 1e-6 <= f["pos"][1] <= hi + 1e-6, (s["tick"], f))
            spawned = events(rows, "fish_spawned")
            self.assertTrue(spawned, "4000 tick phải có ít nhất 1 fish_spawned")
            for e in spawned:
                self.assertEqual(set(e["data"]), {"id", "kind", "pos"})

    def test_p2_02_seed_changes_fish(self):
        with Workdir() as w:
            for s in (1, 2):
                run_ok(self, "--mode", "gather", "--seed", str(s), "--ticks", "0", "--out", w.path(f"{s}.jsonl"))
            a, b = (snapshots(read_jsonl(w.path(f"{s}.jsonl")))[0]["fish"] for s in (1, 2))
            self.assertNotEqual(a, b, "đàn ban đầu/hướng phải phụ thuộc seed")

    def test_p2_02_random_fish_false_freezes_fixture(self):
        fish = [{"id": "F1", "kind": "ca_loc", "pos": [30, 10], "heading_deg": 0}]
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"random_fish": False, "fish": fish}})
            run_ok(self, "--mode", "gather", "--seed", "1", "--ticks", "800", "--scenario", sc, "--out", w.path("g.jsonl"))
            rows = read_jsonl(w.path("g.jsonl"))
            self.assertEqual([f["pos"] for f in snapshots(rows)[-1]["fish"]], [[30, 10]])
            self.assertFalse(events(rows, "fish_spawned"))


# ---------------------------------------------------------------- AC-P2-03 Cá Sấu, Máu, ngất
@need_v11
class MonsterP2(unittest.TestCase):
    def test_p2_03_day1_layout_only_m1(self):
        with Workdir() as w:
            run_ok(self, "--mode", "gather", "--seed", "1", "--ticks", "0", "--out", w.path("g.jsonl"))
            s = snapshots(read_jsonl(w.path("g.jsonl")))[0]
            self.assertEqual([m["id"] for m in s["monsters"]], ["M1"])
            self.assertIn("invuln_ticks", s["player"])

    def test_p2_03_hit_loses_hp_half_hold_lifo_then_invulnerable(self):
        hold = inst("ca_loc", "bong_sung", "bong_sung", "ca_linh")
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"random_fish": False, "hold": hold, "player": {"pos": [61, 24]}}})
            run_ok(self, "--mode", "gather", "--seed", "1", "--ticks", "80", "--scenario", sc, "--snapshot-every", "1",
                   "--out", w.path("g.jsonl"))
            rows = read_jsonl(w.path("g.jsonl"))
            hits = events(rows, "monster_hit")
            self.assertEqual(len(hits), 1, "bất tử 90 tick: chỉ 1 hit trong 80 tick")
            d = hits[0]["data"]
            self.assertEqual(d["monster_id"], "M1")
            self.assertEqual(d["hp"], 2)
            self.assertEqual(kinds_of(d["lost"]), ["ca_linh", "bong_sung"], "floor(4/2)=2, LIFO")
            self.assertEqual(ids_of(d["lost"]), ["I4", "I3"], "v1.2: lost là cá thể theo thứ tự bỏ LIFO")
            after = {r["tick"]: r for r in snapshots(rows)}[hits[0]["tick"]]
            self.assertGreater(after["player"]["invuln_ticks"], 0)

    def test_p2_03_monster_faint_empties_hold(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"random_fish": False, "hold": inst("ca_loc", "ca_loc"),
                                                           "player": {"pos": [61, 24], "hp": 1}}})
            run_ok(self, "--mode", "gather", "--seed", "1", "--ticks", "10", "--scenario", sc, "--out", w.path("g.jsonl"))
            rows = read_jsonl(w.path("g.jsonl"))
            faint = events(rows, "faint")
            self.assertEqual(len(faint), 1)
            self.assertEqual(faint[0]["data"]["cause"], "monster")
            self.assertEqual(faint[0]["data"]["hp"], 0)
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "fainted")
            self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], {"items": []})


# ---------------------------------------------------------------- AC-P2-04 quán 2 bếp / 4 bàn / 6 món
@need_v11
class QuanP2(unittest.TestCase):
    def test_p2_04_tick0_layout(self):
        with Workdir() as w:
            run_ok(self, "--mode", "quan", "--seed", "1", "--ticks", "0", "--out", w.path("q.jsonl"))
            s = snapshots(read_jsonl(w.path("q.jsonl")))[0]
            self.assertEqual([x["id"] for x in s["stoves"]], ["B1", "B2"])
            self.assertEqual([x["id"] for x in s["tables"]], ["T1", "T2", "T3", "T4"])

    def test_p2_04_customers_every_900_ticks_fill_lowest_table(self):
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": inst(*["ca_loc"] * 9)})
            run_ok(self, "--mode", "quan", "--seed", "1", "--ticks", "3000", "--inventory", inv, "--out", w.path("q.jsonl"))
            arr = events(read_jsonl(w.path("q.jsonl")), "customer_arrived")
            self.assertEqual([e["data"]["table_id"] for e in arr], ["T1", "T2", "T3", "T4"])
            ticks = [e["tick"] for e in arr]
            self.assertEqual([b - a for a, b in zip(ticks, ticks[1:])], [900, 900, 900])

    def test_p2_04_standalone_quan_uses_new_dishes(self):
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": inst("ca_keo", "ca_keo")})
            run_ok(self, "--mode", "quan", "--seed", "1", "--ticks", "200", "--inventory", inv, "--out", w.path("q.jsonl"))
            arr = events(read_jsonl(w.path("q.jsonl")), "customer_arrived")
            self.assertEqual([e["data"]["dish_id"] for e in arr], ["ca_keo_nuong"])

    def test_p2_04_new_kinds_accepted_in_inventory(self):
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": inst("ca_keo", "keo_neo")})
            run_ok(self, "--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv, "--out", w.path("q.jsonl"))

    def test_p2_04_invalid_orders_rejected_before_output(self):
        customer = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "state": "waiting", "order_status": "reserved", "order_tick": 0}
        for invalid in (
            customer,
            dict(customer, order_status="assigned"),
            dict(customer, state="eating", order_status="served", eat_ticks_left=1),
        ):
            with self.subTest(customer=invalid), Workdir() as w:
                scenario = write_json(w.path("q.json"), {"quan": {"customers": [invalid]}})
                out = Path(w.path("q.jsonl"))
                code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                         "--scenario", scenario, "--out", str(out))
                self.assertEqual(code, 2, err)
                self.assertFalse(out.exists())

    def test_p2_04_day_orders_checked_against_plan_and_handed_off_stock(self):
        customer = {"id": "C1", "table_id": "T1", "state": "waiting",
                    "order_status": "reserved", "order_tick": 0}
        cases = (
            ("ca_loc_nuong_trui", [], 2),
            ("ca_keo_nuong", inst("ca_keo", "ca_keo"), 2),
            ("ca_loc_nuong_trui", inst("ca_loc"), 0),
        )
        for dish_id, hold, expected in cases:
            with self.subTest(dish=dish_id, hold=kinds_of(hold)), Workdir() as w:
                scenario = {"gather": {"hold": hold, "random_fish": False},
                            "quan": {"customers": [dict(customer, dish_id=dish_id)]}}
                out = Path(w.path("d.jsonl"))
                out.write_text("previous output", encoding="utf-8")
                code, err, rows = day_run(w, out.name, 1, scenario=scenario,
                                          inputs=frames({"tick": 0, "interact": True}))
                self.assertEqual(code, expected, err)
                if expected == 2:
                    self.assertEqual(out.read_text(encoding="utf-8"), "previous output")
                else:
                    snap = snapshots(rows)[-1]
                    self.assertEqual(snap["phase"], "quan")
                    self.assertEqual(counts(snap["stock"]), {"ca_loc": 1})
                    # v1.2: Ngày 1 giữ nguyên id mẫu gather.hold; reserved là mảng id
                    self.assertEqual(ids_of(snap["stock"]), ["I1"])
                    self.assertEqual(snap["customers"][0]["reserved"], ["I1"])


# ---------------------------------------------------------------- AC-P2-01 CLI & scenario mode day (khung v1.1)
@need_v11
class DayCli(unittest.TestCase):
    def test_p2_01_cli_days_flag_domain(self):
        with Workdir() as w:
            out = w.path("o.jsonl")
            for days in ("0", "6", "-1"):
                self.assertEqual(run_headless("--mode", "day", "--days", days, "--seed", "1", "--ticks", "0", "--out", out)[0], 2, days)
            self.assertEqual(run_headless("--mode", "gather", "--days", "1", "--seed", "1", "--ticks", "0", "--out", out)[0], 2)
            inv = write_json(w.path("inv.json"), {"items": []})
            self.assertEqual(run_headless("--mode", "day", "--seed", "1", "--ticks", "0", "--inventory", inv, "--out", out)[0], 2)

    def test_p2_01_cli_day_scenario_rejections(self):
        with Workdir() as w:
            for sc in ({"quan": {"stock": inst("ca_loc")}}, {"quan": {"reputation": 4.0}},
                       {"day": {"money": 300, "earned": 200}}, {"day": {"money": -1, "earned": 0}}):
                p = write_json(w.path("sc.json"), sc)
                self.assertEqual(run_headless("--mode", "day", "--seed", "1", "--ticks", "0", "--scenario", p,
                                              "--out", w.path("o.jsonl"))[0], 2, sc)

    def test_p2_01_cli_ticket_example_scenario_accepted(self):
        with Workdir() as w:
            p = write_json(w.path("sc.json"), {"day": {"money": 200, "earned": 200},
                                               "gather": {"hold": inst("ca_loc", "bong_sung", "bong_sung"), "random_fish": False}})
            run_ok(self, "--mode", "day", "--seed", "1", "--ticks", "0", "--scenario", p, "--out", w.path("o.jsonl"))


# ---------------------------------------------------------------- AC-P2-05 vòng ngày
def day_run(w, name, ticks, days=1, scenario=None, inputs=None, seed=1):
    args = ["--mode", "day", "--days", str(days), "--seed", str(seed), "--ticks", str(ticks), "--out", w.path(name)]
    if scenario is not None:
        args += ["--scenario", write_json(w.path(name + ".sc.json"), scenario)]
    if inputs is not None:
        args += ["--inputs", write_json(w.path(name + ".in.json"), inputs)]
    code, err = run_headless(*args)
    return code, err, (read_jsonl(w.path(name)) if code == 0 else [])


DOCK_NOW = {"day": {"money": 200, "earned": 200}, "gather": {"hold": [], "random_fish": False}}


@need_v11
class DayLoop(unittest.TestCase):
    def test_p2_05_day_day_start_sequence_and_d1_plan(self):
        with Workdir() as w:
            code, err, rows = day_run(w, "d.jsonl", 0)
            self.assertEqual(code, 0, err)
            ev = [r for r in rows if r["type"] == "event"]
            self.assertEqual([e["name"] for e in ev[:3]], ["day_start", "day_plan", "phase_start"])
            self.assertTrue(all(e.get("day") == 1 and e["tick"] == 0 for e in ev[:3]))
            self.assertEqual(ev[1]["data"], {"dishes": PLAN[1][0], "ingredients": PLAN[1][1]})
            self.assertEqual(ev[2]["phase"], "gather")
            s = snapshots(rows)[0]
            for key in ("day", "day_plan", "upgrades", "active_upgrades", "phase"):
                self.assertIn(key, s)

    def test_p2_05_day_one_day_completes_within_budget_and_20s(self):
        with Workdir() as w:
            t0 = time.monotonic()
            code, err, rows = day_run(w, "d.jsonl", DAY_MAX_TICKS)
            elapsed = time.monotonic() - t0
            self.assertEqual(code, 0, err)
            self.assertLessEqual(elapsed, 20, f"headless 1 Ngày phải ≤ 20 s (đo {elapsed:.1f} s)")
            end = rows[-1]
            self.assertEqual((end["reason"], end["days_completed"]), ("days_complete", 1))
            phases = [e["phase"] for e in events(rows, "phase_start")]
            self.assertEqual(phases, ["gather", "quan", "shop"])
            self.assertEqual(len(events(rows, "shop_end")), 1)

    def test_p2_05_day_five_days_publish_d1_to_d5(self):
        with Workdir() as w:
            code, err, rows = day_run(w, "d.jsonl", DAY_MAX_TICKS * 5, days=5)
            self.assertEqual(code, 0, err)
            plans = events(rows, "day_plan")
            self.assertEqual([e["day"] for e in plans], [1, 2, 3, 4, 5])
            for e in plans:
                self.assertEqual(e["data"], {"dishes": PLAN[e["day"]][0], "ingredients": PLAN[e["day"]][1]})
            self.assertEqual((rows[-1]["reason"], rows[-1]["days_completed"]), ("days_complete", 5))
            m_ids = {s["day"]: [m["id"] for m in s["monsters"]] for s in snapshots(rows) if s.get("phase") == "gather"}
            self.assertEqual(m_ids.get(1), ["M1"])
            self.assertEqual(m_ids.get(3), ["M1", "M2"])

    def test_p2_05_day_faint_still_opens_quan_with_empty_stock(self):
        sc = {"gather": {"random_fish": False, "hold": inst("ca_loc"), "player": {"pos": [61, 24], "hp": 1}}}
        with Workdir() as w:
            code, err, rows = day_run(w, "d.jsonl", 200, scenario=sc)
            self.assertEqual(code, 0, err)
            end = events(rows, "gather_end")[0]
            self.assertEqual(end["data"]["reason"], "fainted")
            q = [e for e in events(rows, "phase_start") if e["phase"] == "quan"]
            self.assertEqual(len(q), 1)
            self.assertEqual(q[0]["tick"], end["tick"], "phase_start(quan) cùng tick với gather_end")


# ---------------------------------------------------------------- AC-P2-05 Shop & nâng cấp
def shop_open_tick(test, w, scenario):
    """Chạy dò 1 lần để biết tick Shop mở (phase_start shop), rồi đặt lệnh buy ngay sau đó."""
    code, err, rows = day_run(w, "probe.jsonl", DAY_MAX_TICKS, scenario=scenario,
                              inputs=frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False}))
    test.assertEqual(code, 0, err)
    return [e for e in events(rows, "phase_start") if e["phase"] == "shop"][0]["tick"]


@need_v11
class ShopP2(unittest.TestCase):
    def test_p2_05_shop_buy_oxygen_then_fail_funds_and_unknown(self):
        with Workdir() as w:
            t = shop_open_tick(self, w, DOCK_NOW)
            inp = frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                         {"tick": t + 1, "buy": "oxygen"}, {"tick": t + 2, "buy": "oxygen"}, {"tick": t + 3, "buy": "hp"},
                         {"tick": t + 4, "buy": "xyz"}, {"tick": t + 5, "shop_done": True})
            code, err, rows = day_run(w, "d.jsonl", DAY_MAX_TICKS, scenario=DOCK_NOW, inputs=inp)
            self.assertEqual(code, 0, err)
            bought = events(rows, "bought")
            self.assertEqual(len(bought), 1)
            self.assertEqual(bought[0]["data"], {"upgrade": "oxygen", "level": 1, "price": 200, "money": 0})
            fails = [(e["data"]["action"], e["data"]["reason"]) for e in events(rows, "buy_failed")]
            self.assertEqual([r for _, r in fails], ["funds", "funds", "unknown"])
            self.assertEqual(events(rows, "shop_end")[0]["data"]["reason"], "done")
            end = rows[-1]
            self.assertEqual(end["reason"], "days_complete")
            self.assertEqual(end["earned"], 200, "mua nâng cấp trừ money, giữ earned")

    def test_p2_05_shop_shop_auto_closes_after_600_ticks(self):
        with Workdir() as w:
            t = shop_open_tick(self, w, DOCK_NOW)
            code, err, rows = day_run(w, "d.jsonl", DAY_MAX_TICKS, scenario=DOCK_NOW,
                                      inputs=frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False}))
            self.assertEqual(code, 0, err)
            se = events(rows, "shop_end")[0]
            self.assertEqual(se["data"]["reason"], "time")
            self.assertTrue(abs(se["tick"] - t - 600) <= 1, (t, se["tick"]))

    def test_p2_05_shop_upgrade_applies_from_next_day(self):
        with Workdir() as w:
            t = shop_open_tick(self, w, DOCK_NOW)
            inp = frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                         {"tick": t + 1, "buy": "oxygen"}, {"tick": t + 2, "shop_done": True})
            code, err, rows = day_run(w, "d.jsonl", t + 10, days=2, scenario=DOCK_NOW, inputs=inp)
            self.assertEqual(code, 0, err)
            snaps = snapshots(rows)
            shop = [s for s in snaps if s.get("phase") == "shop"]
            self.assertTrue(shop and shop[-1]["upgrades"].get("oxygen") == 1, "cấp vừa mua hiển thị ngay")
            self.assertNotEqual(shop[-1]["active_upgrades"].get("oxygen"), 1, "chưa áp dụng trong Ngày hiện tại")
            d2 = [s for s in snaps if s.get("day") == 2 and s.get("phase") == "gather"]
            self.assertTrue(d2, "phải có snapshot gather Ngày 2")
            self.assertEqual(d2[0]["active_upgrades"].get("oxygen"), 1)
            self.assertEqual(d2[0]["player"]["oxygen_max_ticks"], 2700)


# ---------------------------------------------------------------- AC-P2-05 pause
@need_v11
class PauseP2(unittest.TestCase):
    def test_p2_05_pause_pause_freezes_gameplay(self):
        with Workdir() as w:
            base = write_json(w.path("a.json"), frames({"tick": 0, "move": [1, 1]}))
            paused = write_json(w.path("b.json"), frames({"tick": 0, "move": [1, 1]}, {"tick": 30, "pause": True},
                                                          {"tick": 31, "pause": False}, {"tick": 40, "pause": True},
                                                          {"tick": 41, "pause": False}))
            run_ok(self, "--mode", "gather", "--seed", "1", "--ticks", "100", "--inputs", base, "--out", w.path("a.jsonl"))
            run_ok(self, "--mode", "gather", "--seed", "1", "--ticks", "110", "--inputs", paused, "--out", w.path("b.jsonl"))
            a, b = read_jsonl(w.path("a.jsonl")), read_jsonl(w.path("b.jsonl"))
            self.assertEqual(len(events(b, "paused")), 1)
            self.assertEqual(len(events(b, "resumed")), 1)
            pa, pb = snapshots(a)[-1]["player"], snapshots(b)[-1]["player"]
            self.assertTrue(math.dist(pa["pos"], pb["pos"]) < 1e-6, "pause 10 bước không được chạy gameplay")
            self.assertEqual(pa["oxygen_ticks"], pb["oxygen_ticks"])

    def test_p2_05_pause_paused_snapshot_state(self):
        with Workdir() as w:
            inp = write_json(w.path("b.json"), frames({"tick": 5, "pause": True}))
            run_ok(self, "--mode", "quan", "--seed", "1", "--ticks", "20", "--inputs", inp, "--out", w.path("q.jsonl"))
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[-1]["state"], "paused")


if __name__ == "__main__":
    unittest.main()
