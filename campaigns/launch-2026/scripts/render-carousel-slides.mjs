import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "../../../apps/web/node_modules/sharp/dist/index.cjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..", "..", "..");
const campaign = path.resolve(here, "..");
const out = path.join(campaign, "exports", "instagram", "carousels");
const publicDir = path.join(root, "apps", "web", "public");
const logo = path.join(publicDir, "brand", "examuploadkit-stacked-light.png");
const paper = "#faf9f6";
const ink = "#111110";
const muted = "#55524b";
const rule = "#d9d5cc";
const signal = "#f04e23";
const W = 1080;
const H = 1350;

const esc = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;");

function lines(xs, x, y, size, step, options = {}) {
  const { weight = 700, family = "Bahnschrift", fill = ink, anchor = "start", tracking = 0 } = options;
  return `<text x="${x}" y="${y}" font-family="${family}" font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}" letter-spacing="${tracking}">${xs.map((line, i) => `<tspan x="${x}" dy="${i ? step : 0}">${esc(line)}</tspan>`).join("")}</text>`;
}

function pill(x, y, width, label, active = false) {
  return `<rect x="${x}" y="${y}" width="${width}" height="58" rx="29" fill="${active ? signal : paper}" stroke="${active ? signal : ink}" stroke-width="3"/><text x="${x + width / 2}" y="${y + 39}" text-anchor="middle" font-family="Arial" font-size="23" font-weight="700" fill="${active ? "#ffffff" : ink}">${esc(label)}</text>`;
}

function frame({ section, number, title, body = [], visual = "", dark = false }) {
  const bg = dark ? ink : paper;
  const fg = dark ? paper : ink;
  const sub = dark ? "#c8c2b7" : muted;
  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <rect width="1080" height="1350" fill="${bg}"/>
    <line x1="72" y1="132" x2="1008" y2="132" stroke="${dark ? "#3a352e" : rule}" stroke-width="2"/>
    <text x="72" y="102" font-family="Arial" font-size="22" font-weight="700" fill="${dark ? "#c8c2b7" : muted}" letter-spacing="2">${esc(section)} / ${String(number).padStart(2, "0")}</text>
    ${lines(title, 72, 236, title.length > 3 ? 68 : 78, title.length > 3 ? 72 : 84, { fill: fg, tracking: -1 })}
    ${body.length ? lines(body, 72, 236 + (title.length - 1) * (title.length > 3 ? 72 : 84) + 94, 31, 43, { weight: 400, family: "Arial", fill: sub }) : ""}
    ${visual}
    <line x1="72" y1="1260" x2="1008" y2="1260" stroke="${dark ? "#3a352e" : rule}" stroke-width="2"/>
    <text x="72" y="1304" font-family="Arial" font-size="20" font-weight="700" fill="${dark ? "#c8c2b7" : muted}" letter-spacing="1.4">EXAMUPLOADKIT.COM</text>
    <text x="1008" y="1304" text-anchor="end" font-family="Arial" font-size="20" fill="${dark ? "#c8c2b7" : muted}">Swipe →</text>
  </svg>`);
}

async function writeSlide(group, index, spec, composites = []) {
  const dir = path.join(out, group);
  await fs.mkdir(dir, { recursive: true });
  const target = path.join(dir, `${String(index).padStart(2, "0")}-${spec.slug}.png`);
  await sharp(frame({ ...spec, section: group.toUpperCase(), number: index }))
    .composite(composites)
    .png({ compressionLevel: 9 })
    .withMetadata({ density: 144 })
    .toFile(target);
  return target;
}

async function imageCard(file, left, top, width, height) {
  const image = await sharp(file).resize({ width, height, fit: "cover", position: "centre" }).jpeg({ quality: 91 }).toBuffer();
  const border = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${width + 8}" height="${height + 8}"><rect x="2" y="2" width="${width + 4}" height="${height + 4}" fill="none" stroke="${ink}" stroke-width="4"/></svg>`);
  return [
    { input: image, left: left + 4, top: top + 4 },
    { input: border, left, top },
  ];
}

const created = [];

// Cover exports are copied so each carousel folder is publish-ready in order.
for (const [group, cover] of [["exam", "01-exam.png"], ["upload", "02-upload.png"], ["kit", "03-kit.png"]]) {
  const dir = path.join(out, group);
  await fs.mkdir(dir, { recursive: true });
  const target = path.join(dir, "01-cover.png");
  await fs.copyFile(path.join(campaign, "exports", "instagram", "covers", cover), target);
  created.push(target);
}

created.push(await writeSlide("exam", 2, {
  slug: "a-particular-file",
  title: ["YOUR EXAM FORM", "DOES NOT ASK", "FOR ‘A PHOTO.’"],
  body: ["It asks for a particular file."],
  visual: `<rect x="72" y="735" width="936" height="315" fill="none" stroke="${ink}" stroke-width="4"/>${lines(["PHOTO.JPG"], 112, 835, 88, 90, { tracking: 2 })}${lines(["200 × 230 px   ·   JPEG   ·   20–50 KB"], 112, 925, 27, 38, { family: "Arial", weight: 400, fill: muted })}<circle cx="946" cy="1000" r="22" fill="${signal}"/>`,
}));

created.push(await writeSlide("exam", 3, {
  slug: "the-rule-stack",
  title: ["ONE UPLOAD.", "SEVERAL RULES."],
  body: ["The exact combination belongs to the examination."],
  visual: `${pill(72, 720, 250, "DIMENSIONS", true)}${pill(340, 720, 220, "FILE SIZE")}${pill(578, 720, 190, "FORMAT")}${pill(786, 720, 222, "BACKGROUND")}${pill(72, 806, 305, "NAME + DATE")}${pill(395, 806, 245, "FILENAME")}${pill(658, 806, 350, "APPEARANCE RULES")}<line x1="72" y1="930" x2="1008" y2="930" stroke="${ink}" stroke-width="3"/>${lines(["Right for one form.", "Wrong for the next."], 72, 1010, 52, 64, { weight: 700 })}`,
}));

created.push(await writeSlide("exam", 4, {
  slug: "rules-change",
  title: ["THE RULES CHANGE", "WITH THE EXAM."],
  body: ["A universal preset cannot represent them."],
  visual: `<rect x="72" y="682" width="446" height="405" fill="#ffffff" stroke="${ink}" stroke-width="3"/><rect x="562" y="682" width="446" height="405" fill="#ffffff" stroke="${ink}" stroke-width="3"/>${lines(["EXAM A"], 112, 750, 28, 34, { fill: signal, tracking: 2 })}${lines(["200 × 230", "20–50 KB", "white background"], 112, 835, 46, 66, {})}${lines(["EXAM B"], 602, 750, 28, 34, { fill: signal, tracking: 2 })}${lines(["413 × 531", "JPEG only", "different framing"], 602, 835, 46, 66, {})}`,
}));

created.push(await writeSlide("exam", 5, {
  slug: "exam-first",
  title: ["THE EXAM", "COMES FIRST."],
  body: ["It configures the preparation work."],
  visual: `<rect x="72" y="705" width="936" height="100" fill="${ink}"/>${lines(["1  CHOOSE THE EXAMINATION"], 112, 771, 32, 40, { fill: paper, tracking: 1 })}<line x1="180" y1="805" x2="180" y2="900" stroke="${signal}" stroke-width="5"/><rect x="72" y="900" width="936" height="100" fill="none" stroke="${ink}" stroke-width="3"/>${lines(["2  READ THE RECORDED RULE"], 112, 966, 32, 40, { tracking: 1 })}<line x1="900" y1="1000" x2="900" y2="1095" stroke="${signal}" stroke-width="5"/><rect x="72" y="1095" width="936" height="100" fill="${signal}"/>${lines(["3  PREPARE THE SUPPORTED FILES"], 112, 1161, 32, 40, { fill: "#ffffff", tracking: 1 })}`,
}));

created.push(await writeSlide("exam", 6, {
  slug: "no-guessing",
  title: ["IF THE RULE IS", "NOT CONFIRMED,", "WE DO NOT GUESS."],
  body: ["The gap stays visible so you know what to check."],
  dark: true,
  visual: `<rect x="72" y="770" width="936" height="270" fill="none" stroke="${signal}" stroke-width="4"/>${lines(["PUBLISHED VALUE"], 112, 842, 25, 32, { fill: "#c8c2b7", tracking: 2 })}${lines(["Not stated in the source"], 112, 930, 50, 56, { fill: paper })}<text x="950" y="993" text-anchor="end" font-family="Arial" font-size="25" fill="${signal}">CHECK YOUR NOTICE</text>`,
}));

created.push(await writeSlide("exam", 7, {
  slug: "start-with-your-exam",
  title: ["START WITH", "YOUR EXAM."],
  body: ["Search 770 examination records at examuploadkit.com", "Launch-day count checked 2 October 2026."],
  dark: true,
  visual: `<rect x="72" y="790" width="936" height="118" rx="59" fill="${paper}"/>${lines(["Search for your examination"], 124, 863, 30, 38, { family: "Arial", weight: 400 })}<circle cx="945" cy="849" r="36" fill="${signal}"/><path d="M932 849h26M949 837l12 12-12 12" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>`,
}));

created.push(await writeSlide("upload", 2, {
  slug: "search",
  title: ["SEARCH FOR YOUR", "EXAMINATION."],
  body: ["Its record decides what comes next."],
  visual: `<rect x="72" y="745" width="936" height="112" rx="56" fill="#ffffff" stroke="${ink}" stroke-width="3"/>${lines(["SSC CGL"], 126, 817, 34, 42, { family: "Arial", weight: 400 })}<circle cx="944" cy="801" r="36" fill="${signal}"/><path d="M930 801h28" stroke="#fff" stroke-width="4"/><rect x="72" y="890" width="936" height="180" fill="#ffffff" stroke="${rule}" stroke-width="3"/>${lines(["SSC Combined Graduate Level Examination 2026"], 112, 958, 31, 42, { family: "Arial" })}${lines(["Open examination →"], 112, 1020, 24, 30, { family: "Arial", fill: signal })}`,
}));

created.push(await writeSlide("upload", 3, {
  slug: "see-the-files",
  title: ["SEE WHAT THE", "APPLICATION ASKS FOR."],
  body: ["Before uploading anything."],
  visual: `${["PHOTOGRAPH", "SIGNATURE", "THUMB IMPRESSION", "DECLARATION", "DOCUMENTS"].map((label, i) => `<rect x="72" y="${690 + i * 92}" width="936" height="70" fill="${i < 2 ? "#ffffff" : paper}" stroke="${i < 2 ? ink : rule}" stroke-width="${i < 2 ? 3 : 2}"/><rect x="96" y="${709 + i * 92}" width="30" height="30" fill="${i < 2 ? signal : "none"}" stroke="${i < 2 ? signal : muted}" stroke-width="3"/>${i < 2 ? `<path d="M103 ${724 + i * 92}l8 8 16-18" fill="none" stroke="#fff" stroke-width="3"/>` : ""}${lines([label], 154, 736 + i * 92, 25, 30, { tracking: 1 })}`).join("")}`,
}));

const beforePhoto = path.join(publicDir, "examples", "band", "photo-a1-uploaded.jpg");
const afterPhoto = path.join(publicDir, "examples", "band", "photo-a1-prepared.jpg");

created.push(await writeSlide("upload", 4, {
  slug: "upload-source",
  title: ["UPLOAD THE SOURCE", "FOR THIS FILE."],
  body: ["The checks follow the selected exam's specification."],
  visual: `<rect x="620" y="720" width="388" height="430" fill="#ffffff" stroke="${ink}" stroke-width="4"/>${lines(["SOURCE PHOTO"], 72, 770, 24, 30, { fill: signal, tracking: 2 })}${lines(["Use a clear,", "front-facing source.", "The product handles", "the file work."], 72, 850, 39, 52, {})}`,
}, await imageCard(beforePhoto, 654, 754, 320, 360)));

created.push(await writeSlide("upload", 5, {
  slug: "preview",
  title: ["SEE THE REAL", "PREPARED PREVIEW."],
  body: ["And any issue the product can actually detect."],
  visual: `${lines(["AS UPLOADED"], 72, 720, 22, 28, { fill: muted, tracking: 2 })}${lines(["PREPARED"], 564, 720, 22, 28, { fill: signal, tracking: 2 })}<text x="72" y="1190" font-family="Arial" font-size="19" fill="${muted}">Representational generated example used on the product site.</text>`,
}, [...await imageCard(beforePhoto, 72, 750, 430, 400), ...await imageCard(afterPhoto, 578, 750, 430, 400)]));

created.push(await writeSlide("upload", 6, {
  slug: "review-price",
  title: ["CHECK THE KIT", "BEFORE YOU PAY."],
  body: ["The prepared files and final price stay visible."],
  visual: `<rect x="72" y="710" width="936" height="140" fill="#fff" stroke="${ink}" stroke-width="3"/>${lines(["ONE FILE"], 112, 775, 25, 30, { tracking: 2 })}${lines(["₹3"], 940, 795, 62, 62, { anchor: "end" })}<rect x="72" y="880" width="936" height="180" fill="${ink}"/>${lines(["TWO OR MORE"], 112, 947, 25, 30, { fill: "#c8c2b7", tracking: 2 })}${lines(["THE WHOLE KIT"], 112, 1004, 34, 40, { fill: paper })}${lines(["₹5"], 940, 1007, 72, 72, { fill: signal, anchor: "end" })}`,
}));

created.push(await writeSlide("upload", 7, {
  slug: "download",
  title: ["DOWNLOAD HERE.", "SUBMIT THERE."],
  body: ["You upload the finished file on the authority's portal."],
  visual: `<rect x="72" y="748" width="380" height="240" fill="${ink}"/>${lines(["PREPARED", "FILE"], 112, 835, 48, 58, { fill: paper })}<path d="M452 868h176" stroke="${signal}" stroke-width="6"/><path d="M606 846l25 22-25 22" fill="none" stroke="${signal}" stroke-width="6"/><rect x="628" y="748" width="380" height="240" fill="#fff" stroke="${ink}" stroke-width="3"/>${lines(["OFFICIAL", "PORTAL"], 668, 835, 48, 58, {})}${lines(["ExamUploadKit does not submit the form for you."], 72, 1065, 25, 32, { family: "Arial", weight: 400, fill: muted })}`,
}));

created.push(await writeSlide("upload", 8, {
  slug: "try-the-flow",
  title: ["TRY THE", "FULL FLOW."],
  body: ["Choose an exam at examuploadkit.com", "Tell us where it becomes unclear."],
  dark: true,
  visual: `<rect x="72" y="790" width="936" height="118" rx="59" fill="${signal}"/>${lines(["OPEN EXAMUPLOADKIT"], 540, 864, 31, 38, { fill: "#fff", anchor: "middle", tracking: 1 })}`,
}));

created.push(await writeSlide("kit", 2, {
  slug: "one-place",
  title: ["ONE EXAMINATION.", "ONE PLACE FOR", "ITS UPLOAD FILES."],
  body: ["That is the kit."],
  visual: `<rect x="72" y="790" width="936" height="250" fill="#fff" stroke="${ink}" stroke-width="4"/>${["PHOTO", "SIGN", "THUMB", "DECL.", "PDF"].map((t, i) => `${pill(100 + i * 181, 875, 155, t, i < 2)}`).join("")}`,
}));

const signAfter = path.join(publicDir, "examples", "band", "sign-s1-prepared.jpg");
created.push(await writeSlide("kit", 3, {
  slug: "what-is-inside",
  title: ["THE FILES YOUR", "APPLICATION NEEDS."],
  body: ["Preparation appears only where the platform supports it."],
  visual: `<rect x="72" y="725" width="560" height="390" fill="#fff" stroke="${ink}" stroke-width="3"/>${lines(["PHOTOGRAPH", "SIGNATURE", "THUMB IMPRESSION", "HANDWRITTEN DECLARATION", "DOCUMENTS + PDF WORK"], 112, 792, 28, 68, { tracking: 1 })}<rect x="672" y="725" width="336" height="390" fill="#fff" stroke="${ink}" stroke-width="3"/>`,
}, await imageCard(signAfter, 700, 812, 280, 210)));

created.push(await writeSlide("kit", 4, {
  slug: "rule-first",
  title: ["THE RULE", "COMES FIRST."],
  body: ["Each value should trace back to what the examination published."],
  visual: `<rect x="72" y="730" width="936" height="330" fill="#fff" stroke="${ink}" stroke-width="3"/>${lines(["SOURCE"], 112, 797, 22, 28, { fill: signal, tracking: 2 })}${lines(["Official notice or application portal"], 112, 858, 34, 42, { family: "Arial", weight: 400 })}<line x1="112" y1="900" x2="968" y2="900" stroke="${rule}" stroke-width="2"/>${lines(["RECORDED RULE"], 112, 953, 22, 28, { fill: signal, tracking: 2 })}${lines(["Shown with the applicable exam and cycle"], 112, 1014, 34, 42, { family: "Arial", weight: 400 })}`,
}));

created.push(await writeSlide("kit", 5, {
  slug: "temporary-files",
  title: ["YOUR UPLOADS", "ARE TEMPORARY."],
  body: ["No account is required."],
  dark: true,
  visual: `<circle cx="330" cy="890" r="150" fill="none" stroke="${signal}" stroke-width="14"/>${lines(["30"], 330, 900, 106, 110, { fill: paper, anchor: "middle" })}${lines(["MINUTES"], 330, 955, 24, 28, { fill: "#c8c2b7", anchor: "middle", tracking: 2 })}<line x1="550" y1="745" x2="550" y2="1060" stroke="#3a352e" stroke-width="3"/>${lines(["UP TO", "1 HOUR"], 640, 860, 62, 76, { fill: paper })}${lines(["with a bounded extension", "requested before expiry"], 640, 1010, 25, 35, { family: "Arial", weight: 400, fill: "#c8c2b7" })}`,
}));

created.push(await writeSlide("kit", 6, {
  slug: "price",
  title: ["SMALL, VISIBLE", "PRICING."],
  body: ["Check the live price before launch-day publishing."],
  visual: `<rect x="72" y="720" width="430" height="350" fill="#fff" stroke="${ink}" stroke-width="3"/>${lines(["ONE FILE"], 112, 795, 25, 30, { tracking: 2 })}${lines(["₹3"], 112, 920, 112, 116, {})}<rect x="544" y="720" width="464" height="350" fill="${ink}"/>${lines(["TWO OR MORE"], 584, 795, 25, 30, { fill: "#c8c2b7", tracking: 2 })}${lines(["₹5"], 584, 920, 112, 116, { fill: signal })}${lines(["THE WHOLE KIT"], 584, 1005, 25, 30, { fill: paper, tracking: 2 })}`,
}));

created.push(await writeSlide("kit", 7, {
  slug: "trust-boundary",
  title: ["PREPARED HERE.", "SUBMITTED BY YOU."],
  body: ["Final acceptance belongs to the examination authority."],
  visual: `<line x1="140" y1="845" x2="940" y2="845" stroke="${ink}" stroke-width="5"/>${["PREPARE", "DOWNLOAD", "SUBMIT"].map((t, i) => `<circle cx="${180 + i * 360}" cy="845" r="38" fill="${i === 2 ? signal : ink}"/>${lines([String(i + 1)], 180 + i * 360, 855, 27, 30, { fill: "#fff", anchor: "middle" })}${lines([t], 180 + i * 360, 940, 27, 32, { anchor: "middle", tracking: 1 })}`).join("")}`,
}));

created.push(await writeSlide("kit", 8, {
  slug: "find-your-exam",
  title: ["FIND YOUR EXAM.", "BUILD YOUR KIT."],
  body: ["examuploadkit.com"],
  dark: true,
  visual: `<rect x="72" y="790" width="936" height="118" rx="59" fill="${paper}"/>${lines(["SEARCH 770 EXAMINATION RECORDS"], 540, 864, 30, 38, { anchor: "middle", tracking: 1 })}`,
}));

const manifest = {
  generatedAt: new Date().toISOString(),
  dimensions: { width: W, height: H },
  format: "PNG",
  sourceAssets: [
    "apps/web/public/brand/examuploadkit-stacked-light.png",
    "apps/web/public/examples/band/photo-a1-uploaded.jpg",
    "apps/web/public/examples/band/photo-a1-prepared.jpg",
    "apps/web/public/examples/band/sign-s1-prepared.jpg",
  ],
  disclosure: "Photo and signature examples are the representational generated examples already disclosed on the product site; they are not candidate files.",
  files: created.map((file) => path.relative(campaign, file).replaceAll("\\", "/")),
};
async function reviewSheet(group) {
  const dir = path.join(out, group);
  const files = (await fs.readdir(dir)).filter((name) => name.endsWith(".png")).sort();
  const thumbWidth = 270;
  const thumbHeight = 338;
  const gap = 18;
  const pad = 24;
  const cols = 4;
  const rows = Math.ceil(files.length / cols);
  const width = pad * 2 + cols * thumbWidth + (cols - 1) * gap;
  const height = pad * 2 + rows * thumbHeight + (rows - 1) * gap;
  const inputs = await Promise.all(files.map((file) => sharp(path.join(dir, file)).resize({ width: thumbWidth, height: thumbHeight, fit: "cover" }).png().toBuffer()));
  const target = path.join(campaign, "exports", "instagram", `review-${group}.png`);
  await sharp({ create: { width, height, channels: 3, background: ink } })
    .composite(inputs.map((input, index) => ({ input, left: pad + (index % cols) * (thumbWidth + gap), top: pad + Math.floor(index / cols) * (thumbHeight + gap) })))
    .png({ compressionLevel: 9 })
    .toFile(target);
  return target;
}

manifest.reviewSheets = {};
for (const group of ["exam", "upload", "kit"]) {
  const file = await reviewSheet(group);
  manifest.reviewSheets[group] = path.relative(campaign, file).replaceAll("\\", "/");
}
await fs.writeFile(path.join(campaign, "exports", "carousel-manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
console.log(JSON.stringify({ count: created.length, out }, null, 2));
