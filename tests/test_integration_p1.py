"""Test tích hợp 2 tiến trình Phase 1 (`gather` -> file kho -> `quan`), kiểu hộp đen."""

import json
import math
import unittest
from fractions import Fraction

from helpers import Workdir, events, inst, frames, read_jsonl, run_headless, snapshots, write_json


def load_tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


class TwoProcessIntegrationP1(unittest.TestCase):
    def test_gather_catch_and_harvest_flows_into_quan_service_and_payment(self):
        """Hái nút + bắt cá ở buổi sáng -> ghi kho -> mở quán phục vụ khách -> trả tiền + boa + uy tín."""
        tuning = load_tuning()
        q = tuning["quan"]
        dish = tuning["menu"]["ca_loc_nuong_trui"]

        with Workdir() as w:
            # 1) Buổi sáng: bắt cá lóc ở bước cuối ca (time_left_ticks=1) -> chốt kho
            g_sc = write_json(w.path("g_sc.json"), {
                "gather": {
                    "player": {"pos": [30, 10]},
                    "hold": [],
                    "nodes": [],
                    "fish": [{"id": "F1", "kind": "ca_loc", "pos": [31, 10]}],
                    "random_fish": False,
                    "time_left_ticks": 1,
                }
            })
            g_in = write_json(w.path("g_in.json"), frames({"tick": 0, "catch": True}))
            inv = w.path("catch.json")
            code, err = run_headless(
                "--mode", "gather", "--seed", "42", "--ticks", "1",
                "--scenario", g_sc, "--inputs", g_in,
                "--inventory-out", inv, "--out", w.path("gather.jsonl"),
            )
            self.assertEqual(code, 0, err)
            with open(inv, encoding="utf-8") as f:
                saved = json.load(f)
            # v1.2: cá thể mới bắt fresh 100, chưa hao ở bước bắt
            self.assertEqual(saved, {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]})

            # 2) Buổi tối: đọc file kho vừa xuất, khách đến gọi ca_loc_nuong_trui, nấu -> bưng -> phục vụ -> thanh toán
            first = q["first_customer_tick"]
            cooked = first + 1 + round(dish["cook_s"] * 60)
            serve = cooked + 2
            paid = serve + round(q["eat_s"] * 60)
            q_sc = write_json(w.path("q_sc.json"), {
                "quan": {
                    "player": {"pos": [2.5, 8]},
                    "tables": [{"id": "T1", "pos": [3.5, 8]}],
                }
            })
            # Đứng tại [2.5, 8]: cách B1 [2, 8] là 0.5m (gần hơn T1 [3.5, 8] là 1.0m) -> interact tại bếp;
            # sau khi nhấc món, dịch sang [3.2, 8] để T1 gần hơn B1 và phục vụ.
            q_in = write_json(w.path("q_in.json"), frames(
                {"tick": first, "interact": True},
                {"tick": first + 1, "interact": False},
                {"tick": cooked - 1, "interact": True},
                {"tick": cooked, "interact": False, "move": [1, 0]},
                {"tick": cooked + 20, "move": [0, 0]},
                {"tick": cooked + 21, "interact": True},
            ))
            total_ticks = cooked + 22 + round(q["eat_s"] * 60)
            code, err = run_headless(
                "--mode", "quan", "--seed", "42", "--ticks", str(total_ticks),
                "--inventory", inv, "--scenario", q_sc, "--inputs", q_in,
                "--snapshot-every", "1", "--out", w.path("quan.jsonl"),
            )
            self.assertEqual(code, 0, err)
            q_rows = read_jsonl(w.path("quan.jsonl"))
            q_snaps = snapshots(q_rows)
            self.assertEqual(q_snaps[0]["stock"], [{"id": "I1", "kind": "ca_loc", "fresh": 100}])
            self.assertIn("vel", q_snaps[0]["player"])

            # v1.1 có 4 bàn (T1–T4) nên tick 1020 khi hết kho sẽ phát no_dish; lọc riêng vòng đời đơn C1
            ev_names = [e["name"] for e in events(q_rows) if e["name"] != "no_dish"]
            self.assertEqual(ev_names, [
                "customer_arrived", "cook_started", "dish_ready", "dish_picked", "served", "paid",
            ])
            end = q_rows[-1]
            # v1.2: giá chốt theo tươi lúc nấu (tick first+1, hao 1/240 mỗi tick ở quán)
            price = math.floor(dish["price"] * (100 - Fraction(first + 1, 240)) / 100)
            expected_tip = math.floor(price * Fraction(str(q["tip_rate"])))
            expected_earned = price + expected_tip
            self.assertEqual(end["money"], expected_earned)
            self.assertEqual(end["earned"], expected_earned)
            self.assertAlmostEqual(end["reputation"], q["reputation_initial"] + q["tip_reputation"])
            self.assertEqual(end["score"], expected_earned + tuning["score"]["reputation_multiplier"] * 3)

    def test_fainted_gather_writes_empty_inventory_and_quan_emits_no_dish(self):
        """Ngất ở buổi sáng -> xuất kho rỗng -> buổi tối đọc vào và phát no_dish đúng lịch."""
        first = load_tuning()["quan"]["first_customer_tick"]
        with Workdir() as w:
            g_sc = write_json(w.path("g_sc.json"), {
                "gather": {
                    "player": {"pos": [20, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                    "hold": inst("ca_loc", "bong_sung"),
                    "nodes": [],
                    "fish": [],
                    "random_fish": False,
                }
            })
            inv = w.path("empty.json")
            code, err = run_headless(
                "--mode", "gather", "--seed", "7", "--ticks", "5",
                "--scenario", g_sc, "--inventory-out", inv, "--out", w.path("g.jsonl"),
            )
            self.assertEqual(code, 0, err)
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})

            code, err = run_headless(
                "--mode", "quan", "--seed", "7", "--ticks", str(first),
                "--inventory", inv, "--out", w.path("q.jsonl"),
            )
            self.assertEqual(code, 0, err)
            q_rows = read_jsonl(w.path("q.jsonl"))
            self.assertEqual(snapshots(q_rows)[0]["stock"], [])
            no_dishes = events(q_rows, "no_dish")
            self.assertEqual(len(no_dishes), 1)
            self.assertEqual(no_dishes[0]["tick"], first)


if __name__ == "__main__":
    unittest.main()
