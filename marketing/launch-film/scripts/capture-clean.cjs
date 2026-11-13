// Full-page captures with fixed/sticky chrome removed, plus that chrome on its own.
const { chromium } = require('playwright');
const path = require('node:path');
const OUT = path.join(__dirname, '..', 'public', 'ui');
const EXE = 'C:/Users/dmbar/AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe';
const SITE = process.env.SITE || 'https://examuploadkit.com';
const pages = [['m-jee', '/exam/jee-main-2026'], ['m-jee-hi', '/hi/exam/jee-main-2026'], ['m-home', '/']];
(async () => {
  const browser = await chromium.launch({ executablePath: EXE });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true });
  for (const [name, route] of pages) {
    const p = await ctx.newPage();
    await p.goto(SITE + route, { waitUntil: 'load', timeout: 90000 });
    await p.waitForTimeout(2500);
    // the bottom action bar and the top bar, on their own
    const fixed = await p.evaluate(() => {
      const out = [];
      document.querySelectorAll('body *').forEach((el, i) => {
        const cs = getComputedStyle(el);
        if (cs.position === 'fixed' || cs.position === 'sticky') {
          const r = el.getBoundingClientRect();
          if (r.width > 300 && r.height > 30) { el.setAttribute('data-cap', String(i)); out.push({ i, top: r.top, h: r.height }); }
        }
      });
      return out;
    });
    for (const fx of fixed) {
      const tag = fx.top > 400 ? 'bottombar' : 'topbar';
      await p.locator(`[data-cap="${fx.i}"]`).screenshot({ path: path.join(OUT, `${name}-${tag}.png`) }).catch(() => {});
    }
    await p.addStyleTag({ content: '[data-cap]{position:static !important; display:none !important}' });
    await p.waitForTimeout(400);
    await p.screenshot({ path: path.join(OUT, `${name}-clean.png`), fullPage: true, timeout: 120000 });
    console.log('ok', name, JSON.stringify(fixed));
    await p.close();
  }
  await browser.close();
})();
