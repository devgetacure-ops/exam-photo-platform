import fs from 'node:fs/promises';
import path from 'node:path';
import sharp from '../../../apps/web/node_modules/sharp/dist/index.cjs';

const root=path.resolve('.');
const out=path.join(root,'campaigns','launch-2026-v3','cover-directions');
const brand=path.join(root,'apps','web','public','brand');
const sources={dark:path.join(brand,'examuploadkit-stacked-dark.png'),light:path.join(brand,'examuploadkit-stacked-light.png')};
const ids=['exam','upload','kit'];
const rows={
  exam:{left:1028,top:96,width:744,height:224},
  upload:{left:844,top:316,width:1112,height:224},
  kit:{left:1120,top:536,width:560,height:224},
};
const W=3240,H=1350,CARD=1080,logoH=190,logoY=580;
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');

async function sourceBg(file){
  const b=await sharp(file).extract({left:0,top:0,width:1,height:1}).removeAlpha().raw().toBuffer();
  return `rgb(${b[0]},${b[1]},${b[2]})`;
}
async function rowLogo(file,id){return sharp(file).extract(rows[id]).resize({height:logoH}).png().toBuffer();}
function svg(s){return Buffer.from(s);}

function coverUtility(){
 return ids.map((_,i)=>{
   const x=i*CARD;
   const steps=Array.from({length:8},(_,n)=>`<rect x="${x+443+n*25}" y="1254" width="${n===0?17:9}" height="4" rx="2" fill="${n===0?'#f04e23':'#ffffff'}" opacity="${n===0?'.95':'.22'}"/>`).join('');
   return `<g font-family="Bahnschrift">
    <text x="${x+64}" y="1265" fill="#f4f0e9" fill-opacity=".62" font-size="17" font-weight="600" letter-spacing="2.1">EXAMUPLOADKIT.COM</text>
    ${steps}
    <text x="${x+928}" y="1265" fill="#f4f0e9" fill-opacity=".62" font-size="17" font-weight="600" letter-spacing="1.8">SWIPE</text>
    <path d="M${x+1001} 1258h20m-7-7 7 7-7 7" fill="none" stroke="#f4f0e9" stroke-opacity=".62" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
   </g>`;
 }).join('');
}

function darkArt(panelBg){return svg(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<defs>
 <linearGradient id="base" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#04050a"/><stop offset=".5" stop-color="#090a0e"/><stop offset="1" stop-color="#05070b"/></linearGradient>
 <radialGradient id="rose"><stop stop-color="#ff326f" stop-opacity=".88"/><stop offset=".34" stop-color="#dc235c" stop-opacity=".34"/><stop offset="1" stop-color="#b9134a" stop-opacity="0"/></radialGradient>
 <radialGradient id="seamGlow"><stop stop-color="#ff477f" stop-opacity=".88"/><stop offset=".42" stop-color="#ff2f70" stop-opacity=".66"/><stop offset=".74" stop-color="#e92061" stop-opacity=".24"/><stop offset="1" stop-color="#d71955" stop-opacity="0"/></radialGradient>
 <radialGradient id="blue"><stop stop-color="#b8efff" stop-opacity=".72"/><stop offset=".22" stop-color="#52bfff" stop-opacity=".36"/><stop offset=".62" stop-color="#3459f2" stop-opacity=".12"/><stop offset="1" stop-color="#213ac9" stop-opacity="0"/></radialGradient>
 <radialGradient id="warm"><stop stop-color="#ffb056" stop-opacity=".28"/><stop offset="1" stop-color="#ff6a2d" stop-opacity="0"/></radialGradient>
 <linearGradient id="glass" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#ffffff" stop-opacity=".085"/><stop offset=".44" stop-color="#ffffff" stop-opacity=".018"/><stop offset="1" stop-color="#000000" stop-opacity=".12"/></linearGradient>
 <filter id="b80"><feGaussianBlur stdDeviation="80"/></filter><filter id="b36"><feGaussianBlur stdDeviation="36"/></filter>
 <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".78" numOctaves="3" seed="41"/><feColorMatrix values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 .032 0"/></filter>
 <filter id="shadow" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="26" stdDeviation="36" flood-color="#000" flood-opacity=".65"/></filter>
</defs>
<rect width="${W}" height="${H}" fill="url(#base)"/>
<ellipse cx="140" cy="170" rx="930" ry="750" fill="url(#rose)" filter="url(#b80)" opacity=".48"/>
<ellipse cx="3235" cy="1265" rx="1020" ry="720" fill="url(#blue)" filter="url(#b80)" opacity=".48"/>
<ellipse cx="1740" cy="1380" rx="720" ry="380" fill="url(#warm)" filter="url(#b80)" opacity=".3"/>
<circle cx="1080" cy="440" r="205" fill="url(#seamGlow)"/>
<rect x="112" y="365" width="3016" height="620" rx="66" fill="#08090d" fill-opacity=".82" stroke="#ffffff" stroke-opacity=".13" stroke-width="2" filter="url(#shadow)"/>
<rect x="112" y="365" width="3016" height="620" rx="66" fill="url(#glass)"/>
<rect x="112" y="365" width="3016" height="2" rx="1" fill="#ffffff" opacity=".38"/>
<path d="M165 918 C 740 855 1100 1018 1650 936 S 2600 855 3075 925" fill="none" stroke="#ffffff" stroke-opacity=".07" stroke-width="2"/>
<rect x="112" y="520" width="3016" height="330" fill="${panelBg}"/>
<rect x="112" y="520" width="3016" height="1" fill="#ffffff" opacity=".1"/>
<rect x="112" y="849" width="3016" height="1" fill="#ffffff" opacity=".08"/>
<g fill="#ffffff" opacity=".22"><circle cx="170" cy="418" r="3"/><circle cx="3070" cy="930" r="3"/></g>
${coverUtility()}
<rect width="${W}" height="${H}" filter="url(#grain)" opacity=".55"/>
</svg>`);}

function lightArt(panelBg){return svg(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<defs>
 <linearGradient id="paper" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#f5f0e8"/><stop offset=".5" stop-color="#fbf8f2"/><stop offset="1" stop-color="#f1eee8"/></linearGradient>
 <radialGradient id="peach"><stop stop-color="#ff725e" stop-opacity=".70"/><stop offset=".35" stop-color="#ff9d80" stop-opacity=".36"/><stop offset="1" stop-color="#ffb695" stop-opacity="0"/></radialGradient>
 <radialGradient id="lilac"><stop stop-color="#9b68ff" stop-opacity=".52"/><stop offset=".48" stop-color="#bc95ff" stop-opacity=".18"/><stop offset="1" stop-color="#d3bbff" stop-opacity="0"/></radialGradient>
 <radialGradient id="lime"><stop stop-color="#9ddb65" stop-opacity=".52"/><stop offset=".5" stop-color="#bfe593" stop-opacity=".18"/><stop offset="1" stop-color="#d8efbf" stop-opacity="0"/></radialGradient>
 <linearGradient id="glass" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#ffffff" stop-opacity=".82"/><stop offset=".5" stop-color="#ffffff" stop-opacity=".58"/><stop offset="1" stop-color="#ffffff" stop-opacity=".42"/></linearGradient>
 <pattern id="tiles" width="54" height="54" patternUnits="userSpaceOnUse"><rect x="3" y="3" width="48" height="48" rx="12" fill="none" stroke="#ffffff" stroke-opacity=".38" stroke-width="1.2"/></pattern>
 <filter id="b90"><feGaussianBlur stdDeviation="90"/></filter>
 <filter id="shadow" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="34" stdDeviation="44" flood-color="#695c50" flood-opacity=".17"/></filter>
 <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".72" numOctaves="3" seed="19"/><feColorMatrix values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 .026 0"/></filter>
</defs>
<rect width="${W}" height="${H}" fill="url(#paper)"/>
<ellipse cx="20" cy="1160" rx="900" ry="630" fill="url(#peach)" filter="url(#b90)"/>
<ellipse cx="820" cy="1380" rx="760" ry="450" fill="url(#lilac)" filter="url(#b90)"/>
<ellipse cx="3230" cy="90" rx="900" ry="640" fill="url(#lime)" filter="url(#b90)"/>
<ellipse cx="2700" cy="-120" rx="620" ry="400" fill="url(#lilac)" filter="url(#b90)" opacity=".42"/>
<rect x="70" y="315" width="3100" height="720" rx="92" fill="url(#glass)" stroke="#ffffff" stroke-opacity=".94" stroke-width="3" filter="url(#shadow)"/>
<rect x="70" y="315" width="3100" height="720" rx="92" fill="none" stroke="#8b8177" stroke-opacity=".10" stroke-width="2"/>
<rect x="70" y="315" width="3100" height="3" rx="1.5" fill="#ffffff" opacity=".95"/>
<path d="M130 950 C 620 900 1000 1020 1510 945 S 2500 900 3110 960" fill="none" stroke="#ffffff" stroke-opacity=".62" stroke-width="2"/>
<rect x="70" y="520" width="3100" height="330" fill="${panelBg}"/>
<rect x="70" y="520" width="3100" height="1" fill="#8a8177" opacity=".10"/>
<rect x="70" y="849" width="3100" height="1" fill="#8a8177" opacity=".08"/>
<rect x="0" y="1030" width="1080" height="320" fill="url(#tiles)" opacity=".22"/>
<rect x="2510" y="0" width="730" height="300" fill="url(#tiles)" opacity=".20"/>
<rect width="${W}" height="${H}" filter="url(#grain)" opacity=".46"/>
</svg>`);}

async function build(theme){
 const file=sources[theme]; const panelBg=await sourceBg(file);
 const art=theme==='dark'?darkArt(panelBg):lightArt(panelBg);
 const comps=[];
 for(let i=0;i<ids.length;i++){
   const logo=await rowLogo(file,ids[i]); const meta=await sharp(logo).metadata();
   comps.push({input:logo,left:i*CARD+Math.round((CARD-meta.width)/2),top:logoY});
 }
 const pano=await sharp(art).composite(comps).png({compressionLevel:9}).toBuffer();
 const dir=path.join(out,theme); await fs.mkdir(dir,{recursive:true});
 await fs.writeFile(path.join(dir,'panorama.png'),pano);
 for(let i=0;i<ids.length;i++) await sharp(pano).extract({left:i*CARD,top:0,width:CARD,height:H}).png({compressionLevel:9}).toFile(path.join(dir,`${ids[i]}.png`));
 const thumbs=[];
 for(let i=0;i<ids.length;i++){
   const thumb=await sharp(pano).extract({left:i*CARD,top:0,width:CARD,height:H}).resize({width:532,height:665}).png().toBuffer();
   thumbs.push({input:thumb,left:36+i*540,top:36});
 }
 const grid=await sharp({create:{width:1692,height:737,channels:3,background:theme==='dark'?'#1b1c21':'#e7e1d8'}}).composite(thumbs).png().toBuffer();
 await fs.writeFile(path.join(dir,'grid.png'),grid);
 return grid;
}

await fs.mkdir(out,{recursive:true});
const dark=await build('dark'),light=await build('light');
const label=(title,sub,w=1764)=>svg(`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="105"><text x="0" y="38" fill="#181818" font-family="Arial" font-size="28" font-weight="700">${esc(title)}</text><text x="0" y="76" fill="#6c665f" font-family="Arial" font-size="20">${esc(sub)}</text></svg>`);
await sharp({create:{width:1836,height:1814,channels:3,background:'#f1eee8'}}).composite([
 {input:label('DARK / CONTROLLED LIGHT','Frosted depth, one concealed colour source, cool ambient edge.'),left:36,top:28},
 {input:dark,left:72,top:122},
 {input:label('LIGHT / QUIET COLOUR','Cream glass surface, colour held to the perimeter, subtle texture.'),left:36,top:925},
 {input:light,left:72,top:1019}
]).png({compressionLevel:9}).toFile(path.join(out,'comparison.png'));
await fs.writeFile(path.join(out,'README.md'),`# Final cover directions\n\nTwo distinct 3240 x 1350 panoramas, each split into three 1080 x 1350 Instagram covers. The authorised logo rows are cropped directly from the supplied brand assets, all at 190 px high and aligned to the same baseline.\n\n- dark/: controlled light and restrained glass\n- light/: quiet colour and cream glass\n\nThe campaign export folders are unchanged until a direction is approved.\n`);
console.log(JSON.stringify({out,panelBackgrounds:{dark:await sourceBg(sources.dark),light:await sourceBg(sources.light)}},null,2));
