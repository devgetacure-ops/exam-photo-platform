// True phone-viewport checks over the DevTools protocol, no packages needed.
// usage: node phone.mjs <chrome-headless-shell.exe> <outdir> <plan.json>
// plan: [{ width, steps: [{url}|{wait}|{eval}|{click}|{shot, full?}] }]
import { spawn } from "node:child_process";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [exe, outdir, planPath] = process.argv.slice(2);
const plan = JSON.parse(readFileSync(planPath, "utf8"));
const port = 9333;
const chrome = spawn(exe, [
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${mkdtempSync(join(tmpdir(), "phone-"))}`,
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
const waiters = [];
ws.addEventListener("message", (m) => {
    const msg = JSON.parse(m.data);
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
    if (msg.method) for (const w of waiters.splice(0)) w(msg);
});
const send = (method, params = {}) => new Promise((resolve) => {
    const id = ++seq; pending.set(id, resolve);
    ws.send(JSON.stringify({ id, method, params }));
});
const evaluate = async (expression) => {
    const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
    return r.result?.exceptionDetails ? { error: r.result.exceptionDetails.exception?.description } : r.result?.result?.value;
};

await send("Page.enable");
for (const run of plan) {
    await send("Emulation.setDeviceMetricsOverride", { width: run.width, height: run.height ?? 844, deviceScaleFactor: 2, mobile: true });
    await send("Emulation.setTouchEmulationEnabled", { enabled: true });
    if (run.dark !== undefined) await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: run.dark ? "dark" : "light" }] });
    for (const step of run.steps) {
        if (step.url) { await send("Page.navigate", { url: step.url }); await sleep(step.settle ?? 2500); }
        if (step.wait) await sleep(step.wait);
        if (step.click) console.log(JSON.stringify({ w: run.width, click: step.click, r: await evaluate(`(() => { const el = document.querySelector(${JSON.stringify(step.click)}); if (!el) return 'missing'; el.click(); return 'ok'; })()`) }));
        if (step.eval) console.log(JSON.stringify({ w: run.width, label: step.label, r: await evaluate(step.eval) }));
        if (step.shot) {
            const params = { format: "png" };
            if (step.full) {
                const h = await evaluate("document.documentElement.scrollHeight");
                params.captureBeyondViewport = true;
                params.clip = { x: 0, y: 0, width: run.width, height: h, scale: 1 };
            }
            const r = await send("Page.captureScreenshot", params);
            writeFileSync(join(outdir, `${step.shot}-${run.width}.png`), Buffer.from(r.result.data, "base64"));
        }
    }
}
ws.close();
chrome.kill();
process.exit(0);
