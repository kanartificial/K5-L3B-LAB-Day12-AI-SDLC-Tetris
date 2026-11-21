"""Nạp và kiểm scenario (Contract D v1.0 & §4.3 v1.1).

Trả về:
- Với mode `gather` hoặc `quan`: dict của khối tương ứng.
- Với mode `day`: dict `{"day": {...}, "gather": {...}, "quan": {...}}`.
"""

import json
import math

from .errors import BadInput
from .inventory import KINDS_V11, is_v12, validate_item_instances, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "monsters", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks", "attack_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
MONSTER_KEYS = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
MONSTER_STATES = {"patrol", "chase", "recoil", "stunned"}
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng ({axis} ∈ [{lo}, {hi}])")


def load_scenario(path, mode: str, tuning: dict, contract_version: str = "1.1") -> dict:
    if path is None:
        return {"day": {}, "gather": {}, "quan": {}} if mode == "day" else {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")

    if mode == "day":
        if not isinstance(data, dict) or not set(data) <= {"day", "gather", "quan"}:
            raise BadInput("scenario chế độ day chỉ nhận các khối 'day', 'gather', 'quan'")
        day_b = data.get("day", {})
        gather_b = data.get("gather", {})
        quan_b = data.get("quan", {})
        for name, blk in (("day", day_b), ("gather", gather_b), ("quan", quan_b)):
            if not isinstance(blk, dict):
                raise BadInput(f"khối {name} phải là object")
        _validate_day(day_b, tuning)
        if gather_b:
            _check_block_keys("gather", gather_b, GATHER_KEYS, tuning)
            _validate_gather(gather_b, tuning, upgrades=day_b.get("upgrades"), contract_version=contract_version)
        if quan_b:
            if "stock" in quan_b:
                raise BadInput("cấm khai quan.stock khi chạy --mode day")
            if "reputation" in quan_b:
                raise BadInput("cấm khai quan.reputation khi chạy --mode day")
            _check_block_keys("quan", quan_b, QUAN_KEYS, tuning)
            _validate_quan(quan_b, tuning, contract_version=contract_version)
        return {"day": day_b, "gather": gather_b, "quan": quan_b}

    if not isinstance(data, dict) or not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    block = data.get(mode, {})
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    _check_block_keys(mode, block, allowed, tuning)
    if mode == "gather":
        _validate_gather(block, tuning, contract_version=contract_version)
    else:
        _validate_quan(block, tuning, contract_version=contract_version)
    return block


def _check_block_keys(mode, block, allowed, tuning):
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")


def _validate_day(b, tuning):
    extra = set(b) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong day: {sorted(extra)}")
    money = b.get("money", 0)
    earned = b.get("earned", 0)
    if "money" in b:
        _nonneg_int("day.money", money)
    if "earned" in b:
        _nonneg_int("day.earned", earned)
    if money > earned:
        raise BadInput("day.money không được lớn hơn day.earned")
    if "reputation" in b:
        rep = b["reputation"]
        q = tuning["quan"]
        if not _num(rep) or not (q["reputation_min"] <= rep <= q["reputation_max"]):
            raise BadInput("day.reputation nằm ngoài dải hợp lệ")
    if "upgrades" in b:
        upg = b["upgrades"]
        if not isinstance(upg, dict):
            raise BadInput("day.upgrades phải là object")
        shop_upgs = tuning.get("shop", {}).get("upgrades", {})
        for k, lvl in upg.items():
            if k not in shop_upgs:
                raise BadInput(f"day.upgrades: nâng cấp không tồn tại {k}")
            max_lvl = max((u["level"] for u in shop_upgs[k]), default=0)
            if isinstance(lvl, bool) or not isinstance(lvl, int) or not (0 <= lvl <= max_lvl):
                raise BadInput(f"day.upgrades.{k}: cấp phải trong [0, {max_lvl}]")
    if "day_plan" in b:
        dp = b["day_plan"]
        if not isinstance(dp, list):
            raise BadInput("day.day_plan phải là mảng")
        seen_days = set()
        menu = tuning["menu"]
        for entry in dp:
            if not isinstance(entry, dict):
                raise BadInput("day.day_plan: phần tử phải là object")
            dnum = entry.get("day")
            if isinstance(dnum, bool) or not isinstance(dnum, int) or not (1 <= dnum <= 5) or dnum in seen_days:
                raise BadInput(f"day.day_plan: day phải là số nguyên duy nhất trong 1..5")
            seen_days.add(dnum)
            dishes = entry.get("dishes")
            if not isinstance(dishes, dict) or not dishes:
                raise BadInput(f"day.day_plan[{dnum}].dishes phải là object khác rỗng")
            calc = {}
            for dish_id, qty in dishes.items():
                if dish_id not in menu:
                    raise BadInput(f"day.day_plan[{dnum}]: món không tồn tại {dish_id}")
                if isinstance(qty, bool) or not isinstance(qty, int) or qty <= 0:
                    raise BadInput(f"day.day_plan[{dnum}].dishes.{dish_id}: số suất phải nguyên dương")
                for kind, cnt in menu[dish_id]["recipe"].items():
                    calc[kind] = calc.get(kind, 0) + cnt * qty
            if "ingredients" in entry:
                if entry["ingredients"] != calc:
                    raise BadInput(f"day.day_plan[{dnum}].ingredients không khớp tổng công thức")


def _effective_limits(tuning, upgrades=None):
    g = tuning["gather"]
    oxy_s = g["oxygen_max_s"]
    hp_max = g["hp_max"]
    if upgrades:
        shop_upgs = tuning.get("shop", {}).get("upgrades", {})
        if upgrades.get("oxygen", 0) > 0:
            for u in shop_upgs.get("oxygen", []):
                if u["level"] == upgrades["oxygen"]:
                    oxy_s = u["oxygen_max_s"]
        if upgrades.get("hp", 0) > 0:
            for u in shop_upgs.get("hp", []):
                if u["level"] == upgrades["hp"]:
                    hp_max = u["hp_max"]
    return int(round(oxy_s * 60)), int(hp_max)


def _validate_gather(b, tuning, upgrades=None, contract_version: str = "1.1"):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish", "monsters"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = b["hold"]
        if is_v12(contract_version):
            validate_item_instances(h)
        else:
            if not isinstance(h, list) or any(k not in KINDS_V11 for k in h):
                raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "attack_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax, hp_max = _effective_limits(tuning, upgrades)
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= hp_max):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] > g["choke_interval_ticks"] - 1:
            raise BadInput("player.zero_oxy_ticks vượt trần")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")
        if "age_ticks" in f:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
    species = g.get("monsters", {}).get("species", {})
    for m in b.get("monsters", []):
        extra_m = set(m) - MONSTER_KEYS
        if extra_m:
            raise BadInput(f"monsters.{m['id']}: trường lạ {sorted(extra_m)}")
        if m.get("kind") not in species:
            raise BadInput(f"monsters.{m['id']}: kind không hợp lệ")
        sp = species[m["kind"]]
        d_lo, d_hi = sp["depths"]
        _pos(f"monsters.{m['id']}.pos", m.get("pos"), bounds)
        if not (d_lo <= m["pos"][1] <= d_hi):
            raise BadInput(f"monsters.{m['id']}.pos ngoài dải độ sâu loài")
        wps = m.get("waypoints")
        if not isinstance(wps, list) or len(wps) != 2:
            raise BadInput(f"monsters.{m['id']}.waypoints phải có đúng 2 điểm")
        for idx, wp in enumerate(wps):
            _pos(f"monsters.{m['id']}.waypoints[{idx}]", wp, bounds)
            if not (d_lo <= wp[1] <= d_hi):
                raise BadInput(f"monsters.{m['id']}.waypoints[{idx}] ngoài dải độ sâu loài")
        tidx = m.get("target_idx", 1)
        if isinstance(tidx, bool) or tidx not in (0, 1):
            raise BadInput(f"monsters.{m['id']}.target_idx phải là 0 hoặc 1")
        st = m.get("state", "patrol")
        if st not in MONSTER_STATES:
            raise BadInput(f"monsters.{m['id']}.state không hợp lệ")
        stl = m.get("state_ticks_left", 0)
        _nonneg_int(f"monsters.{m['id']}.state_ticks_left", stl)
        if st in ("recoil", "stunned") and stl <= 0:
            raise BadInput(f"monsters.{m['id']}: {st} cần state_ticks_left > 0")
        rdir = m.get("recoil_dir")
        if st == "recoil":
            if not (isinstance(rdir, list) and len(rdir) == 2 and all(_num(c) for c in rdir)
                    and abs(math.hypot(rdir[0], rdir[1]) - 1.0) <= 0.05):
                raise BadInput(f"monsters.{m['id']}.recoil_dir phải là vector đơn vị")
        elif rdir is not None:
            raise BadInput(f"monsters.{m['id']}.recoil_dir chỉ dùng khi recoil")


def _validate_quan(b, tuning, contract_version: str = "1.1"):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        if is_v12(contract_version):
            validate_item_instances(b["stock"])
        else:
            validate_items(b["stock"])
    if "reputation" in b:
        rep = b["reputation"]
        q = tuning["quan"]
        if not _num(rep) or not (q["reputation_min"] <= rep <= q["reputation_max"]):
            raise BadInput("quan.reputation nằm ngoài dải hợp lệ")
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = tuning["quan"]["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    known = {t["id"] for t in tuning["quan"]["tables"]} | {t.get("id") for t in b.get("tables", [])}
    for c in b.get("customers", []):
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
        if is_v12(contract_version) and "reserved" in c:
            res = c["reserved"]
            if (not isinstance(res, list)
                    or any(not isinstance(iid, str) or not iid for iid in res)
                    or len(res) != len(set(res))):
                raise BadInput(f"customers.{c['id']}.reserved ở v1.2 phải là mảng id cá thể duy nhất")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
