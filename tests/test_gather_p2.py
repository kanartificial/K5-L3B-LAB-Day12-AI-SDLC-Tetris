"""Test hộp đen bổ sung cho Phase 2 (AC-P2-02 cá bơi/phản xạ/bắt trước khi bơi, AC-P2-03 Cá Sấu/ngạt xuyên bất tử, AC-P2-05 Shop)."""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class GatherP2EdgeCases(unittest.TestCase):
    def test_fish_wall_reflection_and_turn_at_age_120(self):
        """Cá chạm mép phản xạ quãng đường còn lại và đổi hướng ở bước bơi thứ 120."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "random_fish": True,
                    "fish": [{"id": "F1", "kind": "ca_keo", "pos": [95.99, 27.99], "heading_deg": 45, "age_ticks": 0}],
                    "monsters": [],
                }
            })
            code, err = run_headless(
                "--mode", "gather", "--seed", "9", "--ticks", "125",
                "--scenario", sc, "--snapshot-every", "1", "--out", w.path("g.jsonl"),
            )
            self.assertEqual(code, 0, err)
            snaps = {r["tick"]: r for r in snapshots(read_jsonl(w.path("g.jsonl")))}
            # Tick 1: chạm góc [96, 28] -> phản xạ cả 2 thành phần (45° -> 225°)
            f1 = snaps[1]["fish"][0]
            self.assertLessEqual(f1["pos"][0], 96.0)
            self.assertLessEqual(f1["pos"][1], 28.0)
            self.assertAlmostEqual(f1["heading_deg"], 225.0, places=1)
            # Tick 120: đổi hướng theo seed ở bước bơi thứ 120
            h119 = snaps[119]["fish"][0]["heading_deg"]
            h120 = snaps[120]["fish"][0]["heading_deg"]
            self.assertNotAlmostEqual(h119, h120, places=2)

    def test_catch_uses_fish_position_before_swim(self):
        """Bắt cá dùng vị trí cá TRƯỚC khi bơi (mục 4.5)."""
        with Workdir() as w:
            # Cá ở đúng mép catch_radius (2.0 m) đang bơi ra xa (+x)
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [30, 10]},
                    "random_fish": True,
                    "fish": [{"id": "F1", "kind": "ca_loc", "pos": [32, 10], "heading_deg": 0}],
                    "monsters": [],
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc, "--inputs", inp, "--out", w.path("g.jsonl"),
            )
            self.assertEqual(code, 0, err)
            caught = events(read_jsonl(w.path("g.jsonl")), "fish_caught")
            self.assertEqual(len(caught), 1)
            self.assertEqual(caught[0]["data"]["fish_id"], "F1")

    def test_choke_pierces_invulnerability_and_keeps_hold(self):
        """Ngạt xuyên bất tử (invuln_ticks > 0) và không làm rơi hàng (mục 1.1)."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {
                        "pos": [20, 10],
                        "oxygen_ticks": 0,
                        "zero_oxy_ticks": 59,
                        "invuln_ticks": 50,
                        "hp": 3,
                    },
                    "hold": ["ca_loc", "bong_sung"],
                    "random_fish": False,
                    "monsters": [],
                }
            })
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc, "--snapshot-every", "1", "--out", w.path("g.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("g.jsonl"))
            chokes = events(rows, "choke")
            self.assertEqual(len(chokes), 1)
            self.assertEqual(chokes[0]["data"], {"hp": 2})
            self.assertEqual(snapshots(rows)[-1]["hold"], ["ca_loc", "bong_sung"])

    def test_monster_patrol_chase_exit_and_recoil_duration(self):
        """Cá Sấu chuyển patrol -> chase (d>=10, <=10m), thoát chase khi lên d<10, và recoil đúng 60 tick."""
        with Workdir() as w:
            # 1) Bơi lên d < 10 -> thoát chase về patrol
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [60, 15]},  # cách M1 [60,24] đúng 9m <= 10m -> vào chase
                    "random_fish": False,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [0, -1]}))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "100",
                "--scenario", sc, "--inputs", inp, "--snapshot-every", "1", "--out", w.path("g1.jsonl"),
            )
            self.assertEqual(code, 0, err)
            snaps = {r["tick"]: r for r in snapshots(read_jsonl(w.path("g1.jsonl")))}
            self.assertEqual(snaps[1]["monsters"][0]["state"], "chase")
            self.assertLess(snaps[100]["player"]["pos"][1], 10.0)
            self.assertEqual(snaps[100]["monsters"][0]["state"], "patrol")

            # 2) Chạm trùng tâm -> recoil hướng +x, đủ 60 tick mới về patrol
            sc2 = write_json(w.path("sc2.json"), {
                "gather": {
                    "player": {"pos": [60, 24], "hp": 3},
                    "random_fish": False,
                }
            })
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "65",
                "--scenario", sc2, "--snapshot-every", "1", "--out", w.path("g2.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows2 = read_jsonl(w.path("g2.jsonl"))
            hit_t = events(rows2, "monster_hit")[0]["tick"]
            s2 = {r["tick"]: r for r in snapshots(rows2)}
            self.assertEqual(s2[hit_t]["monsters"][0]["state"], "recoil")
            self.assertEqual(s2[hit_t]["monsters"][0]["recoil_dir"], [1.0, 0.0])
            self.assertEqual(s2[hit_t + 59]["monsters"][0]["state"], "recoil")
            self.assertEqual(s2[hit_t + 60]["monsters"][0]["state"], "patrol")

    def test_shop_buy_before_shop_done_on_last_tick_and_hp_upgrade_next_day(self):
        """Mua nâng cấp `hp` cùng tick với `shop_done` ở bước cuối Shop -> áp hp_max=4 ở Ngày 2."""
        sc_obj = {"day": {"money": 800, "earned": 800}, "gather": {"hold": [], "random_fish": False}}
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), sc_obj)
            # Dò tick shop mở
            inp0 = write_json(w.path("in0.json"), frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False}))
            code, err = run_headless(
                "--mode", "day", "--days", "1", "--seed", "1", "--ticks", "22200",
                "--scenario", sc, "--inputs", inp0, "--out", w.path("p.jsonl"),
            )
            self.assertEqual(code, 0, err)
            t = [e for e in events(read_jsonl(w.path("p.jsonl")), "phase_start") if e["phase"] == "shop"][0]["tick"]

            # Mua hp cấp 1 (250), cấp 2 (500), thử mua thêm -> max_level, rồi shop_done ở bước cuối cùng
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False},
                {"tick": t, "buy": "hp"},
                {"tick": t + 1, "buy": "hp"},
                {"tick": t + 2, "buy": "hp", "shop_done": True},
            ))
            code, err = run_headless(
                "--mode", "day", "--days", "2", "--seed", "1", "--ticks", str(t + 10),
                "--scenario", sc, "--inputs", inp, "--out", w.path("d.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("d.jsonl"))
            self.assertEqual([e["data"]["level"] for e in events(rows, "bought")], [1, 2])
            self.assertEqual([e["data"]["reason"] for e in events(rows, "buy_failed")], ["max_level"])
            self.assertEqual(events(rows, "shop_end")[0]["data"]["reason"], "done")
            d2_gather = [s for s in snapshots(rows) if s.get("day") == 2 and s.get("phase") == "gather"]
            self.assertEqual(d2_gather[0]["active_upgrades"].get("hp"), 2)
            self.assertEqual(d2_gather[0]["player"]["hp_max"], 5)
            self.assertEqual(d2_gather[0]["player"]["hp"], 5)


if __name__ == "__main__":
    unittest.main()
