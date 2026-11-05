import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import sharp from "../../../apps/web/node_modules/sharp/dist/index.cjs";

const here=path.dirname(fileURLToPath(import.meta.url));
const campaign=path.resolve(here,"..");
const manifest=JSON.parse(await fs.readFile(path.join(campaign,"exports","manifest.json"),"utf8"));
const expected={"instagram-product-overview":[1080,1350],"linkedin-product-overview":[1200,1500],"reddit-product-overview":[1080,1080],"x-product-overview":[1600,900]};
const errors=[];const hashes=new Map();
for(const relative of manifest.files){
  const absolute=path.join(campaign,relative),buffer=await fs.readFile(absolute),meta=await sharp(buffer).metadata();
  const key=Object.keys(expected).find(k=>relative.includes(k)),dims=expected[key];
  if(!dims||meta.width!==dims[0]||meta.height!==dims[1])errors.push(`${relative}: unexpected ${meta.width}x${meta.height}`);
  if(buffer.length<12000)errors.push(`${relative}: unexpectedly small (${buffer.length} bytes)`);
  const hash=createHash("sha256").update(buffer).digest("hex");if(hashes.has(hash))errors.push(`${relative}: duplicates ${hashes.get(hash)}`);hashes.set(hash,relative);
}
const counts=manifest.counts;
if(counts.instagram!==8||counts.linkedin!==8||counts.reddit!==6||counts.x!==4||manifest.files.length!==26)errors.push(`Expected 8/8/6/4 and 26 files; got ${JSON.stringify(counts)} and ${manifest.files.length}`);
const renderer=await fs.readFile(path.join(campaign,"scripts","render-product-journey.mjs"),"utf8");
for(const phrase of ["portal remains the final authority","used to train models","Deleted within 30 minutes","Razorpay","watermark(","770"]){if(!renderer.includes(phrase))errors.push(`Missing required product fact: ${phrase}`)}
if(/crop\(path\.join\(examples,"photo-/u.test(renderer))errors.push("Candidate photographs must use contain(), never crop().");
const pdf=path.join(campaign,"exports","linkedin-product-overview","examuploadkit-linkedin-product-journey.pdf");
try{const stat=await fs.stat(pdf);if(stat.size<100000)errors.push(`LinkedIn PDF unexpectedly small (${stat.size} bytes)`);}catch{errors.push("LinkedIn PDF is missing");}
if(errors.length){console.error(errors.join("\n"));process.exit(1)}
console.log("PASS: 26 unique images, platform dimensions, protected preview, product facts and LinkedIn PDF verified.");
