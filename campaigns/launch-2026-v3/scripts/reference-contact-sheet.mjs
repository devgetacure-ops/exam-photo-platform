import fs from "node:fs/promises";
import path from "node:path";
import sharp from "../../../apps/web/node_modules/sharp/dist/index.cjs";

const source = "C:/Users/dmbar/Downloads/Telegram Desktop/glass grad";
const target = path.resolve("campaigns/launch-2026-v3/reference-review/contact-sheet.jpg");
const files = (await fs.readdir(source)).filter((name) => /\.(png|jpe?g|webp)$/i.test(name)).sort();
const tileW = 360, tileH = 500, labelH = 46, gap = 16, pad = 20, cols = 4;
const rows = Math.ceil(files.length / cols);
const layers = [];
for (let i = 0; i < files.length; i++) {
  const file = path.join(source, files[i]);
  const image = await sharp(file).rotate().resize(tileW, tileH - labelH, { fit: "contain", background: "#171717" }).jpeg({ quality: 86 }).toBuffer();
  const short = files[i].match(/_(\d{2}_\d{2}_\d{2})_/)?.[1]?.replaceAll("_", ":") ?? String(i + 1).padStart(2, "0");
  const label = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${tileW}" height="${labelH}"><rect width="100%" height="100%" fill="#0d0d0d"/><text x="14" y="30" fill="#f4f1ea" font-family="Arial" font-size="19">${String(i + 1).padStart(2, "0")}  ${short}</text></svg>`);
  const x = pad + (i % cols) * (tileW + gap), y = pad + Math.floor(i / cols) * (tileH + gap);
  layers.push({ input: image, left: x, top: y }, { input: label, left: x, top: y + tileH - labelH });
}
await fs.mkdir(path.dirname(target), { recursive: true });
await sharp({ create: { width: pad * 2 + cols * tileW + (cols - 1) * gap, height: pad * 2 + rows * tileH + (rows - 1) * gap, channels: 3, background: "#252525" } }).composite(layers).jpeg({ quality: 90 }).toFile(target);
console.log(JSON.stringify({ target, count: files.length, files }, null, 2));
