"""Shop cuối Ngày (Contract v1.1 & v1.2): mua nâng cấp oxygen / hp, đóng bằng shop_done hoặc tự đóng sau 600 tick.

Ở v1.2: `stock` dư là mảng cá thể `{id, kind, fresh}` sắp theo `id`; hàng thô ở Shop KHÔNG hao tươi.
"""

from ..ids import sort_by_id
from ..inventory import is_v12, serialize_item


class ShopSim:
    mode = "day"
    phase = "shop"

    def __init__(self, tuning, stock, money, earned, reputation, upgrades, contract_version="1.1"):
        self.tuning = tuning
        self.shop_cfg = tuning["shop"]
        self.v12 = is_v12(contract_version)
        if self.v12 or isinstance(stock, list):
            self.stock = [dict(it) for it in sort_by_id(stock)]
        else:
            self.stock = {k: v for k, v in sorted(stock.items()) if v > 0}
        self.money = money
        self.earned = earned
        self.reputation = reputation
        self.upgrades = upgrades  # dict chung xuyên ngày (cập nhật ngay khi mua)
        self.time_left_ticks = int(self.shop_cfg["max_ticks"])
        self.done = False
        self.reason = None

    def snapshot(self) -> dict:
        if isinstance(self.stock, list):
            return {"stock": [serialize_item(it) for it in sort_by_id(self.stock)]}
        return {
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        # 1. Xử lý tối đa một `buy` trước cạnh `shop_done`, kể cả bước cuối
        if inp.buy is not None:
            action = inp.buy
            shop_upgs = self.shop_cfg.get("upgrades", {})
            if action not in shop_upgs:
                events.append(("buy_failed", {"action": action, "reason": "unknown"}))
            else:
                tiers = shop_upgs[action]
                cur_lvl = int(self.upgrades.get(action, 0))
                next_tier = next((u for u in tiers if u["level"] == cur_lvl + 1), None)
                if next_tier is None:
                    events.append(("buy_failed", {"action": action, "reason": "max_level"}))
                elif self.money < next_tier["price"]:
                    events.append(("buy_failed", {"action": action, "reason": "funds"}))
                else:
                    self.money -= next_tier["price"]
                    self.upgrades[action] = next_tier["level"]
                    events.append(("bought", {
                        "upgrade": action,
                        "level": next_tier["level"],
                        "price": next_tier["price"],
                        "money": self.money,
                    }))

        # 2. Cạnh `shop_done` (ưu tiên hơn hết giờ ở bước cuối)
        if inp.pressed("shop_done"):
            self.done = True
            self.reason = "done"
            events.append(("shop_end", {"reason": "done"}))
            return events

        # 3. Tự đóng khi hết giờ
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("shop_end", {"reason": "time"}))

        return events
