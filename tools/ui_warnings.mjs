// QA Phase 4 (AC-P4-03): chơi thử 3 cảnh báo (thủy quái gần, oxy sắp hết, khách sắp giận) ở chế độ thường
// và tương phản cao bằng Chrome DevTools Protocol (Node ≥ 22, không cần thư viện), chụp ảnh 1280×720.
// Thường được gọi từ tools/playtest_warnings.py (tự dựng server chonoi.live với scenario gây cảnh báo):
//   node tools/ui_warnings.mjs "<chrome>" <outDir> '<cases.json>'
// cases: [{name, url, expect: ["warnOxy", ...], hc: bool}] — in JSON kết quả ra stdout.
import { spawn } from "node:child_process";
import { writeFileSync, mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [chromePath, outDir, casesPath] = process.argv.slice(2);
const cases = JSON.parse(readFileSync(casesPath, "utf8"));
const port = 9334;
const profile = mkdtempSync(join(tmpdir(), "cdp-p4-"));
const chrome = spawn(chromePath, ["--headless=new", `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
  "--window-size=1280,720", "--no-first-run", "about:blank"], { stdio: "ignore" });
const sleep = ms => new Promise(r => setTimeout(r, ms));

let ws, id = 0; const pending = new Map();
async function connect() {
  for (let i = 0; i < 60; i++) {
    try {
      const tabs = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
      const page = tabs.find(t => t.type === "page");
      ws = new WebSocket(page.webSocketDebuggerUrl);
      await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
      ws.onmessage = m => { const d = JSON.parse(m.data); if (pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } };
      return;
    } catch { await sleep(250); }
  }
  throw new Error("không kết nối được Chrome DevTools");
}
const send = (method, params = {}) => new Promise(res => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const js = async expr => (await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true })).result?.result?.value;

const results = [];
try {
  await connect();
  await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 720, deviceScaleFactor: 1, mobile: false });
  for (const c of cases) {
    await send("Page.navigate", { url: c.url });
    let state = null;
    const t0 = Date.now();
    while (Date.now() - t0 < 10000) {
      await sleep(200);
      state = await js(`(() => {
        const ids = ["warnOxy", "warnMonster", "warnAngry"];
        const vis = {};
        for (const i of ids) { const el = document.getElementById(i);
          vis[i] = !!el && el.classList.contains("show") && getComputedStyle(el).display !== "none" ? el.textContent : null; }
        return {visible: vis, hc: document.body.classList.contains("hc"),
                phase: document.getElementById("phasePill")?.textContent};
      })()`);
      if (state && c.expect.every(i => state.visible[i])) break;
    }
    await sleep(400); // để canvas vẽ biểu tượng "!" ở khung kế
    const shot = await send("Page.captureScreenshot", { format: "png" });
    const file = `${c.name}.png`;
    writeFileSync(join(outDir, file), Buffer.from(shot.result.data, "base64"));
    const ok = !!state && c.expect.every(i => state.visible[i]) && state.hc === !!c.hc;
    results.push({ name: c.name, ok, hc: state?.hc, phase: state?.phase, visible: state?.visible, screenshot: file });
  }
} finally {
  try { ws?.close(); } catch {}
  chrome.kill();
}
console.log(JSON.stringify(results));
