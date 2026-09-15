import { describe, expect, test } from "vitest";

import {
    MAX_EDGE,
    MAX_QUALITY,
    MIN_QUALITY,
    ceilingBytes,
    compressToSize,
    compressedFilename,
    type Encoder,
} from "../lib/compress-to-size";

/** A stand-in JPEG: size grows with pixels and with quality, like the real thing. */
function fakeEncoder(bytesPerPixelAtFull = 0.5) {
    const calls: { width: number; height: number; quality: number }[] = [];
    const encode: Encoder = async (width, height, quality) => {
        calls.push({ width, height, quality });
        const size = Math.round(width * height * bytesPerPixelAtFull * quality ** 2);
        return new Blob([new Uint8Array(size)], { type: "image/jpeg" });
    };
    return { encode, calls };
}

describe("compressing to a size (DEC-096)", () => {
    test("lands under the limit, never on it or over it", async () => {
        const { encode } = fakeEncoder();
        const outcome = await compressToSize(1200, 1600, 50, encode);
        expect(outcome.ok).toBe(true);
        if (!outcome.ok) return;
        expect(outcome.result.blob.size).toBeLessThanOrEqual(ceilingBytes(50));
        expect(ceilingBytes(50)).toBeLessThan(50 * 1000);
    });

    test("keeps full resolution when a lower quality fits", async () => {
        const { encode } = fakeEncoder(0.1);
        // 413 x 531 at quality 0.95 is ~19.9 KB here, so 15 KB needs quality, not pixels.
        const outcome = await compressToSize(413, 531, 15, encode);
        expect(outcome.ok).toBe(true);
        if (!outcome.ok) return;
        expect(outcome.result.width).toBe(413);
        expect(outcome.result.quality).toBeGreaterThanOrEqual(MIN_QUALITY);
        expect(outcome.result.quality).toBeLessThan(MAX_QUALITY);
    });

    test("a photograph already small enough is not squeezed", async () => {
        const { encode, calls } = fakeEncoder(0.01);
        const outcome = await compressToSize(400, 500, 200, encode);
        expect(outcome.ok && outcome.result.quality).toBe(MAX_QUALITY);
        expect(calls).toHaveLength(1);
    });

    test("shrinks the photograph only when the lowest quality still does not fit", async () => {
        const { encode } = fakeEncoder();
        const outcome = await compressToSize(3000, 4000, 20, encode);
        expect(outcome.ok).toBe(true);
        if (!outcome.ok) return;
        expect(outcome.result.width).toBeLessThan(3000);
        expect(outcome.result.height / outcome.result.width).toBeCloseTo(4000 / 3000, 1);
        expect(outcome.result.blob.size).toBeLessThanOrEqual(ceilingBytes(20));
    });

    test("never works on more than the largest edge a form needs", async () => {
        const { encode, calls } = fakeEncoder(0.0001);
        await compressToSize(6000, 8000, 500, encode);
        expect(Math.max(calls[0].width, calls[0].height)).toBeLessThanOrEqual(MAX_EDGE);
    });

    test("says so when no usable photograph fits", async () => {
        const encode: Encoder = async () => new Blob([new Uint8Array(5000)]);
        const outcome = await compressToSize(1000, 1000, 1, encode);
        expect(outcome).toEqual({ ok: false, reason: "too-small", smallestBytes: 5000 });
    });

    test("names the file for what it is, without the original's spaces", () => {
        expect(compressedFilename("passport photo.HEIC", 20)).toBe("passport-photo_20kb.jpg");
        expect(compressedFilename(".jpg", 50)).toBe("photo_50kb.jpg");
    });
});
