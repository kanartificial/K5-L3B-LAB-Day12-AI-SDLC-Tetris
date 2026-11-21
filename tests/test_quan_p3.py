"""Kiểm lát Quán v1.2 qua runner với kho cá thể đã được nạp."""

import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.runner import run
from helpers import Workdir, events, read_jsonl, snapshots


class QuanFreshness(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.tuning["freshness"] = {
            "initial": 100, "quan_decay_per_s": 0.25, "spoiled_below": 30,
        }

    def simulate(self, stock, ticks, customers=(), frames=(), **scenario):
        with Workdir() as work:
            out = work.path("quan.jsonl")
            run("quan", self.tuning, dict(scenario, customers=list(customers)), 1,
                frames, ticks, out, 1, inventory=stock, contract_version="1.2")
            rows = read_jsonl(out)
            return events(rows), snapshots(rows)

    def test_spoil_at_first_tick_in_id_order_and_replace_before_cooking(self):
        stock = [
            {"id": "I10", "kind": "ca_loc", "fresh": 30},
            {"id": "I2", "kind": "ca_loc", "fresh": 30},
            {"id": "I4", "kind": "ca_loc", "fresh": 90},
            {"id": "I3", "kind": "ca_loc", "fresh": 90},
        ]
        customer = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "state": "waiting", "order_status": "reserved", "order_tick": 0,
                    "reserved": ["I2"]}
        log, state = self.simulate(stock, 2, [customer], [{"tick": 0, "interact": True}],
                                   player={"pos": self.tuning["quan"]["stoves"][0]["pos"]})
        self.assertEqual([(e["tick"], e["name"]) for e in log],
                         [(1, "spoiled"), (1, "spoiled"), (1, "cook_started")])
        self.assertEqual([e["data"]["item_id"] for e in log[:2]], ["I2", "I10"])
        self.assertEqual(log[2]["data"]["items"][0]["id"], "I3")
        self.assertEqual(log[2]["data"]["base_price"], 53)
        self.assertEqual([i["id"] for i in state[-1]["stock"]], ["I2", "I4", "I10"])

    def test_tick_zero_preserves_handoff_including_already_spoiled(self):
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 29.999}]
        log, state = self.simulate(stock, 1)
        self.assertEqual(log, [])
        self.assertEqual(state[0]["stock"], stock)
        self.assertLess(state[1]["stock"][0]["fresh"], 30)

    def test_exact_threshold_spoils_on_following_tick_once(self):
        log, state = self.simulate([{"id": "I1", "kind": "ca_loc", "fresh": 30.0125}], 5)
        self.assertEqual(state[3]["stock"][0]["fresh"], 30)
        self.assertEqual([(e["tick"], e["name"]) for e in log], [(4, "spoiled")])

    def test_price_uses_average_at_cook_and_boosts_neither_price_nor_tip_later(self):
        stock = [{"id": "I1", "kind": "bong_sung", "fresh": 90},
                 {"id": "I2", "kind": "bong_sung", "fresh": 60}]
        customer = {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                    "state": "waiting", "order_status": "reserved", "order_tick": 0}
        log, state = self.simulate(stock, 1, [customer], [{"tick": 0, "interact": True}],
                                   player={"pos": self.tuning["quan"]["stoves"][0]["pos"]})
        self.assertEqual(log[0]["data"]["base_price"], 29)  # 40 × (75 − 1/240) / 100
        self.assertEqual(state[1]["stoves"][0]["dish"]["base_price"], 29)
        self.assertEqual(state[1]["stock"], [])
        dish = state[1]["stoves"][0]["dish"]
        served, _ = self.simulate([], 1, [dict(customer, order_status="assigned")],
                                  [{"tick": 0, "interact": True}], hand=dish,
                                  player={"pos": self.tuning["quan"]["tables"][0]["pos"]})
        self.assertEqual(served[0]["data"]["base_price"], 29)
        self.assertEqual(served[0]["data"]["tip"], 5)

    def test_no_replacement_keeps_customer_waiting_until_patience_expires(self):
        customer = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "state": "waiting", "order_status": "reserved", "order_tick": 0,
                    "patience_ticks_left": 2}
        log, state = self.simulate([{"id": "I1", "kind": "ca_loc", "fresh": 30}], 2, [customer])
        self.assertEqual(state[1]["customers"][0]["order_status"], "unfulfillable")
        self.assertEqual(state[1]["customers"][0]["reserved"], [])
        self.assertEqual([(e["tick"], e["name"]) for e in log], [(1, "spoiled"), (2, "customer_left")])

    def test_implicit_reservations_pick_freshest_then_id_in_order_priority(self):
        stock = [{"id": f"I{i}", "kind": "ca_loc", "fresh": fresh}
                 for i, fresh in [(1, 70), (2, 90), (10, 90)]]
        order = {"dish_id": "ca_loc_nuong_trui", "state": "waiting",
                 "order_status": "reserved", "order_tick": 0}
        customers = [dict(order, id="C8", table_id="T2"), dict(order, id="C9", table_id="T1")]
        _, state = self.simulate(stock, 0, customers)
        self.assertEqual([c["reserved"] for c in state[0]["customers"]], [["I10"], ["I2"]])

    def test_reject_shared_reservation_and_spoiled_reservation(self):
        order = {"dish_id": "ca_loc_nuong_trui", "state": "waiting",
                 "order_status": "reserved", "order_tick": 0, "reserved": ["I1"]}
        c1 = dict(order, id="C1", table_id="T1")
        for fresh, orders in ((30, [c1, dict(order, id="C2", table_id="T2")]), (29, [c1])):
            with self.subTest(fresh=fresh), self.assertRaises(BadInput):
                self.simulate([{"id": "I1", "kind": "ca_loc", "fresh": fresh}], 0, orders)
