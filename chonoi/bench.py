"""Benchmark có render (Contract v1.3 · `bench_cmd`).

    python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json [--warmup 3] [--browser PATH] [--headed]

Cảnh đo: buổi sáng lõi (độ tươi, cá bơi, Cá Sấu Năm Chèo, hiệu ứng mặc định), Út Sen đứng yên ở bến, cửa sổ 1280×720.
Cách làm: dựng `LiveGame` (cùng sim với bản chơi) + server HTTP cục bộ, mở Chrome/Chromium/Edge ở chế độ headless
(mặc định) vào `/?bench=1&warmup=3&duration=30`. Trang bỏ qua menu, vẽ bằng canvas như bản chơi thật và ghi thời gian
từng khung (`requestAnimationFrame`) sau khi làm nóng, rồi POST về `/bench`. Python tính:

    frames, measured_s  số khung và số giây thực tế trong cửa sổ đo
    avg_fps             frames / measured_s
    p1_low_fps          1 / trung bình thời gian (giây) của max(1, ceil(0.01·frames)) khung chậm nhất
    load_ms             từ lúc khởi chạy lệnh đến khung hình đầu tiên của cảnh đo

Tìm trình duyệt: --browser, biến môi trường CHROME_PATH, rồi các tên/đường dẫn thường gặp trên Linux/macOS/Windows.
Mã thoát: 0 đạt; 1 không chạy được (thiếu trình duyệt, quá thời gian); 2 đối số sai.
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

T_START = time.time()  # mốc load_ms: lúc tiến trình bench bắt đầu chạy

from .contract import load_contract  # noqa: E402
from .live import LiveGame, _Handler  # noqa: E402
from .scenario import load_scenario  # noqa: E402

WINDOW = (1280, 720)

# Cảnh chuẩn: giỏ có sẵn hàng để HUD độ tươi hiện thật, 1 cá thể sát ngưỡng sẽ ươn sau ~2 s (trong lúc làm nóng).
BENCH_SCENARIO = {"gather": {"hold": [
    {"id": "I1", "kind": "ca_linh", "fresh": 100},
    {"id": "I2", "kind": "ca_loc", "fresh": 80},
    {"id": "I3", "kind": "bong_sung", "fresh": 55},
    {"id": "I4", "kind": "bong_dien_dien", "fresh": 31},
]}}

BROWSERS = (
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "microsoft-edge", "msedge",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
)


def find_browser(explicit=None):
    for cand in (explicit, os.environ.get("CHROME_PATH"), *BROWSERS):
        if not cand:
            continue
        if os.path.isfile(cand):
            return cand
        found = shutil.which(cand)
        if found:
            return found
    return None


def summarize(frame_ms, load_ms):
    """Tính 5 trường bench.json từ thời gian từng khung (ms) trong cửa sổ đo."""
    frame_s = [ms / 1000.0 for ms in frame_ms if ms > 0]
    frames = len(frame_s)
    measured = sum(frame_s)
    if frames == 0 or measured <= 0:
        raise ValueError("không đo được khung hình nào")
    k = max(1, math.ceil(0.01 * frames))
    slowest = sorted(frame_s, reverse=True)[:k]
    return {
        "avg_fps": round(frames / measured, 2),
        "p1_low_fps": round(1.0 / (sum(slowest) / k), 2),
        "frames": frames,
        "measured_s": round(measured, 3),
        "load_ms": int(round(load_ms)),
    }


class _BenchSink:
    def __init__(self):
        self.first_frame_epoch_ms = None
        self.result = None
        self.done = threading.Event()


def _make_server(game, sink):
    from http.server import ThreadingHTTPServer

    class BenchHandler(_Handler):
        def do_POST(self):
            if self.path.split("?", 1)[0] != "/bench":
                return super().do_POST()
            n = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            except ValueError:
                self._send(400, b'{"error":"json sai"}')
                return
            if body.get("type") == "first_frame":
                sink.first_frame_epoch_ms = float(body["epoch_ms"])
            elif body.get("type") == "result":
                sink.result = body
                sink.done.set()
            self._send(200, b'{"ok":true}')

    class QuietServer(ThreadingHTTPServer):
        def handle_error(self, request, client_address):  # trình duyệt bị tắt khi còn poll -> bỏ qua reset
            pass

    handler = type("Handler", (BenchHandler,), {"game": game})
    httpd = QuietServer(("127.0.0.1", 0), handler)
    httpd.daemon_threads = True
    return httpd


def run_bench(seed, duration, warmup=3.0, browser=None, headed=False, timeout_pad=60):
    contract = load_contract()
    tuning = contract["tuning"]
    version = contract.get("contract_version", "1.3")
    with tempfile.TemporaryDirectory() as tmp:
        sc_path = os.path.join(tmp, "bench_scenario.json")
        with open(sc_path, "w", encoding="utf-8") as f:
            json.dump(BENCH_SCENARIO, f)
        scenario = load_scenario(sc_path, "gather", tuning, contract_version=version)
        game = LiveGame("gather", tuning, scenario, seed, contract_version=version)
        sink = _BenchSink()
        httpd = _make_server(game, sink)
        port = httpd.server_address[1]
        game.start()
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{port}/?bench=1&warmup={warmup}&duration={duration}"
        exe = find_browser(browser)
        if exe is None:
            raise RuntimeError("không tìm thấy Chrome/Chromium/Edge; truyền --browser PATH hoặc đặt CHROME_PATH")
        args = [exe, f"--window-size={WINDOW[0]},{WINDOW[1]}", f"--user-data-dir={os.path.join(tmp, 'profile')}",
                "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows", "--autoplay-policy=no-user-gesture-required"]
        if not headed:
            args += ["--headless=new", "--hide-scrollbars"]
        else:
            args += [f"--app={url}"]
        if not headed:
            args.append(url)
        proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            if not sink.done.wait(warmup + duration + timeout_pad):
                raise RuntimeError("quá thời gian chờ kết quả từ trình duyệt")
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
            httpd.shutdown()
            httpd.server_close()
            game.stop()
    r = sink.result
    load_ms = (sink.first_frame_epoch_ms or r["first_frame_epoch_ms"]) - T_START * 1000.0
    out = summarize(r["frame_ms"], load_ms)
    meta = {"browser": os.path.basename(exe), "headless": not headed, "window": list(WINDOW),
            "viewport": r.get("viewport"), "seed": seed, "warmup_s": warmup, "duration_s": duration,
            "user_agent": r.get("user_agent")}
    return out, meta


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="chonoi.bench", description="Benchmark có render cảnh buổi sáng (1280×720).")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--duration", type=float, required=True, help="số giây đo sau làm nóng")
    ap.add_argument("--out", required=True)
    ap.add_argument("--warmup", type=float, default=3.0)
    ap.add_argument("--browser", help="đường dẫn Chrome/Chromium/Edge")
    ap.add_argument("--headed", action="store_true", help="mở cửa sổ thật thay vì headless")
    ap.add_argument("--meta-out", help="tùy chọn: ghi thêm thông tin máy/trình duyệt")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    if a.duration <= 0 or a.warmup < 0:
        print("đầu vào sai: --duration > 0, --warmup ≥ 0", file=sys.stderr)
        return 2
    try:
        out, meta = run_bench(a.seed, a.duration, a.warmup, a.browser, a.headed)
    except (RuntimeError, ValueError, OSError) as e:
        print(f"bench lỗi: {e}", file=sys.stderr)
        return 1
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
        f.write("\n")
    if a.meta_out:
        with open(a.meta_out, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
            f.write("\n")
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
