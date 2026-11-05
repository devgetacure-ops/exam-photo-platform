import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "../../../apps/web/node_modules/sharp/dist/index.cjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const campaign = path.resolve(here, "..");
const root = path.resolve(campaign, "..", "..");
const source = path.join(root, "campaigns", "launch-2026-v3", "source-ui");
const examples = path.join(root, "apps", "web", "public", "examples", "band");
const out = path.join(campaign, "exports");

const C = { ink: "#0e0e0d", paper: "#faf8f3", warm: "#eee9df", signal: "#f04e23", rust: "#c8320f", muted: "#aaa297", charcoal: "#2d2a26", green: "#8ec89a" };
const esc = (s) => String(s).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const svg = (W,H,content,bg=C.ink) => Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><rect width="${W}" height="${H}" fill="${bg}"/>${content}</svg>`);
const text = (lines,x,y,size,step,{fill=C.paper,family="Agency FB",weight=700,anchor="start",tracking=0}={}) => `<text x="${x}" y="${y}" fill="${fill}" font-family="${family}" font-size="${size}" font-weight="${weight}" text-anchor="${anchor}" letter-spacing="${tracking}">${lines.map((line,i)=>`<tspan x="${x}" dy="${i?step:0}">${esc(line)}</tspan>`).join("")}</text>`;
const body = (lines,x,y,size=25,step=36,fill=C.muted,anchor="start") => text(lines,x,y,size,step,{fill,family:"Bahnschrift",weight:400,anchor});
const label = (s,x,y,fill=C.muted,anchor="start") => text([s.toUpperCase()],x,y,15,18,{fill,family:"Bahnschrift",weight:700,tracking:2,anchor});
const rule = (x1,y1,x2,y2,color=C.charcoal,w=2) => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${w}"/>`;
const rect = (x,y,w,h,fill="none",stroke="none",sw=0,r=0) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>`;
const arrow = (x1,y1,x2,y2,color=C.signal,w=4) => `${rule(x1,y1,x2,y2,color,w)}<path d="M${x2-14} ${y2-10} L${x2} ${y2} L${x2-14} ${y2+10}" fill="none" stroke="${color}" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round"/>`;

async function contain(file,w,h,bg=C.paper) { return sharp(file).resize({width:Math.round(w),height:Math.round(h),fit:"contain",background:bg}).png().toBuffer(); }
async function crop(file,w,h,position="centre") { return sharp(file).resize({width:Math.round(w),height:Math.round(h),fit:"cover",position}).png().toBuffer(); }
async function watermark(file,w,h) {
  const base=await contain(file,w,h,C.paper);
  const mark=svg(w,h,`<g transform="translate(${w/2} ${h/2}) rotate(-26)" opacity=".56" fill="#fff" stroke="#111" stroke-width="1" paint-order="stroke" font-family="Bahnschrift" font-size="${Math.max(19,Math.round(w*.064))}" font-weight="700" letter-spacing="2" text-anchor="middle"><text y="-42">EXAMUPLOADKIT PREVIEW</text><text y="42">EXAMUPLOADKIT PREVIEW</text></g>`,"transparent");
  return sharp(base).composite([{input:mark}]).png().toBuffer();
}
async function render(file,W,H,content,composites=[],bg=C.ink){
  await fs.mkdir(path.dirname(file),{recursive:true});
  await sharp({create:{width:W,height:H,channels:3,background:bg}}).composite([{input:svg(W,H,content,"transparent")},...composites]).png({compressionLevel:9}).withMetadata({density:144}).toFile(file);
  return file;
}

function journey(W,y,active,total=8,dark=true){
  const x0=64,x1=W-64,gap=(x1-x0)/(total-1),line=dark?"#443d37":"#d4cec3";
  let s=rule(x0,y,x1,y,line,3);
  for(let i=1;i<=total;i++){
    const x=x0+(i-1)*gap,on=i<=active;
    s+=`<circle cx="${x}" cy="${y}" r="${i===active?12:7}" fill="${on?C.signal:line}"/>`;
  }
  return s;
}
function footer(W,H,index,total,dark=true){
  const fill=dark?C.muted:"#686159";
  return `${label("EXAMUPLOADKIT.COM",56,H-34,fill)}${label(`${String(index).padStart(2,"0")} / ${String(total).padStart(2,"0")}`,W-56,H-34,fill,"end")}`;
}
function titleBlock(s,W,H,index,total,dark=true){
  const landscape=W/H>1.3, square=Math.abs(W/H-1)<.08;
  const x=landscape?70:64, top=landscape?78:72, size=landscape?63:square?67:78, step=size*.92;
  const fg=dark?C.paper:C.ink, descY=top+size+(s.title.length-1)*step+46;
  return {x,top,size,step,descY,fg,landscape,square,html:`${journey(W,42,index,total,dark)}${text(s.title,x,top+size,size,step,{fill:fg})}${body(s.body,x,descY,landscape?22:24,34,dark?C.muted:"#57514a")}`};
}

const slides=[
  {kind:"route",title:["FROM EXAM NOTICE", "TO READY FILES."],body:["One guided route. The examination sets the rules.","You stay in control of every file."]},
  {kind:"find",title:["FIND THE EXAM.","START WITH ITS RULES."],body:["Search by name or short form.","The selected examination configures everything that follows."]},
  {kind:"scope",title:["KNOW WHAT WE PREPARE.","KNOW WHAT THE PORTAL KEEPS."],body:["Every requested file is listed before you upload.","Portal-only steps stay clearly outside the kit."]},
  {kind:"select",title:["KEEP ONLY WHAT", "YOUR FORM NEEDS."],body:["Required and optional files stay distinct.","Your selection and price update together."]},
  {kind:"engine",title:["ONE RULESET IN.","THE RIGHT FILE OUT."],body:["Each file gets its own treatment.","No stretching. No generated identity. No guessed rule presented as fact."]},
  {kind:"review",title:["SEE THE RESULT", "BEFORE YOU PAY."],body:["Inspect a protected preview and plain-language checks.","A retry regenerates the file and runs validation again."]},
  {kind:"checkout",title:["REVIEW. PAY.","TAKE YOUR FILES."],body:["The server confirms the quote. Razorpay handles payment.","Clean downloads unlock only after confirmation."]},
  {kind:"trust",title:["THE RULES STAY VISIBLE.","THE LIMITS DO TOO."],body:["Privacy, source markers and portal boundaries are part of the product.","The official examination portal remains the final authority."]},
];

async function stage(slide,W,H,platform,index,total){
  const dark=index%2===1 || slide.kind==="trust" || slide.kind==="engine";
  const bg=dark?C.ink:C.paper;
  const t=titleBlock(slide,W,H,index,total,dark);
  const landscape=t.landscape, square=t.square;
  const sx=landscape?Math.round(W*.50):64;
  const sy=landscape?95:(square?395:435);
  const sw=landscape?W-sx-64:W-128;
  const sh=H-sy-(landscape?70:105);
  let art="", composites=[];
  const paper=dark?C.paper:C.ink, panel=dark?"#171615":"#ffffff", line=dark?"#4b443d":"#cec6ba";

  if(slide.kind==="route"){
    const steps=["FIND","READ","CHOOSE","UPLOAD","PREVIEW","PAY","DOWNLOAD"];
    const y=sy+Math.min(sh*.42,300), gap=sw/(steps.length-1);
    art+=rect(sx,sy,sw,sh,panel,dark?"#36302b":"#d9d2c8",2,14);
    art+=`<path d="M${sx+55} ${y} C ${sx+sw*.28} ${y-135}, ${sx+sw*.62} ${y+135}, ${sx+sw-55} ${y}" fill="none" stroke="${C.signal}" stroke-width="6" stroke-linecap="round"/>`;
    steps.forEach((v,i)=>{const x=sx+35+i*gap; const yy=y+Math.sin(i*1.2)*50; art+=`<circle cx="${x}" cy="${yy}" r="${i===0||i===steps.length-1?30:18}" fill="${i===steps.length-1?C.signal:(dark?C.paper:C.ink)}"/>${label(v,x,yy+65,dark?C.paper:C.ink,"middle")}`;});
    art+=text(["THE EXAM IS THE STARTING POINT."],sx+42,sy+sh-95,landscape?30:41,44,{fill:paper});
    art+=body(["Not a generic resize preset."],sx+42,sy+sh-48,22,30,dark?C.muted:"#5d5750");
  }
  if(slide.kind==="find"){
    const iw=landscape?sw:Math.round(sw*.64), ih=landscape?Math.round(sh*.56):Math.round(sh*.46);
    const shot=await crop(path.join(source,"01-home-hero.png"),iw,ih,"north");
    art+=rect(sx,sy,iw,ih,dark?C.paper:C.ink,"none",0,8);
    composites.push({input:shot,left:sx,top:sy});
    const bx=landscape?sx:sx+iw+24, by=landscape?sy+ih+22:sy, bw=landscape?iw:sw-iw-24;
    art+=rect(bx,by,bw,landscape?sh-ih-22:ih,C.signal,"none",0,8);
    art+=text(["770"],bx+24,by+88,landscape?68:78,70,{fill:C.ink});
    art+=label("EXAM RECORDS",bx+24,by+122,C.ink);
    art+=body(["Search → choose →", "open its file list"],bx+24,by+174,21,31,C.ink);
    art+=rect(sx,sy+ih+24,sw,Math.max(95,sh-ih-24),panel,line,2,10);
    art+=label("WHAT CHANGES WITH THE EXAM",sx+24,sy+ih+58,dark?C.muted:"#675f56");
    art+=body(["files requested  ·  dimensions  ·  KB  ·  format  ·  filename"],sx+24,sy+ih+100,landscape?20:23,30,paper);
  }
  if(slide.kind==="scope"){
    const shot=await crop(path.join(source,"09-exam-page.png"),sw,Math.round(sh*.48),"north");
    composites.push({input:shot,left:sx,top:sy});
    art+=rect(sx,sy,sw,Math.round(sh*.48),"none",C.signal,5,6);
    const y=sy+Math.round(sh*.48)+24, col=(sw-20)/2;
    art+=rect(sx,y,col,sh-(y-sy),dark?"#191817":"#fff",line,2,10);
    art+=rect(sx+col+20,y,col,sh-(y-sy),C.signal,"none",0,10);
    art+=label("WE PREPARE",sx+22,y+38,dark?C.signal:C.rust);
    art+=text(["Signature", "Certificate"],sx+22,y+90,landscape?28:35,48,{fill:paper,family:"Bahnschrift",weight:600});
    art+=label("YOU COMPLETE IN THE PORTAL",sx+col+42,y+38,C.ink);
    art+=body(["Live photo", "Identity input", "Online declaration"],sx+col+42,y+84,landscape?20:24,38,C.ink);
  }
  if(slide.kind==="select"){
    const phoneW=landscape?Math.round(sw*.38):Math.round(sw*.42), phoneH=sh;
    const phone=await crop(path.join(source,"14-mobile-prepare.png"),phoneW,phoneH,"north");
    art+=rect(sx-7,sy-7,phoneW+14,phoneH+14,C.signal,"none",0,12);
    composites.push({input:phone,left:sx,top:sy});
    const bx=sx+phoneW+30,bw=sw-phoneW-30;
    art+=rect(bx,sy,bw,sh,panel,line,2,12);
    const rows=[['REQUIRED','Scanned signature','₹3'],['OPTIONAL','Certificate','included'],['PORTAL','Live capture','you do this']];
    rows.forEach((r,i)=>{const y=sy+34+i*(landscape?110:145);art+=label(r[0],bx+24,y+18,i===0?C.signal:(dark?C.muted:'#6a6258'));art+=body([r[1]],bx+24,y+56,landscape?20:24,30,paper);art+=label(r[2],bx+bw-20,y+56,i===0?C.signal:paper,"end");if(i<2)art+=rule(bx+20,y+(landscape?92:120),bx+bw-20,y+(landscape?92:120),line,2);});
    art+=rect(bx+20,sy+sh-102,bw-40,72,C.signal,"none",0,5);
    art+=text(["PRICE FOLLOWS THE KIT"],bx+bw/2,sy+sh-55,landscape?23:29,30,{fill:C.ink,anchor:"middle"});
  }
  if(slide.kind==="engine"){
    const photoW=landscape?Math.round(sw*.27):Math.round(sw*.29), photoH=Math.round(sh*.52);
    const before=await contain(path.join(examples,"photo-a1-uploaded.jpg"),photoW,photoH,C.paper);
    const after=await contain(path.join(examples,"photo-a1-prepared.jpg"),photoW,photoH,C.paper);
    composites.push({input:before,left:sx,top:sy},{input:after,left:sx+sw-photoW,top:sy});
    art+=rect(sx-5,sy-5,photoW+10,photoH+10,C.paper,C.muted,2,3)+rect(sx+sw-photoW-5,sy-5,photoW+10,photoH+10,C.signal,C.signal,2,3);
    art+=arrow(sx+photoW+25,sy+photoH/2,sx+sw-photoW-25,sy+photoH/2,C.signal,5);
    art+=label("SOURCE",sx,sy+photoH+38,C.muted)+label("PREPARED",sx+sw,sy+photoH+38,C.signal,"end");
    const yy=sy+photoH+80, items=["CHECK FILE","FRAME SUBJECT","SET BACKGROUND","RESIZE + COMPRESS","NAME FOR PORTAL"];
    items.forEach((v,i)=>{const w=(sw-32)/5,x=sx+i*(w+8);art+=rect(x,yy,w,landscape?72:100,i===4?C.signal:"#1a1918",i===4?C.signal:C.charcoal,2,5);art+=label(v,x+w/2,yy+(landscape?42:55),i===4?C.ink:C.paper,"middle");});
    art+=body(["Photographs, signatures, thumbs, declarations and documents do not share one treatment."],sx,sy+sh-34,landscape?19:22,30,C.muted);
  }
  if(slide.kind==="review"){
    const pw=landscape?Math.round(sw*.28):Math.round(sw*.31), ph=Math.round(sh*.50);
    const before=await contain(path.join(examples,"photo-a2-uploaded.jpg"),pw,ph,C.paper);
    const after=await watermark(path.join(examples,"photo-a2-prepared.jpg"),pw,ph);
    composites.push({input:before,left:sx,top:sy},{input:after,left:sx+pw+28,top:sy});
    art+=rect(sx-5,sy-5,pw+10,ph+10,dark?C.paper:C.ink,"none",0,3)+rect(sx+pw+23,sy-5,pw+10,ph+10,C.signal,"none",0,3);
    art+=label("UPLOADED",sx,sy+ph+34,dark?C.muted:'#625c54')+label("PROTECTED PREVIEW",sx+pw+28,sy+ph+34,C.signal);
    const bx=sx+pw*2+62,bw=sw-(pw*2+62);
    art+=rect(bx,sy,bw,ph,panel,line,2,10);
    art+=label("PLAIN-LANGUAGE CHECK",bx+20,sy+36,dark?C.muted:'#625c54');
    const checks=["dimensions","file size","format","framing","filename"];
    checks.forEach((v,i)=>{const y=sy+78+i*(landscape?50:62);art+=`<circle cx="${bx+28}" cy="${y-6}" r="8" fill="${C.green}"/><path d="M${bx+24} ${y-6}l3 4 7-9" fill="none" stroke="${C.ink}" stroke-width="2"/>`;art+=body([v],bx+48,y,landscape?19:22,28,paper);});
    const ry=sy+ph+70,rh=Math.max(88,sh-ph-70);
    art+=rect(sx,ry,sw,rh,C.signal,"none",0,8);
    const retry=[['EDIT','adjust the input'],['REGENERATE','build a new file'],['VALIDATE','run every check']];
    retry.forEach((r,i)=>{const rw=(sw-48)/3,x=sx+i*(rw+24);art+=text([r[0]],x+rw/2,ry+56,landscape?24:29,30,{fill:C.ink,anchor:'middle'});art+=body([r[1]],x+rw/2,ry+91,landscape?16:19,25,C.ink,'middle');if(i<2)art+=arrow(x+rw+5,ry+70,x+rw+19,ry+70,C.ink,2);});
  }
  if(slide.kind==="checkout"){
    const nodes=[['1','REVIEW','protected preview'],['2','QUOTE','price locked'],['3','PAY','Razorpay'],['4','UNLOCK','clean files'],['5','KEEP','download / email']];
    const gap=landscape?18:14, nw=(sw-gap*4)/5, ny=sy+36;
    nodes.forEach((n,i)=>{const x=sx+i*(nw+gap);art+=rect(x,ny,nw,landscape?185:240,i===2?C.signal:panel,i===2?C.signal:line,2,10);art+=text([n[0]],x+18,ny+50,landscape?37:46,48,{fill:i===2?C.ink:C.signal});art+=label(n[1],x+18,ny+(landscape?89:105),i===2?C.ink:paper);art+=body([n[2]],x+18,ny+(landscape?125:150),landscape?16:19,28,i===2?C.ink:(dark?C.muted:'#5f584f'));if(i<4)art+=arrow(x+nw+2,ny+(landscape?92:120),x+nw+gap-2,ny+(landscape?92:120),C.signal,3);});
    const by=ny+(landscape?225:295), boxW=(sw-22)/2;
    art+=rect(sx,by,boxW,sh-(by-sy),panel,line,2,10)+rect(sx+boxW+22,by,boxW,sh-(by-sy),panel,line,2,10);
    art+=text(["₹3"],sx+24,by+86,landscape?70:92,90,{fill:paper})+body(["one prepared file","preview before payment","portal-ready filename"],sx+24,by+126,20,34,dark?C.muted:'#5e574f');
    art+=text(["₹5"],sx+boxW+46,by+86,landscape?70:92,90,{fill:paper})+body(["the whole selected kit","individual files + ZIP","PDF work included"],sx+boxW+46,by+126,20,34,dark?C.muted:'#5e574f');
    art+=label("WHATSAPP SENDS A REMINDER LINK — NOT THE FILES",sx+sw/2,sy+sh-28,dark?C.muted:'#5e574f','middle');
  }
  if(slide.kind==="trust"){
    const facts=[['RULES',['Published source,','or an estimate marker.']],['IDENTITY',['No generated face or outfit.','No whitening or reshaping.']],['PRIVACY',['No account. Uploads are not','used to train models.']],['RETENTION',['Deleted within 30 minutes;','up to one hour if requested.']],['BOUNDARY',['Live capture and portal-only','steps stay with the portal.']],['GUIDANCE',['Review the result and the','exam instructions before upload.']]];
    const cols=landscape?3:2, gap=18, rows=Math.ceil(facts.length/cols), cw=(sw-gap*(cols-1))/cols, ch=(sh-gap*(rows-1))/rows;
    facts.forEach((f,i)=>{const x=sx+(i%cols)*(cw+gap),y=sy+Math.floor(i/cols)*(ch+gap),hot=i===2||i===3;art+=rect(x,y,cw,ch,hot?C.signal:"#181716",hot?C.signal:C.charcoal,2,10);art+=label(f[0],x+22,y+38,hot?C.ink:C.signal);art+=body(f[1],x+22,y+82,landscape?17:20,29,hot?C.ink:C.paper);});
  }
  return {dark,bg,html:t.html+art+footer(W,H,index,total,dark),composites};
}

async function buildSet(name,W,H,set){
  const files=[];
  for(let i=0;i<set.length;i++){
    const s=set[i],built=await stage(s,W,H,name,i+1,set.length);
    const file=path.join(out,`${name}-product-overview`,`${String(i+1).padStart(2,'0')}.png`);
    files.push(await render(file,W,H,built.html,built.composites,built.bg));
  }
  return files;
}
async function contact(name,files,tw,th,cols){
  const pad=24,gap=14,rows=Math.ceil(files.length/cols),buffers=await Promise.all(files.map(f=>sharp(f).resize({width:tw,height:th,fit:"contain",background:"#050505"}).png().toBuffer()));
  const file=path.join(out,"reviews",`${name}.png`);await fs.mkdir(path.dirname(file),{recursive:true});
  await sharp({create:{width:pad*2+cols*tw+(cols-1)*gap,height:pad*2+rows*th+(rows-1)*gap,channels:3,background:"#050505"}}).composite(buffers.map((input,i)=>({input,left:pad+(i%cols)*(tw+gap),top:pad+Math.floor(i/cols)*(th+gap)}))).png().toFile(file);return file;
}

const instagram=await buildSet("instagram",1080,1350,slides);
const linkedin=await buildSet("linkedin",1200,1500,slides);
const redditSet=[slides[0],slides[1],slides[2],slides[4],slides[6],slides[7]];
const reddit=await buildSet("reddit",1080,1080,redditSet);
const xSet=[
  {kind:"find",title:["FIND THE EXAM.","LET ITS RULES LEAD."],body:["Search the examination. Open its file list. Start with the actual requirement."]},
  {kind:"scope",title:["SEE THE WHOLE FORM.","KEEP WHAT APPLIES."],body:["Prepared files and portal-only steps are separated before you upload."]},
  {kind:"engine",title:["UPLOAD ONCE.","WATCH EACH RULE APPLY."],body:["Frame, background, pixels, KB, format and filename — then a protected preview."]},
  {kind:"checkout",title:["REVIEW FIRST.","PAY, DOWNLOAD, SUBMIT."],body:["₹3 for one file. ₹5 for the kit. No account. Short retention."]},
];
const x=await buildSet("x",1600,900,xSet);
const reviews={
  instagram:await contact("instagram",instagram,216,270,4),
  linkedin:await contact("linkedin",linkedin,200,250,4),
  reddit:await contact("reddit",reddit,216,216,3),
  x:await contact("x",x,320,180,2),
};
const manifest={generatedAt:new Date().toISOString(),story:"guided application journey",sourcePolicy:"Interface crops are live-site captures from 2 October 2026. Diagrams explain verified product behavior; example photographs are the site's disclosed representational assets.",counts:{instagram:instagram.length,linkedin:linkedin.length,reddit:reddit.length,x:x.length},files:[...instagram,...linkedin,...reddit,...x].map(f=>path.relative(campaign,f).replaceAll('\\','/')),reviews:Object.fromEntries(Object.entries(reviews).map(([k,v])=>[k,path.relative(campaign,v).replaceAll('\\','/')]))};
await fs.writeFile(path.join(out,"manifest.json"),JSON.stringify(manifest,null,2)+"\n");
console.log(JSON.stringify(manifest.counts,null,2));
