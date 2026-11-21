"""QA Phase 4 — test theo TICKET-04 / Test Contract v1.3 (bench_cmd, soak_cmd).

Gameplay, tuning, kho và JSONL giữ nguyên v1.2 (đã phủ bởi test P1–P3). File này kiểm:
  - manifest v1.3 khai `bench_cmd`, `soak_cmd` ở gốc;
  - soak: chạy qua `soak_cmd` trong MỘT tiến trình, đủ Ngày, 0 crash, kế hoạch D1–D5 lặp ở Ngày 6+, tất định;
  - bench: công thức avg / 1% low; chạy thật `bench_cmd` khi máy có Chrome/Chromium/Edge (không có thì skip).

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_contract_p4 -v   (Windows: "tests;.")
"""

import json
import math
import shlex
import subprocess
import sys
import unittest

from helpers import ROOT, Workdir

from chonoi.bench import find_browser, summarize
from chonoi.contract import load_contract
from chonoi.runner import DaySession


def contract():
    with open(f"{ROOT}/game.contract.json", encoding="utf-8") as f:
        return json.load(f)


def _ver(v):
    return tuple(int(x) for x in str(v).split("."))


V13 = _ver(contract().get("contract_version", "1.0")) >= (1, 3)  # >= thay vì ==: phase sau không tự skip
need_v13 = unittest.skipUnless(V13, "chờ contract_version 1.3 (Phase 4)")


def cmd(key):
    base = shlex.split(contract()[key])
    if base and base[0] == "python3":
        base[0] = sys.executable  # Windows có thể ánh xạ python3 vào Microsoft Store
    return base


def run(key, *args, timeout=300):
    p = subprocess.run([*cmd(key), *args], cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stderr


@need_v13
class ManifestV13(unittest.TestCase):
    def test_p4_01_manifest_declares_bench_and_soak_cmd(self):
        c = contract()
        self.assertGreaterEqual(_ver(c["contract_version"]), (1, 3))
        for key in ("bench_cmd", "soak_cmd", "run_cmd", "headless_cmd"):
            self.assertIsInstance(c.get(key), str, key)
            self.assertTrue(c[key].strip(), key)
        self.assertIn("freshness", c["tuning"], "v1.3 giữ nguyên tuning v1.2")


@need_v13
class SoakV13(unittest.TestCase):
    def soak(self, w, name, seed, days):
        out = w.path(name)
        code, err = run("soak_cmd", "--seed", str(seed), "--days", str(days), "--out", out)
        self.assertEqual(code, 0, err)
        with open(out, encoding="utf-8") as f:
            return json.load(f)

    def test_p4_02_soak_six_days_repeats_plan_and_has_schema(self):
        with Workdir() as w:
            r = self.soak(w, "soak.json", 7, 6)
        self.assertEqual(set(r) - {"error"}, {"days", "days_completed", "crashes", "results", "duration_s"})
        self.assertEqual((r["days"], r["days_completed"], r["crashes"]), (6, 6, 0))
        self.assertEqual([x["day"] for x in r["results"]], [1, 2, 3, 4, 5, 6])
        mult = load_contract()["tuning"]["score"]["reputation_multiplier"]
        for x in r["results"]:
            self.assertEqual(set(x), {"day", "earned", "reputation", "score"})
            self.assertEqual(x["score"], x["earned"] + mult * math.floor(x["reputation"]))
        earned = [x["earned"] for x in r["results"]]
        self.assertEqual(earned, sorted(earned), "tổng thu đi xuyên suốt các Ngày, không reset")

    def test_p4_02_soak_is_deterministic_except_wall_time(self):
        with Workdir() as w:
            a, b = self.soak(w, "a.json", 3, 2), self.soak(w, "b.json", 3, 2)
        a.pop("duration_s"), b.pop("duration_s")
        self.assertEqual(a, b)

    def test_p4_02_soak_bad_args_exit_2(self):
        with Workdir() as w:
            for args in (("--seed", "1", "--days", "0", "--out", w.path("x.json")),
                         ("--seed", "1", "--days", "2"),
                         ("--seed", "x", "--days", "2", "--out", w.path("x.json"))):
                self.assertEqual(run("soak_cmd", *args)[0], 2, args)

    def test_p4_02_day_plan_cycles_d1_to_d5(self):
        s = DaySession(load_contract()["tuning"], None, 1, days=10, contract_version="1.3")
        for day in range(6, 11):
            self.assertEqual(s._plan_payload(day), s._plan_payload(day - 5))


class PlayCampaignVersion(unittest.TestCase):
    def test_play_campaign_uses_manifest_contract_version(self):
        """Hồi quy (sau v1.0.0): play_campaign từng tạo LiveGame không truyền contract_version -> chạy luật v1.1."""
        from unittest import mock

        import chonoi.play_campaign as pc

        seen = {}

        def fake_game(*args, **kwargs):
            seen.update(kwargs)
            raise KeyboardInterrupt  # dừng ngay sau khi dựng game, không mở server / trình duyệt

        with mock.patch.object(pc, "LiveGame", side_effect=fake_game), \
                mock.patch.object(pc.webbrowser, "open_new_tab") as browser:
            pc.main()
        self.assertEqual(seen.get("contract_version"), contract()["contract_version"])
        browser.assert_not_called()


class BenchFormula(unittest.TestCase):
    def test_p4_01_summarize_avg_and_one_percent_low(self):
        # 99 khung 10 ms + 1 khung 50 ms: k = max(1, ceil(1)) = 1 khung chậm nhất -> 1 / 0.05 s = 20 FPS
        r = summarize([10.0] * 99 + [50.0], load_ms=1234.4)
        self.assertEqual(set(r), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
        self.assertEqual(r["frames"], 100)
        self.assertAlmostEqual(r["measured_s"], 1.04, places=3)
        self.assertAlmostEqual(r["avg_fps"], 100 / 1.04, places=2)
        self.assertAlmostEqual(r["p1_low_fps"], 20.0, places=2)
        self.assertEqual(r["load_ms"], 1234)

    def test_p4_01_summarize_k_rounds_up(self):
        # 150 khung -> k = ceil(1.5) = 2 khung chậm nhất (40 ms, 20 ms) -> 1 / 0.03 s
        r = summarize([10.0] * 148 + [20.0, 40.0], load_ms=0)
        self.assertAlmostEqual(r["p1_low_fps"], 1 / 0.03, places=2)

    def test_p4_01_summarize_rejects_empty(self):
        with self.assertRaises(ValueError):
            summarize([], load_ms=0)


@need_v13
@unittest.skipIf(find_browser() is None, "không có Chrome/Chromium/Edge trên máy này")
class BenchRun(unittest.TestCase):
    def test_p4_01_bench_cmd_writes_five_fields(self):
        with Workdir() as w:
            out = w.path("bench.json")
            code, err = run("bench_cmd", "--seed", "42", "--duration", "2", "--warmup", "0.5", "--out", out, timeout=120)
            self.assertEqual(code, 0, err)
            with open(out, encoding="utf-8") as f:
                r = json.load(f)
        self.assertEqual(set(r), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
        self.assertGreater(r["frames"], 0)
        self.assertGreaterEqual(r["measured_s"], 2.0)
        self.assertAlmostEqual(r["avg_fps"], r["frames"] / r["measured_s"], delta=0.05)
        self.assertLessEqual(r["p1_low_fps"], r["avg_fps"] + 0.01)
        self.assertGreater(r["load_ms"], 0)

    def test_p4_01_bench_bad_args_exit_2(self):
        self.assertEqual(run("bench_cmd", "--seed", "42", "--duration", "0", "--out", "x.json")[0], 2)
        self.assertEqual(run("bench_cmd", "--seed", "42", "--out", "x.json")[0], 2)


if __name__ == "__main__":
    unittest.main()
