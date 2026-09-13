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
        if (step.cdp) {
            const r = await send(step.cdp, step.params ?? {});
            console.log(JSON.stringify({ w: run.width, label: step.label ?? step.cdp, r: r.result ?? r.error }));
        }
        // A real finger: touch events through the input pipeline, so
        // touch-action and pointer capture behave as they do on a phone.
        // { drag: selector, from: 0..1, to: 0..1, y?: 0..1 } across the element.
        if (step.drag) {
            await evaluate(`document.querySelector(${JSON.stringify(step.drag)})?.scrollIntoView({ block: "center" })`);
            await sleep(400);
            const box = await evaluate(`(() => { const el = document.querySelector(${JSON.stringify(step.drag)}); if (!el) return null; const r = el.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; })()`);
            if (!box) console.log(JSON.stringify({ w: run.width, drag: step.drag, r: "missing" }));
            else {
                const y = box.y + box.h * (step.y ?? 0.5);
                const at = (f) => box.x + box.w * f;
                await send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x: at(step.from), y }] });
                for (let i = 1; i <= 12; i++) {
                    await send("Input.dispatchTouchEvent", { type: "touchMove", touchPoints: [{ x: at(step.from + ((step.to - step.from) * i) / 12), y }] });
                    await sleep(16);
                }
                await send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
                console.log(JSON.stringify({ w: run.width, drag: step.drag, r: "done" }));
            }
        }
        // { tap: selector }: a touch tap at the element's centre.
        if (step.tap) {
            await evaluate(`document.querySelector(${JSON.stringify(step.tap)})?.scrollIntoView({ block: "center" })`);
            await sleep(400);
            const p = await evaluate(`(() => { const el = document.querySelector(${JSON.stringify(step.tap)}); if (!el) return null; const r = el.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; })()`);
            if (p) {
                await send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [p] });
                await send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
            }
            console.log(JSON.stringify({ w: run.width, tap: step.tap, r: p ? "done" : "missing" }));
        }
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
