const sharp = require('sharp');
(async()=>{
const path = require('path');
const outDir = path.join(process.cwd(), 'campaigns', 'launch-2026-v3', 'reference-review');
const root = 'C:\\Users\\dmbar\\Downloads\\Telegram Desktop\\glass grad';
const refs = [
  {file:'Screenshot_2026_10_02_09_39_38_84_1c337646f29875672b5a61192b9010f9.jpg', x:0,y:330,w:632,h:290, title:'DARK 01', note:'Frosted glass, one colour source'},
  {file:'Screenshot_2026_10_02_09_39_38_84_1c337646f29875672b5a61192b9010f9.jpg', x:632,y:590,w:632,h:790, title:'DARK 02', note:'Gradient used as light and depth'},
  {file:'Screenshot_2026_10_02_09_39_57_71_1c337646f29875672b5a61192b9010f9.jpg', x:0,y:565,w:632,h:785, title:'DARK 03', note:'Black field, warm restrained glow'},
  {file:'Screenshot_2026_10_02_09_39_33_92_1c337646f29875672b5a61192b9010f9.jpg', x:632,y:625,w:632,h:790, title:'LIGHT 01', note:'White surface, colour held at edge'},
  {file:'Screenshot_2026_10_02_09_39_19_25_1c337646f29875672b5a61192b9010f9.jpg', x:632,y:1400,w:632,h:790, title:'LIGHT 02', note:'Cream field, soft warm colour pool'},
  {file:'Screenshot_2026_10_02_09_39_57_71_1c337646f29875672b5a61192b9010f9.jpg', x:632,y:565,w:632,h:790, title:'LIGHT 03', note:'Blurred organic colour and texture'},
];
const W=1800,H=2380, margin=72,gap=36,cardW=810,cardH=680,imgH=535;
const comps=[];
comps.push({input:Buffer.from(`<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#111214"/><text x="72" y="96" fill="#f7f3ec" font-family="Arial" font-size="46" font-weight="700">REFERENCE EDIT — WHAT TO KEEP</text><text x="72" y="145" fill="#a8a49d" font-family="Arial" font-size="25">Six cues selected from the folder. These guide atmosphere and restraint, not literal copying.</text></svg>`),left:0,top:0});
for(let i=0;i<refs.length;i++){
 const ref=refs[i], col=i%2,row=Math.floor(i/2), left=margin+col*(cardW+gap),top=205+row*(cardH+gap);
 const crop=await sharp(path.join(root,ref.file)).extract({left:ref.x,top:ref.y,width:ref.w,height:ref.h}).resize(cardW,imgH,{fit:'cover'}).jpeg({quality:92}).toBuffer();
 const label=Buffer.from(`<svg width="${cardW}" height="${cardH-imgH}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#1b1c1f"/><text x="28" y="52" fill="#ff5a32" font-family="Arial" font-size="22" font-weight="700" letter-spacing="2">${ref.title}</text><text x="28" y="99" fill="#f3f0e9" font-family="Arial" font-size="27">${ref.note}</text></svg>`);
 const card=await sharp({create:{width:cardW,height:cardH,channels:4,background:'#1b1c1f'}}).composite([{input:crop,left:0,top:0},{input:label,left:0,top:imgH}]).png().toBuffer();
 comps.push({input:card,left,top});
}
const foot=Buffer.from(`<svg width="${W}" height="170" xmlns="http://www.w3.org/2000/svg"><line x1="0" y1="1" x2="${W}" y2="1" stroke="#333438"/><text x="0" y="57" fill="#f3f0e9" font-family="Arial" font-size="28" font-weight="700">Shared rule for both routes</text><text x="0" y="103" fill="#aaa69f" font-family="Arial" font-size="24">One connected panorama across EXAM / UPLOAD / KIT. Exact logo. Equal scale. Quiet centre. Effects stay behind the identity.</text></svg>`);
comps.push({input:foot,left:margin,top:2200});
await sharp({create:{width:W,height:H,channels:4,background:'#111214'}}).composite(comps).jpeg({quality:94}).toFile(path.join(outDir,'selected-references.jpg'));
console.log(path.join(outDir,'selected-references.jpg'));
})();

