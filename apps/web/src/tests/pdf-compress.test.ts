import { describe, expect, test } from "vitest";

import { ceilingBytes } from "../lib/compress-to-size";
import {
    PDF_DPIS,
    PDF_QUALITIES,
    buildJpegPdf,
    compressPdf,
    compressedPdfFilename,
    type DrawnPage,
} from "../lib/pdf-compress";

/** Compressing a PDF to a size (DEC-098). */

const ascii = (bytes: Uint8Array) => new TextDecoder("latin1").decode(bytes);

function fakeJpeg(size: number): Uint8Array {
    const bytes = new Uint8Array(size);
    bytes[0] = 0xff;
    bytes[1] = 0xd8;
    return bytes;
}

describe("the PDF it writes", () => {
    const pdf = buildJpegPdf([
        { jpeg: fakeJpeg(1200), pixelWidth: 1240, pixelHeight: 1754, pointWidth: 595.28, pointHeight: 841.89 },
        { jpeg: fakeJpeg(900), pixelWidth: 1754, pixelHeight: 1240, pointWidth: 841.89, pointHeight: 595.28 },
    ]);
    const body = ascii(pdf);

    test("is a PDF with one page per image, each its source's size", () => {
        expect(body.startsWith("%PDF-1.4")).toBe(true);
        expect(body.trimEnd().endsWith("%%EOF")).toBe(true);
        expect(body).toContain("/Type /Pages /Count 2");
        expect(body).toContain("/MediaBox [0 0 595.28 841.89]");
        expect(body).toContain("/MediaBox [0 0 841.89 595.28]");
        expect(body).toContain("/Filter /DCTDecode /Length 1200");
    });

    test("every cross-reference points at the object it names", () => {
        const startxref = Number(body.match(/startxref\n(\d+)/)![1]);
        expect(body.slice(startxref, startxref + 4)).toBe("xref");
        const entries = body.slice(startxref).match(/^(\d{10}) 00000 n $/gm)!;
        expect(entries).toHaveLength(8);
        entries.forEach((entry, index) => {
            const offset = Number(entry.slice(0, 10));
            expect(body.slice(offset, offset + `${index + 1} 0 obj`.length)).toBe(`${index + 1} 0 obj`);
        });
    });
});

describe("the size search", () => {
    function drawer(bytesPerPixelAtFull: number) {
        const calls: number[] = [];
        const draw = async (_index: number, dpi: number): Promise<DrawnPage> => {
            calls.push(dpi);
            const width = Math.round(8.27 * dpi);
            const height = Math.round(11.69 * dpi);
            return {
                pointWidth: 595.28,
                pointHeight: 841.89,
                encode: async (quality) => ({
                    jpeg: fakeJpeg(Math.round(width * height * bytesPerPixelAtFull * quality)),
                    width,
                    height,
                }),
                release: () => {},
            };
        };
        return { draw, calls };
    }

    test("keeps the highest resolution and the best quality that fit, under the limit", async () => {
        const { draw } = drawer(0.08);
        const outcome = await compressPdf(2, draw, 300, undefined);
        expect(outcome.ok).toBe(true);
        if (!outcome.ok) return;
        expect(outcome.pdf.length).toBeLessThanOrEqual(ceilingBytes(300));
        expect(outcome.dpi).toBe(PDF_DPIS[0]);
        expect(outcome.quality).toBeLessThan(PDF_QUALITIES[0]);
    });

    test("lowers the resolution only when no quality fits", async () => {
        const { draw, calls } = drawer(0.5);
        const outcome = await compressPdf(1, draw, 100);
        expect(outcome.ok).toBe(true);
        if (!outcome.ok) return;
        expect(outcome.dpi).toBeLessThan(PDF_DPIS[0]);
        expect(calls[0]).toBe(PDF_DPIS[0]);
    });

    test("says so when nothing fits", async () => {
        // Even 72 DPI at the lowest quality is ~88 KB a page here.
        const { draw } = drawer(0.5);
        const outcome = await compressPdf(3, draw, 10);
        expect(outcome.ok).toBe(false);
    });

    test("names the file for what it is", () => {
        expect(compressedPdfFilename("Class 10 marksheet.pdf", 300)).toBe("class-10-marksheet_300kb.pdf");
    });
});
