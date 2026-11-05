import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "../../../apps/web/node_modules/sharp/dist/index.cjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..", "..", "..");
const campaign = path.resolve(here, "..");
const out = path.join(campaign, "exports", "channels");
const publicDir = path.join(root, "apps", "web", "public");
const logoPath = path.join(publicDir, "brand", "examuploadkit-stacked-light.png");
const beforePath = path.join(publicDir, "examples", "band", "photo-a1-uploaded.jpg");
const afterPath = path.join(publicDir, "examples", "band", "photo-a1-prepared.jpg");
const paper = "#faf9f6";
const ink = "#111110";
const muted = "#55524b";
const signal = "#f04e23";

const esc = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
function text(lines, x, y, size, step, { fill = ink, weight = 700, family = "Bahnschrift", anchor = "start", tracking = 0 } = {}) {
  return `<text x="${x}" y="${y}" font-family="${family}" font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}" letter-spacing="${tracking}">${lines.map((line, i) => `<tspan x="${x}" dy="${i ? step : 0}">${esc(line)}</tspan>`).join("")}</text>`;
}

async function renderSvg(file, svg, composites = []) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  await sharp(Buffer.from(svg)).composite(composites).png({ compressionLevel: 9 }).withMetadata({ density: 144 }).toFile(file);
  return file;
}

const storyDir = path.join(out, "personal-story-status");
const storyFrames = [
  {
    file: "01-complete.png",
    bg: ink,
    label: "A PERSONAL NOTE",
    title: ["I FINALLY BUILT", "SOMETHING", "COMPLETE."],
    body: ["It is live. It works end to end.", "And it solves a real problem."],
  },
  {
    file: "02-the-problem.png",
    bg: paper,
    label: "THE PROBLEM",
    title: ["EXAM FORMS ASK", "FOR VERY PARTICULAR", "UPLOAD FILES."],
    body: ["Photographs, signatures and other files", "have their own dimensions, formats and limits."],
  },
  {
    file: "03-the-product.png",
    bg: paper,
    label: "IT IS CALLED",
    title: [],
    body: ["Exam application files, prepared to the rules."],
    logo: true,
  },
  {
    file: "04-send-it.png",
    bg: ink,
    label: "ONE REQUEST",
    title: ["APPEARING FOR", "AN EXAM?", "KNOW SOMEONE", "WHO IS?"],
    body: ["Please try it, or send it to them."],
  },
  {
    file: "05-feedback.png",
    bg: signal,
    label: "HONEST FEEDBACK, PLEASE",
    title: ["TELL ME WHAT", "BREAKS."],
    body: ["Tell me what could be better.", "I am very happy today.", "And this is only the beginning."],
  },
];

const created = [];
for (const frame of storyFrames) {
  const fg = frame.bg === paper ? ink : paper;
  const sub = frame.bg === paper ? muted : "#ddd7cc";
  const titleY = frame.logo ? 420 : 420;
  const logo = frame.logo ? await sharp(logoPath).trim({ background: paper, threshold: 8 }).resize({ width: 880 }).png().toBuffer() : null;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 1080 1920">
    <rect width="1080" height="1920" fill="${frame.bg}"/>
    <line x1="72" y1="160" x2="1008" y2="160" stroke="${frame.bg === paper ? "#d9d5cc" : frame.bg === signal ? "#ff8a66" : "#3a352e"}" stroke-width="3"/>
    ${text([frame.label], 72, 124, 23, 30, { fill: sub, family: "Arial", tracking: 3 })}
    ${frame.title.length ? text(frame.title, 72, titleY, frame.title.length > 3 ? 78 : 92, frame.title.length > 3 ? 86 : 100, { fill: fg, tracking: -1 }) : ""}
    ${text(frame.body, 72, frame.logo ? 1150 : 1030, 34, 52, { fill: sub, family: "Arial", weight: 400 })}
    <line x1="72" y1="1740" x2="1008" y2="1740" stroke="${frame.bg === paper ? "#d9d5cc" : frame.bg === signal ? "#ff8a66" : "#3a352e"}" stroke-width="3"/>
    ${text(["EXAMUPLOADKIT.COM"], 72, 1810, 24, 30, { fill: fg, family: "Arial", tracking: 2 })}
    ${frame.file === "04-send-it.png" ? `<rect x="72" y="1430" width="936" height="120" rx="60" fill="${signal}"/>${text(["OPEN EXAMUPLOADKIT"], 540, 1506, 31, 38, { fill: "#fff", anchor: "middle", tracking: 1 })}` : ""}
  </svg>`;
  const composites = logo ? [{ input: logo, left: 100, top: 530 }] : [];
  created.push(await renderSvg(path.join(storyDir, frame.file), svg, composites));
}

const linkedInSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="627" viewBox="0 0 1200 627">
  <rect width="1200" height="627" fill="${paper}"/>
  <rect x="0" y="0" width="22" height="627" fill="${signal}"/>
  ${text(["EXAM APPLICATION FILES,", "PREPARED TO THE RULES."], 72, 150, 60, 67, { tracking: -1 })}
  ${text(["Photograph · signature · thumb · declaration · documents"], 72, 330, 24, 32, { fill: muted, family: "Arial", weight: 400 })}
  <rect x="72" y="420" width="410" height="78" rx="39" fill="${ink}"/>
  ${text(["EXAMUPLOADKIT.COM"], 277, 470, 24, 30, { fill: paper, anchor: "middle", family: "Arial", tracking: 1 })}
  <line x1="760" y1="80" x2="760" y2="547" stroke="#d9d5cc" stroke-width="3"/>
  ${text(["770"], 980, 280, 118, 120, { anchor: "middle" })}
  ${text(["EXAMINATION", "RECORDS"], 980, 345, 24, 32, { anchor: "middle", fill: muted, family: "Arial", tracking: 2 })}
</svg>`;
created.push(await renderSvg(path.join(out, "linkedin", "launch-card-1200x627.png"), linkedInSvg));

const before = await sharp(beforePath).resize({ width: 520, height: 440, fit: "cover", position: "centre" }).jpeg({ quality: 91 }).toBuffer();
const after = await sharp(afterPath).resize({ width: 520, height: 440, fit: "cover", position: "centre" }).jpeg({ quality: 91 }).toBuffer();
const xSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">
  <rect width="1600" height="900" fill="${ink}"/>
  ${text(["I BUILT A TOOL FOR", "EXAM APPLICATION UPLOADS."], 72, 125, 66, 72, { fill: paper, tracking: -1 })}
  ${text(["Choose the exam. Prepare the files. Download them."], 72, 292, 27, 35, { fill: "#c8c2b7", family: "Arial", weight: 400 })}
  ${text(["AS UPLOADED"], 72, 378, 22, 28, { fill: "#c8c2b7", family: "Arial", tracking: 2 })}
  ${text(["PREPARED"], 640, 378, 22, 28, { fill: signal, family: "Arial", tracking: 2 })}
  <rect x="70" y="395" width="524" height="444" fill="none" stroke="${paper}" stroke-width="4"/>
  <rect x="638" y="395" width="524" height="444" fill="none" stroke="${signal}" stroke-width="4"/>
  ${text(["EXAMUPLOADKIT.COM"], 1380, 510, 24, 30, { fill: paper, anchor: "middle", family: "Arial", tracking: 2 })}
  ${text(["Representational", "generated example", "used on the site."], 1380, 620, 22, 31, { fill: "#c8c2b7", anchor: "middle", family: "Arial", weight: 400 })}
</svg>`;
created.push(await renderSvg(path.join(out, "x", "launch-proof-card-1600x900.png"), xSvg, [
  { input: before, left: 72, top: 397 },
  { input: after, left: 640, top: 397 },
]));

const manifest = {
  generatedAt: new Date().toISOString(),
  personalBoundary: "The Story/Status sequence uses personal first-person copy. Public cards use the product identity and disclose generated demonstration imagery.",
  files: created.map((file) => path.relative(campaign, file).replaceAll("\\", "/")),
};
await fs.mkdir(path.join(campaign, "exports"), { recursive: true });
await fs.writeFile(path.join(campaign, "exports", "channel-assets-manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
console.log(JSON.stringify({ count: created.length, out }, null, 2));
