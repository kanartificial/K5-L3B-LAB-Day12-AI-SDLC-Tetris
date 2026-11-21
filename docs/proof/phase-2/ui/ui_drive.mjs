// QA Phase 2 (AC-P2-06): lái UI chonoi.live --mode day bằng Chrome DevTools Protocol (Node ≥ 22, không cần thư viện),
// bấm qua menu → DayIntro → pause → gather → EveningIntro → quán → DayResult → Shop × 5 Ngày → Summary, chụp ảnh 1280×720.
// Chạy: python3 -m chonoi.live --mode day --port 8774 --scenario docs/proof/phase-2/ui/scenario.json
//       node docs/proof/phase-2/ui/ui_drive.mjs "<đường dẫn chrome>" http://127.0.0.1:8774/ docs/proof/phase-2/ui
import { spawn } from "node:child_process";
import { writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [chromePath, url, outDir] = process.argv.slice(2);
const port = 9333;
const profile = mkdtempSync(join(tmpdir(), "cdp-"));
const chrome = spawn(chromePath, ["--headless=new", "--disable-gpu", `--remote-debugging-port=${port}`,
  `--user-data-dir=${profile}`, "--window-size=1280,720", "about:blank"], { stdio: "ignore" });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const log = [];
const note = (ok, msg) => { const line = `${ok ? "ĐẠT" : "LỖI"} · ${msg}`; log.push(line); console.log(line); };

let ws, id = 0; const pending = new Map();
async function connect() {
  for (let i = 0; i < 40; i++) {
    try {
      const tabs = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
      const page = tabs.find(t => t.type === "page");
      ws = new WebSocket(page.webSocketDebuggerUrl);
      await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
      ws.onmessage = m => { const d = JSON.parse(m.data); if (pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } };
      return;
    } catch { await sleep(250); }
  }
  throw new Error("không kết nối được Chrome");
}
const send = (method, params = {}) => new Promise(res => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const js = async expr => (await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true })).result?.result?.value;
const shot = async name => {
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(outDir, name), Buffer.from(r.result.data, "base64"));
};
const state = () => js(`({phase: snap?.phase, day: snap?.day, st: snap?.state, fin: !!snap?.finished, t: snap?.time_left_ticks,
  ui: uiPhase, open: [...document.querySelectorAll('.overlay.show')].map(e => e.id)})`);
async function waitFor(pred, ms = 20000, step = 150) {
  const end = Date.now() + ms;
  while (Date.now() < end) { const s = await state(); if (pred(s)) return s; await sleep(step); }
  return await state();
}
const pressE = () => js(`press("interact")`);

try {
  await connect();
  await send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 720, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url });
  await sleep(1500);

  // 1. Menu chính: đồng hồ đứng yên
  let a = await state(); await sleep(1200); let b = await state();
  note(a.open.includes("mainMenu") && a.t === b.t && b.st === "paused", `Menu chính hiện, đồng hồ đứng yên (${a.t} → ${b.t}, state ${b.st})`);
  await shot("p2-01-menu.png");

  // 2. Chơi → DayIntro, mô phỏng dừng trong lúc đọc kế hoạch
  await js(`$("btnPlay").click()`);
  let s = await waitFor(s => s.open.includes("dayIntro") && s.st === "paused", 3000);
  note(s.open.includes("dayIntro") && s.st === "paused", `DayIntro Ngày ${s.day} hiện, mô phỏng tạm dừng (${s.st})`);
  await shot("p2-02-dayintro.png");
  s = await waitFor(s => !s.open.includes("dayIntro") && s.st === "playing", 6000);
  note(!s.open.includes("dayIntro") && s.st === "playing", "DayIntro tự đóng sau 4 s, chơi tiếp");
  await sleep(600);
  await shot("p2-03-gather-hud.png");

  // 3. Pause / Tiếp tục
  await js(`togglePause()`);
  s = await waitFor(s => s.st === "paused" && s.open.includes("pauseOverlay"), 2000);
  const t1 = s.t; await sleep(800); const t2 = (await state()).t;
  note(s.open.includes("pauseOverlay") && t1 === t2, `Pause: khung Tạm dừng hiện, đồng hồ đứng (${t1} → ${t2})`);
  await shot("p2-04-pause.png");
  await js(`$("btnResume").click()`);
  s = await waitFor(s => s.st === "playing" && !s.open.includes("pauseOverlay"), 2000);
  note(s.st === "playing" && !s.open.includes("pauseOverlay"), "Nút Tiếp tục bỏ pause thật (state playing)");

  for (let day = 1; day <= 5; day++) {
    if (day > 1) {
      s = await waitFor(s => s.open.includes("dayIntro") && s.st === "paused", 5000);
      note(s.open.includes("dayIntro") && s.day === day, `DayIntro Ngày ${day} ${JSON.stringify(s)}`);
      await js(`advanceIntro()`);
      await waitFor(s => s.st === "playing", 2000);
    }
    // Cập bến ngay (xuất phát trong bán kính bến) → EveningIntro
    await pressE();
    s = await waitFor(s => s.open.includes("eveningIntro") && s.st === "paused", 4000);
    note(s.open.includes("eveningIntro") && s.st === "paused" && s.phase === "quan", `Ngày ${day}: EveningIntro hiện, quán chờ (${s.st})`);
    if (day === 1) await shot("p2-05-evening.png");
    await js(`$("btnStartQuan").click()`);
    s = await waitFor(s => s.st === "playing", 2000);
    if (day === 1) { await sleep(3500); await shot("p2-06-quan-hud.png"); }
    // Hết ca → DayResult + Shop
    s = await waitFor(s => s.open.includes("dayResult"), 15000);
    note(s.open.includes("dayResult") && s.phase === "shop", `Ngày ${day}: DayResult hiện khi sang Shop ${JSON.stringify(s)}`);
    if (day === 1) await shot("p2-07-dayresult.png");
    await js(`$("btnToShop").click()`);
    await waitFor(s => s.st === "playing" && s.open.includes("shopOverlay"), 2000);
    if (day === 1) {
      await js(`document.querySelector('[data-buy="oxygen"]')?.click()`);
      await sleep(600);
      const up = await js(`JSON.stringify(snap.upgrades)`);
      note(up.includes('"oxygen":1'), `Shop: mua Bình oxy cấp 1 (upgrades ${up})`);
      await shot("p2-08-shop.png");
    }
    await js(`$("btnCloseShop").click()`);
    note(true, `sau đóng shop ngày ${day}: ${JSON.stringify(await waitFor(s => s.day !== day || s.fin, 3000))}`);
    if (day === 1) {
      await waitFor(s => s.day === 2 && s.phase === "gather", 4000);
      const ox = await js(`snap.player?.oxygen_max_ticks`);
      note(ox === 2700, `Ngày 2 áp dụng Bình oxy cấp 1: oxy tối đa ${ox} tick (cần 2700)`);
    }
  }
  s = await waitFor(s => s.open.includes("summaryOverlay"), 6000);
  note(s.open.includes("summaryOverlay"), "Summary hiện sau Ngày 5");
  const sumText = await js(`$("summaryText").innerText`);
  note(/bán chạy/i.test(sumText), `Summary: ${sumText.replace(/\n+/g, " | ")}`);
  await shot("p2-09-summary.png");
  const fonts = await js(`(() => { const bad = new Set();
    document.querySelectorAll('body *').forEach(e => { if (e.offsetParent === null || !e.childNodes.length) return;
      const own = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
      if (own) { const f = parseFloat(getComputedStyle(e).fontSize); if (f < 18) bad.add(e.tagName + '#' + (e.id||e.className) + ':' + f); } });
    return [...bad]; })()`);
  note(fonts.length === 0, `Chữ HTML đang hiển thị < 18 px: ${fonts.length ? fonts.join(", ") : "không có"}`);
  const scale = await js(`canvas.getBoundingClientRect().width / 960`);
  note(17 * scale >= 18, `Chữ canvas nhỏ nhất 17 px × tỉ lệ ${scale.toFixed(3)} = ${(17 * scale).toFixed(1)} px`);
} catch (e) {
  note(false, "script lỗi: " + e.message);
} finally {
  writeFileSync(join(outDir, "ui-check.log"), log.join("\n") + "\n");
  try { ws?.close(); } catch {}
  chrome.kill();
}
