import { describe, expect, test } from "vitest";

import { MAX_ZOOM, centreOf, frameRect, resizedFilename } from "../lib/crop-frame";
import { MAX_QUALITY, ceilingBytes, compressAtSize, type Encoder } from "../lib/compress-to-size";

/** The crop frame for exact-pixel sizes (DEC-098). */
describe("the crop frame", () => {
    test("is the published shape, as large as the photograph allows", () => {
        const rect = frameRect(3000, 4000, 200 / 230, 1, 1500, 2000);
        expect(rect.w / rect.h).toBeCloseTo(200 / 230, 5);
        expect(rect.w).toBeCloseTo(3000, 5);
        expect(rect.h).toBeLessThanOrEqual(4000);
    });

    test("a wide frame on a tall photograph uses the full width", () => {
        const rect = frameRect(1000, 2000, 140 / 60, 1, 500, 1000);
        expect(rect.w).toBe(1000);
        expect(rect.h).toBeCloseTo(1000 / (140 / 60), 5);
    });

    test("never leaves the photograph, however far it is pushed", () => {
        const rect = frameRect(3000, 4000, 0.75, 2, -500, 99999);
        expect(rect.x).toBe(0);
        expect(rect.y + rect.h).toBeCloseTo(4000, 5);
    });

    test("zoom narrows the frame and is bounded", () => {
        const one = frameRect(3000, 4000, 0.75, 1, 1500, 2000);
        const two = frameRect(3000, 4000, 0.75, 2, 1500, 2000);
        const huge = frameRect(3000, 4000, 0.75, 99, 1500, 2000);
        expect(two.w).toBeCloseTo(one.w / 2, 5);
        expect(huge.w).toBeCloseTo(one.w / MAX_ZOOM, 5);
        expect(centreOf(two)).toEqual({ x: 1500, y: 2000 });
    });

    test("names the file with its size", () => {
        expect(resizedFilename("my photo.JPG", 200, 230)).toBe("my-photo_200x230.jpg");
    });
});

describe("a limit at an exact size", () => {
    const encoder = (bytesPerPixel: number) => {
        const sizes: number[] = [];
        const encode: Encoder = async (width, height, quality) => {
            const size = Math.round(width * height * bytesPerPixel * quality);
            sizes.push(width);
            return new Blob([new Uint8Array(size)]);
        };
        return { encode, sizes };
    };

    test("keeps the size and lowers only the quality", async () => {
        const { encode, sizes } = encoder(1);
        const outcome = await compressAtSize(200, 230, 30, encode);
        expect(outcome.ok).toBe(true);
        if (!outcome.ok) return;
        expect(outcome.result.width).toBe(200);
        expect(new Set(sizes)).toEqual(new Set([200]));
        expect(outcome.result.blob.size).toBeLessThanOrEqual(ceilingBytes(30));
    });

    test("a file already under the limit is left at full quality", async () => {
        const { encode } = encoder(0.01);
        const outcome = await compressAtSize(200, 230, 50, encode);
        expect(outcome.ok && outcome.result.quality).toBe(MAX_QUALITY);
    });

    test("says so when even the lowest quality does not fit", async () => {
        const { encode } = encoder(100);
        const outcome = await compressAtSize(1200, 1200, 10, encode);
        expect(outcome.ok).toBe(false);
    });
});
