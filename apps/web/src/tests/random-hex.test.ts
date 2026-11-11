import { afterEach, describe, expect, it, vi } from "vitest";
import { randomHex } from "../lib/random-hex";

/** Uploads must work on a plain-HTTP page, where randomUUID is missing. */

afterEach(() => vi.unstubAllGlobals());

describe("randomHex", () => {
    it("is 32 hex characters", () => {
        expect(randomHex()).toMatch(/^[0-9a-f]{32}$/);
    });

    it("still works where randomUUID does not exist (an http:// LAN page)", () => {
        vi.stubGlobal("crypto", { getRandomValues: (a: Uint8Array) => a.fill(171) });
        expect(randomHex()).toBe("ab".repeat(16));
    });

    it("still works with no Web Crypto at all", () => {
        vi.stubGlobal("crypto", undefined);
        expect(randomHex()).toMatch(/^[0-9a-f]{32}$/);
    });
});
