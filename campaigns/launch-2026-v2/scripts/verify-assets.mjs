import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import sharp from "../../../apps/web/node_modules/sharp/dist/index.cjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const campaign = path.resolve(here, "..");
const manifest = JSON.parse(await fs.readFile(path.join(campaign, "exports", "manifest.json"), "utf8"));
const failures = [];
const hashes = new Map();

function expected(file) {
  if (file.includes("/instagram/carousels/")) return [1080, 1350];
  if (file.includes("/story-status/")) return [1080, 1920];
  if (file.includes("/linkedin/")) return [1200, 627];
  if (file.includes("/x/")) return [1600, 900];
  if (file.includes("/reddit/")) return [1200, 628];
  return null;
}

for (const relative of manifest.files) {
  const absolute = path.join(campaign, relative);
  const buffer = await fs.readFile(absolute);
  if (!buffer.length) failures.push(`${relative}: empty`);
  const meta = await sharp(buffer).metadata();
  const dims = expected(relative);
  if (dims && (meta.width !== dims[0] || meta.height !== dims[1])) failures.push(`${relative}: ${meta.width}x${meta.height}, expected ${dims.join("x")}`);
  const hash = createHash("sha256").update(buffer).digest("hex");
  if (hashes.has(hash)) failures.push(`${relative}: duplicates ${hashes.get(hash)}`);
  hashes.set(hash, relative);
}

for (const relative of manifest.sourceArt) {
  const absolute = path.join(campaign, relative);
  const stat = await fs.stat(absolute);
  if (!stat.isFile() || stat.size < 100_000) failures.push(`${relative}: missing or unexpectedly small`);
}

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}

console.log(`PASS: ${manifest.files.length} final assets; dimensions, non-empty files, source art and duplicate checks verified.`);

