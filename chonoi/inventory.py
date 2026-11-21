"""Adapter file kho cho Contract v1.0/v1.1 (kho đếm) và v1.2 (kho cá thể có độ tươi).

- v1.0 / v1.1: {"items": {kind: số nguyên >= 0}}
- v1.2:        {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}
  Bên đọc chọn schema theo `contract_version`; v1.2 từ chối file kho đếm (BadInput -> mã 2).
  Độ tươi lưu nội bộ bằng `Fraction` (chuẩn hóa bội số 1/240 khi đọc lại) để so ngưỡng `< 30`
  và tính `floor(price * avg_fresh / 100)` không sai số dấu phẩy động.
"""

from fractions import Fraction
import json
import math
import os
import tempfile

from .errors import BadInput
from .ids import id_key, sort_by_id

KINDS_V11 = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
KINDS_P1 = KINDS_V11
ITEM_KEYS = {"id", "kind", "fresh"}
FRESH_SCALE = 240  # 240 đơn vị / điểm tươi -> gather -2/tick (0.5/s), quan -1/tick (0.25/s)


def is_v12(contract_version: str) -> bool:
    return contract_version == "1.2"


def to_fresh(val) -> Fraction:
    """Chuyển số độ tươi trong [0, 100] sang Fraction chính xác (khớp bội số 1/240 khi sai khác <= 1e-9)."""
    if isinstance(val, Fraction):
        if not (0 <= val <= 100):
            raise BadInput(f"fresh phải trong [0, 100], đang là {val}")
        return val
    if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val):
        raise BadInput(f"fresh phải là số hữu hạn trong [0, 100], đang là {val!r}")
    if not (0 <= val <= 100):
        raise BadInput(f"fresh phải trong [0, 100], đang là {val!r}")
    if isinstance(val, int):
        return Fraction(val, 1)
    units = round(val * FRESH_SCALE)
    if abs(val - units / FRESH_SCALE) <= 1e-9:
        return Fraction(units, FRESH_SCALE)
    return Fraction(str(val))


def fresh_to_json(val):
    """Xuất độ tươi ra JSON đủ chính xác để giữ giá trị và nhánh tại ngưỡng 30 khi đọc lại."""
    if isinstance(val, Fraction):
        return int(val.numerator) if val.denominator == 1 else float(val)
    return val


def serialize_item(item: dict) -> dict:
    return {
        "id": item["id"],
        "kind": item["kind"],
        "fresh": fresh_to_json(item["fresh"]),
    }


def sort_items_by_kind_id(items: list) -> list:
    return sorted(items, key=lambda it: (it["kind"], id_key(it["id"])))


def validate_items(items, kinds=KINDS_V11):
    """Kiểm kho đếm (v1.0/v1.1): {kind: int >= 0}."""
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def validate_item_instances(items, kinds=KINDS_V11) -> list:
    """Kiểm kho cá thể (v1.2): [{"id": str, "kind": str, "fresh": number in [0, 100]}]."""
    if not isinstance(items, list):
        raise BadInput("items ở contract v1.2 phải là mảng cá thể (từ chối kho đếm)")
    seen = set()
    out = []
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            raise BadInput(f"items[{i}] phải là object")
        extra = set(it) - ITEM_KEYS
        missing = ITEM_KEYS - set(it)
        if extra or missing:
            raise BadInput(f"items[{i}] phải có đúng các khóa id, kind, fresh")
        iid = it["id"]
        if not isinstance(iid, str) or not iid:
            raise BadInput(f"items[{i}].id phải là chuỗi khác rỗng")
        if iid in seen:
            raise BadInput(f"id cá thể trùng: {iid}")
        seen.add(iid)
        kind = it["kind"]
        if kind not in kinds:
            raise BadInput(f"nguyên liệu lạ: {kind}")
        fresh = to_fresh(it["fresh"])
        out.append({"id": iid, "kind": kind, "fresh": fresh})
    return out


def read_inventory(path: str, kinds=KINDS_V11, contract_version: str = "1.1"):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    if is_v12(contract_version):
        return validate_item_instances(data["items"], kinds)
    return validate_items(data["items"], kinds)


def hold_to_items(hold: list, contract_version: str = "1.1"):
    """Khoang -> payload `items` theo contract_version (v1.1: dict đếm; v1.2: list cá thể sắp theo id)."""
    if is_v12(contract_version):
        return [serialize_item(it) for it in sort_by_id(hold)]
    counts = {}
    for k in hold:
        kind = k["kind"] if isinstance(k, dict) else k
        counts[kind] = counts.get(kind, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items, contract_version: str = "1.1"):
    if is_v12(contract_version):
        payload = [serialize_item(it) for it in sort_by_id(items)]
    else:
        payload = {k: items[k] for k in sorted(items) if items[k] > 0}
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": payload}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
