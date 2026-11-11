import { describe, expect, it } from "vitest";
import { languageAlternates, localePath, localValue } from "../lib/i18n";

/** Hindi alongside English (DEC-129). */

describe("Hindi addresses", () => {
    it("live under /hi and leave English where it is", () => {
        expect(localePath("hi", "/exam/ctet")).toBe("/hi/exam/ctet");
        expect(localePath("hi", "/")).toBe("/hi");
        expect(localePath("en", "/exam/ctet")).toBe("/exam/ctet");
    });

    it("name both languages and English as the default", () => {
        expect(languageAlternates("/exam/ctet")).toEqual({
            "en-IN": "/exam/ctet",
            "hi-IN": "/hi/exam/ctet",
            "x-default": "/exam/ctet",
        });
    });
});

describe("figures in Hindi", () => {
    it("keep units and numbers exactly, translating only the words around them", () => {
        expect(localValue("hi", "350 × 450 px preferred")).toBe("350 × 450 px (सुझाया गया)");
        expect(localValue("hi", "#ffffff")).toBe("सफ़ेद");
        expect(localValue("hi", "10–100 KB")).toBe("10–100 KB");
        expect(localValue("en", "#fff")).toBe("white");
    });
});
