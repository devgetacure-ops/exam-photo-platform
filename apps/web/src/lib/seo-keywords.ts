/**
 * The keyword map (DEC-088): every search we mean to be found for, what the
 * person searching wants, and the page that should answer it.
 *
 * Generated from the examination records, so it grows with the catalogue and
 * never names a file an examination does not ask for or a figure no notice
 * published. Hand-written only where no record could supply it: the generic
 * tool searches ("compress photo to 20kb", "jpg to pdf") that people type
 * without naming an examination.
 *
 * Every row carries a coverage verdict, because a keyword without a page that
 * genuinely answers it cannot rank and should not be chased with a thin one:
 *
 * - `prepares`: the target page does the thing searched for.
 * - `explains`: the target page answers the question but cannot do the task
 *   on its own (the PDF page describes compression that runs inside a kit).
 * - `gap`: no page answers it yet; `target_url` is the page to build.
 *
 * Priority is a rule of thumb, not measured search volume: short forms and
 * the photograph and signature first, long tails and translations last. Real
 * volumes come from Search Console and Keyword Planner once the site is live.
 *
 * Self-contained on purpose (no imports), so `scripts/build-keywords.mjs` can
 * run it directly under Node's type stripping.
 */

export interface RawFileSize {
    published_minimum?: number;
    published_maximum?: number;
    size_unit_as_published?: string;
}

export interface RawDimensions {
    width_px?: number;
    height_px?: number;
}

export interface RawRequirement {
    requirement_type?: string;
    requirement_status?: string;
    platform_support?: string;
    file_spec?: { file_size?: RawFileSize; dimensions?: RawDimensions } | null;
}

export interface RawRecord {
    fictional_example?: boolean;
    exam?: {
        exam_id?: string;
        exam_name?: string;
        conducting_body?: string;
        examination_year?: number;
        aliases?: string[];
        category?: string;
    };
    image_requirements?: {
        file_size?: RawFileSize;
        dimensions?: RawDimensions;
        background?: { mode?: string; required_colour?: string };
    };
    requirements?: RawRequirement[];
}

export interface UnavailableExam {
    exam_name?: string;
}

export type Intent = "tool" | "informational" | "question" | "navigational";
export type Coverage = "prepares" | "explains" | "gap";
export type Language = "en" | "hi" | "hi-Latn";

export interface KeywordRow {
    keyword: string;
    cluster: string;
    intent: Intent;
    language: Language;
    priority: 1 | 2 | 3;
    target_url: string;
    coverage: Coverage;
    exam_ids: string;
    basis: string;
}

// ---- words ----------------------------------------------------------------

/** How candidates name each file in a search box, most common first. */
const FILE_WORDS: Record<string, string[]> = {
    photograph: ["photo", "photograph"],
    signature: ["signature", "sign"],
    thumb_impression: ["thumb impression", "left thumb impression"],
    handwritten_declaration: ["declaration", "handwritten declaration"],
    certificate_scan: ["certificate", "documents"],
    identity_document: ["id proof"],
};

const HINDI_FILE: Record<string, string> = {
    photograph: "फोटो",
    signature: "सिग्नेचर",
};

const PREPARED = new Set(["supported", "partially_supported"]);

export function normalise(text: string): string {
    return text
        .toLowerCase()
        .replace(/&/g, " and ")
        .replace(/[()[\]{}"“”'’,:;!?/\\|_]/g, " ")
        .replace(/\s+-\s+/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}

/**
 * A record's name the way a person would type it: no year, and none of the
 * catalogue's own qualifiers ("prior-cycle official fallback", "current portal
 * scope") that exist to tell two records apart and that nobody searches for.
 */
export function searchableName(name: string): string {
    let n = name.replace(/\s+-\s+.*$/, "");
    n = n.replace(/\([^)]*(live|fallback|scope)[^)]*\)/gi, " ");
    n = n.replace(/\b(19|20)\d{2}(-\d{2})?\b/g, " ");
    n = n.replace(
        /\b(current recruitment|current online application|online application|one time registration|photograph specification|photograph instruction|general|portal|photograph|live capture|online upload)\b/gi,
        " ",
    );
    return normalise(n);
}

function unit(size: RawFileSize | undefined): string | null {
    const u = size?.size_unit_as_published?.toLowerCase();
    return u === "kb" || u === "mb" ? u : null;
}

// ---- the builder ------------------------------------------------------------

class Rows {
    private map = new Map<string, KeywordRow>();

    add(row: Omit<KeywordRow, "keyword" | "exam_ids"> & { keyword: string; exam_ids?: string }): void {
        const keyword = normalise(row.keyword);
        if (!keyword) return;
        const existing = this.map.get(keyword);
        if (existing) {
            // The same words for two records (a shared short form): one row,
            // every examination named, the first target kept.
            if (row.exam_ids && !existing.exam_ids.split("|").includes(row.exam_ids)) {
                existing.exam_ids = existing.exam_ids ? `${existing.exam_ids}|${row.exam_ids}` : row.exam_ids;
            }
            if (row.priority < existing.priority) existing.priority = row.priority;
            return;
        }
        this.map.set(keyword, { ...row, keyword, exam_ids: row.exam_ids ?? "" });
    }

    list(): KeywordRow[] {
        return [...this.map.values()].sort(
            (a, b) => a.priority - b.priority || a.cluster.localeCompare(b.cluster) || a.keyword.localeCompare(b.keyword),
        );
    }
}

/**
 * The family hubs (DEC-096). A copy of `lib/exam-families.ts`, because this
 * file imports nothing; `exam-families.test.ts` fails if the two ever send an
 * examination to different hubs.
 */
const FAMILY_TARGETS: { slug: string; words: string[]; categories: string[] }[] = [
    { slug: "ssc-and-upsc", words: ["ssc", "ssc exam", "upsc", "upsc exam"], categories: ["central_recruitment"] },
    { slug: "banking-and-insurance", words: ["bank exam", "banking exam", "ibps", "bank po", "insurance exam", "lic exam"], categories: ["banking", "insurance"] },
    { slug: "railways", words: ["railway exam", "rrb", "railway"], categories: ["railway_recruitment", "railway_security", "railways"] },
    { slug: "police", words: ["police exam", "police constable", "police recruitment"], categories: ["police_recruitment"] },
    { slug: "defence", words: ["defence exam", "agniveer", "army exam"], categories: ["defence", "defence_recruitment"] },
    { slug: "teaching", words: ["tet", "teacher exam", "teacher recruitment"], categories: ["teacher_eligibility", "teacher_recruitment", "teacher_education_entrance", "teaching_eligibility", "teaching_research_eligibility", "teaching_and_non_teaching_recruitment"] },
    { slug: "state-commissions", words: ["psc exam", "state psc"], categories: ["state_psc", "state_psc_recruitment", "state_recruitment", "state_recruitment_family", "state_common_eligibility", "state_recruitment_common_eligibility"] },
    { slug: "entrance-exams", words: ["entrance exam", "engineering entrance", "medical entrance"], categories: ["entrance", "state_entrance", "management_entrance", "medical_entrance", "private_entrance", "school_admission_entrance"] },
];

/** Which family hub an examination belongs to, from its category. */
export function familySlugOf(record: RawRecord): string | null {
    const category = record.exam?.category ?? "";
    return FAMILY_TARGETS.find((family) => family.categories.includes(category))?.slug ?? null;
}

function examRows(rows: Rows, record: RawRecord): void {
    const exam = record.exam;
    const id = exam?.exam_id;
    if (!exam || !id || !exam.exam_name) return;

    const examUrl = `/exam/${id}`;
    const rulesUrl = `/exam/${id}/rules`;
    const requirements = record.requirements ?? [];
    const types = new Set(requirements.map((r) => r.requirement_type ?? ""));
    const prepares = (type: string) =>
        requirements.some((r) => r.requirement_type === type && PREPARED.has(r.platform_support ?? ""));

    const aliases = [...new Set((exam.aliases ?? []).map(normalise).filter(Boolean))];
    const fullName = searchableName(exam.exam_name);
    const primary = aliases[0] ?? fullName;
    const names: { name: string; short: boolean }[] = aliases.map((name) => ({ name, short: true }));
    if (fullName && !aliases.includes(fullName) && fullName.split(" ").length <= 7) {
        names.push({ name: fullName, short: false });
    }
    const year = exam.examination_year;
    const base = { exam_ids: id, basis: `record ${id}` };

    for (const { name: n, short } of names) {
        const core = (p: 1 | 2 | 3) => (short ? p : (Math.min(3, p + 1) as 1 | 2 | 3));

        for (const [type, words] of Object.entries(FILE_WORDS)) {
            if (!types.has(type)) continue;
            const headline = type === "photograph" || type === "signature";
            const toolCoverage: Coverage = prepares(type) ? "prepares" : "explains";

            words.forEach((w, wi) => {
                const first = wi === 0;
                const lead: 1 | 2 | 3 = headline && first ? 1 : 2;
                const info = { cluster: "exam-file-size", intent: "informational" as const, language: "en" as const, target_url: rulesUrl, coverage: "explains" as const, ...base };
                const tool = { cluster: "exam-file-prepare", intent: "tool" as const, language: "en" as const, target_url: examUrl, coverage: toolCoverage, ...base };

                rows.add({ ...info, keyword: `${n} ${w} size`, priority: core(lead) });
                rows.add({ ...tool, keyword: `${n} ${w} resize`, priority: core(lead) });
                if (!short && !first) return; // a long name keeps only the core searches

                rows.add({ ...info, keyword: `${n} ${w} size in kb`, priority: core(2) });
                rows.add({ ...info, keyword: `${w} size for ${n}`, priority: 3 });
                rows.add({ ...tool, keyword: `${n} ${w} resizer`, priority: 3 });
                rows.add({ ...tool, keyword: `resize ${w} for ${n}`, priority: 3 });
                rows.add({ ...tool, keyword: `${n} ${w} upload`, priority: core(2) });
                if (!short) return;

                rows.add({ ...info, keyword: `${n} ${w} kb`, priority: 3 });
                rows.add({ ...info, keyword: `${n} ${w} format`, priority: 3 });
                rows.add({ ...tool, keyword: `${n} ${w} compress`, priority: 3 });
                if (type !== "certificate_scan" && type !== "identity_document") {
                    rows.add({ ...info, keyword: `${n} ${w} dimensions`, priority: 3 });
                    rows.add({ ...info, keyword: `${n} ${w} pixel size`, priority: 3 });
                }
                if (headline) {
                    rows.add({ ...info, cluster: "exam-rejection", keyword: `${n} ${w} rejected`, priority: 3 });
                    rows.add({ ...info, cluster: "exam-question", intent: "question", keyword: `what is the ${w} size for ${n}`, priority: 3 });
                    rows.add({ ...info, cluster: "exam-question", intent: "question", keyword: `how many kb ${w} for ${n}`, priority: 3 });
                }
                // A short form that already carries its year ("cat 2025") would
                // read "cat 2025 2025".
                if (n === primary && year && first && !/\b(19|20)\d{2}\b/.test(n)) {
                    rows.add({ ...info, keyword: `${n} ${year} ${w} size`, priority: headline ? 2 : 3 });
                }
            });

            if (short && headline) {
                const hindiWord = HINDI_FILE[type];
                const w = words[0];
                rows.add({ cluster: "exam-hinglish", intent: "question", language: "hi-Latn", keyword: `${n} ${w} size kitna hona chahiye`, priority: 3, target_url: rulesUrl, coverage: "explains", ...base });
                rows.add({ cluster: "exam-hinglish", intent: "tool", language: "hi-Latn", keyword: `${n} ${w} resize kaise kare`, priority: 3, target_url: examUrl, coverage: toolCoverage, ...base });
                if (hindiWord) {
                    rows.add({ cluster: "exam-hindi", intent: "informational", language: "hi", keyword: `${n} ${hindiWord} साइज`, priority: 3, target_url: rulesUrl, coverage: "explains", ...base, basis: `record ${id}; no Hindi page yet` });
                }
            }
        }

        // The whole application, not one file.
        const whole = { cluster: "exam-application", language: "en" as const, ...base };
        if (types.has("photograph") && types.has("signature")) {
            rows.add({ ...whole, intent: "informational", keyword: `${n} photo and signature size`, priority: core(1), target_url: rulesUrl, coverage: "explains" });
            rows.add({ ...whole, intent: "tool", keyword: `${n} photo and signature resize`, priority: core(2), target_url: examUrl, coverage: prepares("photograph") && prepares("signature") ? "prepares" : "explains" });
        }
        if (requirements.length > 0) {
            rows.add({ ...whole, intent: "informational", keyword: `${n} documents required`, priority: core(2), target_url: rulesUrl, coverage: "explains" });
        }
        if (!short) continue;
        if (types.has("photograph")) {
            rows.add({ ...whole, intent: "informational", keyword: `${n} application form photo size`, priority: 2, target_url: rulesUrl, coverage: "explains" });
            rows.add({ ...whole, intent: "informational", keyword: `${n} form fill up photo size`, priority: 3, target_url: rulesUrl, coverage: "explains" });
            rows.add({ ...whole, intent: "tool", keyword: `${n} photo crop`, priority: 3, target_url: examUrl, coverage: prepares("photograph") ? "prepares" : "explains" });
            const background = record.image_requirements?.background;
            if (background?.mode === "exact_colour") {
                rows.add({ ...whole, intent: "tool", keyword: `${n} photo background`, priority: 3, target_url: examUrl, coverage: prepares("photograph") ? "prepares" : "explains" });
            }
        }
        if (types.has("certificate_scan")) {
            rows.add({ ...whole, intent: "informational", keyword: `${n} documents upload size`, priority: 3, target_url: rulesUrl, coverage: "explains" });
            rows.add({ ...whole, intent: "informational", keyword: `${n} certificate pdf size`, priority: 3, target_url: rulesUrl, coverage: "explains" });
        }
        rows.add({ ...whole, intent: "informational", keyword: `${n} upload rules`, priority: 3, target_url: rulesUrl, coverage: "explains" });
    }
}

/** Figures that some examination actually published, as generic searches. */
function specValueRows(rows: Rows, records: RawRecord[]): void {
    const sizes = new Map<string, { word: string; max: number; min?: number; unit: string; ids: Set<string> }>();
    const dims = new Map<string, { word: string; w: number; h: number; ids: Set<string> }>();

    const note = (type: string, id: string, size?: RawFileSize, dim?: RawDimensions) => {
        const word = FILE_WORDS[type]?.[0];
        if (!word) return;
        const u = unit(size);
        if (u && size?.published_maximum) {
            const key = `${word}|${size.published_minimum ?? ""}|${size.published_maximum}|${u}`;
            const entry = sizes.get(key) ?? { word, max: size.published_maximum, min: size.published_minimum, unit: u, ids: new Set<string>() };
            entry.ids.add(id);
            sizes.set(key, entry);
        }
        if (dim?.width_px && dim?.height_px) {
            const key = `${word}|${dim.width_px}x${dim.height_px}`;
            const entry = dims.get(key) ?? { word, w: dim.width_px, h: dim.height_px, ids: new Set<string>() };
            entry.ids.add(id);
            dims.set(key, entry);
        }
    };

    for (const record of records) {
        const id = record.exam?.exam_id;
        if (!id) continue;
        if ((record.requirements ?? []).some((r) => r.requirement_type === "photograph")) {
            note("photograph", id, record.image_requirements?.file_size, record.image_requirements?.dimensions);
        }
        for (const r of record.requirements ?? []) {
            if (r.requirement_type && r.requirement_type !== "photograph") {
                note(r.requirement_type, id, r.file_spec?.file_size ?? undefined, r.file_spec?.dimensions ?? undefined);
            }
        }
    }

    const used = (ids: Set<string>) => `published by ${ids.size} record${ids.size === 1 ? "" : "s"}: ${[...ids].slice(0, 6).join(", ")}${ids.size > 6 ? ", …" : ""}`;

    for (const { word, max, min, unit: u, ids } of sizes.values()) {
        const target = `/resize/${word.replace(/\s+/g, "-")}-to-${max}${u}`;
        const common = { cluster: "spec-value", intent: "tool" as const, language: "en" as const, target_url: target, coverage: "gap" as const, exam_ids: [...ids].join("|"), basis: used(ids) };
        const p: 1 | 2 | 3 = ids.size >= 3 ? 2 : 3;
        rows.add({ ...common, keyword: `resize ${word} to ${max} ${u}`, priority: p });
        rows.add({ ...common, keyword: `compress ${word} to ${max}${u}`, priority: p });
        rows.add({ ...common, keyword: `${word} ${max} ${u}`, priority: 3 });
        if (min !== undefined) {
            rows.add({ ...common, keyword: `${word} ${min} to ${max} ${u}`, priority: 3 });
            rows.add({ ...common, keyword: `${word} size ${min}-${max} ${u}`, priority: 3 });
        }
    }
    for (const { word, w, h, ids } of dims.values()) {
        const target = `/resize/${word.replace(/\s+/g, "-")}-${w}x${h}`;
        const common = { cluster: "spec-value", intent: "tool" as const, language: "en" as const, target_url: target, coverage: "gap" as const, exam_ids: [...ids].join("|"), basis: used(ids) };
        rows.add({ ...common, keyword: `${word} ${w}x${h}`, priority: ids.size >= 3 ? 2 : 3 });
        rows.add({ ...common, keyword: `${word} ${w} x ${h} pixels`, priority: 3 });
        rows.add({ ...common, keyword: `resize ${word} to ${w}x${h}`, priority: 3 });
    }
}

/** Searches that name no examination: the tools people reach for around a form. */
function genericRows(rows: Rows): void {
    const gen = (cluster: string, intent: Intent, target: string, coverage: Coverage, basis: string) =>
        (keyword: string, priority: 1 | 2 | 3, language: Language = "en") =>
            rows.add({ keyword, cluster, intent, language, priority, target_url: target, coverage, exam_ids: "", basis });

    // Made for a form: what the product does for every examination.
    const form = gen("generic-exam-form", "tool", "/", "prepares", "the kit prepares these for every listed examination");
    for (const k of [
        "photo resize for exam form", "photo resize for online form", "photo resize for govt exam", "exam photo resizer",
        "online form photo resizer", "resize photo for application form", "signature resize for exam form",
        "signature resize for online form", "signature resizer", "photo and signature resizer",
        "photo and signature resize for online form", "exam photo maker", "exam photo editor",
        "passport size photo for exam form", "photo crop for exam form", "thumb impression resize",
        "left thumb impression for online form", "handwritten declaration for online form",
        "change photo background to white for exam form", "remove background for exam photo",
        "government exam photo resize", "sarkari exam photo resize", "photo resize for sarkari form",
    ]) form(k, 1);
    for (const k of [
        "photo resize for ssc form", "photo resize for bank form", "photo resize for railway form",
        "photo resize for upsc form", "signature resize online free", "photo size reducer for online form",
        "online application photo editor", "exam form photo white background",
    ]) form(k, 2);

    // Generic information, not yet a page of its own.
    const info = gen("generic-exam-info", "informational", "/photo-size-for-exams", "gap", "no single page answers the generic question yet");
    for (const k of [
        "exam photo size", "online form photo size", "govt exam photo size in kb", "photo size for online application",
        "signature size for online form", "signature size in kb", "passport size photo size in kb",
        "standard photo size for exam form", "photo size for government exam", "sarkari form photo size",
    ]) info(k, 2);

    // Compression to a size: the free in-browser tool (DEC-096).
    const sizes = ["10kb", "15kb", "20kb", "25kb", "30kb", "40kb", "50kb", "60kb", "80kb", "100kb", "150kb", "200kb", "300kb", "500kb", "1mb", "2mb"];
    const common = new Set(["20kb", "50kb", "100kb", "200kb"]);
    for (const object of ["photo", "image", "jpg", "jpeg", "png", "signature", "passport size photo", "picture"]) {
        const tool = gen("compress-image-to-size", "tool", "/compress-image", "prepares", "the compress-to-size tool, in the browser");
        for (const size of sizes) {
            const spaced = size.replace(/(kb|mb)$/, " $1");
            const p: 1 | 2 | 3 = common.has(size) && ["photo", "image", "signature", "jpg"].includes(object) ? 1 : object === "picture" || object === "png" ? 3 : 2;
            tool(`compress ${object} to ${size}`, p);
            tool(`reduce ${object} size to ${size}`, p);
            tool(`resize ${object} to ${spaced}`, p === 1 ? 2 : 3);
            tool(`${object} to ${size} online`, 3);
        }
    }

    const pdfSizes = ["50kb", "100kb", "200kb", "300kb", "500kb", "1mb", "2mb"];
    const pdfCompress = gen("compress-pdf-to-size", "tool", "/compress-pdf", "gap", "the PDF page describes compression that runs inside a kit; a standalone tool is needed");
    for (const size of pdfSizes) {
        const p: 1 | 2 | 3 = size === "100kb" || size === "200kb" || size === "500kb" ? 1 : 2;
        pdfCompress(`compress pdf to ${size}`, p);
        pdfCompress(`reduce pdf size to ${size}`, p);
        pdfCompress(`pdf size reduce to ${size}`, 3);
    }

    // PDF work the site genuinely does on its own, and work it only describes.
    const toImage = gen("pdf-convert", "tool", "/pdf", "prepares", "the in-browser converter on /pdf");
    const described = gen("pdf-work", "tool", "/pdf", "explains", "described on /pdf; runs inside a kit, not on its own");
    const modifiers = ["", " online", " free", " for exam form"];
    for (const m of modifiers) {
        for (const k of ["pdf to jpg", "pdf to image", "pdf to png", "convert pdf page to image"]) toImage(`${k}${m}`, m ? 2 : 1);
        for (const k of ["jpg to pdf", "image to pdf", "photo to pdf", "merge pdf", "combine pdf files", "rearrange pdf pages", "rotate pdf", "delete pages from pdf", "certificate to pdf"]) {
            described(`${k}${m}`, m === " for exam form" || !m ? 2 : 3);
        }
    }
    for (const k of ["jpg to pdf under 100kb", "jpg to pdf under 200kb", "multiple images to one pdf", "scan certificate to pdf for online form", "marksheet pdf size reduce"]) described(k, 2);

    // Background, crop and passport-photo searches that name no examination.
    const background = gen("background-and-crop", "tool", "/background-remover", "gap", "background replacement runs inside a kit; a standalone tool is needed");
    for (const k of [
        "remove background from photo", "photo background remove", "change photo background to white", "white background photo",
        "photo background white online", "passport photo background white", "photo background change online", "blue background photo to white",
    ]) background(k, 2);
    const crop = gen("background-and-crop", "tool", "/crop-photo", "gap", "cropping runs inside a kit; a standalone tool is needed");
    for (const k of [
        "crop photo online", "crop image for form", "passport size photo maker", "passport size photo maker online",
        "3.5 x 4.5 cm photo", "crop photo 3.5 x 4.5 cm", "35x45 mm photo", "photo with name and date", "photo with name and date for exam",
    ]) crop(k, 2);

    // Hinglish and Hindi, typed the way they are typed.
    const hinglish = gen("generic-hinglish", "question", "/", "explains", "English pages today; no Hindi page yet");
    for (const k of [
        "photo ka size kaise kam kare", "photo kb kaise kam kare", "photo ko 20kb me kaise kare", "photo ko 50kb me kaise kare",
        "signature resize kaise kare", "signature ka size kaise kam kare", "pdf ka size kaise kam kare",
        "exam form ke liye photo resize", "online form me photo kaise upload kare", "photo background white kaise kare",
    ]) hinglish(k, 3, "hi-Latn");
    const hindi = gen("generic-hindi", "question", "/hi", "gap", "no Hindi page yet");
    for (const k of [
        "फोटो का साइज कैसे कम करें", "फोटो को 20 kb में कैसे करें", "फोटो को 50 kb में कैसे करें", "फोटो को 100 kb में कैसे करें",
        "सिग्नेचर का साइज कैसे कम करें", "पीडीएफ का साइज कैसे कम करें", "ऑनलाइन फॉर्म के लिए फोटो", "सरकारी परीक्षा फोटो साइज",
        "फोटो रिसाइज ऑनलाइन", "फोटो बैकग्राउंड सफेद कैसे करें",
    ]) hindi(k, 3, "hi");

    const brand = gen("brand", "navigational", "/", "prepares", "the site itself");
    for (const k of ["examuploadkit", "exam upload kit", "examuploadkit.com", "exam upload kit photo resize"]) brand(k, 1);
}

function familyRows(rows: Rows, records: RawRecord[]): void {
    const members = new Map<string, string[]>();
    for (const record of records) {
        const family = familySlugOf(record);
        const id = record.exam?.exam_id;
        if (family && id) members.set(family, [...(members.get(family) ?? []), id]);
    }
    for (const [family, ids] of members) {
        const target = `/exams/${family}`;
        const words = FAMILY_TARGETS.find((entry) => entry.slug === family)?.words ?? [];
        for (const f of words) {
            // The hub lists the sizes; the resizing itself happens on each exam page.
            const common = { cluster: "exam-family", intent: "informational" as const, language: "en" as const, target_url: target, coverage: "explains" as const, exam_ids: ids.join("|"), basis: `hub page for ${ids.length} examinations` };
            rows.add({ ...common, keyword: `${f} photo size`, priority: 2 });
            rows.add({ ...common, keyword: `${f} signature size`, priority: 2 });
            rows.add({ ...common, keyword: `${f} photo size in kb`, priority: 3 });
            rows.add({ ...common, keyword: `${f} photo and signature size`, priority: 2 });
            rows.add({ ...common, keyword: `photo size for ${f}`, priority: 3 });
            rows.add({ ...common, intent: "tool", keyword: `${f} photo resize`, priority: 2 });
            rows.add({ ...common, keyword: `${f} form photo size`, priority: 3 });
        }
    }
}

export function buildKeywords(records: RawRecord[], unavailable: UnavailableExam[] = []): KeywordRow[] {
    const real = records.filter((record) => !record.fictional_example && record.exam?.exam_id);
    const rows = new Rows();
    for (const record of real) examRows(rows, record);
    specValueRows(rows, real);
    familyRows(rows, real);
    genericRows(rows);
    for (const item of unavailable) {
        const name = item.exam_name ? normalise(item.exam_name) : "";
        if (!name) continue;
        const common = { cluster: "exam-not-yet-covered", intent: "informational" as const, language: "en" as const, target_url: "/exam-request", coverage: "gap" as const, exam_ids: "", basis: "researched but not yet encoded" };
        rows.add({ ...common, keyword: `${name} photo size`, priority: 3 });
        rows.add({ ...common, keyword: `${name} signature size`, priority: 3 });
        rows.add({ ...common, intent: "tool", keyword: `${name} photo resize`, priority: 3 });
    }
    return rows.list();
}

// ---- output ------------------------------------------------------------------

const COLUMNS: (keyof KeywordRow)[] = ["keyword", "cluster", "intent", "language", "priority", "target_url", "coverage", "exam_ids", "basis"];

export function toCsv(rows: KeywordRow[]): string {
    const cell = (value: unknown) => {
        const text = String(value);
        return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
    };
    return `${COLUMNS.join(",")}\n${rows.map((row) => COLUMNS.map((c) => cell(row[c])).join(",")).join("\n")}\n`;
}

export function summarise(rows: KeywordRow[]): string {
    const count = <K extends keyof KeywordRow>(key: K) => {
        const map = new Map<string, number>();
        for (const row of rows) map.set(String(row[key]), (map.get(String(row[key])) ?? 0) + 1);
        return [...map].sort((a, b) => b[1] - a[1]);
    };
    const table = (title: string, entries: [string, number][]) =>
        [`| ${title} | Keywords |`, "|---|---:|", ...entries.map(([k, v]) => `| ${k} | ${v.toLocaleString("en-IN")} |`)].join("\n");

    const gaps = new Map<string, { rows: number; p1: number; example: string }>();
    for (const row of rows.filter((r) => r.coverage === "gap")) {
        const entry = gaps.get(row.target_url) ?? { rows: 0, p1: 0, example: row.keyword };
        entry.rows += 1;
        if (row.priority === 1) entry.p1 += 1;
        gaps.set(row.target_url, entry);
    }
    // Hubs and tools that would answer many searches first.
    const gapGroups = new Map<string, { rows: number; p1: number; example: string; pages: number }>();
    for (const [url, entry] of gaps) {
        const group = url.startsWith("/resize/") ? "/resize/… (one page per published figure)" : url.startsWith("/exams/") ? "/exams/… (one hub per family)" : url;
        const g = gapGroups.get(group) ?? { rows: 0, p1: 0, example: entry.example, pages: 0 };
        g.rows += entry.rows;
        g.p1 += entry.p1;
        g.pages += 1;
        gapGroups.set(group, g);
    }

    const samples = [...new Set(rows.map((r) => r.cluster))].map((cluster) => {
        const picks = rows.filter((r) => r.cluster === cluster).slice(0, 6).map((r) => `\`${r.keyword}\``);
        return `- **${cluster}**: ${picks.join(", ")}`;
    });

    return [
        "# Keyword map — generated",
        "",
        "Written by `apps/web/scripts/build-keywords.mjs` from the examination records. Do not edit by hand; re-run `npm run seo:keywords` after the catalogue changes. The strategy that explains it is `KEYWORD_STRATEGY.md`; every row is in `keywords.csv`.",
        "",
        `**${rows.length.toLocaleString("en-IN")} keywords.** Priority is a rule of thumb, not measured volume.`,
        "",
        table("Coverage", count("coverage")),
        "",
        table("Priority", count("priority").map(([k, v]) => [`P${k}`, v] as [string, number])),
        "",
        table("Cluster", count("cluster")),
        "",
        table("Language", count("language")),
        "",
        "## Pages to build, by the searches waiting for them",
        "",
        "| Page | Pages | Keywords | P1 | For example |",
        "|---|---:|---:|---:|---|",
        ...[...gapGroups]
            .sort((a, b) => b[1].p1 - a[1].p1 || b[1].rows - a[1].rows)
            .map(([url, g]) => `| \`${url}\` | ${g.pages} | ${g.rows.toLocaleString("en-IN")} | ${g.p1} | \`${g.example}\` |`),
        "",
        "## What each cluster looks like",
        "",
        ...samples,
        "",
    ].join("\n");
}
