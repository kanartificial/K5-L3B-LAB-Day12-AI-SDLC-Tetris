"""Buổi sáng — Lặn & Hái (`gather`, hỗ trợ Contract v1.1 & v1.2).

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Phase 3 (v1.2 — khi contract_version == "1.2"):
- Giỏ chứa cá thể `{id, kind, fresh}` (cấp `I1, I2…` xuyên pha & xuyên Ngày qua `item_ids`).
- Hàng mới bắt/hái có `fresh = 100`, bắt đầu hao từ bước sau (`gather_decay_per_s = 0.5/s`, chính xác `2/240` mỗi tick).
- Bước 1 đầu bước giảm độ tươi hàng có sẵn (dừng khi pause), phát `spoiled(item_id, kind, location:"hold")`
  đúng 1 lần theo `id` khi vượt từ `>= 30` xuống `< 30` trước làm tròn.
- Rơi hàng (`monster_hit`) và ngất (`faint`) bỏ theo LIFO, `lost` là mảng cá thể; `gather_end.data.inventory`
  theo schema kho cá thể sắp theo `id`.
"""

from fractions import Fraction
import math

from ..ids import id_key, sort_by_id
from ..inventory import (
    hold_to_items,
    is_v12,
    serialize_item,
    to_fresh,
)
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


def _reflect_1d(val: float, vel: float, lo: float, hi: float):
    while val < lo or val > hi:
        if val < lo:
            val = lo + (lo - val)
            vel = -vel
        elif val > hi:
            val = hi - (val - hi)
            vel = -vel
    if val <= lo and vel < 0:
        val = lo
        vel = -vel
    elif val >= hi and vel > 0:
        val = hi
        vel = -vel
    return val, vel


def _effective_oxygen_and_hp(tuning: dict, active_upgrades: dict | None):
    g = tuning["gather"]
    oxy_s = g["oxygen_max_s"]
    hp_max = g["hp_max"]
    if active_upgrades:
        shop_upgs = tuning.get("shop", {}).get("upgrades", {})
        oxy_lvl = active_upgrades.get("oxygen", 0)
        if oxy_lvl > 0:
            for u in shop_upgs.get("oxygen", []):
                if u["level"] == oxy_lvl:
                    oxy_s = u["oxygen_max_s"]
        hp_lvl = active_upgrades.get("hp", 0)
        if hp_lvl > 0:
            for u in shop_upgs.get("hp", []):
                if u["level"] == hp_lvl:
                    hp_max = u["hp_max"]
    return int(round(oxy_s * TICK)), int(hp_max)


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1, active_upgrades=None,
                 money=0, earned=0, reputation=None, contract_version="1.1",
                 item_ids=None, reassign_hold_ids=False):
        t = tuning["gather"]
        self.t = t
        self.tuning = tuning
        self.contract_version = contract_version
        self.v12 = is_v12(contract_version)
        self.rng = streams
        self.ids = ids
        self.item_ids = item_ids if item_ids is not None else ids
        self.day = day
        self.phase_tick = 0
        self.random_fish = scenario.get("random_fish", True)

        # Tham số độ tươi v1.2 (chỉ đọc từ tuning.freshness, không hard-code)
        f_cfg = tuning.get("freshness", {
            "initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30,
        })
        self.fresh_initial = to_fresh(f_cfg["initial"])
        self.fresh_decay_per_tick = to_fresh(f_cfg["gather_decay_per_s"]) / 60
        self.spoiled_below = to_fresh(f_cfg["spoiled_below"])

        self.oxygen_max, self.hp_max = _effective_oxygen_and_hp(tuning, active_upgrades)

        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", self.hp_max)
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))

        # Giỏ: v1.1 là mảng kind; v1.2 là mảng cá thể {id, kind, fresh: Fraction} theo thứ tự nhặt
        raw_hold = scenario.get("hold", [])
        if self.v12:
            self.hold = []
            for it in raw_hold:
                iid = self.item_ids.new("I") if reassign_hold_ids else it["id"]
                if not reassign_hold_ids:
                    self.item_ids.reserve(iid)
                self.hold.append({"id": iid, "kind": it["kind"], "fresh": to_fresh(it["fresh"])})
        else:
            self.hold = list(raw_hold)

        # Nút hái
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        for n in self.nodes:
            ids.reserve(n["id"])

        # Đàn cá
        self.fish = []
        if "fish" in scenario:
            for f in scenario["fish"]:
                self.fish.append({
                    "id": f["id"],
                    "kind": f["kind"],
                    "pos": [float(c) for c in f["pos"]],
                    "heading_deg": float(f.get("heading_deg", 0)),
                    "age_ticks": int(f.get("age_ticks", 0)),
                })
                ids.reserve(f["id"])
        elif self.random_fish:
            fi = t["fish_initial"]
            if isinstance(fi, list):
                for f in fi:
                    self.fish.append({
                        "id": f["id"],
                        "kind": f["kind"],
                        "pos": [float(c) for c in f["pos"]],
                        "heading_deg": float(f.get("heading_deg", 0)),
                        "age_ticks": 0,
                    })
                    ids.reserve(f["id"])
            else:
                self._spawn_initial_fish(int(fi))

        # Thủy quái (Cá Sấu Năm Chèo)
        self.monsters = []
        m_cfg = t.get("monsters", {})
        if "monsters" in scenario:
            for m in scenario["monsters"]:
                self.monsters.append({
                    "id": m["id"],
                    "kind": m["kind"],
                    "pos": [float(c) for c in m["pos"]],
                    "waypoints": [[float(c) for c in wp] for wp in m["waypoints"]],
                    "target_idx": int(m.get("target_idx", 1)),
                    "state": m.get("state", "patrol"),
                    "state_ticks_left": int(m.get("state_ticks_left", 0)),
                    "recoil_dir": [float(c) for c in m["recoil_dir"]] if m.get("recoil_dir") is not None else None,
                })
                ids.reserve(m["id"])
        else:
            for sp in m_cfg.get("spawns", []):
                if sp.get("from_day", 1) <= day:
                    wps = [[float(c) for c in wp] for wp in sp["waypoints"]]
                    pos = [float(c) for c in sp.get("pos", wps[0])]
                    self.monsters.append({
                        "id": sp["id"],
                        "kind": sp["kind"],
                        "pos": pos,
                        "waypoints": wps,
                        "target_idx": 1,
                        "state": "patrol",
                        "state_ticks_left": 0,
                        "recoil_dir": None,
                    })
                    ids.reserve(sp["id"])

        self.money = money
        self.earned = earned
        self.reputation = tuning["quan"]["reputation_initial"] if reputation is None else reputation
        self.done = False
        self.reason = None

    def _spawn_initial_fish(self, count: int):
        rng = self.rng.get("fish_spawn")
        used_pos = set()
        weights_cfg = self.t["fish_weights"]
        spawn_x = sorted(self.t["fish_spawn_x"])
        spawn_depths = self.t["fish_spawn_depths"]
        species_order = sorted(weights_cfg.keys())

        for _ in range(count):
            avail_by_species = {}
            for kind in species_order:
                pts = [(float(x), float(d)) for x in spawn_x for d in sorted(spawn_depths[kind])
                       if (float(x), float(d)) not in used_pos]
                if pts:
                    avail_by_species[kind] = pts
            if not avail_by_species:
                break
            kind = self._pick_weighted_species(rng, avail_by_species, weights_cfg)
            pt = rng.choice(avail_by_species[kind])
            used_pos.add(pt)
            heading = rng.uniform(0.0, 360.0)
            fid = self.ids.new("F")
            self.fish.append({
                "id": fid,
                "kind": kind,
                "pos": [pt[0], pt[1]],
                "heading_deg": heading,
                "age_ticks": 0,
            })

    @staticmethod
    def _pick_weighted_species(rng, avail_by_species, weights_cfg):
        kinds = sorted(avail_by_species.keys())
        total = sum(float(weights_cfg[k]) for k in kinds)
        r = rng.random() * total
        acc = 0.0
        for k in kinds:
            acc += float(weights_cfg[k])
            if r < acc:
                return k
        return kinds[-1]

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self):
        """Payload JSON cho `gather_end.data.inventory.items` và `write_inventory`."""
        return hold_to_items(self.hold, contract_version=self.contract_version)

    def inventory_items_raw(self):
        """Bàn giao nội bộ trong `day` (giữ nguyên Fraction độ tươi cho v1.2, không hao thêm)."""
        if self.v12:
            return [{"id": it["id"], "kind": it["kind"], "fresh": it["fresh"]} for it in sort_by_id(self.hold)]
        return self.inventory_items()

    def _serialize_hold(self):
        if self.v12:
            return [serialize_item(it) for it in self.hold]
        return list(self.hold)

    def _serialize_lost(self, dropped: list):
        if self.v12:
            return [serialize_item(it) for it in dropped]
        return list(dropped)

    def _add_to_hold(self, kind: str, count: int):
        for _ in range(count):
            if self.v12:
                self.hold.append({
                    "id": self.item_ids.new("I"),
                    "kind": kind,
                    "fresh": self.fresh_initial,
                })
            else:
                self.hold.append(kind)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": list(self.pos), "vel": list(self.vel), "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self._serialize_hold(), "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": list(n["pos"]), "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": list(f["pos"]), "kind": f["kind"],
                      "heading_deg": f["heading_deg"], "age_ticks": f["age_ticks"]}
                     for f in sort_by_id(self.fish)],
            "monsters": [{"id": m["id"], "kind": m["kind"], "pos": list(m["pos"]),
                          "waypoints": [list(wp) for wp in m["waypoints"]],
                          "target_idx": m["target_idx"], "state": m["state"],
                          "state_ticks_left": m["state_ticks_left"],
                          "recoil_dir": list(m["recoil_dir"]) if m["recoil_dir"] is not None else None}
                         for m in sort_by_id(self.monsters)],
        }

    # --- một bước (thứ tự mục 4.5 v1.1 & mục 1 v1.2) -------------------------
    def step(self, inp):
        events = []
        # 1. Đồng hồ, cooldown, giảm bất tử, hồi nút và độ tươi của hàng có sẵn ở đầu bước
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        if self.v12 and self.hold:
            for it in sort_by_id(self.hold):
                prev = it["fresh"]
                nxt = max(Fraction(0), prev - self.fresh_decay_per_tick)
                it["fresh"] = nxt
                if prev >= self.spoiled_below and nxt < self.spoiled_below:
                    events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "hold"}))

        # 2. Bơi, chặn biên, dive/surface, oxy, ngạt (xuyên bất tử)
        was_surface = self._at_surface()
        self._move(inp)
        now_surface = self._at_surface()
        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif not was_surface and now_surface:
            events.append(("surface", {"pos": list(self.pos)}))

        if now_surface:
            refill = int(self.t["oxygen_refill_per_tick"])
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + refill)
            self.zero_oxy_ticks = 0
        else:
            prev_oxy = self.oxygen_ticks
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
            if prev_oxy > 0 and self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))
            if self.oxygen_ticks == 0:
                self.zero_oxy_ticks += 1
                if self.zero_oxy_ticks >= int(self.t["choke_interval_ticks"]):
                    self.zero_oxy_ticks = 0
                    self.hp = max(0, self.hp - 1)
                    events.append(("choke", {"hp": self.hp}))
                    if self.hp <= 0:
                        lost = self._serialize_lost(list(reversed(self.hold)))
                        self.hold = []
                        events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
                        self._finish("fainted", events)
                        return events

        # 3. Cập nhật quái theo id rồi xét tối đa một hit
        if self._update_monsters_and_hit(events):
            return events

        # 4. Tương tác: bến trước, rồi hái nút ở mặt nước
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if now_surface:
                self._try_harvest(events)

        # 5. Bắt cá theo vị trí cá TRƯỚC khi bơi
        if inp.pressed("catch"):
            if self.catch_cd_ticks == 0 and not now_surface:
                self._try_catch(events)

        # 6. Xét hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events

        # 7. Còn giờ: cá bơi, rồi sinh thêm theo lịch
        if self.random_fish and "fish_speed" in self.t:
            self._move_fish()
            self._maybe_spawn_fish(events)

        return events

    # --- Quái (Cá Sấu Năm Chèo) -----------------------------------------------
    def _clamp_monster(self, m, d_min, d_max):
        bx = self.t["bounds"]["x"]
        bd = self.t["bounds"]["d"]
        m["pos"][0] = min(float(bx[1]), max(float(bx[0]), m["pos"][0]))
        m["pos"][1] = min(float(min(bd[1], d_max)), max(float(max(bd[0], d_min)), m["pos"][1]))

    def _update_monsters_and_hit(self, events) -> bool:
        m_cfg = self.t.get("monsters")
        if not m_cfg or not self.monsters:
            return False
        species_map = m_cfg["species"]
        eligible_hitters = []

        for m in sort_by_id(self.monsters):
            sp = species_map[m["kind"]]
            d_min, d_max = sp["depths"]
            state = m["state"]
            if state == "recoil":
                step_d = float(sp["recoil_dist"]) / int(sp["recoil_ticks"])
                rx, rd = m["recoil_dir"]
                m["pos"][0] += rx * step_d
                m["pos"][1] += rd * step_d
                self._clamp_monster(m, d_min, d_max)
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] <= 0:
                    m["state"] = "patrol"
                    m["state_ticks_left"] = 0
                    m["recoil_dir"] = None
                continue
            if state == "stunned":
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] <= 0:
                    m["state"] = "patrol"
                    m["state_ticks_left"] = 0
                continue

            # patrol / chase
            dist_p = math.dist(m["pos"], self.pos)
            if state == "patrol":
                if self.pos[1] >= d_min and dist_p <= sp["detect_radius"]:
                    m["state"] = "chase"
            elif state == "chase":
                if self.pos[1] < d_min or dist_p > sp["exit_radius"]:
                    m["state"] = "patrol"

            if m["state"] == "chase":
                step = float(sp["chase_speed"]) / TICK
                if dist_p > 0:
                    mv = min(step, dist_p)
                    m["pos"][0] += (self.pos[0] - m["pos"][0]) / dist_p * mv
                    m["pos"][1] += (self.pos[1] - m["pos"][1]) / dist_p * mv
            else:
                wp = m["waypoints"][m["target_idx"]]
                dw = math.dist(m["pos"], wp)
                step = float(sp["patrol_speed"]) / TICK
                if dw <= step:
                    m["pos"][0] = float(wp[0])
                    m["pos"][1] = float(wp[1])
                    m["target_idx"] = 1 - m["target_idx"]
                else:
                    m["pos"][0] += (wp[0] - m["pos"][0]) / dw * step
                    m["pos"][1] += (wp[1] - m["pos"][1]) / dw * step

            self._clamp_monster(m, d_min, d_max)
            eligible_hitters.append((m, sp))

        if self.invuln_ticks > 0 or not eligible_hitters:
            return False

        best = None
        best_key = None
        for m, sp in eligible_hitters:
            d_min = sp["depths"][0]
            if self.pos[1] < d_min:
                continue
            dist_p = math.dist(m["pos"], self.pos)
            if dist_p <= sp["hit_radius"]:
                key = (dist_p, id_key(m["id"]))
                if best_key is None or key < best_key:
                    best_key = key
                    best = (m, sp)

        if best is None:
            return False

        m, sp = best
        self.hp = max(0, self.hp - 1)
        n_drop = int(math.floor(len(self.hold) * float(m_cfg["loss_ratio"])))
        dropped = [self.hold.pop() for _ in range(n_drop)]
        lost = self._serialize_lost(dropped)
        self.invuln_ticks = int(m_cfg["invuln_ticks"])

        dx = m["pos"][0] - self.pos[0]
        dd = m["pos"][1] - self.pos[1]
        norm = math.hypot(dx, dd)
        rdir = [1.0, 0.0] if norm == 0.0 else [dx / norm, dd / norm]
        m["state"] = "recoil"
        m["state_ticks_left"] = int(sp["recoil_ticks"])
        m["recoil_dir"] = rdir

        events.append(("monster_hit", {
            "monster_id": m["id"],
            "hp": self.hp,
            "lost": lost,
            "pos": list(self.pos),
        }))

        if self.hp <= 0:
            rem_lost = self._serialize_lost(list(reversed(self.hold)))
            self.hold = []
            events.append(("faint", {"cause": "monster", "lost": rem_lost, "hp": 0}))
            self._finish("fainted", events)
            return True
        return False

    # --- Cá bơi & sinh theo lịch ----------------------------------------------
    def _move_fish(self):
        turn_ticks = int(self.t["fish_turn_ticks"])
        step = float(self.t["fish_speed"]) / TICK
        x_lo, x_hi = float(self.t["fish_x"][0]), float(self.t["fish_x"][1])
        depths_cfg = self.t["fish_depths"]
        rng = self.rng.get("fish_turn")

        for f in sort_by_id(self.fish):
            f["age_ticks"] += 1
            if f["age_ticks"] % turn_ticks == 0:
                f["heading_deg"] = rng.uniform(0.0, 360.0)
            rad = math.radians(f["heading_deg"])
            vx = math.cos(rad)
            vd = math.sin(rad)
            d_lo, d_hi = float(depths_cfg[f["kind"]][0]), float(depths_cfg[f["kind"]][1])
            nx, vx = _reflect_1d(f["pos"][0] + vx * step, vx, x_lo, x_hi)
            nd, vd = _reflect_1d(f["pos"][1] + vd * step, vd, d_lo, d_hi)
            f["pos"][0] = nx
            f["pos"][1] = nd
            f["heading_deg"] = math.degrees(math.atan2(vd, vx)) % 360.0

    def _maybe_spawn_fish(self, events):
        spawn_ticks = int(self.t["fish_spawn_ticks"])
        if self.phase_tick < spawn_ticks or self.phase_tick % spawn_ticks != 0:
            return
        if len(self.fish) >= int(self.t["fish_max"]):
            return
        clearance = float(self.t["fish_spawn_clearance"])
        weights_cfg = self.t["fish_weights"]
        spawn_x = sorted(self.t["fish_spawn_x"])
        spawn_depths = self.t["fish_spawn_depths"]
        live_pos = [f["pos"] for f in self.fish]

        avail_by_species = {}
        for kind in sorted(weights_cfg.keys()):
            pts = []
            for x in spawn_x:
                for d in sorted(spawn_depths[kind]):
                    pt = (float(x), float(d))
                    if all(math.dist(pt, lp) > clearance for lp in live_pos):
                        pts.append(pt)
            if pts:
                avail_by_species[kind] = pts
        if not avail_by_species:
            return
        rng = self.rng.get("fish_spawn")
        kind = self._pick_weighted_species(rng, avail_by_species, weights_cfg)
        pt = rng.choice(avail_by_species[kind])
        heading = rng.uniform(0.0, 360.0)
        fid = self.ids.new("F")
        self.fish.append({
            "id": fid,
            "kind": kind,
            "pos": [pt[0], pt[1]],
            "heading_deg": heading,
            "age_ticks": 0,
        })
        events.append(("fish_spawned", {"id": fid, "kind": kind, "pos": [pt[0], pt[1]]}))

    # --- Hái & Bắt cá ---------------------------------------------------------
    def _try_harvest(self, events):
        radius = self.t["interact_radius"]
        best = None
        best_key = None
        for n in self.nodes:
            if n["regrow_ticks"] != 0:
                continue
            dist = math.dist(self.pos, n["pos"])
            if dist <= radius:
                key = (dist, id_key(n["id"]))
                if best_key is None or key < best_key:
                    best_key = key
                    best = n
        if best is None:
            return
        req = int(self.t["node_yield"])
        free = int(self.t["hold_capacity"]) - len(self.hold)
        if free >= req:
            self._add_to_hold(best["kind"], req)
            best["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
            events.append(("gather", {"node_id": best["id"], "kind": best["kind"], "amount": req}))
        else:
            events.append(("hold_full", {
                "action": "gather",
                "node_id": best["id"],
                "required": req,
                "free": free,
            }))

    def _try_catch(self, events):
        radius = self.t["catch_radius"]
        best_idx = None
        best_key = None
        for idx, f in enumerate(self.fish):
            dist = math.dist(self.pos, f["pos"])
            if dist <= radius:
                key = (dist, id_key(f["id"]))
                if best_key is None or key < best_key:
                    best_key = key
                    best_idx = idx
        if best_idx is None:
            return
        fish = self.fish[best_idx]
        yld = int(self.t["fish_yield"][fish["kind"]])
        free = int(self.t["hold_capacity"]) - len(self.hold)
        if free >= yld:
            self._add_to_hold(fish["kind"], yld)
            self.fish.pop(best_idx)
            self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
            events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "yield": yld}))
        else:
            events.append(("hold_full", {
                "action": "catch",
                "fish_id": fish["id"],
                "required": yld,
                "free": free,
            }))

    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
