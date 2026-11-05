const { chromium } = require('C:/Users/dmbar/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
(async () => {
 const browser = await chromium.launch({headless:true,executablePath:'C:/Users/dmbar/AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'});
 const page = await browser.newPage();
 const errors=[]; page.on('pageerror',e=>errors.push(e.message));
 const out=__dirname, results=[];
 for (const width of [360,390,430,768,1024,1280,1440]) {
  await page.setViewportSize({width,height:900});
  await page.goto('http://localhost:3101/we-vs-ai',{waitUntil:'networkidle',timeout:120000});
  await page.evaluate(()=>document.fonts.ready);
  await page.evaluate(async()=>{for(let y=0;y<document.body.scrollHeight;y+=700){scrollTo(0,y);await new Promise(r=>setTimeout(r,35))}scrollTo(0,0)});
  await page.waitForTimeout(600);
  for (const theme of ['light','dark']) {
   await page.evaluate(t=>document.documentElement.dataset.theme=t,theme);
   const metrics=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,h1:document.querySelector('h1')?.textContent,faq:document.querySelectorAll('details').length,canonical:document.querySelector('link[rel=canonical]')?.href,structured:[...document.querySelectorAll('script[type="application/ld+json"]')].every(x=>{try{JSON.parse(x.textContent);return true}catch{return false}})}));
   results.push({width,theme,...metrics});
   if([390,1440].includes(width)) {
    await page.screenshot({path:path.join(out,`${width}-${theme}.png`),fullPage:true});
    if(theme==='light') await page.screenshot({path:path.join(out,`${width}-hero.png`)});
   }
  }
 }
 await page.setViewportSize({width:390,height:844});
 await page.locator('summary').first().focus(); await page.keyboard.press('Enter');
 results.push({keyboardDisclosure:await page.locator('details').first().getAttribute('open')!==null,errors});
 await page.screenshot({path:path.join(out,'faq-open.png'),fullPage:true});
 fs.writeFileSync(path.join(out,'qa.json'),JSON.stringify(results,null,2)); console.log(JSON.stringify(results,null,2));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
