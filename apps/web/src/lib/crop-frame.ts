/**
 * The arithmetic of the crop frame (DEC-098), kept apart from the canvas so it
 * can be tested: a frame of the published shape over the photograph, as large
 * as the photograph allows, zoomed and moved by the candidate, never outside
 * the photograph and never stretched.
 */

export const MAX_ZOOM = 4;

export interface Rect {
    x: number;
    y: number;
    w: number;
    h: number;
}

function clamp(value: number, low: number, high: number): number {
    return Math.min(Math.max(value, low), Math.max(low, high));
}

/** The part of the photograph the frame covers, centred as near (cx, cy) as it can be. */
export function frameRect(
    imageWidth: number,
    imageHeight: number,
    aspect: number,
    zoom: number,
    cx: number,
    cy: number,
): Rect {
    let w: number;
    let h: number;
    if (imageWidth / imageHeight > aspect) {
        h = imageHeight;
        w = h * aspect;
    } else {
        w = imageWidth;
        h = w / aspect;
    }
    const z = clamp(zoom, 1, MAX_ZOOM);
    w /= z;
    h /= z;
    return {
        x: clamp(cx - w / 2, 0, imageWidth - w),
        y: clamp(cy - h / 2, 0, imageHeight - h),
        w,
        h,
    };
}

export function centreOf(rect: Rect): { x: number; y: number } {
    return { x: rect.x + rect.w / 2, y: rect.y + rect.h / 2 };
}

/** "my photo.jpg" at 200 x 230 -> "my-photo_200x230.jpg". */
export function resizedFilename(sourceName: string, width: number, height: number): string {
    const stem = sourceName
        .replace(/\.[^.]+$/, "")
        .normalize("NFKD")
        .replace(/[^\w-]+/g, "-")
        .replace(/-+/g, "-")
        .replace(/^-|-$/g, "")
        .toLowerCase();
    return `${stem || "photo"}_${width}x${height}.jpg`;
}
