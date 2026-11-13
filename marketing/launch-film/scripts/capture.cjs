// Captures the real, live product UI for the film. Our own public site only.
const { chromium } = require('playwright');
const path = require('node:path');
const OUT = path.join(__dirname, '..', 'public', 'ui');
const EXE = 'C:/Users/dmbar/AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe';
const SITE = process.env.SITE || 'https://examuploadkit.com';
const mobile = [
  ['m-home', '/'], ['m-exams', '/exams'], ['m-jee', '/exam/jee-main-2026'],
  ['m-jee-hi', '/hi/exam/jee-main-2026'], ['m-deadlines', '/deadlines'], ['m-pdf', '/pdf'],
  ['m-neet', '/exam/neet-ug-2026'],
];
const desktop = [['d-home', '/'], ['d-jee', '/exam/jee-main-2026']];
(async () => {
  const browser = await chromium.launch({ executablePath: EXE });
  const m = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true, colorScheme: 'light' });
  for (const [name, route] of mobile) {
    const p = await m.newPage();
    await p.goto(SITE + route, { waitUntil: 'networkidle', timeout: 60000 }).catch(e => console.log(name, e.message));
    await p.waitForTimeout(1200);
    await p.screenshot({ path: path.join(OUT, name + '.png') });
    if (!['m-exams','m-deadlines'].includes(name)) await p.screenshot({ path: path.join(OUT, name + '-full.png'), fullPage: true, timeout: 90000 }).catch(e=>console.log('full fail',name));
    console.log('ok', name);
    await p.close();
  }
  const d = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2, colorScheme: 'light' });
  for (const [name, route] of desktop) {
    const p = await d.newPage();
    await p.goto(SITE + route, { waitUntil: 'networkidle', timeout: 60000 }).catch(e => console.log(name, e.message));
    await p.waitForTimeout(1200);
    await p.screenshot({ path: path.join(OUT, name + '.png') });
    console.log('ok', name);
    await p.close();
  }
  await browser.close();
})();
