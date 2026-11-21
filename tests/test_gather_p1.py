"""Test hộp đen cho Lát 1 & Lát 2 của buổi sáng (`gather`) theo PRD Phase 1 (Test Contract v1.0).

Bao phủ:
- Lát 1: bơi, lặn/nổi (`dive`/`surface`), oxy tiêu/hồi/kẹp, `oxygen_empty`, đếm ngạt (`zero_oxy_ticks`),
  `choke` đúng tick t+59, nổi lên đúng bước đáng lẽ ngạt không bị ngạt, `faint` mất giỏ LIFO + kho rỗng.
- Lát 2: hái nút trên mặt nước (đúng mép bán kính, hòa theo id, `regrow_ticks` -> `node_regrown` hái ngay,
  `hold_full`, không hái dưới nước), bắt đàn cá dưới nước (yield đầy đủ, xóa đàn, cooldown L dùng lại từ t+L,
  hòa theo id, `hold_full` giữ đàn & cooldown và không thử đàn khác, không bắt ở mặt nước, không có cá không hồi chiêu),
  ưu tiên cập bến trước hái, hành động hợp lệ ở bước cuối vẫn vào kho, `faint` ưu tiên hơn `time`.
"""

import json
import unittest

from helpers import Workdir, counts, events, frames, inst, kinds_of, read_jsonl, run_headless, snapshots, write_json


def tuning_gather():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


class GatherSlice1OxygenAndFaint(unittest.TestCase):
    def test_dive_and_surface_events_and_oxygen_drain_refill(self):
        g = tuning_gather()
        with Workdir() as w:
            # Bắt đầu đúng biên mặt nước d = 0.5 với oxy = 100
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [20, g["surface_depth"]], "oxygen_ticks": 100},
                    "nodes": [],
                    "fish": [],
                    "random_fish": False,
                }
            })
            # Tick 0..5 bơi xuống dưới nước; tick 6..25 bơi lên về mặt nước
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "move": [0, 1]},
                {"tick": 6, "move": [0, -1]},
            ))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "30",
                "--scenario", sc, "--inputs", inp, "--snapshot-every", "1",
                "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            dives = events(rows, "dive")
            surfaces = events(rows, "surface")
            self.assertEqual(len(dives), 1)
            self.assertEqual(dives[0]["tick"], 1)
            self.assertGreater(dives[0]["data"]["pos"][1], g["surface_depth"])
            self.assertEqual(len(surfaces), 1)
            self.assertLessEqual(surfaces[0]["data"]["pos"][1], g["surface_depth"])

            # Kiểm tra oxy giảm 1/tick khi dưới nước và hồi oxygen_refill_per_tick khi ở mặt nước
            snaps = {r["tick"]: r["player"] for r in snapshots(rows)}
            self.assertEqual(snaps[1]["oxygen_ticks"], 99)
            self.assertFalse(snaps[1]["at_surface"])
            st = surfaces[0]["tick"]
            self.assertTrue(snaps[st]["at_surface"])
            self.assertEqual(
                snaps[st]["oxygen_ticks"],
                min(snaps[st]["oxygen_max_ticks"], snaps[st - 1]["oxygen_ticks"] + g["oxygen_refill_per_tick"]),
            )

    def test_oxygen_empty_and_choke_at_t_plus_59(self):
        """Chạm oxy 0 ở tick t và ở dưới nước liên tục -> ngạt lần đầu đúng ở t+59."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [20, 10], "oxygen_ticks": 2, "hp": 3},
                    "nodes": [],
                    "fish": [],
                    "random_fish": False,
                }
            })
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "65",
                "--scenario", sc, "--snapshot-every", "1",
                "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            empties = events(rows, "oxygen_empty")
            self.assertEqual(len(empties), 1)
            t = empties[0]["tick"]
            self.assertEqual(t, 2)
            self.assertEqual(empties[0]["data"], {"oxygen_ticks": 0})

            chokes = events(rows, "choke")
            self.assertEqual(len(chokes), 1)
            self.assertEqual(chokes[0]["tick"], t + 59)  # 61
            self.assertEqual(chokes[0]["data"], {"hp": 2})

            snaps = {r["tick"]: r["player"] for r in snapshots(rows)}
            self.assertEqual(snaps[t]["zero_oxy_ticks"], 1)
            self.assertEqual(snaps[t + 58]["zero_oxy_ticks"], 59)
            self.assertEqual(snaps[t + 59]["zero_oxy_ticks"], 0)
            self.assertEqual(snaps[t + 59]["hp"], 2)

    def test_surface_on_would_be_choke_tick_prevents_choke(self):
        """Nổi lên đúng bước đáng lẽ ngạt thì hồi oxy, reset ngạt và không mất Máu."""
        g = tuning_gather()
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {
                        "pos": [20, g["surface_depth"] + 0.01],
                        "oxygen_ticks": 0,
                        "zero_oxy_ticks": 59,
                        "hp": 1,
                    },
                    "nodes": [],
                    "fish": [],
                    "random_fish": False,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [0, -1]}))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc, "--inputs", inp, "--snapshot-every", "1",
                "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(len(events(rows, "surface")), 1)
            self.assertEqual(events(rows, "choke"), [])
            self.assertEqual(events(rows, "faint"), [])
            p = snapshots(rows)[-1]["player"]
            self.assertEqual(p["hp"], 1)
            self.assertEqual(p["oxygen_ticks"], g["oxygen_refill_per_tick"])
            self.assertEqual(p["zero_oxy_ticks"], 0)

    def test_faint_loses_hold_lifo_writes_empty_inventory_and_stops_step(self):
        """Máu về 0 -> choke -> faint (lost LIFO) -> gather_end(fainted, items={}), ghi kho rỗng, dừng bước."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {
                        "pos": [2, 1.0],  # nằm trong bán kính bến (3m từ [2,0]) nhưng dưới nước
                        "oxygen_ticks": 0,
                        "zero_oxy_ticks": 59,
                        "hp": 1,
                    },
                    "hold": inst("ca_loc", "bong_sung", "ca_linh"),
                    "nodes": [],
                    "fish": [],
                    "random_fish": False,
                    "time_left_ticks": 1,  # đúng bước cuối ca
                }
            })
            # Dù bấm interact trong bến ở bước cuối, ngất ở bước 2 phải xảy ra trước
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            inv = w.path("inv.json")
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "5",
                "--scenario", sc, "--inputs", inp,
                "--inventory-out", inv, "--snapshot-every", "1",
                "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            evs = [r for r in rows if r["type"] == "event"]
            self.assertEqual([e["name"] for e in evs], ["choke", "faint", "gather_end"])
            self.assertEqual(evs[0]["data"], {"hp": 0})
            # v1.2: lost là mảng cá thể theo thứ tự bỏ LIFO
            self.assertEqual(evs[1]["data"]["cause"], "choke")
            self.assertEqual(evs[1]["data"]["hp"], 0)
            self.assertEqual([it["id"] for it in evs[1]["data"]["lost"]], ["I3", "I2", "I1"])
            self.assertEqual(kinds_of(evs[1]["data"]["lost"]), ["ca_linh", "bong_sung", "ca_loc"])
            self.assertEqual(evs[2]["data"], {"reason": "fainted", "inventory": {"items": []}})
            self.assertEqual(rows[-1]["reason"], "fainted")
            self.assertEqual(rows[-1]["state"], "finished")
            self.assertEqual(snapshots(rows)[-1]["hold"], [])
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})


class GatherSlice2HarvestCatchAndDock(unittest.TestCase):
    def test_harvest_boundary_tiebreak_regrow_and_immediate_reharvest(self):
        g = tuning_gather()
        regrow_ticks = int(round(g["regrow_s"] * 60))
        with Workdir() as w:
            # Hai nút cùng khoảng cách đúng mép interact_radius (2.0): N2 phải thắng N10
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [20, 0]},
                    "nodes": [
                        {"id": "N10", "kind": "bong_sung", "pos": [22, 0]},
                        {"id": "N2", "kind": "bong_dien_dien", "pos": [18, 0]},
                    ],
                    "fish": [],
                    "random_fish": False,
                }
            })
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False},
                # Đúng tick nút N2 mọc lại (tick = regrow_ticks, event tại regrow_ticks + 1) -> hái ngay được
                {"tick": regrow_ticks, "interact": True},
            ))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", str(regrow_ticks + 1),
                "--scenario", sc, "--inputs", inp, "--snapshot-every", "1",
                "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            gathers = events(rows, "gather")
            self.assertEqual(len(gathers), 2)
            self.assertEqual(gathers[0]["tick"], 1)
            self.assertEqual(gathers[0]["data"], {"node_id": "N2", "kind": "bong_dien_dien", "amount": g["node_yield"]})

            regrowns = events(rows, "node_regrown")
            self.assertEqual(len(regrowns), 1)
            self.assertEqual(regrowns[0]["tick"], regrow_ticks + 1)
            self.assertEqual(regrowns[0]["data"], {"node_id": "N2"})
            self.assertEqual(gathers[1]["tick"], regrow_ticks + 1)
            self.assertEqual(gathers[1]["data"]["node_id"], "N2")

            # Thứ tự event trong tick mọc lại: node_regrown trước gather
            tick_evs = [r["name"] for r in rows if r["type"] == "event" and r["tick"] == regrow_ticks + 1]
            self.assertEqual(tick_evs, ["node_regrown", "gather"])

    def test_harvest_hold_full_and_underwater_ignored(self):
        g = tuning_gather()
        with Workdir() as w:
            # 1) Giỏ đầy -> hold_full, nút giữ nguyên ready
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [20, 0]},
                    "hold": inst(*["ca_loc"] * g["hold_capacity"]),
                    "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [21, 0]}],
                    "fish": [],
                    "random_fish": False,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc, "--inputs", inp, "--snapshot-every", "1",
                "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "gather"), [])
            hf = events(rows, "hold_full")
            self.assertEqual(len(hf), 1)
            self.assertEqual(hf[0]["data"], {"action": "gather", "node_id": "N1", "required": g["node_yield"], "free": 0})
            self.assertTrue(snapshots(rows)[-1]["nodes"][0]["ready"])

            # 2) Dưới nước (d = 1.0 > 0.5) dù cách nút 1.0 <= 2.0 -> không hái
            sc2 = write_json(w.path("sc2.json"), {
                "gather": {
                    "player": {"pos": [20, 1.0]},
                    "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}],
                    "fish": [],
                    "random_fish": False,
                }
            })
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc2, "--inputs", inp, "--out", w.path("o2.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows2 = read_jsonl(w.path("o2.jsonl"))
            self.assertEqual(events(rows2, "gather"), [])
            self.assertEqual(events(rows2, "hold_full"), [])

    def test_catch_fish_tiebreak_cooldown_and_remove(self):
        g = tuning_gather()
        cd = int(round(g["catch_cooldown_s"] * 60))
        with Workdir() as w:
            # F2 và F10 cùng khoảng cách đúng mép catch_radius (2.0) -> F2 thắng F10
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [30, 10]},
                    "nodes": [],
                    "fish": [
                        {"id": "F10", "kind": "ca_loc", "pos": [32, 10]},
                        {"id": "F2", "kind": "ca_linh", "pos": [28, 10]},
                    ],
                    "random_fish": False,
                }
            })
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "catch": True},          # t = 1: bắt F2, đặt cd = 30
                {"tick": 1, "catch": False},
                {"tick": cd - 1, "catch": True},     # t = 30 (t+L-1): còn cooldown
                {"tick": cd, "catch": False},
            ))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", str(cd),
                "--scenario", sc, "--inputs", inp, "--snapshot-every", "1",
                "--out", w.path("o1.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows1 = read_jsonl(w.path("o1.jsonl"))
            caught1 = events(rows1, "fish_caught")
            self.assertEqual(len(caught1), 1)
            self.assertEqual(caught1[0]["tick"], 1)
            self.assertEqual(caught1[0]["data"], {"fish_id": "F2", "kind": "ca_linh", "yield": g["fish_yield"]["ca_linh"]})
            self.assertEqual([f["id"] for f in snapshots(rows1)[-1]["fish"]], ["F10"])

            # Giờ bấm đúng tick = cd (event ở t = 1 + cd = t + L) -> bắt được F10 ngay
            inp2 = write_json(w.path("in2.json"), frames(
                {"tick": 0, "catch": True},
                {"tick": 1, "catch": False},
                {"tick": cd, "catch": True},
            ))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", str(cd + 1),
                "--scenario", sc, "--inputs", inp2, "--snapshot-every", "1",
                "--out", w.path("o2.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows2 = read_jsonl(w.path("o2.jsonl"))
            caught2 = events(rows2, "fish_caught")
            self.assertEqual(len(caught2), 2)
            self.assertEqual(caught2[1]["tick"], 1 + cd)
            self.assertEqual(caught2[1]["data"], {"fish_id": "F10", "kind": "ca_loc", "yield": g["fish_yield"]["ca_loc"]})
            self.assertEqual(snapshots(rows2)[-1]["fish"], [])
            self.assertEqual(kinds_of(snapshots(rows2)[-1]["hold"]), ["ca_linh", "ca_linh", "ca_linh", "ca_loc"])
            self.assertEqual([it["id"] for it in snapshots(rows2)[-1]["hold"]], ["I1", "I2", "I3", "I4"])

    def test_catch_hold_full_does_not_try_other_fish_and_keeps_cooldown(self):
        g = tuning_gather()
        with Workdir() as w:
            # Còn trống 2 ô: F1 (ca_linh, yield 3) gần hơn F2 (ca_loc, yield 1).
            # Phải phát hold_full cho F1, giữ cả F1 & F2, không bắt F2, cooldown giữ 0.
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [30, 10]},
                    "hold": inst(*["bong_sung"] * (g["hold_capacity"] - 2)),
                    "nodes": [],
                    "fish": [
                        {"id": "F1", "kind": "ca_linh", "pos": [30.5, 10]},
                        {"id": "F2", "kind": "ca_loc", "pos": [31.5, 10]},
                    ],
                    "random_fish": False,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc, "--inputs", inp, "--snapshot-every", "1",
                "--out", w.path("o.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "fish_caught"), [])
            hf = events(rows, "hold_full")
            self.assertEqual(len(hf), 1)
            self.assertEqual(hf[0]["data"], {"action": "catch", "fish_id": "F1", "required": 3, "free": 2})
            snap = snapshots(rows)[-1]
            self.assertEqual(len(snap["fish"]), 2)
            self.assertEqual(snap["player"]["catch_cd_ticks"], 0)

    def test_catch_at_surface_or_empty_range_no_event_no_cooldown(self):
        with Workdir() as w:
            # Ở mặt nước d = 0.5 dù cá cách 1m -> không bắt, không hồi chiêu
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [30, 0.5]},
                    "nodes": [],
                    "fish": [{"id": "F1", "kind": "ca_loc", "pos": [30, 1.5]}],
                    "random_fish": False,
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc, "--inputs", inp, "--snapshot-every", "1",
                "--out", w.path("o1.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows1 = read_jsonl(w.path("o1.jsonl"))
            self.assertEqual(events(rows1, "fish_caught"), [])
            self.assertEqual(snapshots(rows1)[-1]["player"]["catch_cd_ticks"], 0)

            # Dưới nước nhưng không có cá trong tầm -> không event, không hồi chiêu
            sc2 = write_json(w.path("sc2.json"), {
                "gather": {
                    "player": {"pos": [30, 10]},
                    "nodes": [],
                    "fish": [{"id": "F1", "kind": "ca_loc", "pos": [40, 10]}],
                    "random_fish": False,
                }
            })
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc2, "--inputs", inp, "--snapshot-every", "1",
                "--out", w.path("o2.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows2 = read_jsonl(w.path("o2.jsonl"))
            self.assertEqual(events(rows2, "fish_caught"), [])
            self.assertEqual(events(rows2, "hold_full"), [])
            self.assertEqual(snapshots(rows2)[-1]["player"]["catch_cd_ticks"], 0)

    def test_dock_precedes_harvest_and_last_tick_actions_saved_to_inventory(self):
        with Workdir() as w:
            # 1) Đứng đúng mép bến [5, 0] có luôn nút ready [5, 0], bước cuối ca -> docked, không hái
            sc1 = write_json(w.path("sc1.json"), {
                "gather": {
                    "player": {"pos": [5, 0]},
                    "hold": inst("ca_loc"),
                    "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [5, 0]}],
                    "fish": [],
                    "random_fish": False,
                    "time_left_ticks": 1,
                }
            })
            inp1 = write_json(w.path("in1.json"), frames({"tick": 0, "interact": True}))
            inv1 = w.path("inv1.json")
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc1, "--inputs", inp1, "--inventory-out", inv1,
                "--out", w.path("o1.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows1 = read_jsonl(w.path("o1.jsonl"))
            self.assertEqual(events(rows1, "gather"), [])
            self.assertEqual(events(rows1, "gather_end")[0]["data"]["reason"], "docked")
            self.assertEqual(rows1[-1]["reason"], "docked")
            with open(inv1, encoding="utf-8") as f:
                self.assertEqual(counts(json.load(f)), {"ca_loc": 1})

            # 2) Ngoài bến, bắt cá hợp lệ ở bước cuối ca -> vào kho trước khi gather_end(time)
            sc2 = write_json(w.path("sc2.json"), {
                "gather": {
                    "player": {"pos": [30, 10]},
                    "hold": inst("bong_dien_dien"),
                    "nodes": [],
                    "fish": [{"id": "F1", "kind": "ca_linh", "pos": [31, 10]}],
                    "random_fish": False,
                    "time_left_ticks": 1,
                }
            })
            inp2 = write_json(w.path("in2.json"), frames({"tick": 0, "catch": True}))
            inv2 = w.path("inv2.json")
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc2, "--inputs", inp2, "--inventory-out", inv2,
                "--out", w.path("o2.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows2 = read_jsonl(w.path("o2.jsonl"))
            self.assertEqual(len(events(rows2, "fish_caught")), 1)
            end_ev = events(rows2, "gather_end")[0]["data"]
            self.assertEqual(end_ev["reason"], "time")
            self.assertEqual(counts(end_ev["inventory"]), {"bong_dien_dien": 1, "ca_linh": 3})
            # v1.2: cá mới bắt cấp tiếp id sau hàng có sẵn (I1) theo thứ tự vào giỏ
            self.assertEqual([it["id"] for it in end_ev["inventory"]["items"]], ["I1", "I2", "I3", "I4"])
            with open(inv2, encoding="utf-8") as f:
                self.assertEqual(counts(json.load(f)), {"bong_dien_dien": 1, "ca_linh": 3})

            # 3) Ngoài bến, hái nút hợp lệ ở bước cuối ca -> vào kho trước khi gather_end(time)
            sc3 = write_json(w.path("sc3.json"), {
                "gather": {
                    "player": {"pos": [12, 0]},
                    "hold": [],
                    "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}],
                    "fish": [],
                    "random_fish": False,
                    "time_left_ticks": 1,
                }
            })
            inp3 = write_json(w.path("in3.json"), frames({"tick": 0, "interact": True}))
            inv3 = w.path("inv3.json")
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1",
                "--scenario", sc3, "--inputs", inp3, "--inventory-out", inv3,
                "--out", w.path("o3.jsonl"),
            )
            self.assertEqual(code, 0, err)
            rows3 = read_jsonl(w.path("o3.jsonl"))
            self.assertEqual(len(events(rows3, "gather")), 1)
            end_ev3 = events(rows3, "gather_end")[0]["data"]
            self.assertEqual(end_ev3["reason"], "time")
            self.assertEqual(end_ev3["inventory"], {"items": [{"id": "I1", "kind": "bong_dien_dien", "fresh": 100}]})
            with open(inv3, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": [{"id": "I1", "kind": "bong_dien_dien", "fresh": 100}]})


if __name__ == "__main__":
    unittest.main()
