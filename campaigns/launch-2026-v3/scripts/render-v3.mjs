import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "../../../apps/web/node_modules/sharp/dist/index.cjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const campaign = path.resolve(here, "..");
const root = path.resolve(campaign, "..", "..");
const ui = path.join(campaign, "source-ui");
const out = path.join(campaign, "exports");
const publicDir = path.join(root, "apps", "web", "public");
const logoDark = path.join(publicDir, "brand", "examuploadkit-stacked-dark.png");
const logoLight = path.join(publicDir, "brand", "examuploadkit-stacked-light.png");
const exampleDir = path.join(publicDir, "examples", "band");

const C = { ink: "#111110", paper: "#faf9f6", paper2: "#f2f0ea", signal: "#f04e23", muted: "#a59d91", line: "#3a352e" };
const rows = {
  exam: { left: 1028, top: 96, width: 744, height: 224 },
  upload: { left: 844, top: 316, width: 1112, height: 224 },
  kit: { left: 1120, top: 536, width: 560, height: 224 },
};

const esc = (s) => String(s).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
function txt(lines, x, y, size, step, o = {}) {
  const { fill = C.paper, family = "Agency FB", weight = 700, anchor = "start", tracking = 0 } = o;
  return `<text x="${x}" y="${y}" fill="${fill}" font-family="${family}" font-size="${size}" font-weight="${weight}" text-anchor="${anchor}" letter-spacing="${tracking}">${lines.map((line,i)=>`<tspan x="${x}" dy="${i?step:0}">${esc(line)}</tspan>`).join("")}</text>`;
}
function body(lines, x, y, size = 28, step = 40, fill = C.muted) {
  return txt(lines,x,y,size,step,{fill,family:"Bahnschrift",weight:400,tracking:0});
}
function footer(W,H,index,total,dark=true) {
  const fill=dark?C.muted:"#55524b";
  return `<text x="64" y="${H-42}" fill="${fill}" font-family="Bahnschrift" font-size="15" font-weight="700" letter-spacing="2">EXAMUPLOADKIT.COM</text><text x="${W-64}" y="${H-42}" fill="${fill}" font-family="Bahnschrift" font-size="15" text-anchor="end">${String(index).padStart(2,"0")} / ${String(total).padStart(2,"0")}</text>`;
}
function svg(W,H,bg,content){return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><rect width="${W}" height="${H}" fill="${bg}"/>${content}</svg>`);}

async function crop(file,width,height,position="centre") {
  return sharp(file).resize({width,height,fit:"cover",position}).png().toBuffer();
}
async function contain(file,width,height,bg=C.paper) {
  return sharp(file).resize({width,height,fit:"contain",background:bg}).png().toBuffer();
}
async function previewPhoto(file,width,height,bg=C.paper) {
  const base=await contain(file,width,height,bg);
  const label=esc("EXAMUPLOADKIT  PREVIEW");
  const fontSize=Math.max(20,Math.round(width*.068));
  const watermark=Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><g transform="translate(${width/2} ${height/2}) rotate(-27)" font-family="Bahnschrift" font-size="${fontSize}" font-weight="700" letter-spacing="2" text-anchor="middle" fill="#ffffff" stroke="#111110" stroke-width="1.15" paint-order="stroke" opacity="0.46"><text x="0" y="-46">${label}</text><text x="0" y="46">${label}</text></g></svg>`);
  return sharp(base).composite([{input:watermark}]).png().toBuffer();
}
async function rowLogo(id,width,variant="dark") {
  const source=variant==="dark"?logoDark:logoLight;
  return sharp(source).extract(rows[id]).resize({width}).png().toBuffer();
}
async function rowLogoAtHeight(id,height,variant="dark") {
  const source=variant==="dark"?logoDark:logoLight;
  return sharp(source).extract(rows[id]).resize({height}).png().toBuffer();
}
async function fullLogo(width,variant="dark") {
  const source=variant==="dark"?logoDark:logoLight;
  return sharp(source).trim({background:variant==="dark"?C.ink:C.paper,threshold:6}).resize({width}).png().toBuffer();
}
async function render(file,W,H,bg,content,composites=[]) {
  await fs.mkdir(path.dirname(file),{recursive:true});
  await sharp({create:{width:W,height:H,channels:3,background:bg}}).composite([{input:svg(W,H,"transparent",content)},...composites]).png({compressionLevel:9}).withMetadata({density:144}).toFile(file);
  return file;
}
function hardFrame(x,y,w,h,dark=false){return `<rect x="${x+8}" y="${y+8}" width="${w}" height="${h}" fill="${dark?C.signal:C.ink}"/><rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${dark?C.ink:C.paper}" stroke="${dark?C.paper:C.ink}" stroke-width="3"/>`;}
function toolTabs(x,y,scale=1){const items=["resize","remove bg","compress","convert","rename","still wrong"];let cursor=x;return items.map((v,i)=>{const w=(v.length*11+34)*scale;const r=`<rect x="${cursor}" y="${y}" width="${w}" height="${54*scale}" fill="${i===5?C.signal:"#1b1815"}" stroke="${i===5?C.signal:C.line}" stroke-width="2"/><text x="${cursor+16*scale}" y="${y+35*scale}" fill="${i===5?C.ink:C.muted}" font-family="Bahnschrift" font-size="${17*scale}" font-weight="600">${v}</text>`;cursor+=w+7*scale;return r;}).join("");}

let coverTriptychBuilt=false;
async function buildCoverTriptych(){
  const W=3240,H=1350;
  const approvedPath=path.join(campaign,"cover-directions","dark","panorama.png");
  try {
    const approved=await fs.readFile(approvedPath);
    const ids=["exam","upload","kit"];
    for(let i=0;i<ids.length;i++){
      const target=path.join(out,"instagram","pinned",ids[i],"01-cover.png");
      await fs.mkdir(path.dirname(target),{recursive:true});
      await sharp(approved).extract({left:i*1080,top:0,width:1080,height:1350}).png({compressionLevel:9}).withMetadata({density:144}).toFile(target);
    }
    return;
  } catch (error) {
    if(error?.code!=="ENOENT") throw error;
  }
  const art=Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#070707"/><stop offset=".48" stop-color="#15110f"/><stop offset="1" stop-color="#050505"/></linearGradient>
      <linearGradient id="signal" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ff3715"/><stop offset=".46" stop-color="#ff6a2a"/><stop offset="1" stop-color="#e83812"/></linearGradient>
      <linearGradient id="glass" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity=".12"/><stop offset=".5" stop-color="#ffffff" stop-opacity=".025"/><stop offset="1" stop-color="#000000" stop-opacity=".18"/></linearGradient>
      <radialGradient id="flare"><stop offset="0" stop-color="#ff5a22" stop-opacity=".42"/><stop offset="1" stop-color="#ff5a22" stop-opacity="0"/></radialGradient>
      <filter id="blur"><feGaussianBlur stdDeviation="42"/></filter>
      <filter id="soft"><feGaussianBlur stdDeviation="14"/></filter>
      <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".72" numOctaves="3" seed="12"/><feColorMatrix values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 .055 0"/></filter>
    </defs>
    <rect width="${W}" height="${H}" fill="url(#bg)"/>
    <ellipse cx="500" cy="420" rx="760" ry="610" fill="url(#flare)" filter="url(#blur)" opacity=".48"/>
    <ellipse cx="2750" cy="980" rx="760" ry="610" fill="url(#flare)" filter="url(#blur)" opacity=".30"/>
    <path d="M-260 1010 C 320 140 900 1160 1410 390 S 2420 1050 3510 250" fill="none" stroke="#ff4b1f" stroke-width="230" stroke-linecap="round" opacity=".16" filter="url(#blur)"/>
    <path d="M-260 1010 C 320 140 900 1160 1410 390 S 2420 1050 3510 250" fill="none" stroke="url(#signal)" stroke-width="104" stroke-linecap="round" opacity=".96"/>
    <path d="M-260 1010 C 320 140 900 1160 1410 390 S 2420 1050 3510 250" fill="none" stroke="#ffcab7" stroke-width="3" stroke-linecap="round" opacity=".72"/>
    <g opacity=".72">
      <rect x="240" y="80" width="530" height="420" rx="44" fill="url(#glass)" stroke="#ffffff" stroke-opacity=".16" stroke-width="2" transform="rotate(-8 505 290)"/>
      <rect x="1390" y="45" width="460" height="390" rx="42" fill="url(#glass)" stroke="#ffffff" stroke-opacity=".14" stroke-width="2" transform="rotate(7 1620 240)"/>
      <rect x="2540" y="110" width="480" height="400" rx="44" fill="url(#glass)" stroke="#ffffff" stroke-opacity=".16" stroke-width="2" transform="rotate(-6 2780 310)"/>
    </g>
    <g fill="none" stroke="#ffffff" stroke-opacity=".12" stroke-width="2">
      <circle cx="40" cy="70" r="390"/><circle cx="3200" cy="1280" r="430"/>
      <path d="M0 225h3240M0 1125h3240"/><path d="M1080 0v1350M2160 0v1350" stroke-opacity=".055"/>
    </g>
    <rect x="0" y="455" width="3240" height="420" fill="#0b0b0b" fill-opacity=".93"/>
    <rect x="0" y="455" width="3240" height="1.5" fill="#ffffff" opacity=".32"/>
    <rect x="0" y="873" width="3240" height="2" fill="#ffffff" opacity=".18"/>
    <path d="M0 890h3240" stroke="url(#signal)" stroke-width="8"/>
    <g opacity=".38" fill="#ffffff"><circle cx="165" cy="1110" r="4"/><circle cx="3075" cy="240" r="4"/><rect x="1570" y="1128" width="100" height="3"/></g>
    <rect width="${W}" height="${H}" filter="url(#grain)" opacity=".34"/>
  </svg>`);
  const ids=["exam","upload","kit"];
  const logos=await Promise.all(ids.map(id=>rowLogoAtHeight(id,190,"dark")));
  const composites=[];
  for(let i=0;i<ids.length;i++){
    const meta=await sharp(logos[i]).metadata();
    composites.push({input:logos[i],left:i*1080+Math.round((1080-meta.width)/2),top:570});
  }
  const panorama=await sharp(art).composite(composites).png({compressionLevel:9}).toBuffer();
  for(let i=0;i<ids.length;i++){
    const target=path.join(out,"instagram","pinned",ids[i],"01-cover.png");
    await fs.mkdir(path.dirname(target),{recursive:true});
    await sharp(panorama).extract({left:i*1080,top:0,width:1080,height:1350}).png({compressionLevel:9}).withMetadata({density:144}).toFile(target);
  }
}

async function cover(id,index) {
  if(!coverTriptychBuilt){await buildCoverTriptych();coverTriptychBuilt=true;}
  return path.join(out,"instagram","pinned",id,`${String(index).padStart(2,"0")}-cover.png`);
}

async function pinnedExam() {
  const W=1080,H=1350,total=8,dir=path.join(out,"instagram","pinned","exam"),made=[];
  made.push(await cover("exam",1));
  made.push(await render(path.join(dir,"02-six-tabs.png"),W,H,C.ink,`${toolTabs(64,170,.82)}${txt(["SIX TABS.","FOUR TOOLS.","AND THE PHOTO IS"],64,410,108,102)}<rect x="64" y="700" width="785" height="118" fill="${C.signal}"/>${txt(["STILL WRONG."],82,794,112,112,{fill:C.ink})}${body(["It was never your photograph.","It was the specification."],66,905,31,44,C.paper)}${footer(W,H,2,total)}`));
  const frameSvg=[{x:70,y:570,w:180,h:207,t:"200 × 230"},{x:305,y:540,w:210,h:210,t:"1200 × 1200"},{x:570,y:520,w:170,h:227,t:"150 × 200"},{x:790,y:570,w:220,h:170,t:"413 × 319"}].map(f=>`${hardFrame(f.x,f.y,f.w,f.h)}<text x="${f.x+f.w/2}" y="${f.y+f.h+48}" fill="${C.ink}" font-family="Bahnschrift" font-size="22" text-anchor="middle">${f.t}</text>`).join("");
  made.push(await render(path.join(dir,"03-one-face.png"),W,H,C.paper,`${txt(["ONE FACE.","SIX EXAMINATIONS."],64,185,101,93,{fill:C.ink})}${body(["No preset fits all six.","Each rule comes from what the examination published."],64,420,29,42,"#3a3833")}${frameSvg}<rect x="64" y="930" width="952" height="210" fill="${C.ink}"/>${txt(["DIMENSIONS ARE ONLY THE START."],96,1022,52,58)}${body(["Background · file limit · format · framing · filename"],96,1094,24,34,C.muted)}${footer(W,H,3,total,false)}`));
  const files=[{n:"PHOTOGRAPH",shape:"<rect x='100' y='650' width='130' height='170' fill='none' stroke='#faf9f6' stroke-width='4'/><circle cx='165' cy='708' r='27' fill='none' stroke='#f04e23' stroke-width='4'/><path d='M125 790q40-64 80 0' fill='none' stroke='#faf9f6' stroke-width='4'/>"},{n:"SIGNATURE",shape:"<path d='M310 750q45-90 80 0q25-80 55 0q26-55 58-4' fill='none' stroke='#f04e23' stroke-width='5'/>"},{n:"THUMB",shape:"<ellipse cx='635' cy='742' rx='57' ry='80' fill='none' stroke='#faf9f6' stroke-width='4'/><ellipse cx='635' cy='742' rx='35' ry='57' fill='none' stroke='#f04e23' stroke-width='4'/>"},{n:"DECLARATION",shape:"<path d='M795 650h140v190h-140zM820 700h90M820 735h90M820 770h68' fill='none' stroke='#faf9f6' stroke-width='4'/><path d='M838 812q35-38 66 0' fill='none' stroke='#f04e23' stroke-width='4'/>"}];
  made.push(await render(path.join(dir,"04-not-one-photo.png"),W,H,C.ink,`${txt(["AN APPLICATION IS RARELY", "ONE PHOTOGRAPH."],64,190,84,82)}${body(["It can ask for a signature, thumb impression,", "declaration and a stack of certificates."],64,390,29,42,C.muted)}${files.map((f,i)=>`${f.shape}<text x="${[165,407,635,865][i]}" y="900" text-anchor="middle" fill="${C.paper}" font-family="Agency FB" font-size="29" font-weight="700">${f.n}</text>`).join("")}<rect x="64" y="1000" width="952" height="4" fill="${C.signal}"/>${txt(["EVERY ONE HAS ITS OWN RULE."],64,1100,52,58)}${footer(W,H,4,total)}`));
  const problemShot=await crop(path.join(ui,"04-problem.png"),940,570,"centre");
  made.push(await render(path.join(dir,"05-what-ready-misses.png"),W,H,C.paper,`${txt(["WHAT ‘READY’", "USUALLY LEAVES OUT."],64,165,88,82,{fill:C.ink})}<rect x="54" y="418" width="972" height="590" fill="${C.signal}"/>${body(["A background remover does not know the dimensions.","A cropper does not know how much of the frame your face should fill.","A compressor does not check whether the photo is blurred or too dark."],64,1080,24,37,"#3a3833")}${footer(W,H,5,total,false)}`,[{input:problemShot,left:70,top:400}]));
  made.push(await render(path.join(dir,"06-smallest-part.png"),W,H,C.signal,`${txt(["₹3"],64,265,210,210,{fill:C.ink})}${txt(["AGAINST"],380,175,43,48,{fill:C.ink})}${txt(["THE APPLICATION", "YOU PREPARED FOR."],380,255,78,74,{fill:C.ink})}<rect x="64" y="520" width="952" height="5" fill="${C.ink}"/>${txt(["THE SMALLEST PART OF", "YOUR APPLICATION SHOULDN’T", "COST YOU THE BIGGEST."],64,660,78,76,{fill:C.ink})}${body(["Strict upload rules have nothing to do with how well", "you know the syllabus. They still affect the application."],64,960,29,42,C.ink)}${footer(W,H,6,total,false)}`));
  made.push(await render(path.join(dir,"07-principles.png"),W,H,C.ink,`${txt(["IT NEVER CHANGES YOUR FACE."],64,150,63,68)}${body(["Exposure and contrast, yes. Whitening or reshaping, never."],64,220,24,34,C.muted)}<line x1="64" y1="290" x2="1016" y2="290" stroke="${C.signal}" stroke-width="4"/>${txt(["IT NEVER GUESSES A RULE."],64,415,63,68)}${body(["An unpublished value is marked as an estimate for you to check."],64,485,24,34,C.muted)}<line x1="64" y1="555" x2="1016" y2="555" stroke="${C.signal}" stroke-width="4"/>${txt(["IT NEVER PRETENDS."],64,680,63,68)}${body(["If the portal must capture or add something itself, we say so."],64,750,24,34,C.muted)}<line x1="64" y1="820" x2="1016" y2="820" stroke="${C.signal}" stroke-width="4"/>${txt(["IT FORGETS YOUR FILES."],64,945,63,68)}${body(["No account. Files deleted within 30 minutes, or within an hour if you ask."],64,1015,24,34,C.muted)}${footer(W,H,7,total)}`));
  const hero=await crop(path.join(ui,"01-home-hero.png"),952,490,"centre");
  made.push(await render(path.join(dir,"08-choose-exam.png"),W,H,C.paper,`${txt(["CHOOSE YOUR EXAMINATION."],64,145,78,82,{fill:C.ink})}${body(["The files, the rules and the preparation follow."],64,215,28,38,"#3a3833")}<rect x="54" y="330" width="972" height="510" fill="${C.ink}"/><rect x="64" y="910" width="952" height="148" fill="${C.signal}"/>${txt(["FIND YOUR EXAMINATION"],540,1004,48,54,{fill:C.ink,anchor:"middle"})}${body(["examuploadkit.com"],540,1128,25,32,"#3a3833").replace('text-anchor="start"','text-anchor="middle"')}${footer(W,H,8,total,false)}`,[{input:hero,left:64,top:320}]));
  return made;
}

async function pinnedUpload() {
  const W=1080,H=1350,total=8,dir=path.join(out,"instagram","pinned","upload"),made=[];
  made.push(await cover("upload",1));
  const desktopHome=await contain(path.join(ui,"01-home-hero.png"),920,550,C.paper);
  made.push(await render(path.join(dir,"02-find-exam.png"),W,H,C.ink,`${txt(["FIND YOUR", "EXAMINATION."],64,165,94,90)}${body(["Search by name or short form.","770 examinations are on file."],64,355,29,42,C.muted)}<rect x="52" y="475" width="976" height="590" fill="${C.signal}"/>${footer(W,H,2,total)}`,[{input:desktopHome,left:80,top:495}]));
  const examPage=await crop(path.join(ui,"09-exam-page.png"),952,660,"centre");
  made.push(await render(path.join(dir,"03-see-what-it-asks.png"),W,H,C.paper,`${txt(["SEE EXACTLY WHAT", "THE FORM ASKS FOR."],64,155,85,80,{fill:C.ink})}${body(["What we prepare. What you complete yourself.","No upload button where the portal has to handle it."],64,335,27,39,"#3a3833")}<rect x="52" y="455" width="976" height="690" fill="${C.ink}"/>${footer(W,H,3,total,false)}`,[{input:examPage,left:64,top:440}]));
  const desktopPrepare=await contain(path.join(ui,"10-prepare-files.png"),920,640,C.paper);
  made.push(await render(path.join(dir,"04-keep-what-you-need.png"),W,H,C.signal,`${txt(["KEEP WHAT", "YOU NEED."],64,150,92,88,{fill:C.ink})}${body(["Everything the form asks for is already ticked.","Untick what your application does not need. The price follows."],64,335,27,40,C.ink)}<rect x="52" y="455" width="976" height="690" fill="${C.ink}"/>${footer(W,H,4,total,false)}`,[{input:desktopPrepare,left:80,top:480}]));
  made.push(await render(path.join(dir,"05-file-by-file.png"),W,H,C.ink,`${txt(["EACH FILE GETS", "ITS OWN TREATMENT."],64,155,86,82)}${[ ["PHOTOGRAPH","frame · background · KB · filename"], ["SIGNATURE","clear paper · firm ink · no stretching"], ["THUMB","even light · close crop · ridges preserved"], ["DECLARATION","straight page · complete writing"], ["DOCUMENTS","order · merge · convert · compress"] ].map((r,i)=>`<rect x="64" y="${410+i*145}" width="952" height="112" fill="${i===0?C.signal:"none"}" stroke="${i===0?C.signal:C.line}" stroke-width="2"/>${txt([r[0]],92,466+i*145,38,42,{fill:i===0?C.ink:C.paper})}${body([r[1]],430,463+i*145,22,30,i===0?C.ink:C.muted)}`).join("")}${footer(W,H,5,total)}`));
  made.push(await render(path.join(dir,"06-watch-it-happen.png"),W,H,C.paper,`${txt(["WATCH IT HAPPEN", "STAGE BY STAGE."],64,155,88,82,{fill:C.ink})}${["UPLOAD","CHECK","PREPARE","REVIEW","KEEP"].map((s,i)=>`<circle cx="${120+i*210}" cy="540" r="52" fill="${i===2?C.signal:C.ink}"/><text x="${120+i*210}" y="552" fill="${i===2?C.ink:C.paper}" text-anchor="middle" font-family="Agency FB" font-size="31" font-weight="700">${i+1}</text>${i<4?`<line x1="${172+i*210}" y1="540" x2="${278+i*210}" y2="540" stroke="${C.ink}" stroke-width="4"/>`:""}<text x="${120+i*210}" y="630" fill="${C.ink}" text-anchor="middle" font-family="Bahnschrift" font-size="18" font-weight="700">${s}</text>`).join("")}<rect x="64" y="760" width="952" height="310" fill="${C.ink}"/>${txt(["YOU WON’T NEED TO KNOW", "WHAT A KILOBYTE IS."],100,890,63,68)}${body(["The examination's specification runs the preparation."],100,1010,24,34,C.muted)}${footer(W,H,6,total,false)}`));
  // Candidate photographs must always preserve the complete head and natural margins.
  // The source is 3:4, so the advertising frame uses the same ratio instead of cropping it.
  const before=await contain(path.join(exampleDir,"photo-a1-uploaded.jpg"),360,480,C.paper); const after=await previewPhoto(path.join(exampleDir,"photo-a1-prepared.jpg"),360,480,C.paper);
  made.push(await render(path.join(dir,"07-preview.png"),W,H,C.ink,`${txt(["CHECK THE REAL RESULT", "BEFORE YOU PAY."],64,150,79,76)}<rect x="64" y="355" width="380" height="500" fill="${C.paper}"/><rect x="636" y="355" width="380" height="500" fill="${C.signal}"/><text x="64" y="895" fill="${C.muted}" font-family="Bahnschrift" font-size="19">AS UPLOADED</text><text x="636" y="895" fill="${C.signal}" font-family="Bahnschrift" font-size="19">PREPARED</text>${body(["A watermarked preview of the result.","A plain note of anything worth a second look."],64,980,28,42,C.paper)}${footer(W,H,7,total)}`,[{input:before,left:74,top:365},{input:after,left:646,top:365}]));
  const mobileHome=await contain(path.join(ui,"13-mobile-home.png"),300,650,C.paper);
  const mobilePrepare=await contain(path.join(ui,"14-mobile-prepare.png"),300,650,C.paper);
  made.push(await render(path.join(dir,"08-keep.png"),W,H,C.ink,`${txt(["INSTALL IT ON", "YOUR PHONE."],64,150,88,84)}${body(["Add ExamUploadKit to your home screen.","It opens like an app, ready when the form is."],64,330,27,39,C.muted)}<rect x="126" y="465" width="320" height="690" fill="${C.signal}"/><rect x="634" y="465" width="320" height="690" fill="${C.signal}"/>${footer(W,H,8,total)}`,[{input:mobileHome,left:136,top:485},{input:mobilePrepare,left:644,top:485}]));
  return made;
}

async function pinnedKit() {
  const W=1080,H=1350,total=8,dir=path.join(out,"instagram","pinned","kit"),made=[];
  made.push(await cover("kit",1));
  const pb=await contain(path.join(exampleDir,"photo-a2-uploaded.jpg"),330,440,C.paper), pa=await contain(path.join(exampleDir,"photo-a2-prepared.jpg"),330,440,C.paper);
  made.push(await render(path.join(dir,"02-photo.png"),W,H,C.ink,`${txt(["YOUR PHOTOGRAPH."],64,145,91,96)}${body(["Framed for the examination. Background replaced.","Compressed under the limit. Named for the portal."],64,230,26,38,C.muted)}<rect x="64" y="385" width="350" height="460" fill="${C.paper}"/><rect x="666" y="385" width="350" height="460" fill="${C.signal}"/><path d="M465 605h150m-32-30l32 30-32 30" fill="none" stroke="${C.signal}" stroke-width="6"/><text x="64" y="890" fill="${C.muted}" font-family="Bahnschrift" font-size="18">UPLOADED</text><text x="666" y="890" fill="${C.signal}" font-family="Bahnschrift" font-size="18">PREPARED</text>${txt(["YOUR FACE STAYS YOURS."],64,1045,55,60)}${footer(W,H,2,total)}`,[{input:pb,left:74,top:395},{input:pa,left:676,top:395}]));
  const sb=await crop(path.join(exampleDir,"sign-s2-uploaded.jpg"),800,300,"centre"),sa=await crop(path.join(exampleDir,"sign-s2-prepared.jpg"),800,300,"centre");
  made.push(await render(path.join(dir,"03-signature.png"),W,H,C.paper,`${txt(["YOUR SIGNATURE."],64,145,91,96,{fill:C.ink})}${body(["Paper cleared around the strokes. Ink made firm.","Never stretched - because a stretched signature is no longer yours."],64,230,25,37,"#3a3833")}<rect x="90" y="405" width="900" height="330" fill="${C.ink}"/><text x="90" y="778" fill="#55524b" font-family="Bahnschrift" font-size="21" font-weight="700" letter-spacing="1.8">UPLOADED</text><rect x="90" y="810" width="900" height="330" fill="${C.signal}"/><text x="90" y="1183" fill="${C.signal}" font-family="Bahnschrift" font-size="21" font-weight="700" letter-spacing="1.8">PREPARED</text>${footer(W,H,3,total,false)}`,[{input:sb,left:110,top:420},{input:sa,left:110,top:825}]));
  made.push(await render(path.join(dir,"04-rest-of-kit.png"),W,H,C.ink,`${txt(["THUMB.","DECLARATION.","CERTIFICATES.","PDF."],64,165,93,89)}<rect x="610" y="120" width="400" height="250" fill="none" stroke="${C.paper}" stroke-width="4"/><ellipse cx="810" cy="245" rx="58" ry="86" fill="none" stroke="${C.signal}" stroke-width="5"/><rect x="610" y="430" width="400" height="310" fill="none" stroke="${C.paper}" stroke-width="4"/><path d="M665 515h280M665 565h280M665 615h210" stroke="${C.muted}" stroke-width="4"/><path d="M730 690q80-70 150 0" fill="none" stroke="${C.signal}" stroke-width="5"/><rect x="610" y="800" width="400" height="260" fill="${C.paper}"/><path d="M660 850h300v160H660z" fill="none" stroke="${C.ink}" stroke-width="4"/>${body(["We prepare the supported file.","The portal remains the final authority."],64,1080,27,39,C.muted)}${footer(W,H,4,total)}`));
  const pricing=await crop(path.join(ui,"07-pricing.png"),952,620,"centre");
  made.push(await render(path.join(dir,"05-price.png"),W,H,C.paper,`${txt(["THE WHOLE KIT IS ₹5."],64,145,79,84,{fill:C.ink})}${body(["One file is ₹3. Two files or more stop at ₹5."],64,215,27,38,"#3a3833")}<rect x="54" y="340" width="972" height="650" fill="${C.signal}"/>${txt(["THE PRICE FOLLOWS", "WHAT YOU KEEP."],64,1110,62,64,{fill:C.ink})}${footer(W,H,5,total,false)}`,[{input:pricing,left:64,top:330}]));
  made.push(await render(path.join(dir,"06-pdf.png"),W,H,C.signal,`${txt(["EVERY PDF JOB,", "FREE WITH ANY", "PREPARED FILE."],64,175,96,91,{fill:C.ink})}${["IMAGE TO PDF","PDF TO IMAGE","MERGE PDFS","REORDER PAGES","REMOVE PAGES","ROTATE PAGES","COMPRESS TO LIMIT","NAME FOR PORTAL"].map((v,i)=>`<rect x="${64+(i%2)*480}" y="${520+Math.floor(i/2)*120}" width="450" height="88" fill="${i===7?C.ink:C.paper}" stroke="${C.ink}" stroke-width="3"/><text x="${289+(i%2)*480}" y="${575+Math.floor(i/2)*120}" fill="${i===7?C.paper:C.ink}" font-family="Bahnschrift" font-size="20" font-weight="700" text-anchor="middle">${v}</text>`).join("")}${footer(W,H,6,total,false)}`));
  made.push(await render(path.join(dir,"07-privacy.png"),W,H,C.ink,`${txt(["NO ACCOUNT.","NO FOREVER FOLDER."],64,175,91,87)}<circle cx="270" cy="630" r="165" fill="none" stroke="${C.signal}" stroke-width="12"/><text x="270" y="615" fill="${C.paper}" text-anchor="middle" font-family="Agency FB" font-size="105" font-weight="700">30</text><text x="270" y="680" fill="${C.muted}" text-anchor="middle" font-family="Bahnschrift" font-size="21">MINUTES</text><line x1="515" y1="450" x2="515" y2="820" stroke="${C.line}" stroke-width="3"/>${txt(["UP TO", "1 HOUR"],610,585,77,75)}${body(["Only when you ask us", "to keep the files longer."],610,760,24,35,C.muted)}${body(["Payment does not extend the window. Download when ready."],64,990,28,39,C.paper)}${footer(W,H,7,total)}`));
  const logo=await fullLogo(850,"dark");
  made.push(await render(path.join(dir,"08-ready.png"),W,H,C.ink,`${txt(["EVERY FILE YOUR EXAM", "APPLICATION NEEDS,"],64,175,77,74)}<rect x="64" y="350" width="825" height="105" fill="${C.signal}"/>${txt(["PREPARED TO THE RULES."],82,428,66,68,{fill:C.ink})}${body(["You review it. You download it.","You submit it on the official portal."],64,565,29,42,C.muted)}<rect x="64" y="770" width="952" height="4" fill="${C.signal}"/>${footer(W,H,8,total)}`,[{input:logo,left:110,top:850}]));
  return made;
}

const overview = [
  {title:["WHAT EXAMUPLOADKIT", "ACTUALLY DOES."],body:["Choose the examination. Prepare the files it asks for.","Review the result before you pay."],source:"01-home-hero.png",position:"centre"},
  {title:["THE PROBLEM ISN’T", "‘RESIZE A PHOTO.’"],body:["It is getting every file to the examination's own specification."],source:"04-problem.png",position:"centre"},
  {title:["PHOTOGRAPH. SIGNATURE.","THUMB. DECLARATION.","CERTIFICATES."],body:["Everything the form asks you to attach, in one place."],source:"02-what-we-prepare.png",position:"north"},
  {title:["START WITH", "THE EXAMINATION."],body:["770 examination records, each tied to the rules it published."],source:"01-home-hero.png",position:"centre"},
  {title:["SEE WHAT WE PREPARE -", "AND WHAT YOU DO YOURSELF."],body:["The product does not pretend it can handle a portal-only step."],source:"09-exam-page.png",position:"centre"},
  {title:["KEEP WHAT", "YOUR FORM NEEDS."],body:["The full kit is ticked. Untick anything you do not need."],source:"10-prepare-files.png",position:"centre"},
  {title:["CHECK THE RESULT", "BEFORE YOU PAY."],body:["A protected preview and a plain note of anything worth checking."],source:"03-how-it-works.png",position:"centre"},
  {title:["₹3 FOR ONE FILE.","₹5 FOR THE KIT."],body:["PDF work is free with any prepared file."],source:"07-pricing.png",position:"centre"},
  {title:["NO ACCOUNT.","FILES HELD BRIEFLY."],body:["Deleted within 30 minutes, or within an hour if you ask."],source:"08-principles.png",position:"centre"},
  {title:["INSTALL IT ON", "YOUR PHONE."],body:["Add ExamUploadKit to your home screen. It opens like an app."],mobilePair:true},
  {title:["YOU PREPARE", "FOR THE EXAM."],body:["We'll prepare the files.","examuploadkit.com"],source:"01-home-hero.png",position:"centre"},
];

async function renderOverviewPlatform(platform,W,H,slides) {
  const dir=path.join(out,platform,"product-overview"),made=[];
  for(let i=0;i<slides.length;i++){
    const s=slides[i],index=i+1,total=slides.length,target=path.join(dir,`${String(index).padStart(2,"0")}.png`);
    const dark=i%3!==1;
    const bg=dark?C.ink:C.paper;
    const fg=dark?C.paper:C.ink;
    const titleSize=W/H>1.3?64:W/H<.85?74:68;
    const top=platform==="x"?80:platform==="reddit"?70:80;
    if(s.mobilePair){
      const phoneW=platform==="x"?300:platform==="reddit"?250:platform==="linkedin"?330:300;
      const phoneH=platform==="x"?500:platform==="reddit"?540:platform==="linkedin"?720:650;
      const phoneTop=platform==="x"?330:platform==="reddit"?390:platform==="linkedin"?610:540;
      const leftA=platform==="x"?430:platform==="reddit"?220:platform==="linkedin"?190:145;
      const leftB=platform==="x"?870:platform==="reddit"?610:platform==="linkedin"?680:635;
      const home=await contain(path.join(ui,"13-mobile-home.png"),phoneW,phoneH,C.paper);
      const prepare=await contain(path.join(ui,"14-mobile-prepare.png"),phoneW,phoneH,C.paper);
      const content=`${txt(s.title,64,top+titleSize,titleSize,titleSize*.92,{fill:fg})}${body(s.body,64,top+titleSize+s.title.length*titleSize*.92+38,platform==="x"?22:24,35,dark?C.muted:"#55524b")}<rect x="${leftA-12}" y="${phoneTop-12}" width="${phoneW+24}" height="${phoneH+24}" fill="${C.signal}"/><rect x="${leftB-12}" y="${phoneTop-12}" width="${phoneW+24}" height="${phoneH+24}" fill="${C.signal}"/>${footer(W,H,index,total,dark)}`;
      made.push(await render(target,W,H,bg,content,[{input:home,left:leftA,top:phoneTop},{input:prepare,left:leftB,top:phoneTop}]));
      continue;
    }
    const imgTop=platform==="x"?320:platform==="reddit"?390:450;
    const imgHeight=H-imgTop-(platform==="x"?70:115);
    const imgWidth=W-128;
    const shot=await contain(path.join(ui,s.source),imgWidth,imgHeight,dark?C.ink:C.paper);
    const panel=`<rect x="${52}" y="${imgTop-12}" width="${W-104}" height="${imgHeight+24}" fill="${C.signal}"/><rect x="64" y="${imgTop}" width="${imgWidth}" height="${imgHeight}" fill="${dark?C.paper:C.ink}"/>`;
    const content=`${txt(s.title,64,top+titleSize,titleSize,titleSize*.92,{fill:fg})}${body(s.body,64,top+titleSize+s.title.length*titleSize*.92+38,platform==="x"?22:24,35,dark?C.muted:"#55524b")}${panel}${footer(W,H,index,total,dark)}`;
    made.push(await render(target,W,H,bg,content,[{input:shot,left:64,top:imgTop}]));
  }
  return made;
}

async function sheet(name,files,tw=216,th=270,cols=4){
  const gap=14,pad=24,rowsN=Math.ceil(files.length/cols),buffers=await Promise.all(files.map(f=>sharp(f).resize({width:tw,height:th,fit:"cover"}).png().toBuffer()));
  const target=path.join(out,"reviews",`${name}.png`); await fs.mkdir(path.dirname(target),{recursive:true});
  await sharp({create:{width:pad*2+cols*tw+(cols-1)*gap,height:pad*2+rowsN*th+(rowsN-1)*gap,channels:3,background:"#050505"}}).composite(buffers.map((input,i)=>({input,left:pad+(i%cols)*(tw+gap),top:pad+Math.floor(i/cols)*(th+gap)}))).png({compressionLevel:9}).toFile(target); return target;
}

await fs.mkdir(out,{recursive:true});
const exam=await pinnedExam(); const upload=await pinnedUpload(); const kit=await pinnedKit();
const instagram=await renderOverviewPlatform("instagram",1080,1350,overview);
const linkedin=await renderOverviewPlatform("linkedin",1200,1500,overview);
const reddit=await renderOverviewPlatform("reddit",1080,1080,[overview[0],overview[1],overview[3],overview[4],overview[6],overview[7],overview[9],overview[10]]);
const x=await renderOverviewPlatform("x",1600,900,[overview[1],overview[3],overview[6],overview[9]]);
const reviews={
  profile:await sheet("pinned-profile-row",[exam[0],upload[0],kit[0]],360,450,3),
  exam:await sheet("pinned-exam",exam), upload:await sheet("pinned-upload",upload), kit:await sheet("pinned-kit",kit),
  instagram:await sheet("overview-instagram",instagram), linkedin:await sheet("overview-linkedin",linkedin,200,250,5), reddit:await sheet("overview-reddit",reddit,216,216,4), x:await sheet("overview-x",x,320,180,2),
};
const all=[...exam,...upload,...kit,...instagram,...linkedin,...reddit,...x];
const manifest={generatedAt:new Date().toISOString(),source:"Live screenshots captured from examuploadkit.com on 2 October 2026 plus the site's disclosed representational example assets.",logoPolicy:"Authorised logo assets only. Covers crop and scale complete logo rows without reconstruction or recolouring.",viewportPolicy:"Desktop product views are used throughout walkthrough slides. Mobile views appear only on the dedicated installable-application slide.",counts:{pinned:24,instagramOverview:instagram.length,linkedinOverview:linkedin.length,redditOverview:reddit.length,xOverview:x.length,total:all.length},files:all.map(f=>path.relative(campaign,f).replaceAll("\\","/")),reviews:Object.fromEntries(Object.entries(reviews).map(([k,v])=>[k,path.relative(campaign,v).replaceAll("\\","/")]))};
await fs.writeFile(path.join(out,"manifest.json"),JSON.stringify(manifest,null,2)+"\n");
console.log(JSON.stringify(manifest.counts,null,2));
