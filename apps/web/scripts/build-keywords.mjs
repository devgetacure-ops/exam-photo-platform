// Writes docs/seo/keywords.csv and docs/seo/KEYWORD_MAP.md from the
// examination records (DEC-088). Run from apps/web: npm run seo:keywords
import { mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { buildKeywords, summarise, toCsv } from "../src/lib/seo-keywords.ts";

const repo = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const rulesDir = join(repo, "examples", "rules");

const records = readdirSync(rulesDir)
    .filter((name) => name.startsWith("exam_") && name.endsWith(".json"))
    .sort()
    .map((name) => JSON.parse(readFileSync(join(rulesDir, name), "utf8")));

let unavailable = [];
try {
    unavailable = JSON.parse(readFileSync(join(rulesDir, "unavailable_examinations.json"), "utf8")).examinations ?? [];
} catch {
    // No research register: the covered examinations are enough.
}

const rows = buildKeywords(records, unavailable);
const out = join(repo, "docs", "seo");
mkdirSync(out, { recursive: true });
writeFileSync(join(out, "keywords.csv"), toCsv(rows));
// The first-priority rows alone, small enough to open in a spreadsheet and act on.
writeFileSync(join(out, "keywords-priority-1.csv"), toCsv(rows.filter((row) => row.priority === 1)));
writeFileSync(join(out, "KEYWORD_MAP.md"), summarise(rows));
console.log(`${rows.length} keywords from ${records.length} records written to docs/seo/`);
