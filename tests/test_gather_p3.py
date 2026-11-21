"""Test Phase 3 (Contract v1.2) cho phạm vi Adapter (`AC-P3-01`), `sim/gather` (`AC-P3-02`), và `day`/`Shop` (`AC-P3-04`).

Chạy trực tiếp chế độ `contract_version="1.2"` song song khi `game.contract.json` vẫn giữ `"1.1"` cho tới khi `sim/quan` hoàn tất `AC-P3-03`.
"""

from fractions import Fraction
import json
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer, LiveInputs
from chonoi.inventory import (
    hold_to_items,
    read_inventory,
    to_fresh,
    write_inventory,
)
from chonoi.rng import Streams
from chonoi.runner import DaySession, Session
from chonoi.scenario import load_scenario
from chonoi.sim.gather import GatherSim
from chonoi.sim.shop import ShopSim

from helpers import Workdir, frames, write_json


def load_tuning():
    return load_contract()["tuning"]


class AdapterAndSchemaV12(unittest.TestCase):
    def test_v12_rejects_counted_inventory_and_invalid_items(self):
        """Contract v1.2 từ chối file kho đếm, id trùng, kind lạ, fresh ngoài [0, 100]."""
        with Workdir() as w:
            for bad in (
                {"items": {"ca_loc": 1}},  # kho đếm v1.1 -> phải từ chối
                {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I1", "kind": "ca_loc", "fresh": 90}]},
                {"items": [{"id": "", "kind": "ca_loc", "fresh": 100}]},
                {"items": [{"id": "I1", "kind": "ca_la", "fresh": 100}]},
                {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100.1}]},
                {"items": [{"id": "I1", "kind": "ca_loc", "fresh": -0.1}]},
                {"items": [{"id": "I1", "kind": "ca_loc"}]},
            ):
                p = write_json(w.path("inv.json"), bad)
                with self.assertRaises(BadInput, msg=str(bad)):
                    read_inventory(p, contract_version="1.2")

    def test_v12_write_and_read_inventory_preserves_threshold_precision(self):
        """Ghi nguyên tử sắp theo id và đọc lại giữ chính xác bội số 1/240 tại ngưỡng 30."""
        with Workdir() as w:
            p = w.path("inv.json")
            # 30 + 1/120 (chưa ươn) và 30 - 1/240 (đã ươn)
            items = [
                {"id": "I10", "kind": "ca_loc", "fresh": Fraction(7202, 240)},
                {"id": "I2", "kind": "ca_linh", "fresh": Fraction(7199, 240)},
            ]
            write_inventory(p, items, contract_version="1.2")
            raw = json.loads(open(p, encoding="utf-8").read())
            self.assertEqual([x["id"] for x in raw["items"]], ["I2", "I10"])

            loaded = read_inventory(p, contract_version="1.2")
            self.assertEqual([x["id"] for x in loaded], ["I2", "I10"])
            self.assertEqual(loaded[0]["fresh"], Fraction(7199, 240))
            self.assertLess(loaded[0]["fresh"], Fraction(30))
            self.assertEqual(loaded[1]["fresh"], Fraction(7202, 240))
            self.assertGreater(loaded[1]["fresh"], Fraction(30))
            # Sau 2 tick hao ở quán (-2/240), I10 chạm đúng 30 (chưa ươn); tick thứ 3 mới ươn!
            self.assertEqual(loaded[1]["fresh"] - Fraction(2, 240), Fraction(30))
            self.assertLess(loaded[1]["fresh"] - Fraction(3, 240), Fraction(30))

    def test_v12_scenario_validation_hold_stock_and_reserved(self):
        tuning = load_tuning()
        with Workdir() as w:
            # Hợp lệ v1.2
            ok_g = write_json(w.path("g_ok.json"), {
                "gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}], "random_fish": False, "monsters": []}
            })
            blk = load_scenario(ok_g, "gather", tuning, contract_version="1.2")
            self.assertEqual(len(blk["hold"]), 1)

            # Kho chuỗi v1.1 phải bị từ chối ở v1.2
            bad_g = write_json(w.path("g_bad.json"), {"gather": {"hold": ["ca_linh"]}})
            with self.assertRaises(BadInput):
                load_scenario(bad_g, "gather", tuning, contract_version="1.2")

            # quan.stock đếm v1.1 phải bị từ chối ở v1.2
            bad_q = write_json(w.path("q_bad.json"), {"quan": {"stock": {"ca_loc": 1}}})
            with self.assertRaises(BadInput):
                load_scenario(bad_q, "quan", tuning, contract_version="1.2")

            # quan.stock mảng cá thể + customers[].reserved mảng id hợp lệ ở v1.2
            ok_q = write_json(w.path("q_ok.json"), {
                "quan": {
                    "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 95}],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}],
                }
            })
            load_scenario(ok_q, "quan", tuning, contract_version="1.2")

            # customers[].reserved dạng dict (v1.1) bị từ chối ở v1.2
            bad_res = write_json(w.path("q_bad_res.json"), {
                "quan": {
                    "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 95}],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": {"ca_loc": 1}}],
                }
            })
            with self.assertRaises(BadInput):
                load_scenario(bad_res, "quan", tuning, contract_version="1.2")


class GatherFreshnessV12(unittest.TestCase):
    def test_spoiled_fires_once_at_tick_1_when_fresh_starts_at_30(self):
        """Ví dụ TICKET-03: fresh=30 ươn ngay bước đầu -> phát spoiled đúng 1 lần tại tick 1."""
        tuning = load_tuning()
        sc = {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}], "random_fish": False, "monsters": []}
        sess = Session("gather", tuning, sc, seed=1, contract_version="1.2")
        pl = InputPlayer([])
        evs1 = sess.step(pl.advance(0))
        self.assertEqual(evs1, [{
            "type": "event", "tick": 1, "phase": "gather", "name": "spoiled",
            "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"},
        }])
        # Bước 2 không phát spoiled lần nữa
        evs2 = sess.step(pl.advance(1))
        self.assertEqual(evs2, [])
        self.assertEqual(sess.sim.hold[0]["fresh"], Fraction(30) - Fraction(2, 120))

    def test_new_item_starts_at_100_decays_next_tick_and_ids_increment(self):
        """Hái/bắt tạo cá thể fresh=100, chỉ bắt đầu hao từ bước sau, cấp I1, I2, I3... theo thứ tự."""
        tuning = load_tuning()
        sc = {
            "player": {"pos": [12, 0]},
            "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}],
            "fish": [],
            "random_fish": False,
            "monsters": [],
        }
        sess = Session("gather", tuning, sc, seed=1, contract_version="1.2")
        pl = InputPlayer(frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False})["frames"])
        evs1 = sess.step(pl.advance(0))
        self.assertEqual([e["name"] for e in evs1], ["gather"])
        self.assertEqual(sess.snapshot()["hold"], [{"id": "I1", "kind": "bong_dien_dien", "fresh": 100}])
        # Bước tiếp theo mới hao 0.5/60 = 1/120
        sess.step(pl.advance(1))
        self.assertEqual(sess.sim.hold[0]["fresh"], Fraction(11999, 120))

    def test_pause_freezes_freshness_decay(self):
        """Pause phải dừng hao tươi hoàn toàn."""
        tuning = load_tuning()
        sc = {"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}], "random_fish": False, "monsters": []}
        sess = Session("gather", tuning, sc, seed=1, contract_version="1.2")
        pl = InputPlayer(frames(
            {"tick": 0, "pause": True},
            {"tick": 1, "pause": False},
            {"tick": 5, "pause": True},
        )["frames"])
        for k in range(5):
            sess.step(pl.advance(k))
        # Đang pause trong 5 tick -> fresh vẫn đúng 100
        self.assertEqual(sess.sim.hold[0]["fresh"], Fraction(100))
        # Tick 5: resume + chạy 1 bước gameplay -> hao đúng 1/120
        evs = sess.step(pl.advance(5))
        self.assertEqual([e["name"] for e in evs], ["resumed"])
        self.assertEqual(sess.sim.hold[0]["fresh"], Fraction(11999, 120))

    def test_monster_hit_and_faint_emit_item_objects_lifo_and_empty_inventory(self):
        """monster_hit và faint xuất `lost` là mảng cá thể theo LIFO; ngất ghi kho rỗng {"items":[]}."""
        tuning = load_tuning()
        sc = {
            "player": {"pos": [61, 24], "hp": 1},
            "hold": [
                {"id": "I1", "kind": "ca_loc", "fresh": 100},
                {"id": "I2", "kind": "bong_sung", "fresh": 90},
                {"id": "I3", "kind": "ca_linh", "fresh": 80},
            ],
            "random_fish": False,
        }
        with Workdir() as w:
            sess = Session("gather", tuning, sc, seed=1, contract_version="1.2")
            pl = InputPlayer([])
            all_evs = []
            for k in range(10):
                if sess.done:
                    break
                all_evs.extend(sess.step(pl.advance(k)))
            hit = [e for e in all_evs if e["name"] == "monster_hit"][0]["data"]
            faint = [e for e in all_evs if e["name"] == "faint"][0]["data"]
            end = [e for e in all_evs if e["name"] == "gather_end"][0]["data"]
            # floor(3/2) = 1 -> I3 rơi lúc monster_hit; phần còn lại [I2, I1] rơi theo LIFO lúc faint
            self.assertEqual([x["id"] for x in hit["lost"]], ["I3"])
            self.assertEqual([x["id"] for x in faint["lost"]], ["I2", "I1"])
            self.assertEqual(end["inventory"], {"items": []})
            inv_path = w.path("faint.json")
            sess.write_inventory_if_done(inv_path)
            self.assertEqual(json.loads(open(inv_path, encoding="utf-8").read()), {"items": []})

    def test_dock_smoke_writes_exact_v12_inventory_file(self):
        """Smoke bàn giao TICKET-03: fresh=100, interact ở tick 0 -> file kho chứa fresh sau 1 bước hao."""
        tuning = load_tuning()
        sc = {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}], "random_fish": False, "monsters": []}
        with Workdir() as w:
            sess = Session("gather", tuning, sc, seed=1, contract_version="1.2")
            pl = InputPlayer(frames({"tick": 0, "interact": True})["frames"])
            evs = sess.step(pl.advance(0))
            self.assertTrue(sess.done)
            end_inv = [e for e in evs if e["name"] == "gather_end"][0]["data"]["inventory"]
            inv_path = w.path("catch.json")
            sess.write_inventory_if_done(inv_path)
            saved = json.loads(open(inv_path, encoding="utf-8").read())
            self.assertEqual(saved, end_inv)
            reloaded = read_inventory(inv_path, contract_version="1.2")
            self.assertEqual(reloaded, [{"id": "I1", "kind": "ca_linh", "fresh": Fraction(11999, 120)}])


class ShopAndDayItemIdsV12(unittest.TestCase):
    def test_shop_preserves_item_instances_without_decay(self):
        """Shop ở v1.2 giữ nguyên mảng cá thể `stock` và KHÔNG hao tươi."""
        tuning = load_tuning()
        stock = [{"id": "I5", "kind": "ca_loc", "fresh": Fraction(50)}, {"id": "I2", "kind": "ca_linh", "fresh": Fraction(30)}]
        shop = ShopSim(tuning, stock, money=200, earned=200, reputation=3.0, upgrades={}, contract_version="1.2")
        pl = InputPlayer([])
        for k in range(20):
            shop.step(pl.advance(k))
        snap = shop.snapshot()
        self.assertEqual(snap["stock"], [
            {"id": "I2", "kind": "ca_linh", "fresh": 30},
            {"id": "I5", "kind": "ca_loc", "fresh": 50},
        ])

    def test_day_reassigns_fixture_hold_ids_from_day_2_onward(self):
        """Trong day v1.2: Ngày 1 giữ nguyên id mẫu gather.hold, Ngày 2 cấp id mới tăng tiếp sau id lớn nhất."""
        tuning = load_tuning()
        item_ids = IdAllocator()
        sc = {"hold": [{"id": "I3", "kind": "ca_loc", "fresh": 95}], "random_fish": False, "monsters": []}
        g1 = GatherSim(tuning, sc, Streams(1), IdAllocator(), day=1, contract_version="1.2",
                       item_ids=item_ids, reassign_hold_ids=False)
        self.assertEqual([x["id"] for x in g1.hold], ["I3"])
        g2 = GatherSim(tuning, sc, Streams(1), IdAllocator(), day=2, contract_version="1.2",
                       item_ids=item_ids, reassign_hold_ids=True)
        self.assertEqual([x["id"] for x in g2.hold], ["I4"])
        self.assertEqual(g2.hold[0]["fresh"], Fraction(95))


if __name__ == "__main__":
    unittest.main()
