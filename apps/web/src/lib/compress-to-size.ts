/**
 * Compress a photograph under a byte size, in the candidate's own browser
 * (DEC-096; the owner chose free and in-browser).
 *
 * The search keeps as much of the photograph as the size allows: full
 * resolution at the best JPEG quality that fits, and only when even the
 * lowest acceptable quality does not fit, a smaller photograph. It lands just
 * under the limit, never on it or over it -- the owner's rule for every file
 * the product makes.
 *
 * The search is written against an `Encoder` so it can be tested without a
 * canvas; `canvasEncoder` is the real one.
 */

/** 1 KB = 1000 bytes: the smaller reading, so a file under it passes either way. */
export const BYTES_PER_KB = 1000;
/** Aim this far under the limit, as the engine does. est. */
export const CEILING_RATIO = 0.96;
/** Below this quality a JPEG shows blocks on a face; shrink instead. est. */
export const MIN_QUALITY = 0.5;
export const MAX_QUALITY = 0.95;
const QUALITY_STEPS = 7;
/** No portal needs more, and a phone decoding a 50 MP photo runs out of memory. */
export const MAX_EDGE = 2400;
/** Below this the photograph is no longer usable for anything. */
export const MIN_EDGE = 120;
export const MAX_SOURCE_BYTES = 25 * 1024 * 1024;
export const PRESET_KB = [10, 20, 50, 100, 200] as const;

export type Encoder = (width: number, height: number, quality: number) => Promise<Blob>;

export interface Compressed {
    blob: Blob;
    width: number;
    height: number;
    quality: number;
}

export type CompressOutcome =
    | { ok: true; result: Compressed }
    | { ok: false; reason: "too-small"; smallestBytes: number };

export function ceilingBytes(targetKb: number): number {
    return Math.floor(targetKb * BYTES_PER_KB * CEILING_RATIO);
}

export async function compressToSize(
    sourceWidth: number,
    sourceHeight: number,
    targetKb: number,
    encode: Encoder,
): Promise<CompressOutcome> {
    const ceiling = ceilingBytes(targetKb);
    const longest = Math.max(sourceWidth, sourceHeight);
    let scale = Math.min(1, MAX_EDGE / longest);
    let smallestBytes = Number.POSITIVE_INFINITY;

    for (;;) {
        const width = Math.max(1, Math.round(sourceWidth * scale));
        const height = Math.max(1, Math.round(sourceHeight * scale));
        if (Math.max(width, height) < MIN_EDGE) {
            return { ok: false, reason: "too-small", smallestBytes };
        }

        const best = await encode(width, height, MAX_QUALITY);
        if (best.size <= ceiling) {
            return { ok: true, result: { blob: best, width, height, quality: MAX_QUALITY } };
        }

        const worst = await encode(width, height, MIN_QUALITY);
        smallestBytes = Math.min(smallestBytes, worst.size);
        if (worst.size <= ceiling) {
            let low = MIN_QUALITY;
            let high = MAX_QUALITY;
            let found: Compressed = { blob: worst, width, height, quality: MIN_QUALITY };
            for (let step = 0; step < QUALITY_STEPS; step++) {
                const quality = (low + high) / 2;
                const blob = await encode(width, height, quality);
                if (blob.size <= ceiling) {
                    found = { blob, width, height, quality };
                    low = quality;
                } else {
                    high = quality;
                }
            }
            return { ok: true, result: found };
        }

        // A JPEG's size follows its pixel count, so jump most of the way there
        // in one step rather than creeping down 15% at a time.
        const jump = Math.sqrt(ceiling / worst.size) * 0.95;
        scale *= Math.min(0.85, Math.max(0.5, jump));
    }
}

/** "passport photo.HEIC" at 20 KB -> "passport-photo_20kb.jpg". */
export function compressedFilename(sourceName: string, targetKb: number): string {
    const stem = sourceName.replace(/\.[^.]+$/, "").trim();
    const safe = stem
        .normalize("NFKD")
        .replace(/[^\w-]+/g, "-")
        .replace(/-+/g, "-")
        .replace(/^-|-$/g, "")
        .toLowerCase();
    return `${safe || "photo"}_${targetKb}kb.jpg`;
}

/**
 * The real encoder: the decoded photograph drawn onto a white canvas (so a
 * transparent PNG does not turn black) and saved as a JPEG. A canvas carries
 * no EXIF, so location and camera data never survive into the result.
 */
export async function canvasEncoder(file: Blob): Promise<{
    width: number;
    height: number;
    encode: Encoder;
    close: () => void;
}> {
    const bitmap = await createImageBitmap(file);
    const canvas = document.createElement("canvas");
    const encode: Encoder = async (width, height, quality) => {
        canvas.width = width;
        canvas.height = height;
        const context = canvas.getContext("2d");
        if (!context) throw new Error("No canvas context");
        context.fillStyle = "#ffffff";
        context.fillRect(0, 0, width, height);
        context.imageSmoothingEnabled = true;
        context.imageSmoothingQuality = "high";
        context.drawImage(bitmap, 0, 0, width, height);
        const blob = await new Promise<Blob | null>((resolve) =>
            canvas.toBlob(resolve, "image/jpeg", quality),
        );
        if (!blob) throw new Error("Could not encode the photo");
        return blob;
    };
    return {
        width: bitmap.width,
        height: bitmap.height,
        encode,
        close: () => {
            bitmap.close();
            canvas.width = 0;
            canvas.height = 0;
        },
    };
}
