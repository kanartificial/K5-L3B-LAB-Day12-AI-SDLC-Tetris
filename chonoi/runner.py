"""Vòng tick (Contract B v1.0 & §4.2–4.5 v1.1): hỗ trợ gather, quan, day và pause/resumed.

Thứ tự ghi: event tick 0 (nếu có, vd mode day) -> snapshot tick 0 -> với mỗi bước:
sự kiện (theo thứ tự xử lý) rồi snapshot (nếu tới lượt, đổi pha, mua nâng cấp hoặc kết thúc) -> dòng 'end'.
Mỗi tick tối đa một snapshot.
"""

import copy
import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim
from .sim.shop import ShopSim


def build_sim(mode, tuning, scenario, seed, inventory):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory)


def _common(sim, tick, sim_tick, phase_tick, tuning, state, mode_override=None):
    mult = tuning["score"]["reputation_multiplier"]
    return {
        "type": "snapshot", "tick": tick, "sim_tick": sim_tick,
        "mode": mode_override or sim.mode, "phase": sim.phase,
        "phase_tick": phase_tick, "state": state, "time_left_ticks": sim.time_left_ticks,
        "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
        "score": sim.earned + mult * math.floor(sim.reputation),
    }


class Session:
    """Một lượt chơi độc lập (`gather` hoặc `quan`) với hỗ trợ `pause`/`resumed`."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory)
        self.tick = 0
        self.sim_tick = 0
        self.phase_tick = 0
        self.paused = False
        self.just_changed_phase = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def initial_events(self) -> list:
        return []

    def snapshot(self) -> dict:
        state = "finished" if self.sim.done else ("paused" if self.paused else "playing")
        s = _common(self.sim, self.tick, self.sim_tick, self.phase_tick, self.tuning, state)
        s.update(self.sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước ngoài với `inp`; trả các dòng event (tick = k + 1)."""
        self.just_changed_phase = False
        rows = []
        if inp.pressed("pause"):
            if not self.paused:
                self.paused = True
                self.tick += 1
                return [{"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": "paused", "data": {}}]
            self.paused = False
            rows.append({"type": "event", "tick": self.tick + 1, "phase": self.sim.phase, "name": "resumed", "data": {}})
        elif self.paused:
            self.tick += 1
            return []

        events = self.sim.step(inp)
        self.tick += 1
        self.sim_tick += 1
        self.phase_tick += 1
        for name, data in events:
            rows.append({"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": name, "data": data})
        return rows

    def end_row(self) -> dict:
        sim = self.sim
        state = "finished" if sim.done else ("paused" if self.paused else "playing")
        score = _common(sim, self.tick, self.sim_tick, self.phase_tick, self.tuning, state)["score"]
        return {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
                "state": state,
                "reason": sim.reason if sim.done else "tick_limit",
                "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score}

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


class DaySession:
    """Chế độ `--mode day --days 1..5`: vòng gather -> quan -> shop -> Ngày kế + pause."""

    def __init__(self, tuning, scenario, seed, days=1):
        self.mode = "day"
        self.tuning = tuning
        self.scenario = scenario or {"day": {}, "gather": {}, "quan": {}}
        self.streams = Streams(seed)
        self.days_target = int(days)
        self.days_completed = 0
        self.tick = 0
        self.sim_tick = 0
        self.phase_tick = 0
        self.paused = False
        self.done = False
        self.reason = None
        self.just_changed_phase = False

        day_sc = self.scenario.get("day", {})
        self.money = int(day_sc.get("money", 0))
        self.earned = int(day_sc.get("earned", 0))
        self.reputation = float(day_sc.get("reputation", tuning["quan"]["reputation_initial"]))
        self.upgrades = {k: int(v) for k, v in day_sc.get("upgrades", {}).items() if int(v) > 0}
        self.active_upgrades = dict(self.upgrades)

        # Kế hoạch D1..D5 (kèm ghi đè từ scenario.day.day_plan nếu có)
        self.day_plans = {}
        for entry in tuning["day_plan"]:
            self.day_plans[entry["day"]] = {
                "day": entry["day"],
                "dishes": dict(entry["dishes"]),
                "ingredients": dict(entry["ingredients"]),
            }
        menu = tuning["menu"]
        for entry in day_sc.get("day_plan", []):
            dnum = entry["day"]
            dishes = dict(entry["dishes"])
            ingredients = {}
            for dish_id, qty in dishes.items():
                for kind, cnt in menu[dish_id]["recipe"].items():
                    ingredients[kind] = ingredients.get(kind, 0) + cnt * qty
            self.day_plans[dnum] = {"day": dnum, "dishes": dishes, "ingredients": ingredients}

        self.day = 1
        self.sim = None
        self._init_events = self._start_day(1, tick=0)

    def _ev(self, tick, phase, day, name, data):
        return {"type": "event", "tick": tick, "phase": phase, "day": day, "name": name, "data": data}

    def _plan_payload(self, day_num):
        p = self.day_plans[day_num]
        return {"dishes": dict(p["dishes"]), "ingredients": dict(p["ingredients"])}

    def _start_day(self, day_num: int, tick: int) -> list:
        self.day = day_num
        self.active_upgrades = dict(self.upgrades)
        self.phase_tick = 0
        g_sc = copy.deepcopy(self.scenario.get("gather", {}))
        self.sim = GatherSim(
            self.tuning, g_sc, self.streams, IdAllocator(),
            day=day_num, active_upgrades=self.active_upgrades,
            money=self.money, earned=self.earned, reputation=self.reputation,
        )
        return [
            self._ev(tick, "gather", day_num, "day_start", {}),
            self._ev(tick, "gather", day_num, "day_plan", self._plan_payload(day_num)),
            self._ev(tick, "gather", day_num, "phase_start", {}),
        ]

    def initial_events(self) -> list:
        return list(self._init_events)

    def snapshot(self) -> dict:
        state = "finished" if self.done else ("paused" if self.paused else "playing")
        s = _common(self.sim, self.tick, self.sim_tick, self.phase_tick, self.tuning, state, mode_override="day")
        s["day"] = self.day
        s["day_plan"] = self._plan_payload(self.day)
        s["upgrades"] = dict(self.upgrades)
        s["active_upgrades"] = dict(self.active_upgrades)
        s.update(self.sim.snapshot())
        return s

    def step(self, inp) -> list:
        self.just_changed_phase = False
        rows = []
        cur_phase = self.sim.phase
        cur_day = self.day

        if inp.pressed("pause"):
            if not self.paused:
                self.paused = True
                self.tick += 1
                return [self._ev(self.tick, cur_phase, cur_day, "paused", {})]
            self.paused = False
            rows.append(self._ev(self.tick + 1, cur_phase, cur_day, "resumed", {}))
        elif self.paused:
            self.tick += 1
            return []

        events = self.sim.step(inp)
        self.tick += 1
        self.sim_tick += 1
        self.phase_tick += 1
        for name, data in events:
            rows.append(self._ev(self.tick, cur_phase, cur_day, name, data))

        # Đồng bộ tài nguyên chung
        self.money = self.sim.money
        self.earned = self.sim.earned
        self.reputation = self.sim.reputation

        # Chuyển pha ngay cùng tick khi pha hiện tại kết thúc (mục 4.5)
        if self.sim.done:
            if cur_phase == "gather":
                inv = self.sim.inventory_items()
                q_sc = copy.deepcopy(self.scenario.get("quan", {}))
                allowed = set(self.day_plans[self.day]["dishes"].keys())
                self.sim = QuanSim(
                    self.tuning, q_sc, self.streams, IdAllocator(),
                    inventory=inv, allowed_dishes=allowed,
                    money=self.money, earned=self.earned, reputation=self.reputation,
                )
                self.phase_tick = 0
                self.just_changed_phase = True
                rows.append(self._ev(self.tick, "quan", self.day, "phase_start", {}))
            elif cur_phase == "quan":
                leftover = dict(self.sim.stock)
                self.sim = ShopSim(
                    self.tuning, leftover, self.money, self.earned, self.reputation, self.upgrades,
                )
                self.phase_tick = 0
                self.just_changed_phase = True
                rows.append(self._ev(self.tick, "shop", self.day, "phase_start", {}))
            elif cur_phase == "shop":
                self.days_completed += 1
                if self.days_completed >= self.days_target:
                    self.done = True
                    self.reason = "days_complete"
                else:
                    self.just_changed_phase = True
                    rows.extend(self._start_day(self.day + 1, tick=self.tick))
        return rows

    def end_row(self) -> dict:
        state = "finished" if self.done else ("paused" if self.paused else "playing")
        score = _common(self.sim, self.tick, self.sim_tick, self.phase_tick, self.tuning, state, mode_override="day")["score"]
        return {
            "type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": "day",
            "state": state,
            "reason": self.reason if self.done else "tick_limit",
            "days_completed": self.days_completed,
            "money": self.money, "earned": self.earned, "reputation": self.reputation, "score": score,
        }

    def write_inventory_if_done(self, inventory_out):
        pass


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every,
        inventory=None, inventory_out=None, days=1):
    if mode == "day":
        sess = DaySession(tuning, scenario, seed, days=days)
    else:
        sess = Session(mode, tuning, scenario, seed, inventory)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        for row in sess.initial_events():
            w.write(row)
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario & phát event tick 0
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            step_rows = sess.step(inp)
            for row in step_rows:
                w.write(row)
            has_bought = any(r["name"] == "bought" for r in step_rows)
            if sess.tick % snapshot_every == 0 or sess.done or sess.just_changed_phase or has_bought:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
