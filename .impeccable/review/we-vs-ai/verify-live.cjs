const {chromium}=require('C:/Users/dmbar/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Users/dmbar/AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'});
 const page=await browser.newPage(); const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const checks=[];
 for(const width of [390,1440]){
  await page.setViewportSize({width,height:900});
  const response=await page.goto('https://examuploadkit.com/we-vs-ai',{waitUntil:'networkidle'});
  await page.evaluate(()=>document.fonts.ready);
  checks.push({width,status:response.status(),...await page.evaluate(()=>({heading:document.querySelector('h1')?.textContent,canonical:document.querySelector('link[rel=canonical]')?.href,overflow:document.documentElement.scrollWidth>innerWidth,faqs:document.querySelectorAll('details').length}))});
  await page.screenshot({path:__dirname+'/live-'+width+'.png'});
 }
 await page.locator('summary').first().focus();await page.keyboard.press('Enter');
 checks.push({keyboardDisclosure:await page.locator('details').first().getAttribute('open')!==null,errors});
 for(const route of ['/sitemap.xml','/llms.txt']){const r=await page.request.get('https://examuploadkit.com'+route);checks.push({route,status:r.status(),containsComparison:(await r.text()).includes('/we-vs-ai')});}
 fs.writeFileSync(__dirname+'/live-qa.json',JSON.stringify(checks,null,2));console.log(JSON.stringify(checks,null,2));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
