"""Test hộp đen cho vòng đời đơn hàng Quán Phase 1."""

import json
import unittest
from fractions import Fraction
from math import floor
from pathlib import Path

from helpers import ROOT, Workdir, counts, events, frames, ids_of, inst, read_jsonl, run_headless, snapshots, write_json


TUNING = json.loads((Path(ROOT) / "game.contract.json").read_text(encoding="utf-8"))["tuning"]
QUAN = TUNING["quan"]
DISH_ID = "ca_loc_nuong_trui"
DISH = TUNING["menu"][DISH_ID]
TICK_HZ = TUNING["tick_hz"]


class QuanPhaseOne(unittest.TestCase):
    def simulate(self, ticks, scenario, *input_frames):
        with Workdir() as work:
            out = work.path("out.jsonl")
            fixture = write_json(work.path("scenario.json"), {"quan": scenario})
            inputs = write_json(work.path("inputs.json"), frames(*input_frames))
            code, stderr = run_headless(
                "--mode", "quan", "--seed", "1", "--ticks", str(ticks),
                "--scenario", fixture, "--inputs", inputs, "--snapshot-every", "1", "--out", out,
            )
            self.assertEqual(code, 0, stderr)
            rows = read_jsonl(out)
            return events(rows), {row["tick"]: row for row in snapshots(rows)}, rows[-1]

    def waiting_order(self, patience=1):
        return {
            "id": "C1", "table_id": "T1", "dish_id": DISH_ID, "order_tick": 0,
            "state": "waiting", "order_status": "assigned", "patience_ticks_left": patience,
        }

    def test_arrival_reserves_recipe_without_consuming_stock(self):
        first = QUAN["first_customer_tick"]
        stock = inst("ca_loc")  # v1.2: kho cá thể
        log, state, _ = self.simulate(first + 1, {"stock": stock})
        self.assertEqual(state[first - 1]["customers"], [])
        self.assertEqual([(e["tick"], e["name"], e["data"]) for e in log], [
            (first, "customer_arrived", {"order_id": "C1", "table_id": "T1", "dish_id": DISH_ID}),
        ])
        customer, = state[first]["customers"]
        self.assertEqual(customer["order_tick"], first)
        self.assertEqual(customer["order_status"], "reserved")
        # v1.2: giữ theo id, kho vẫn còn nguyên cá thể (chỉ hao tươi)
        self.assertEqual(customer["reserved"], ["I1"])
        self.assertEqual(ids_of(state[first]["stock"]), ["I1"])
        patience = round(QUAN["patience_s"] * TICK_HZ)
        self.assertEqual(customer["patience_ticks_left"], patience)
        self.assertEqual(state[first + 1]["customers"][0]["patience_ticks_left"], patience - 1)

    def test_empty_stock_emits_no_dish_on_schedule(self):
        first = QUAN["first_customer_tick"]
        second = first + round(QUAN["customer_interval_s"] * TICK_HZ)
        log, state, _ = self.simulate(second, {})
        self.assertEqual([(e["tick"], e["name"], e["data"]) for e in log], [
            (first, "no_dish", {}), (second, "no_dish", {}),
        ])
        self.assertEqual(state[second]["customers"], [])

    def test_cook_pick_serve_and_pay(self):
        first = QUAN["first_customer_tick"]
        cooked = first + 1 + round(DISH["cook_s"] * TICK_HZ)
        # Đặt bàn gần bếp để đường đi chỉ cần một đoạn thẳng ngắn.
        travel = round(TICK_HZ / QUAN["walk_speed"])
        serve = cooked + travel + QUAN["ramp_max_ticks"] + 1
        paid = serve + round(QUAN["eat_s"] * TICK_HZ)
        log, state, end = self.simulate(
            paid, {"stock": inst("ca_loc"), "player": {"pos": [2, 8]},
                   "tables": [{"id": "T1", "pos": [3, 8]}]},
            {"tick": first, "interact": True}, {"tick": first + 1, "interact": False},
            {"tick": cooked - 1, "interact": True},
            {"tick": cooked, "interact": False, "move": [1, 0]},
            {"tick": cooked + travel, "move": [0, 0]},
            {"tick": serve - 1, "interact": True},
        )
        # v1.1 có 4 bàn (T1–T4) nên tick 1020 khi hết kho phát thêm no_dish tại bàn trống; lọc riêng vòng đời đơn C1
        order_log = [(e["tick"], e["name"]) for e in log if e["name"] != "no_dish"]
        self.assertEqual(order_log, [
            (first, "customer_arrived"), (first + 1, "cook_started"),
            (cooked, "dish_ready"), (cooked, "dish_picked"), (serve, "served"), (paid, "paid"),
        ])
        self.assertEqual([(it["id"], it["kind"]) for it in log[1]["data"]["items"]], [("I1", "ca_loc")])
        self.assertEqual(state[first + 1]["stock"], [])
        self.assertEqual(state[cooked]["hand"]["order_id"], "C1")
        self.assertEqual(state[serve]["customers"][0]["eat_ticks_left"], paid - serve)
        self.assertIsNone(state[serve]["hand"])
        self.assertIsNone(state[paid]["tables"][0]["customer_id"])
        # v1.2 thay giá niêm yết bằng giá theo tươi: hàng hao 0.25/s trong first+1 tick trước khi nấu
        fresh = 100 - Fraction(first + 1, 240)
        price = floor(DISH["price"] * fresh / 100)
        self.assertEqual(log[1]["data"]["base_price"], price)
        tip = floor(price * Fraction(str(QUAN["tip_rate"])))
        self.assertEqual(log[-1]["data"]["reason"], "finished_eating")
        self.assertEqual(log[-1]["data"]["tip"], tip)
        self.assertEqual(end["money"], price + tip)
        self.assertAlmostEqual(end["reputation"], QUAN["reputation_initial"] + QUAN["tip_reputation"])

    def test_ready_timer_starts_at_zero(self):
        log, state, _ = self.simulate(2, {
            "customers": [self.waiting_order(patience=10)],
            "stoves": [{"id": "B1", "state": "cooking", "dish": self.dish_payload(), "cook_ticks_left": 1}],
        })
        self.assertEqual([(e["tick"], e["name"]) for e in log], [(1, "dish_ready")])
        self.assertEqual(state[1]["stoves"][0]["ready_ticks"], 0)
        self.assertEqual(state[2]["stoves"][0]["ready_ticks"], 1)

    def test_serving_at_zero_patience_on_closing_tick(self):
        log, state, end = self.simulate(1, {
            "time_left_ticks": 1, "customers": [self.waiting_order()],
            "player": {"pos": QUAN["tables"][0]["pos"]}, "hand": self.dish_payload(),
        }, {"tick": 0, "interact": True})
        self.assertEqual([e["name"] for e in log], ["served", "paid", "quan_end"])
        self.assertEqual(log[0]["data"]["patience_ticks_left"], 0)
        self.assertEqual(log[1]["data"]["tip"], 0)
        self.assertEqual(log[1]["data"]["reason"], "closing")
        self.assertEqual(state[1]["customers"], [])
        self.assertEqual(end["money"], DISH["price"])

    def test_departure_clears_dish_and_only_patience_costs_reputation(self):
        for reason, time_left, delta in (
            ("patience", 2, QUAN["left_reputation_delta"]), ("closing", 1, 0),
        ):
            with self.subTest(reason=reason):
                log, state, _ = self.simulate(1, {
                    "time_left_ticks": time_left, "customers": [self.waiting_order()],
                    "stoves": [{"id": "B1", "state": "cooking", "dish": self.dish_payload(), "cook_ticks_left": 2}],
                })
                self.assertEqual(log[0]["name"], "customer_left")
                self.assertEqual(log[0]["data"]["reason"], reason)
                self.assertAlmostEqual(log[0]["data"]["reputation"], QUAN["reputation_initial"] + delta)
                self.assertEqual(state[1]["stock"], [])
                self.assertEqual(state[1]["stoves"][0]["state"], "idle")
                self.assertIsNone(state[1]["stoves"][0]["dish"])
                self.assertIsNone(state[1]["tables"][0]["customer_id"])

    @staticmethod
    def dish_payload():
        return {"order_id": "C1", "dish_id": DISH_ID, "base_price": DISH["price"]}


if __name__ == "__main__":
    unittest.main()
