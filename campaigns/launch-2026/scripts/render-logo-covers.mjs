import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "../../../apps/web/node_modules/sharp/dist/index.cjs";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const campaignDir = path.resolve(scriptDir, "..");
const outputDir = path.join(campaignDir, "exports", "instagram", "covers");
const sourcePath = path.resolve(
  campaignDir,
  "..",
  "..",
  "apps",
  "web",
  "public",
  "brand",
  "examuploadkit-stacked-light.png",
);

const CANVAS = { width: 1080, height: 1350 };
const PAPER = "#faf9f6";
const SAFE_SQUARE = { left: 0, top: 135, width: 1080, height: 1080 };
const TARGET_UPLOAD_WIDTH = 920;

// Pixel-exact row bounds in the authorised 2800 x 856 source asset.
// The rows interlock in the full logo, so each crop includes its complete
// outer rule and no reconstructed lettering or CSS-drawn substitute.
const rows = [
  { id: "01-exam", title: "EXAM", left: 1028, top: 96, width: 744, height: 224 },
  { id: "02-upload", title: "UPLOAD", left: 844, top: 316, width: 1112, height: 224 },
  { id: "03-kit", title: "KIT", left: 1120, top: 536, width: 560, height: 224 },
];

async function renderCover(row) {
  const scale = TARGET_UPLOAD_WIDTH / rows[1].width;
  const width = Math.round(row.width * scale);
  const height = Math.round(row.height * scale);
  const left = Math.round((CANVAS.width - width) / 2);
  const top = Math.round(SAFE_SQUARE.top + (SAFE_SQUARE.height - height) / 2);

  const excerpt = await sharp(sourcePath)
    .extract({ left: row.left, top: row.top, width: row.width, height: row.height })
    .resize({ width, height, fit: "fill", kernel: sharp.kernel.lanczos3 })
    .png()
    .toBuffer();

  const outputPath = path.join(outputDir, `${row.id}.png`);
  await sharp({
    create: {
      width: CANVAS.width,
      height: CANVAS.height,
      channels: 3,
      background: PAPER,
    },
  })
    .composite([{ input: excerpt, left, top }])
    .png({ compressionLevel: 9, palette: false })
    .withMetadata({ density: 144 })
    .toFile(outputPath);

  return { ...row, outputPath, placed: { left, top, width, height } };
}

async function renderGridPreview(covers) {
  const thumbWidth = 480;
  const thumbHeight = 600;
  const gap = 18;
  const pad = 36;
  const previewWidth = pad * 2 + thumbWidth * 3 + gap * 2;
  const previewHeight = pad * 2 + thumbHeight;

  const images = await Promise.all(
    covers.map((cover) =>
      sharp(cover.outputPath)
        .resize({ width: thumbWidth, height: thumbHeight, fit: "cover" })
        .png()
        .toBuffer(),
    ),
  );

  const outputPath = path.join(outputDir, "00-pinned-profile-row-preview.png");
  await sharp({
    create: {
      width: previewWidth,
      height: previewHeight,
      channels: 3,
      background: "#111110",
    },
  })
    .composite(
      images.map((input, index) => ({
        input,
        left: pad + index * (thumbWidth + gap),
        top: pad,
      })),
    )
    .png({ compressionLevel: 9, palette: false })
    .withMetadata({ density: 144 })
    .toFile(outputPath);

  return outputPath;
}

await fs.mkdir(outputDir, { recursive: true });
const covers = [];
for (const row of rows) covers.push(await renderCover(row));
const previewPath = await renderGridPreview(covers);

const manifest = {
  campaign: "ExamUploadKit launch 2026",
  generatedAt: new Date().toISOString(),
  source: path.relative(campaignDir, sourcePath).replaceAll("\\", "/"),
  sourcePolicy: "Authorised logo artwork is cropped and scaled only; lettering, rules, colour and proportions are unchanged.",
  canvas: CANVAS,
  profileCropSafeSquare: SAFE_SQUARE,
  covers: covers.map(({ id, title, outputPath, placed }) => ({
    id,
    title,
    file: path.relative(campaignDir, outputPath).replaceAll("\\", "/"),
    placed,
  })),
  preview: path.relative(campaignDir, previewPath).replaceAll("\\", "/"),
};

await fs.writeFile(
  path.join(campaignDir, "exports", "manifest.json"),
  `${JSON.stringify(manifest, null, 2)}\n`,
  "utf8",
);

console.log(JSON.stringify(manifest, null, 2));
