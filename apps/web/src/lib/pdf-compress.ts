/**
 * Compress a PDF under a byte size, in the candidate's own browser (DEC-098).
 *
 * Each page is drawn by pdf.js and saved as a JPEG, and the JPEGs are written
 * into a new PDF of the same page sizes. That is what a scanned certificate
 * already is, so for the common case nothing is lost but bytes; a PDF with
 * real text becomes a picture of that text, which the page says.
 *
 * The search keeps the sharpest result that fits: the highest resolution
 * first, the best quality at it, and a lower resolution only when even the
 * lowest quality does not fit. Every quality at a resolution is encoded from
 * one drawing of each page, so trying six qualities costs six encodes, not six
 * renders.
 */

import { ceilingBytes } from "./compress-to-size";

export const PDF_DPIS = [150, 120, 100, 85, 72] as const;
export const PDF_QUALITIES = [0.85, 0.75, 0.65, 0.55, 0.45, 0.35] as const;
export const PDF_PRESET_KB = [100, 200, 300, 500] as const;

export interface JpegPage {
    jpeg: Uint8Array;
    pixelWidth: number;
    pixelHeight: number;
    /** The source page's size in PDF points, so the new page is the same size. */
    pointWidth: number;
    pointHeight: number;
}

const text = new TextEncoder();

function points(value: number): string {
    return Number(value.toFixed(2)).toString();
}

/** A minimal, valid PDF whose every page is one full-page JPEG. */
export function buildJpegPdf(pages: JpegPage[]): Uint8Array {
    const chunks: Uint8Array[] = [];
    const offsets: number[] = [];
    let length = 0;
    const push = (part: string | Uint8Array) => {
        const bytes = typeof part === "string" ? text.encode(part) : part;
        chunks.push(bytes);
        length += bytes.length;
    };
    const object = (id: number, parts: (string | Uint8Array)[]) => {
        offsets[id] = length;
        push(`${id} 0 obj\n`);
        parts.forEach(push);
        push("\nendobj\n");
    };

    push("%PDF-1.4\n%âãÏÓ\n");
    const pageIds = pages.map((_, index) => 3 + index * 3);
    object(1, ["<< /Type /Catalog /Pages 2 0 R >>"]);
    object(2, [
        `<< /Type /Pages /Count ${pages.length} /Kids [${pageIds.map((id) => `${id} 0 R`).join(" ")}] >>`,
    ]);
    pages.forEach((page, index) => {
        const pageId = 3 + index * 3;
        const contentId = pageId + 1;
        const imageId = pageId + 2;
        const w = points(page.pointWidth);
        const h = points(page.pointHeight);
        const content = `q ${w} 0 0 ${h} 0 0 cm /Im0 Do Q`;
        object(pageId, [
            `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${w} ${h}] /Resources << /XObject << /Im0 ${imageId} 0 R >> >> /Contents ${contentId} 0 R >>`,
        ]);
        object(contentId, [`<< /Length ${text.encode(content).length} >>\nstream\n${content}\nendstream`]);
        object(imageId, [
            `<< /Type /XObject /Subtype /Image /Width ${page.pixelWidth} /Height ${page.pixelHeight} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${page.jpeg.length} >>\nstream\n`,
            page.jpeg,
            "\nendstream",
        ]);
    });

    const count = 3 + pages.length * 3;
    const xref = length;
    push(`xref\n0 ${count}\n0000000000 65535 f \n`);
    for (let id = 1; id < count; id++) push(`${String(offsets[id]).padStart(10, "0")} 00000 n \n`);
    push(`trailer\n<< /Size ${count} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`);

    const out = new Uint8Array(length);
    let at = 0;
    for (const chunk of chunks) {
        out.set(chunk, at);
        at += chunk.length;
    }
    return out;
}

/** One page drawn at one resolution, ready to be encoded at any quality. */
export interface DrawnPage {
    pointWidth: number;
    pointHeight: number;
    encode: (quality: number) => Promise<{ jpeg: Uint8Array; width: number; height: number }>;
    release: () => void;
}

export type PdfOutcome =
    | { ok: true; pdf: Uint8Array; dpi: number; quality: number }
    | { ok: false; reason: "too-small"; smallestBytes: number };

export async function compressPdf(
    pageCount: number,
    draw: (pageIndex: number, dpi: number) => Promise<DrawnPage>,
    targetKb: number,
    onProgress?: (step: { dpi: number; page: number; pages: number }) => void,
): Promise<PdfOutcome> {
    const ceiling = ceilingBytes(targetKb);
    let smallestBytes = Number.POSITIVE_INFINITY;

    for (const dpi of PDF_DPIS) {
        const byQuality: JpegPage[][] = PDF_QUALITIES.map(() => []);
        for (let index = 0; index < pageCount; index++) {
            onProgress?.({ dpi, page: index + 1, pages: pageCount });
            const page = await draw(index, dpi);
            try {
                for (let q = 0; q < PDF_QUALITIES.length; q++) {
                    const { jpeg, width, height } = await page.encode(PDF_QUALITIES[q]);
                    byQuality[q].push({
                        jpeg,
                        pixelWidth: width,
                        pixelHeight: height,
                        pointWidth: page.pointWidth,
                        pointHeight: page.pointHeight,
                    });
                }
            } finally {
                page.release();
            }
        }
        for (let q = 0; q < PDF_QUALITIES.length; q++) {
            const pdf = buildJpegPdf(byQuality[q]);
            smallestBytes = Math.min(smallestBytes, pdf.length);
            if (pdf.length <= ceiling) return { ok: true, pdf, dpi, quality: PDF_QUALITIES[q] };
        }
    }
    return { ok: false, reason: "too-small", smallestBytes };
}

/** "Class 10 marksheet.pdf" at 300 KB -> "class-10-marksheet_300kb.pdf". */
export function compressedPdfFilename(sourceName: string, targetKb: number): string {
    const stem = sourceName
        .replace(/\.pdf$/i, "")
        .normalize("NFKD")
        .replace(/[^\w-]+/g, "-")
        .replace(/-+/g, "-")
        .replace(/^-|-$/g, "")
        .toLowerCase();
    return `${stem || "document"}_${targetKb}kb.pdf`;
}
