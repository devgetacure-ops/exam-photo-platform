import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "../../../apps/web/node_modules/sharp/dist/index.cjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const campaign = path.resolve(here, "..");
const root = path.resolve(campaign, "..", "..");
const exportsDir = path.join(campaign, "exports");
const artDir = path.join(campaign, "source-art");
const logoPath = path.join(root, "apps", "web", "public", "brand", "examuploadkit-stacked-dark.png");
const W = 1080;
const H = 1350;
const INK = "#0e0d0c";
const PAPER = "#f3eee5";
const MUTED = "#b8afa2";
const SIGNAL = "#ee4b22";

const rows = {
  exam: { left: 1028, top: 96, width: 744, height: 224 },
  upload: { left: 844, top: 316, width: 1112, height: 224 },
  kit: { left: 1120, top: 536, width: 560, height: 224 },
};

const groups = {
  exam: {
    label: "01 / WHY",
    deck: "THE PROBLEM",
    art: "why-problem.png",
    descriptor: "Why this exists",
    slides: [
      { title: ["THE EXAM", "IS HARD."], kicker: "THE UPLOAD SHOULD NOT BE.", body: [] },
      { title: ["ONE FORM.", "SEVERAL FILES."], kicker: "EACH WITH A DIFFERENT RULE.", body: ["Photo. Signature. Thumb impression.", "Declaration. Documents."] },
      { title: ["IT CAN LOOK RIGHT", "AND STILL BE WRONG."], kicker: "THE FILE HAS TO MATCH THE RULE.", body: ["Dimensions. File size. Format. Background."] },
      { title: ["MOST TOOLS FIX", "ONE PART."], kicker: "THE FORM JUDGES THE WHOLE FILE.", body: ["A generic preset cannot know the examination."] },
      { title: ["SO WE START", "WITH THE EXAM."], kicker: "THAT IS THE PROBLEM WE CHOSE TO SOLVE.", body: ["The examination configures the work."] },
    ],
  },
  upload: {
    label: "02 / HOW",
    deck: "THE METHOD",
    art: "how-system.png",
    descriptor: "How it works",
    slides: [
      { title: ["CHOOSE THE", "EXAM FIRST."], kicker: "THE RECORD SETS THE REQUIREMENTS.", body: ["The tool follows the examination you select."] },
      { title: ["WE READ", "THE RULE."], kicker: "NOT A UNIVERSAL PRESET.", body: ["If a published value is unclear, the gap stays visible."] },
      { title: ["EACH FILE GETS", "ITS OWN TREATMENT."], kicker: "ONLY WHAT THAT FILE REQUIRES.", body: ["Crop. Background. Dimensions.", "Compression. Format. Filename."] },
      { title: ["SEE THE RESULT", "BEFORE YOU PAY."], kicker: "THE PREPARED PREVIEW STAYS VISIBLE.", body: ["Detected issues stay visible too."] },
      { title: ["DOWNLOAD HERE.", "SUBMIT THERE."], kicker: "YOU STAY IN CONTROL.", body: ["We prepare the file. You upload it on the official portal."] },
      { title: ["NO GUESSING", "IN BETWEEN."], kicker: "EXAMUPLOADKIT.COM", body: ["Choose. Prepare. Review. Download."] },
    ],
  },
  kit: {
    label: "03 / WHAT",
    deck: "THE OUTCOME",
    art: "what-kit.png",
    descriptor: "What you get",
    slides: [
      { title: ["EVERYTHING THE FORM", "ASKS YOU TO ATTACH."], kicker: "ONE EXAMINATION. ONE ORGANISED KIT.", body: [] },
      { title: ["ONE PLACE.", "INSTEAD OF SIX TOOLS."], kicker: "THE RULE DOES NOT NEED TO BE REBUILT EACH TIME.", body: ["Prepare the supported files together."] },
      { title: ["LESS TIME ON", "PIXELS + KILOBYTES."], kicker: "MORE ATTENTION ON THE APPLICATION.", body: [] },
      { title: ["NO ACCOUNT.", "FILES HELD BRIEFLY."], kicker: "DOWNLOAD THEM WHEN THEY ARE READY.", body: ["Temporary files are deleted after the short processing window."] },
      { title: ["READY FOR WHAT", "MATTERS NEXT."], kicker: "FIND YOUR EXAMINATION.", body: ["examuploadkit.com"] },
    ],
  },
};

const esc = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
function textLines(lines, x, y, size, step, opts = {}) {
  const { fill = PAPER, weight = 700, family = "Bahnschrift", anchor = "start", tracking = -1 } = opts;
  return `<text x="${x}" y="${y}" fill="${fill}" font-family="${family}" font-size="${size}" font-weight="${weight}" text-anchor="${anchor}" letter-spacing="${tracking}">${lines.map((line, index) => `<tspan x="${x}" dy="${index ? step : 0}">${esc(line)}</tspan>`).join("")}</text>`;
}

async function cropArt(name, width, height, position = "centre", tint = 0) {
  let pipeline = sharp(path.join(artDir, name)).resize({ width, height, fit: "cover", position });
  if (tint) pipeline = pipeline.modulate({ brightness: 1 - tint, saturation: 0.86 });
  return pipeline.png().toBuffer();
}

async function logoRow(id, width) {
  const row = rows[id];
  return sharp(logoPath).extract(row).resize({ width }).png().toBuffer();
}

function rails(section, index, total, label) {
  return `<text x="70" y="84" fill="${MUTED}" font-family="Arial" font-size="18" font-weight="700" letter-spacing="3">${esc(label)}</text>
  <text x="1010" y="84" fill="${MUTED}" font-family="Arial" font-size="18" text-anchor="end" letter-spacing="2">${String(index).padStart(2,"0")} / ${String(total).padStart(2,"0")}</text>
  <line x1="70" y1="110" x2="1010" y2="110" stroke="#514a42" stroke-width="1"/>
  <line x1="70" y1="1262" x2="1010" y2="1262" stroke="#514a42" stroke-width="1"/>
  <text x="70" y="1306" fill="${MUTED}" font-family="Arial" font-size="17" font-weight="700" letter-spacing="2">EXAMUPLOADKIT.COM</text>
  <text x="1010" y="1306" fill="${MUTED}" font-family="Arial" font-size="17" text-anchor="end">SWIPE  →</text>`;
}

async function renderCover(id, spec) {
  const out = path.join(exportsDir, "instagram", "carousels", id, "01-cover.png");
  await fs.mkdir(path.dirname(out), { recursive: true });
  const bg = await cropArt(spec.art, W, H, id === "exam" ? "south" : "centre", 0.05);
  const targetWidth = id === "upload" ? 820 : id === "exam" ? 550 : 415;
  const excerpt = await logoRow(id, targetWidth);
  const meta = await sharp(excerpt).metadata();
  const left = Math.round((W - meta.width) / 2);
  const top = Math.round((H - meta.height) / 2) - 10;
  const overlay = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">
    <defs><linearGradient id="shade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity=".28"/><stop offset=".48" stop-color="#000" stop-opacity=".08"/><stop offset="1" stop-color="#000" stop-opacity=".54"/></linearGradient></defs>
    <rect width="1080" height="1350" fill="url(#shade)"/>
    <line x1="70" y1="112" x2="1010" y2="112" stroke="#d8d0c4" stroke-opacity=".52"/>
    <text x="70" y="82" fill="${PAPER}" font-family="Arial" font-size="19" font-weight="700" letter-spacing="3">${spec.label}</text>
    <text x="1010" y="82" fill="${PAPER}" font-family="Arial" font-size="19" text-anchor="end" letter-spacing="2">${spec.deck}</text>
    <rect x="0" y="${top - 46}" width="1080" height="${meta.height + 92}" fill="#080706" fill-opacity=".66"/>
    <line x1="0" y1="${top - 46}" x2="1080" y2="${top - 46}" stroke="${SIGNAL}" stroke-width="3"/>
    <text x="70" y="1236" fill="${PAPER}" font-family="Bahnschrift" font-size="31" font-weight="600" letter-spacing=".5">${esc(spec.descriptor)}</text>
    <text x="1010" y="1236" fill="${PAPER}" font-family="Arial" font-size="18" text-anchor="end" letter-spacing="2">EXAMUPLOADKIT.COM</text>
  </svg>`);
  await sharp(bg).composite([{ input: overlay }, { input: excerpt, left, top }]).png({ compressionLevel: 9 }).withMetadata({ density: 144 }).toFile(out);
  return out;
}

async function renderSlide(id, spec, slide, index, total) {
  const out = path.join(exportsDir, "instagram", "carousels", id, `${String(index).padStart(2,"0")}-${index === total ? "close" : "story"}.png`);
  const variant = index % 4;
  let composites = [];
  if (variant === 0) {
    const art = await cropArt(spec.art, 1080, 600, id === "exam" ? "south" : "centre", .12);
    composites.push({ input: art, left: 0, top: 750 });
  } else if (variant === 1) {
    const art = await cropArt(spec.art, 440, 1140, id === "kit" ? "east" : "centre", .08);
    composites.push({ input: art, left: 640, top: 110 });
  } else if (variant === 2) {
    const art = await cropArt(spec.art, 1080, 1350, id === "exam" ? "south" : "centre", .2);
    composites.push({ input: art, left: 0, top: 0 });
  } else {
    const art = await cropArt(spec.art, 520, 690, id === "exam" ? "southwest" : "centre", .1);
    composites.push({ input: art, left: 0, top: 540 });
  }

  const titleSize = variant === 3 ? (slide.title.some((x) => x.length > 18) ? 48 : 56) : (slide.title.some((x) => x.length > 18) ? 65 : 78);
  const titleStep = titleSize + 7;
  const x = variant === 1 ? 70 : variant === 3 ? 560 : 70;
  const y = variant === 0 ? 220 : variant === 2 ? 205 : variant === 3 ? 690 : 250;
  const widthMask = variant === 1 ? `<rect x="0" y="110" width="690" height="1152" fill="${INK}"/>` : variant === 2 ? `<rect width="1080" height="1350" fill="#080706" fill-opacity=".64"/>` : variant === 3 ? `<rect x="500" y="110" width="580" height="1152" fill="${INK}"/>` : `<rect x="0" y="110" width="1080" height="710" fill="${INK}"/>`;
  const kickerY = y + slide.title.length * titleStep + 58;
  const bodyY = kickerY + 68;
  const giant = `<text x="${variant === 3 ? 1010 : 70}" y="${variant === 3 ? 420 : 1130}" fill="none" stroke="${SIGNAL}" stroke-opacity=".62" stroke-width="2" font-family="Bahnschrift" font-size="230" font-weight="700" text-anchor="${variant === 3 ? "end" : "start"}">${String(index - 1).padStart(2,"0")}</text>`;
  const overlay = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">
    ${widthMask}
    ${rails(id, index, total, spec.deck)}
    ${giant}
    <rect x="${x}" y="${y - 52}" width="52" height="5" fill="${SIGNAL}"/>
    ${textLines(slide.title, x, y, titleSize, titleStep)}
    ${textLines([slide.kicker], x, kickerY, 22, 30, { fill: SIGNAL, family: "Arial", weight: 700, tracking: 1.5 })}
    ${slide.body.length ? textLines(slide.body, x, bodyY, 24, 36, { fill: MUTED, family: "Arial", weight: 400, tracking: 0 }) : ""}
  </svg>`);
  composites.push({ input: overlay });
  await sharp({ create: { width: W, height: H, channels: 3, background: INK } }).composite(composites).png({ compressionLevel: 9 }).withMetadata({ density: 144 }).toFile(out);
  return out;
}

async function reviewSheet(id) {
  const dir = path.join(exportsDir, "instagram", "carousels", id);
  const files = (await fs.readdir(dir)).filter((x) => x.endsWith(".png")).sort();
  const tw = 216, th = 270, gap = 14, pad = 24, cols = 4;
  const rowsCount = Math.ceil(files.length / cols);
  const buffers = await Promise.all(files.map((file) => sharp(path.join(dir, file)).resize(tw, th).png().toBuffer()));
  const out = path.join(exportsDir, "instagram", `review-${id}.png`);
  await sharp({ create: { width: pad * 2 + cols * tw + (cols - 1) * gap, height: pad * 2 + rowsCount * th + (rowsCount - 1) * gap, channels: 3, background: "#050505" } })
    .composite(buffers.map((input, i) => ({ input, left: pad + (i % cols) * (tw + gap), top: pad + Math.floor(i / cols) * (th + gap) })))
    .png({ compressionLevel: 9 }).toFile(out);
  return out;
}

async function renderStory() {
  const frames = [
    { art: "why-problem.png", label: "A PERSONAL NOTE", title: ["TODAY FEELS", "SPECIAL."], body: ["I finally get to share something I built", "that is complete, live and solving a real problem."] },
    { art: "how-system.png", label: "IT IS CALLED EXAMUPLOADKIT", title: ["THE EXAM IS HARD.", "THE UPLOAD", "SHOULD NOT BE."], body: ["It prepares the files an exam application asks for,", "according to the examination you choose."] },
    { art: "what-kit.png", label: "ONE REQUEST", title: ["APPEARING FOR", "AN EXAM?"], body: ["Or know someone who is?", "Please try it, or send it to them."], cta: "EXAMUPLOADKIT.COM" },
    { art: "what-kit.png", label: "HONEST FEEDBACK, PLEASE", title: ["TELL ME WHAT", "IS CONFUSING."], body: ["Tell me what could be better.", "I am very happy today.", "This is only the beginning."], cta: "EXAMUPLOADKIT.COM" },
  ];
  const made = [];
  for (let i = 0; i < frames.length; i++) {
    const f = frames[i];
    const bg = await cropArt(f.art, 1080, 1920, i === 0 ? "south" : "centre", .15);
    const titleSize = f.title.some((x) => x.length > 16) ? 76 : 92;
    const overlay = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920">
      <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#050505" stop-opacity=".35"/><stop offset=".45" stop-color="#050505" stop-opacity=".78"/><stop offset="1" stop-color="#050505" stop-opacity=".94"/></linearGradient></defs>
      <rect width="1080" height="1920" fill="url(#g)"/><line x1="70" y1="160" x2="1010" y2="160" stroke="#82786c"/>
      ${textLines([f.label],70,125,20,28,{fill:PAPER,family:"Arial",weight:700,tracking:3})}
      <rect x="70" y="844" width="55" height="6" fill="${SIGNAL}"/>
      ${textLines(f.title,70,950,titleSize,titleSize+10)}
      ${textLines(f.body,70,1320,29,45,{fill:"#d8d0c4",family:"Arial",weight:400,tracking:0})}
      ${f.cta ? `<rect x="70" y="1580" width="940" height="104" fill="${SIGNAL}"/>${textLines([f.cta],540,1648,25,30,{fill:"#fff",family:"Arial",weight:700,anchor:"middle",tracking:2})}` : ""}
      <text x="70" y="1820" fill="${PAPER}" font-family="Arial" font-size="18" font-weight="700" letter-spacing="2">EXAMUPLOADKIT.COM</text>
      <text x="1010" y="1820" fill="${MUTED}" font-family="Arial" font-size="18" text-anchor="end">${String(i+1).padStart(2,"0")} / 04</text>
    </svg>`);
    const out = path.join(exportsDir, "story-status", `${String(i+1).padStart(2,"0")}.png`);
    await fs.mkdir(path.dirname(out), { recursive: true });
    await sharp(bg).composite([{input:overlay}]).png({compressionLevel:9}).toFile(out);
    made.push(out);
  }
  return made;
}

async function renderPlatformCards() {
  const made = [];
  const what = await cropArt("what-kit.png", 1200, 627, "east", .08);
  const li = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="627"><rect width="1200" height="627" fill="#070707" fill-opacity=".55"/><rect x="0" width="585" height="627" fill="${INK}"/><rect x="64" y="78" width="54" height="6" fill="${SIGNAL}"/>${textLines(["THE LAST PART", "OF THE EXAM", "NOBODY PREPARES", "YOU FOR."],64,165,53,58)}${textLines(["Exam application files, prepared to the rules."],64,485,22,30,{fill:MUTED,family:"Arial",weight:400,tracking:0})}${textLines(["EXAMUPLOADKIT.COM"],64,565,18,24,{fill:PAPER,family:"Arial",weight:700,tracking:2})}</svg>`);
  const liOut = path.join(exportsDir,"linkedin","launch-editorial-1200x627.png"); await fs.mkdir(path.dirname(liOut),{recursive:true}); await sharp(what).composite([{input:li}]).png({compressionLevel:9}).toFile(liOut); made.push(liOut);

  const how = await cropArt("how-system.png",1600,900,"centre",.1);
  const xo = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900"><defs><linearGradient id="x" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#050505" stop-opacity=".98"/><stop offset=".64" stop-color="#050505" stop-opacity=".22"/><stop offset="1" stop-color="#050505" stop-opacity=".42"/></linearGradient></defs><rect width="1600" height="900" fill="url(#x)"/><rect x="78" y="84" width="62" height="7" fill="${SIGNAL}"/>${textLines(["CHOOSE THE EXAM.","PREPARE THE FILES.","STOP GUESSING."],78,205,67,78)}${textLines(["I built ExamUploadKit for the upload screen."],78,520,27,36,{fill:MUTED,family:"Arial",weight:400,tracking:0})}${textLines(["EXAMUPLOADKIT.COM"],78,812,20,28,{family:"Arial",weight:700,tracking:2})}</svg>`);
  const xOut=path.join(exportsDir,"x","launch-1600x900.png"); await fs.mkdir(path.dirname(xOut),{recursive:true}); await sharp(how).composite([{input:xo}]).png({compressionLevel:9}).toFile(xOut); made.push(xOut);

  const why = await cropArt("why-problem.png",1200,628,"south",.12);
  const ro = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="628"><defs><linearGradient id="r" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#050505" stop-opacity=".97"/><stop offset=".7" stop-color="#050505" stop-opacity=".28"/></linearGradient></defs><rect width="1200" height="628" fill="url(#r)"/><rect x="62" y="72" width="54" height="6" fill="${SIGNAL}"/>${textLines(["I BUILT THIS FOR", "THE UPLOAD SCREEN."],62,164,55,64)}${textLines(["Self-promotion. Honest criticism welcome."],62,365,23,32,{fill:MUTED,family:"Arial",weight:400,tracking:0})}${textLines(["EXAMUPLOADKIT.COM"],62,556,18,24,{family:"Arial",weight:700,tracking:2})}</svg>`);
  const rOut=path.join(exportsDir,"reddit","launch-context-1200x628.png"); await fs.mkdir(path.dirname(rOut),{recursive:true}); await sharp(why).composite([{input:ro}]).png({compressionLevel:9}).toFile(rOut); made.push(rOut);
  return made;
}

await fs.mkdir(exportsDir,{recursive:true});
const files=[]; const reviews={};
for (const [id,spec] of Object.entries(groups)) {
  files.push(await renderCover(id,spec));
  const total=spec.slides.length+1;
  for(let i=0;i<spec.slides.length;i++) files.push(await renderSlide(id,spec,spec.slides[i],i+2,total));
  reviews[id]=await reviewSheet(id);
}
files.push(...await renderStory());
files.push(...await renderPlatformCards());
const manifest={campaign:"ExamUploadKit launch v2",generatedAt:new Date().toISOString(),dimensions:{instagram:{width:1080,height:1350},story:{width:1080,height:1920},linkedin:{width:1200,height:627},x:{width:1600,height:900},reddit:{width:1200,height:628}},sourcePolicy:"Original generated photography supplies scene art. All copy and the authorised logo excerpts are composited deterministically. The logo is cropped and scaled only, without recolouring or reconstruction.",sourceArt:["source-art/why-problem.png","source-art/how-system.png","source-art/what-kit.png"],files:files.map(x=>path.relative(campaign,x).replaceAll("\\","/")),reviews:Object.fromEntries(Object.entries(reviews).map(([k,v])=>[k,path.relative(campaign,v).replaceAll("\\","/")]))};
await fs.writeFile(path.join(exportsDir,"manifest.json"),JSON.stringify(manifest,null,2)+"\n");
console.log(JSON.stringify({created:files.length,reviews},null,2));
