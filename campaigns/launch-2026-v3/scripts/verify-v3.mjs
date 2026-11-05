import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import sharp from "../../../apps/web/node_modules/sharp/dist/index.cjs";

const here=path.dirname(fileURLToPath(import.meta.url));
const campaign=path.resolve(here,"..");
const manifest=JSON.parse(await fs.readFile(path.join(campaign,"exports","manifest.json"),"utf8"));
const errors=[];
const hashes=new Map();

function expected(file){
  if(file.includes("/instagram/")) return [1080,1350];
  if(file.includes("/linkedin/")) return [1200,1500];
  if(file.includes("/reddit/")) return [1080,1080];
  if(file.includes("/x/")) return [1600,900];
  return null;
}

for(const relative of manifest.files){
  const absolute=path.join(campaign,relative);
  const buffer=await fs.readFile(absolute);
  const meta=await sharp(buffer).metadata();
  const dims=expected(relative);
  if(!dims || meta.width!==dims[0] || meta.height!==dims[1]) errors.push(`${relative}: unexpected ${meta.width}x${meta.height}`);
  if(buffer.length<8_000) errors.push(`${relative}: unexpectedly small (${buffer.length} bytes)`);
  const hash=createHash("sha256").update(buffer).digest("hex");
  if(hashes.has(hash)) errors.push(`${relative}: duplicates ${hashes.get(hash)}`);
  hashes.set(hash,relative);
}

const captures=(await fs.readdir(path.join(campaign,"source-ui"))).filter(x=>x.endsWith(".png"));
if(captures.length!==14) errors.push(`Expected 14 source UI captures, found ${captures.length}`);

const renderer=await fs.readFile(path.join(campaign,"scripts","render-v3.mjs"),"utf8");
if(/crop\(path\.join\(exampleDir,"photo-/u.test(renderer)) errors.push("Candidate example photographs must use contain(), never crop().");
if(!renderer.includes('contain(path.join(exampleDir,"photo-a1-uploaded.jpg"') || !renderer.includes('contain(path.join(exampleDir,"photo-a2-uploaded.jpg"')) errors.push("Expected full-frame candidate photograph placements were not found.");
if(!renderer.includes('previewPhoto(path.join(exampleDir,"photo-a1-prepared.jpg"')) errors.push("The before-payment prepared preview must carry the preview watermark.");
if(!renderer.includes('contain(path.join(exampleDir,"photo-a2-prepared.jpg"')) errors.push("The KIT photograph example must use the clean prepared source without a preview watermark.");
if(renderer.includes('source:"13-mobile-home.png"') || renderer.includes('source:"14-mobile-prepare.png"')) errors.push("Mobile captures must not be mixed into ordinary product walkthrough slides.");
if(!renderer.includes("mobilePair:true")) errors.push("Dedicated installable-application slide is missing.");

if(manifest.counts.total!==58 || manifest.files.length!==58) errors.push(`Expected 58 final images, manifest reports ${manifest.files.length}`);

if(errors.length){console.error(errors.join("\n"));process.exit(1);}
console.log("PASS: 58 final images, consistent desktop walkthroughs, dedicated mobile-install slides, protected before-payment preview, clean KIT photograph example, dimensions, source captures, file sizes and duplicate checks verified.");
