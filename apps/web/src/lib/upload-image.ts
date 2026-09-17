import { canvasEncoder, type Encoder } from "./compress-to-size";

/**
 * Every photograph leaves the phone at a size the engine takes (DEC-103).
 *
 * A phone camera writes 12 to 108 megapixels and 3 to 15 MB, and a selfie
 * over 5 MB was refused with "Choose a file smaller than 5 MB" on launch day.
 * Raising the server's limit would not have been enough: the engine also
 * refuses more than 16 megapixels, and a 50 MP photograph is three times that,
 * and a candidate on mobile data would wait for every one of those megabytes.
 * So a large photograph is made smaller here, in the browser, before it is
 * uploaded. The longest side is kept at 3200 px, far above anything prepared
 * (the largest photograph any examination asks for is a few hundred pixels
 * tall), so nothing the engine uses is lost.
 *
 * WebP is converted the same way whatever its size, because the site accepts
 * WebP and the engine reads only JPEG and PNG.
 *
 * Drawing onto a canvas also applies the photograph's orientation and drops
 * its EXIF, so no location or camera data is uploaded. A transparent PNG is
 * drawn over white, as the free compress tool does.
 */

/** What the engine accepts per file. */
export const UPLOAD_LIMIT_BYTES = 5 * 1024 * 1024;
/** Above this, a photograph is made smaller before it leaves the phone. */
export const SHRINK_ABOVE_BYTES = 4 * 1024 * 1024;
/** The longest side after shrinking. 3200 x 2400 is 7.7 MP, under the engine's 16. */
export const UPLOAD_MAX_EDGE = 3200;
/** Larger than this is refused outright: a phone decoding it can run out of memory. */
export const MAX_SOURCE_BYTES = 40 * 1024 * 1024;

const QUALITIES = [0.92, 0.85, 0.75] as const;

export type UploadOutcome =
    | { ok: true; file: File; shrunk: boolean }
    | { ok: false; reason: "too_large" | "unreadable" };

export type Decoder = (file: Blob) => Promise<{
    width: number;
    height: number;
    encode: Encoder;
    close: () => void;
}>;

/** The size to draw at: the longest side at most `maxEdge`, the shape kept. */
export function shrinkTo(
    width: number,
    height: number,
    maxEdge = UPLOAD_MAX_EDGE,
): { width: number; height: number } {
    const longest = Math.max(width, height);
    if (longest <= maxEdge) return { width, height };
    const scale = maxEdge / longest;
    return {
        width: Math.max(1, Math.round(width * scale)),
        height: Math.max(1, Math.round(height * scale)),
    };
}

/** Converted whatever their size: the engine reads only JPEG and PNG. HEIC is
 * what an iPhone camera writes; Safari can decode it, and elsewhere the decode
 * fails and the candidate is told plainly. */
const CONVERT = new Set(["image/webp", "image/heic", "image/heif"]);

function needsWork(file: File): boolean {
    if (CONVERT.has(file.type)) return true;
    if (file.type !== "image/jpeg" && file.type !== "image/png") return false;
    return file.size > SHRINK_ABOVE_BYTES;
}

function jpegName(name: string): string {
    const base = name.replace(/\.[^.]+$/, "") || "photo";
    return `${base}.jpg`;
}

/**
 * The file to upload: the original when it already fits, otherwise a JPEG the
 * engine takes. Documents (PDFs) and small JPEG or PNG files pass untouched.
 */
export async function prepareUpload(
    file: File,
    decode: Decoder = canvasEncoder,
): Promise<UploadOutcome> {
    if (!needsWork(file)) {
        return file.size > UPLOAD_LIMIT_BYTES && file.type !== "application/pdf"
            ? { ok: false, reason: "too_large" }
            : { ok: true, file, shrunk: false };
    }
    if (file.size > MAX_SOURCE_BYTES) return { ok: false, reason: "too_large" };

    let decoded: Awaited<ReturnType<Decoder>>;
    try {
        decoded = await decode(file);
    } catch {
        return { ok: false, reason: "unreadable" };
    }
    try {
        const size = shrinkTo(decoded.width, decoded.height);
        for (const quality of QUALITIES) {
            const blob = await decoded.encode(size.width, size.height, quality);
            if (blob.size <= UPLOAD_LIMIT_BYTES) {
                return {
                    ok: true,
                    file: new File([blob], jpegName(file.name), {
                        type: "image/jpeg",
                        lastModified: file.lastModified,
                    }),
                    shrunk: true,
                };
            }
        }
        return { ok: false, reason: "too_large" };
    } catch {
        return { ok: false, reason: "unreadable" };
    } finally {
        decoded.close();
    }
}

export function uploadRefusal(reason: "too_large" | "unreadable"): string {
    return reason === "too_large"
        ? "This photo is too large to use. Take it again with the camera at its normal setting, or choose a smaller photo."
        : "We couldn’t open this photo on your phone. Choose it again, or take a new one.";
}
