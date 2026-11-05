import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "file:///C:/Users/dmbar/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";

const campaign = path.resolve("campaigns/launch-2026-v3");
const out = path.join(campaign, "source-ui");
await fs.mkdir(out, { recursive: true });

const browser = await chromium.launch({
  headless: true,
  executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1.5 });
await page.goto("https://examuploadkit.com", { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(1800);
await page.emulateMedia({ reducedMotion: "reduce", colorScheme: "light" });

async function elementShot(name, selector, padding = 0) {
  const item = page.locator(selector).first();
  await item.scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  const box = await item.boundingBox();
  if (!box) throw new Error(`No box for ${selector}`);
  const clip = {
    x: Math.max(0, box.x - padding),
    y: Math.max(0, box.y - padding),
    width: Math.min(1440, box.width + padding * 2),
    height: Math.min(1600, box.height + padding * 2),
  };
  await page.screenshot({ path: path.join(out, `${name}.png`), clip, animations: "disabled" });
}

await elementShot("01-home-hero", ".euk-hero");
await elementShot("02-what-we-prepare", "#what");
await elementShot("03-how-it-works", "#how");
await elementShot("04-problem", "#problem");
await elementShot("05-one-face-many-rules", ".euk-plate");
await elementShot("06-why", "#why");
await elementShot("07-pricing", "#pricing");
await elementShot("08-principles", "#story");

const examUrl = "https://examuploadkit.com/exam/ssc-combined-graduate-level-examination-2026-live-capture";
await page.goto(examUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(1800);
await elementShot("09-exam-page", "main");

await page.goto(`${examUrl}/prepare`, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(1800);
await elementShot("10-prepare-files", "main");

await page.goto(`${examUrl}/rules`, { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(1800);
await elementShot("11-rules", "main");

await page.goto("https://examuploadkit.com/pdf", { waitUntil: "domcontentloaded", timeout: 60000 });
await page.waitForTimeout(1800);
await elementShot("12-pdf-tools", "main");

const phone = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
await phone.goto("https://examuploadkit.com", { waitUntil: "domcontentloaded", timeout: 60000 });
await phone.waitForTimeout(1800);
await phone.emulateMedia({ reducedMotion: "reduce", colorScheme: "light" });
await phone.screenshot({ path: path.join(out, "13-mobile-home.png"), fullPage: false, animations: "disabled" });
await phone.goto(`${examUrl}/prepare`, { waitUntil: "domcontentloaded", timeout: 60000 });
await phone.waitForTimeout(1800);
await phone.screenshot({ path: path.join(out, "14-mobile-prepare.png"), fullPage: false, animations: "disabled" });

await browser.close();
console.log(`Captured 14 live product views to ${out}`);
