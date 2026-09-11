import "server-only";
import { readFileSync, statSync } from "node:fs";
import path from "node:path";

/**
 * Reads the real dimensions, byte size and format of a file in `public/`.
 *
 * The hero claims specific numbers about the two photographs it shows. Those
 * numbers are measured here at build time rather than typed into the markup,
 * so swapping either file updates what the page says about it and there is no
 * way for the copy to drift away from the asset it describes.
 *
 * Header parsing rather than a decoding dependency: we need four facts about
 * our own two files, not a general-purpose image library.
 */
export interface ImageFacts {
    name: string;
    src: string;
    width: number;
    height: number;
    bytes: number;
    format: string;
}

function pngSize(buf: Buffer): { width: number; height: number } | null {
    // 8-byte signature, then an IHDR chunk whose width and height are the
    // first two big-endian 32-bit values of its data.
    if (buf.length < 24) return null;
    if (buf.readUInt32BE(0) !== 0x89504e47) return null;
    return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
}

function jpegSize(buf: Buffer): { width: number; height: number } | null {
    if (buf.length < 4 || buf.readUInt16BE(0) !== 0xffd8) return null;
    let offset = 2;
    while (offset + 9 < buf.length) {
        if (buf[offset] !== 0xff) {
            offset += 1;
            continue;
        }
        const marker = buf[offset + 1];
        // SOF0..SOF15, excluding the four that are not frame headers.
        const isFrameHeader =
            marker >= 0xc0 &&
            marker <= 0xcf &&
            marker !== 0xc4 &&
            marker !== 0xc8 &&
            marker !== 0xcc;
        if (isFrameHeader) {
            return {
                height: buf.readUInt16BE(offset + 5),
                width: buf.readUInt16BE(offset + 7),
            };
        }
        offset += 2 + buf.readUInt16BE(offset + 2);
    }
    return null;
}

export function readImageFacts(publicPath: string): ImageFacts | null {
    const rel = publicPath.replace(/^\//, "");
    const abs = path.join(process.cwd(), "public", rel);
    let buf: Buffer;
    try {
        buf = readFileSync(abs);
    } catch {
        return null;
    }
    const size = pngSize(buf) ?? jpegSize(buf);
    if (!size) return null;
    const ext = path.extname(abs).replace(".", "").toUpperCase();
    return {
        name: path.basename(abs),
        src: publicPath,
        width: size.width,
        height: size.height,
        bytes: statSync(abs).size,
        format: ext === "JPEG" ? "JPG" : ext,
    };
}

export function formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    const kb = bytes / 1024;
    return kb < 1000 ? `${kb.toFixed(kb < 10 ? 1 : 0)} KB` : `${(kb / 1024).toFixed(1)} MB`;
}
