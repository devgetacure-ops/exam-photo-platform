import { describe, expect, test, vi } from "vitest";

import type { Encoder } from "../lib/compress-to-size";

import {
    MAX_SOURCE_BYTES,
    UPLOAD_LIMIT_BYTES,
    prepareUpload,
    shrinkTo,
    type Decoder,
} from "../lib/upload-image";

/**
 * DEC-103. A phone photograph over 5 MB, or in WebP, must still reach the
 * engine: it is made into a JPEG the engine takes, in the browser.
 */

const MB = 1024 * 1024;

function fileOf(bytes: number, type: string, name = "IMG_2041.jpg"): File {
    const file = new File([new Uint8Array(1)], name, { type });
    Object.defineProperty(file, "size", { value: bytes });
    return file;
}

function decoder(width: number, height: number, sizes: number[]) {
    const encode = vi.fn<Encoder>(
        async () => new Blob([new Uint8Array(sizes.shift() ?? 1)]),
    );
    const close = vi.fn();
    const decode: Decoder = vi.fn(async () => ({ width, height, encode, close }));
    return { decode, encode, close };
}

describe("a photograph on its way to the engine", () => {
    test("the longest side is kept to 3200 px and the shape is kept", () => {
        expect(shrinkTo(8160, 6120)).toEqual({ width: 3200, height: 2400 });
        expect(shrinkTo(2448, 3264)).toEqual({ width: 2400, height: 3200 });
        expect(shrinkTo(1200, 1600)).toEqual({ width: 1200, height: 1600 });
    });

    test("a small JPEG goes up untouched, without being decoded", async () => {
        const { decode } = decoder(3000, 4000, []);
        const file = fileOf(2 * MB, "image/jpeg");
        const outcome = await prepareUpload(file, decode);
        expect(outcome).toEqual({ ok: true, file, shrunk: false });
        expect(decode).not.toHaveBeenCalled();
    });

    test("a selfie over 5 MB is made smaller and uploaded as a JPEG", async () => {
        const { decode, encode, close } = decoder(6120, 8160, [2 * MB]);
        const outcome = await prepareUpload(fileOf(7.4 * MB, "image/jpeg"), decode);
        expect(outcome.ok).toBe(true);
        if (!outcome.ok) return;
        expect(outcome.shrunk).toBe(true);
        expect(outcome.file.type).toBe("image/jpeg");
        expect(outcome.file.name).toBe("IMG_2041.jpg");
        expect(encode).toHaveBeenCalledWith(2400, 3200, 0.92);
        expect(close).toHaveBeenCalled();
    });

    test("quality steps down only until it fits", async () => {
        const { decode, encode } = decoder(3000, 4000, [6 * MB, 4.5 * MB]);
        const outcome = await prepareUpload(fileOf(9 * MB, "image/png", "scan.png"), decode);
        expect(outcome.ok && outcome.file.name).toBe("scan.jpg");
        expect(encode.mock.calls.map((call) => call[2])).toEqual([0.92, 0.85]);
    });

    test("WebP is always converted, because the engine reads only JPEG and PNG", async () => {
        const { decode } = decoder(1080, 1440, [300_000]);
        const outcome = await prepareUpload(fileOf(400_000, "image/webp", "a.webp"), decode);
        expect(outcome.ok && outcome.file.type).toBe("image/jpeg");
        expect(decode).toHaveBeenCalled();
    });

    test("a PDF is never touched", async () => {
        const { decode } = decoder(1, 1, []);
        const pdf = fileOf(8 * MB, "application/pdf", "marks.pdf");
        expect(await prepareUpload(pdf, decode)).toEqual({ ok: true, file: pdf, shrunk: false });
        expect(decode).not.toHaveBeenCalled();
    });

    test("it refuses rather than hanging a phone, and says why", async () => {
        const { decode } = decoder(1, 1, []);
        expect(await prepareUpload(fileOf(MAX_SOURCE_BYTES + 1, "image/jpeg"), decode)).toEqual({
            ok: false,
            reason: "too_large",
        });
        const broken: Decoder = vi.fn(async () => {
            throw new Error("out of memory");
        });
        expect(await prepareUpload(fileOf(12 * MB, "image/jpeg"), broken)).toEqual({
            ok: false,
            reason: "unreadable",
        });
        const { decode: never } = decoder(4000, 3000, [UPLOAD_LIMIT_BYTES + 1, UPLOAD_LIMIT_BYTES + 1, UPLOAD_LIMIT_BYTES + 1]);
        expect(await prepareUpload(fileOf(20 * MB, "image/jpeg"), never)).toEqual({
            ok: false,
            reason: "too_large",
        });
    });
});
