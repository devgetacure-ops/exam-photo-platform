/**
 * The arithmetic behind turning PDF pages into images, kept apart from pdf.js
 * so it can be tested without a browser canvas.
 */

export type ImageFormat = "jpeg" | "png";

/** PDF user space is measured in points: 72 to the inch. */
export const PDF_POINTS_PER_INCH = 72;

export const DPI_CHOICES = [100, 150, 200] as const;

/** Large enough for any certificate; small enough that a phone won't run out of memory. */
export const MAX_PDF_BYTES = 20 * 1024 * 1024;
export const MAX_PDF_PAGES = 30;

export function scaleForDpi(dpi: number): number {
    return dpi / PDF_POINTS_PER_INCH;
}

export function isPdfFile(file: { name: string; type: string }): boolean {
    return file.type === "application/pdf" || /\.pdf$/i.test(file.name);
}

/**
 * A filename a portal will accept: the source's own name, reduced to safe
 * characters, with the page number, so page two of a mark sheet doesn't
 * overwrite page one in the candidate's Downloads folder.
 */
export function pdfPageFilename(
    sourceName: string,
    pageNumber: number,
    format: ImageFormat,
): string {
    const base =
        sourceName
            .replace(/\.pdf$/i, "")
            .replace(/[^A-Za-z0-9_-]+/g, "_")
            .replace(/^_+|_+$/g, "")
            .slice(0, 60) || "document";
    return `${base}_page${pageNumber}.${format === "png" ? "png" : "jpg"}`;
}
