import { describe, expect, test } from "vitest";
import { isPdfFile, pdfPageFilename, scaleForDpi } from "../lib/pdf-image";

describe("PDF to image arithmetic", () => {
    test("resolution is dots per inch over PDF's 72 points per inch", () => {
        expect(scaleForDpi(72)).toBe(1);
        expect(scaleForDpi(150)).toBeCloseTo(2.0833, 3);
        // An A4 page is 595 points wide: 1240 px at 150 dpi.
        expect(Math.floor(595 * scaleForDpi(150))).toBe(1239);
    });

    test("a PDF is recognised by type or by name", () => {
        expect(isPdfFile({ name: "marks.pdf", type: "" })).toBe(true);
        expect(isPdfFile({ name: "scan", type: "application/pdf" })).toBe(true);
        expect(isPdfFile({ name: "photo.jpg", type: "image/jpeg" })).toBe(false);
    });

    test("filenames keep the source name, the page, and only safe characters", () => {
        expect(pdfPageFilename("Class 10 Marksheet (2019).pdf", 2, "jpeg")).toBe(
            "Class_10_Marksheet_2019_page2.jpg",
        );
        expect(pdfPageFilename("दस्तावेज़.pdf", 1, "png")).toBe("document_page1.png");
    });
});
