"""Bot tất định cho soak (Phase 4): chơi gather → quan → shop chỉ dựa trên snapshot hiện tại.

Không dùng ngẫu nhiên, không đọc đồng hồ: cùng seed + cùng luật → cùng chuỗi input → cùng kết quả.
- gather: hái nút / bắt cá có trong kế hoạch Ngày, nổi lên khi oxy < 40%, đầy giỏ hoặc sắp hết giờ thì về bến cập.
- quan: có món trên tay → phục vụ; bếp chín → nhấc; có đơn đã giữ hàng + bếp trống → nấu.
- shop: mua nâng cấp rẻ nhất còn mua được (oxygen trước hp), bước sau bấm shop_done.
"""

import math

from .inputs import InputState, normalize

_EMPTY = {"interact": False, "catch": False, "pause": False, "shop_done": False, "attack": False, "photo": False}


def _state(move=(0.0, 0.0), press=(), buy=None):
    held = dict(_EMPTY)
    for b in press:
        held[b] = True
    return InputState(normalize(move), held, set(press), buy=buy)


def _toward(pos, target, stop=0.15):
    dx, dy = target[0] - pos[0], target[1] - pos[1]
    if math.hypot(dx, dy) <= stop:
        return (0.0, 0.0)
    return (dx, dy)


def _id_key(ident):
    head = ident.rstrip("0123456789")
    tail = ident[len(head):]
    return head, int(tail) if tail else -1


class SoakBot:
    def __init__(self, tuning):
        self.t = tuning
        self.g = tuning["gather"]
        self.q = tuning["quan"]
        self.menu = tuning["menu"]
        self._shop_bought_day = None

    # ------------------------------------------------------------------ gather
    def _gather(self, s):
        p = s["player"]
        pos = p["pos"]
        dock = self.g["dock_pos"]
        hold_n = s.get("hold_count", len(s.get("hold", [])))
        cap = s.get("hold_capacity", self.g["hold_capacity"])
        speed = self.g["swim_speed"]
        back_ticks = math.dist(pos, dock) / speed * 60 + 180
        want = set((s.get("day_plan") or {}).get("ingredients", {}))

        if hold_n >= cap or s["time_left_ticks"] <= back_ticks:
            if math.dist(pos, dock) <= self.g["dock_radius"] - 0.5:
                return _state(press=("interact",))
            return _state(_toward(pos, dock))

        o_frac = p["oxygen_ticks"] / max(1, p["oxygen_max_ticks"])
        if not p.get("at_surface") and o_frac < 0.4:
            return _state((0.0, -1.0))

        targets = []
        far_from_dock = self.g["dock_radius"] + 1.0
        for n in s.get("nodes", []):
            if n.get("ready") and (not want or n["kind"] in want) and math.dist(n["pos"], dock) > far_from_dock:
                targets.append((math.dist(pos, n["pos"]), 0, _id_key(n["id"]), n["pos"], "interact", self.g["interact_radius"]))
        if o_frac > 0.6:
            for f in s.get("fish", []):
                if f["kind"] in want and f["pos"][1] <= 9:
                    targets.append((math.dist(pos, f["pos"]), 1, _id_key(f["id"]), f["pos"], "catch", self.g["catch_radius"]))
        if not targets:
            return _state(_toward(pos, [pos[0], 0.0]))  # chờ ở mặt nước cho oxy hồi / nút mọc lại
        dist, _, _, tpos, action, radius = min(targets)
        if dist <= radius * 0.8:
            return _state(_toward(pos, tpos), press=(action,))
        return _state(_toward(pos, tpos))

    # ------------------------------------------------------------------ quan
    def _quan(self, s):
        pos = s["player"]["pos"]
        stoves = {st["id"]: st for st in s.get("stoves", [])}
        tables = {tb["id"]: tb for tb in s.get("tables", [])}
        customers = s.get("customers", [])
        hand = s.get("hand")
        target = None
        if hand is not None:
            c = next((c for c in customers if c["id"] == hand["order_id"]), None)
            if c is not None and c.get("state") == "waiting":
                target = tables[c["table_id"]]["pos"]
        if target is None and hand is None:
            ready = [st for st in stoves.values() if st["state"] == "ready"]
            if ready:
                target = min(ready, key=lambda st: (math.dist(pos, st["pos"]), _id_key(st["id"])))["pos"]
        if target is None:
            waiting = [c for c in customers if c.get("order_status") == "reserved"]
            idle = [st for st in stoves.values() if st["state"] == "idle"]
            if waiting and idle and hand is None:
                target = min(idle, key=lambda st: (math.dist(pos, st["pos"]), _id_key(st["id"])))["pos"]
        if target is None:
            return _state(_toward(pos, self.q["start_pos"]))
        if math.dist(pos, target) <= 0.4:
            return _state(press=("interact",))
        return _state(_toward(pos, target))

    # ------------------------------------------------------------------ shop
    def _shop(self, s):
        day = s.get("day")
        if self._shop_bought_day != day:
            self._shop_bought_day = day
            upgrades = s.get("upgrades", {})
            for name in ("oxygen", "hp"):
                tiers = self.t["shop"]["upgrades"][name]
                nxt = next((u for u in tiers if u["level"] == upgrades.get(name, 0) + 1), None)
                if nxt is not None and s["money"] >= nxt["price"]:
                    return _state(buy=name)
            return _state()
        return _state(press=("shop_done",))

    def act(self, snapshot):
        phase = snapshot["phase"]
        if phase == "gather":
            return self._gather(snapshot)
        if phase == "quan":
            return self._quan(snapshot)
        return self._shop(snapshot)
