"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
    Đã làm: lịch khách, chọn món, giữ chỗ, no_dish và xử lý khách bỏ đi.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
    Đã làm: nấu, lấy món, phục vụ, thanh toán và dọn đơn khi đóng ca.
"""

from math import dist, floor

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None,
                 allowed_dishes=None, money=0, earned=0, reputation=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.allowed_dishes = set(allowed_dishes) if allowed_dishes is not None else None
        self.rng = streams
        self.ids = ids
        self.phase_tick = 0
        self.random_customers = scenario.get("random_customers", True)
        self.patience_ticks = round(t["patience_s"] * TICK)
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = (
            reputation if reputation is not None else scenario.get("reputation", t["reputation_initial"])
        )
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        # TODO(nhóm): khách dựng sẵn từ scenario (customers[]) và suy ra giữ chỗ (reserved).
        self.customers = []
        for customer in scenario.get("customers", []):
            recipe = self.menu.get(customer.get("dish_id"), {}).get("recipe", {})
            reserved = recipe if customer.get("order_status") == "reserved" else {}
            self.customers.append(dict(customer, reserved=customer.get("reserved", reserved).copy()))
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = money
        self.earned = earned
        self.shift_earned = 0
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": list(self.pos), "vel": list(self.vel)},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        # TODO(nhóm): giảm kiên nhẫn / nấu / ăn; bếp chín -> ready; xử lý khách theo thứ tự PRD-0 mục F.
        # Bước 1: chỉ tăng ready_ticks cho bếp đã ready từ đầu bước.
        for stove in self.stoves:
            if stove["state"] == "cooking":
                stove["cook_ticks_left"] = max(0, stove["cook_ticks_left"] - 1)
            elif stove["state"] == "ready":
                stove["ready_ticks"] += 1
        for customer in self.customers:
            if customer.get("state") == "waiting":
                remaining = customer.get("patience_ticks_left", self.patience_ticks)
                customer["patience_ticks_left"] = max(0, remaining - 1)
            elif customer.get("state") == "eating":
                customer["eat_ticks_left"] = max(0, customer["eat_ticks_left"] - 1)

        # Bước 2: bếp đã được sắp theo ID trong _merge. Phase 1 không có cháy món.
        for stove in self.stoves:
            if stove["state"] == "cooking" and stove["cook_ticks_left"] == 0:
                stove.update(state="ready", ready_ticks=0)
                events.append(("dish_ready", self._stove_event(stove)))

        self._move(inp)
        # TODO(nhóm): tối đa MỘT interact, chọn đối tượng theo (khoảng cách, bếp trước bàn, id).
        if inp.pressed("interact"):
            self._interact(events)
        # TODO(nhóm): thanh toán và dọn khách trước khi xét lượt khách mới.
        closing = self.time_left_ticks == 0
        self._settle_customers(closing, events)
        if closing:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events
        # TODO(nhóm): khách mới theo lịch (first_customer_tick, customer_interval_s), no_dish.
        # Đã làm trong _arrive_customer; chỉ xét khi ca còn giờ.
        self._arrive_customer(events)
        return events

    def _interact(self, events):
        targets = [
            (dist(self.pos, target["pos"]), kind, id_key(target["id"]), target)
            for kind, group in enumerate((self.stoves, self.tables))
            for target in group
        ]
        if not targets:
            return
        distance, kind, _, target = min(targets, key=lambda candidate: candidate[:3])
        if distance > self.t["interact_radius"]:
            return
        if kind == 0:
            self._interact_stove(target, events)
        else:
            self._serve(target, events)

    def _interact_stove(self, stove, events):
        if stove["state"] == "ready" and self.hand is None:
            self.hand = stove["dish"]
            events.append(("dish_picked", self._stove_event(stove)))
            self._clear_stove(stove)
        elif stove["state"] == "idle":
            orders = (c for c in self.customers if c.get("order_status") == "reserved")
            customer = min(orders, key=lambda c: (c["order_tick"], id_key(c["table_id"])), default=None)
            if customer is None:
                return
            dish_id = customer["dish_id"]
            dish = self.menu[dish_id]
            reserved = customer["reserved"]
            for kind, count in reserved.items():
                self.stock[kind] -= count
            customer.update(order_status="assigned", reserved={}, base_price=dish["price"])
            stove.update(
                state="cooking",
                dish={"order_id": customer["id"], "dish_id": dish_id, "base_price": dish["price"]},
                cook_ticks_left=round(dish["cook_s"] * TICK),
                ready_ticks=0,
            )
            items = [kind for kind in sorted(reserved) for _ in range(reserved[kind])]
            events.append(("cook_started", dict(self._stove_event(stove), items=items, base_price=dish["price"])))

    def _serve(self, table, events):
        if self.hand is None:
            return
        customer = next((c for c in self.customers if c["table_id"] == table["id"]), None)
        if customer is None or customer.get("state") != "waiting" or customer["id"] != self.hand["order_id"]:
            return
        remaining = customer["patience_ticks_left"]
        price = self.hand["base_price"]
        tip = 0
        if remaining / self.patience_ticks >= self.t["tip_min_patience_ratio"]:
            tip = floor(price * self.t["tip_rate"])
        customer.update(
            state="eating", order_status="served", eat_ticks_left=round(self.t["eat_s"] * TICK),
            base_price=price, tip=tip,
        )
        events.append(("served", {
            "order_id": customer["id"], "table_id": table["id"], "dish_id": self.hand["dish_id"],
            "patience_ticks_left": remaining, "base_price": price, "tip": tip,
        }))
        self.hand = None

    def _settle_customers(self, closing, events):
        for customer in sort_by_id(self.customers, key=lambda c: c["table_id"]):
            state = customer.get("state")
            if state == "eating" and (customer["eat_ticks_left"] == 0 or closing):
                reason = "finished_eating" if customer["eat_ticks_left"] == 0 else "closing"
                self._pay(customer, reason, events)
            elif state == "waiting" and (closing or customer["patience_ticks_left"] == 0):
                if not closing:
                    self._change_reputation(self.t["left_reputation_delta"])
                events.append(("customer_left", {
                    "order_id": customer["id"], "table_id": customer["table_id"],
                    "reason": "closing" if closing else "patience", "reputation": self.reputation,
                }))
            else:
                continue
            self._remove_customer(customer)

    def _pay(self, customer, reason, events):
        price, tip = customer["base_price"], customer["tip"]
        amount = price + tip
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if tip > 0:
            self._change_reputation(self.t["tip_reputation"])
        events.append(("paid", {
            "order_id": customer["id"], "table_id": customer["table_id"], "base_price": price,
            "tip": tip, "amount": amount, "reason": reason,
        }))

    def _change_reputation(self, delta):
        self.reputation = min(self.t["reputation_max"], max(self.t["reputation_min"], self.reputation + delta))

    def _remove_customer(self, customer):
        order_id = customer["id"]
        if self.hand is not None and self.hand["order_id"] == order_id:
            self.hand = None
        for stove in self.stoves:
            if stove["dish"] is not None and stove["dish"]["order_id"] == order_id:
                self._clear_stove(stove)
        # reserved nằm trên khách, nên xóa khách tự nhả phần giữ.
        self.customers.remove(customer)

    @staticmethod
    def _clear_stove(stove):
        stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)

    @staticmethod
    def _stove_event(stove):
        dish = stove["dish"]
        return {"stove_id": stove["id"], "order_id": dish["order_id"], "dish_id": dish["dish_id"]}

    def _arrive_customer(self, events):
        elapsed = self.phase_tick - self.t["first_customer_tick"]
        interval = round(self.t["customer_interval_s"] * TICK)
        if not self.random_customers or elapsed < 0 or elapsed % interval != 0:
            return

        occupied = {customer["table_id"] for customer in self.customers}
        table = next((table for table in self.tables if table["id"] not in occupied), None)
        if table is None:
            return

        available = self.stock.copy()
        for customer in self.customers:
            for kind, count in customer["reserved"].items():
                available[kind] = available.get(kind, 0) - count

        candidates = [
            dish_id for dish_id, dish in sorted(self.menu.items())
            if (self.allowed_dishes is None or dish_id in self.allowed_dishes)
            and all(available.get(kind, 0) >= count for kind, count in dish["recipe"].items())
        ]
        if not candidates:
            events.append(("no_dish", {}))
            return

        dish_id = self.rng.get("customer_dish").choice(candidates)
        dish = self.menu[dish_id]
        order_id = self.ids.new("C")
        self.customers.append({
            "id": order_id,
            "table_id": table["id"],
            "dish_id": dish_id,
            "order_tick": self.phase_tick,
            "state": "waiting",
            "patience_ticks_left": self.patience_ticks,
            "eat_ticks_left": 0,
            "order_status": "reserved",
            "reserved": dish["recipe"].copy(),
            "base_price": dish["price"],
            "tip": 0,
        })
        events.append(("customer_arrived", {
            "order_id": order_id, "table_id": table["id"], "dish_id": dish_id,
        }))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
