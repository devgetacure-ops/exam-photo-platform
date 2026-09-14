// Renders the stacked wordmark (EXAM / UPLOAD / KIT) as brand assets.
//
// The owner asked for a logo in three centred rows with the wordmark's own
// construction and type (item H, 2026-09-14): asset files only, PNG and JPG,
// light and dark. Drawn by the site itself -- the same `.euk-lock` cells and
// Big Shoulders the header uses -- so it can never drift from the wordmark.
//
// usage: node scripts/render-stacked-logo.mjs <chrome-headless-shell.exe> <site-url> <outdir>
// e.g.   node scripts/render-stacked-logo.mjs "<shell>" http://localhost:3100 public/brand
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [exe, site, outdir] = process.argv.slice(2);
mkdirSync(outdir, { recursive: true });
const port = 9334;
const chrome = spawn(exe, [
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${mkdtempSync(join(tmpdir(), "logo-"))}`,
    "--hide-scrollbars",
    "about:blank",
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let target;
for (let i = 0; i < 50 && !target; i++) {
    try {
        const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
        target = list.find((t) => t.type === "page");
    } catch { await sleep(200); }
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r));
let seq = 0;
const pending = new Map();
ws.addEventListener("message", (m) => {
    const msg = JSON.parse(m.data);
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
});
const send = (method, params = {}) => new Promise((resolve) => {
    const id = ++seq; pending.set(id, resolve);
    ws.send(JSON.stringify({ id, method, params }));
});
const evaluate = async (expression) => {
    const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
    return r.result?.result?.value;
};

// Rows share one construction: joined cells, one outer border per row, and
// the rows stacked so their borders meet. Centred, so KIT sits in the middle.
const ROWS = ["EXAM", "UPLOAD", "KIT"];
const build = (dark) => `(() => {
    const root = document.querySelector('.euk') || document.body;
    document.body.innerHTML = '';
    const stage = document.createElement('div');
    stage.className = root.className;
    ${dark ? "document.documentElement.setAttribute('data-theme', 'dark');" : "document.documentElement.setAttribute('data-theme', 'light');"}
    stage.style.cssText = 'display:inline-flex;flex-direction:column;align-items:center;gap:0;padding:48px;background:var(--paper);';
    stage.id = 'logo-stage';
    const rows = ${JSON.stringify(ROWS)};
    rows.forEach((word, i) => {
        const lock = document.createElement('span');
        lock.className = 'euk-lock';
        lock.style.cssText = '--cell-w:92px;--cell-h:108px;--cell-t:74px;' + (i > 0 ? 'margin-top:-2px;' : '');
        for (const letter of word) {
            const cell = document.createElement('span');
            cell.className = 'euk-cell';
            cell.textContent = letter;
            lock.appendChild(cell);
        }
        stage.appendChild(lock);
    });
    document.body.style.margin = '0';
    document.body.style.background = 'transparent';
    document.body.appendChild(stage);
    return document.fonts.ready.then(() => {
        const r = stage.getBoundingClientRect();
        return { x: r.left, y: r.top, width: r.width, height: r.height };
    });
})()`;

await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", { width: 1400, height: 900, deviceScaleFactor: 2, mobile: false });
for (const theme of ["light", "dark"]) {
    await send("Page.navigate", { url: `${site}/` });
    await sleep(6000);
    const clip = await evaluate(build(theme === "dark"));
    await sleep(800);
    for (const format of ["png", "jpeg"]) {
        const r = await send("Page.captureScreenshot", {
            format,
            ...(format === "jpeg" ? { quality: 95 } : {}),
            clip: { ...clip, scale: 1 },
        });
        const name = `examuploadkit-stacked-${theme}.${format === "jpeg" ? "jpg" : "png"}`;
        writeFileSync(join(outdir, name), Buffer.from(r.result.data, "base64"));
        console.log(JSON.stringify({ wrote: name, width: Math.round(clip.width * 2), height: Math.round(clip.height * 2) }));
    }
}
ws.close();
chrome.kill();
process.exit(0);
