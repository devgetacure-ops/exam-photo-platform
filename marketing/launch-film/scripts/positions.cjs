// Where things sit on the live JEE page (CSS px, page coordinates, bars hidden as in the clean capture).
const { chromium } = require('playwright');
const EXE = 'C:/Users/dmbar/AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe';
(async () => {
  const b = await chromium.launch({ executablePath: EXE });
  const p = await (await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true })).newPage();
  await p.goto('https://examuploadkit.com/exam/jee-main-2026', { waitUntil: 'load', timeout: 90000 });
  await p.waitForTimeout(2000);
  await p.evaluate(() => document.querySelectorAll('body *').forEach((el) => { const cs = getComputedStyle(el); if (cs.position === 'fixed' || cs.position === 'sticky') { const r = el.getBoundingClientRect(); if (r.width > 300 && r.height > 30) el.style.display = 'none'; } }));
  const find = (t) => p.evaluate((t) => { const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n; while ((n = w.nextNode())) { if (n.textContent.trim().startsWith(t)) { const r = n.parentElement.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top + scrollY), Math.round(r.width), Math.round(r.height)]; } } return null; }, t);
  for (const t of ['THE ANSWER', '6 files, and what', 'Candidate photograph', 'Candidate signature', 'Identity proof scan', 'Worth knowing']) console.log(JSON.stringify([t, await find(t)]));
  await b.close();
})();
