"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
    Đã làm: lịch khách, chọn món, giữ chỗ, no_dish và xử lý khách bỏ đi.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
    Đã làm: nấu, lấy món, phục vụ, thanh toán và dọn đơn khi đóng ca.
"""

from collections import Counter
from fractions import Fraction
from math import dist, floor, isfinite

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import KINDS_V11, validate_items
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
        freshness = tuning.get("freshness")
        self.freshness = freshness is not None
        stock = inventory if inventory is not None else scenario.get("stock", [] if self.freshness else {})
        if self.freshness:
            self.initial_freshness = Fraction(str(freshness["initial"]))
            self.spoiled_below = Fraction(str(freshness["spoiled_below"]))
            self.decay = Fraction(str(freshness["quan_decay_per_s"])) / tuning["tick_hz"]
            self.stock = self._load_fresh_stock(stock, freshness["initial"])
        else:
            self.stock = dict(stock)
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
            dish_id = customer.get("dish_id")
            if not isinstance(dish_id, str) or dish_id not in self.menu:
                raise BadInput(f"đơn {customer['id']} có dish_id không hợp lệ")
            recipe = self.menu[dish_id]["recipe"]
            reserved = recipe if customer.get("order_status") == "reserved" else {}
            if self.freshness:
                reserved = customer.get("reserved")
                if "reserved" in customer:
                    if not isinstance(reserved, list) or any(not isinstance(i, str) for i in reserved):
                        raise BadInput("reserved phải là mảng ID nguyên liệu")
                    reserved = list(reserved)
            else:
                reserved = validate_items(customer.get("reserved", reserved))
            self.customers.append(dict(customer, reserved=reserved))
        self._validate_orders()
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
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _validate_orders(self):
        customers = {customer["id"]: customer for customer in self.customers}
        for stove in self.stoves:
            state = stove["state"]
            if state not in ("idle", "cooking", "ready") or (state == "idle") != (stove["dish"] is None):
                raise BadInput(f"trạng thái và món của bếp {stove['id']} mâu thuẫn")
            for key in ("cook_ticks_left", "ready_ticks"):
                if type(stove[key]) is not int or stove[key] < 0:
                    raise BadInput(f"bếp {stove['id']} có {key} không hợp lệ")
        dishes = [stove["dish"] for stove in self.stoves if stove["dish"] is not None]
        if self.hand is not None:
            dishes.append(self.hand)
        assigned = set()
        for dish in dishes:
            if not isinstance(dish, dict) or not isinstance(dish.get("order_id"), str):
                raise BadInput("món trên bếp/tay phải có order_id")
            order_id = dish["order_id"]
            customer = customers.get(order_id)
            if (customer is None or customer.get("order_status") != "assigned"
                    or order_id in assigned or dish.get("dish_id") != customer.get("dish_id")
                    or type(dish.get("base_price")) is not int or dish["base_price"] <= 0):
                raise BadInput(f"món trên bếp/tay mâu thuẫn với đơn {order_id}")
            assigned.add(order_id)

        available = {} if self.freshness else self.stock.copy()
        for order_id, customer in customers.items():
            dish_id = customer.get("dish_id")
            if self.allowed_dishes is not None and dish_id not in self.allowed_dishes:
                raise BadInput(f"món {dish_id} của đơn {order_id} ngoài kế hoạch Ngày")
            status = customer.get("order_status")
            if status == "assigned" and order_id not in assigned:
                raise BadInput(f"đơn assigned {order_id} phải có đúng một món trên bếp hoặc tay")
            if customer.get("state") == "eating" and any(
                type(customer.get(key)) is not int or customer[key] < 0
                for key in ("base_price", "tip", "eat_ticks_left")
            ):
                raise BadInput(f"khách eating {order_id} cần base_price, tip và eat_ticks_left hợp lệ")
            reserved = customer["reserved"]
            expected = self.menu[dish_id]["recipe"] if status == "reserved" else {}
            if self.freshness:
                continue
            if reserved != expected:
                raise BadInput(f"phần giữ của đơn {order_id} không khớp trạng thái hoặc công thức")
            for kind, count in reserved.items():
                available[kind] = available.get(kind, 0) - count
                if available[kind] < 0:
                    raise BadInput(f"phần giữ của đơn {order_id} vượt kho {kind}")
        if self.freshness:
            self._validate_fresh_reservations()

    @staticmethod
    def _load_fresh_stock(stock, initial):
        if not isinstance(stock, list):
            raise BadInput("kho Quán v1.2 phải là mảng cá thể")
        by_id = {}
        for item in stock:
            if not isinstance(item, dict) or set(item) != {"id", "kind", "fresh"}:
                raise BadInput("cá thể kho cần đúng id, kind, fresh")
            item_id, fresh = item["id"], item["fresh"]
            if not isinstance(item_id, str) or not item_id or item_id in by_id:
                raise BadInput("ID cá thể kho phải khác rỗng và duy nhất")
            if (item["kind"] not in KINDS_V11 or type(fresh) not in (int, float)
                    or not 0 <= fresh <= initial or not isfinite(fresh)):
                raise BadInput(f"kind hoặc fresh không hợp lệ cho {item_id}")
            by_id[item_id] = dict(item, fresh=Fraction(str(fresh)))
        return by_id

    def _validate_fresh_reservations(self):
        claimed = set()
        implicit = []
        for customer in self.customers:
            reserved = customer["reserved"]
            if customer.get("order_status") != "reserved":
                if reserved:
                    raise BadInput(f"đơn {customer['id']} không được giữ nguyên liệu")
                customer["reserved"] = []
                continue
            if type(customer.get("order_tick")) is not int or customer["order_tick"] < 0:
                raise BadInput(f"order_tick không hợp lệ cho đơn {customer['id']}")
            if reserved is None:
                implicit.append(customer)
                continue
            kinds = Counter()
            for item_id in reserved:
                item = self.stock.get(item_id)
                if item is None or item_id in claimed or item["fresh"] < self.spoiled_below:
                    raise BadInput(f"phần giữ của đơn {customer['id']} có ID thiếu, trùng hoặc đã ươn: {item_id}")
                claimed.add(item_id)
                kinds[item["kind"]] += 1
            if kinds != self.menu[customer["dish_id"]]["recipe"]:
                raise BadInput(f"phần giữ của đơn {customer['id']} không khớp công thức")
        for customer in sorted(implicit, key=self._order_key):
            picked = self._select_fresh(self.menu[customer["dish_id"]]["recipe"], claimed)
            if picked is None:
                raise BadInput(f"phần giữ của đơn {customer['id']} vượt kho khả dụng")
            customer["reserved"] = picked
            claimed.update(picked)

    @staticmethod
    def _order_key(customer):
        return customer["order_tick"], id_key(customer["table_id"])

    def _select_fresh(self, recipe, claimed):
        pool = sort_by_id(self.stock.values())
        pool.sort(key=lambda item: item["fresh"], reverse=True)
        picked = []
        for kind, count in sorted(recipe.items()):
            matches = [item["id"] for item in pool if item["kind"] == kind
                       and item["id"] not in claimed and item["fresh"] >= self.spoiled_below]
            if len(matches) < count:
                return None
            picked.extend(matches[:count])
        return picked

    def _age_stock(self, events):
        spoiled = set()
        for item in sort_by_id(self.stock.values()):
            previous = item["fresh"]
            item["fresh"] = max(Fraction(0), previous - self.decay)
            if previous >= self.spoiled_below > item["fresh"]:
                spoiled.add(item["id"])
                events.append(("spoiled", {"item_id": item["id"], "kind": item["kind"], "location": "stock"}))
        if not spoiled:
            return
        affected = [c for c in self.customers if spoiled.intersection(c["reserved"])]
        for customer in affected:
            customer["reserved"] = []
        claimed = {item_id for customer in self.customers for item_id in customer["reserved"]}
        for customer in sorted(affected, key=self._order_key):
            picked = self._select_fresh(self.menu[customer["dish_id"]]["recipe"], claimed)
            if picked is None:
                customer["order_status"] = "unfulfillable"
            else:
                customer["reserved"] = picked
                claimed.update(picked)

    @staticmethod
    def _item_payload(item):
        return dict(item, fresh=float(item["fresh"]))

    def stock_snapshot(self):
        if self.freshness:
            return [self._item_payload(item) for item in sort_by_id(self.stock.values())]
        return {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": list(self.pos), "vel": list(self.vel)},
            "stock": self.stock_snapshot(),
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

        if self.freshness:
            self._age_stock(events)
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
            customer = min(orders, key=self._order_key, default=None)
            if customer is None:
                return
            dish_id = customer["dish_id"]
            dish = self.menu[dish_id]
            reserved = customer["reserved"]
            price = dish["price"]
            if self.freshness:
                ingredients = [self.stock.pop(item_id) for item_id in reserved]
                total_freshness = sum(item["fresh"] for item in ingredients)
                price = floor(price * total_freshness / (len(ingredients) * self.initial_freshness))
                items = [self._item_payload(item) for item in ingredients]
                items.sort(key=lambda item: (item["kind"], id_key(item["id"])))
            else:
                for kind, count in reserved.items():
                    self.stock[kind] -= count
                items = [kind for kind in sorted(reserved) for _ in range(reserved[kind])]
            customer.update(order_status="assigned", reserved=[] if self.freshness else {}, base_price=price)
            stove.update(
                state="cooking",
                dish={"order_id": customer["id"], "dish_id": dish_id, "base_price": price},
                cook_ticks_left=round(dish["cook_s"] * TICK),
                ready_ticks=0,
            )
            events.append(("cook_started", dict(self._stove_event(stove), items=items, base_price=price)))

    def _serve(self, table, events):
        if self.hand is None:
            return
        customer = next((c for c in self.customers if c["table_id"] == table["id"]), None)
        if customer is None or customer.get("state") != "waiting" or customer["id"] != self.hand["order_id"]:
            return
        remaining = customer["patience_ticks_left"]
        price = self.hand["base_price"]
        tip = 0
        if self.freshness:
            if Fraction(remaining, self.patience_ticks) >= Fraction(str(self.t["tip_min_patience_ratio"])):
                tip = floor(price * Fraction(str(self.t["tip_rate"])))
        elif remaining / self.patience_ticks >= self.t["tip_min_patience_ratio"]:
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

        candidates = self._available_orders()
        if not candidates:
            events.append(("no_dish", {}))
            return

        dish_id = self.rng.get("customer_dish").choice(list(candidates))
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
            "reserved": candidates[dish_id],
            "base_price": dish["price"],
            "tip": 0,
        })
        events.append(("customer_arrived", {
            "order_id": order_id, "table_id": table["id"], "dish_id": dish_id,
        }))

    def _available_orders(self):
        if self.freshness:
            claimed = {item_id for customer in self.customers for item_id in customer["reserved"]}
        else:
            available = self.stock.copy()
            for customer in self.customers:
                for kind, count in customer["reserved"].items():
                    available[kind] = available.get(kind, 0) - count
        candidates = {}
        for dish_id, dish in sorted(self.menu.items()):
            if self.allowed_dishes is not None and dish_id not in self.allowed_dishes:
                continue
            recipe = dish["recipe"]
            if self.freshness:
                picked = self._select_fresh(recipe, claimed)
                if picked is not None:
                    candidates[dish_id] = picked
            elif all(available.get(kind, 0) >= count for kind, count in recipe.items()):
                candidates[dish_id] = recipe.copy()
        return candidates

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
