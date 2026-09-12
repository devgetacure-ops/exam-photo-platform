import { describe, expect, it } from "vitest";
import { nextStep, type KitFile } from "../lib/kit-next";

const KIT: KitFile[] = [
    { requirementId: "photo", name: "Photograph" },
    { requirementId: "sign", name: "Signature" },
    { requirementId: "thumb", name: "Thumb impression" },
];

const all = ["photo", "sign", "thumb"];

describe("what comes next in the kit", () => {
    it("offers the next file that is both in the kit and still waiting", () => {
        expect(
            nextStep({
                kit: KIT,
                included: all,
                prepared: ["photo"],
                current: "photo",
            }),
        ).toEqual({
            kind: "file",
            requirementId: "sign",
            name: "Signature",
            prepared: 1,
            total: 3,
        });
    });

    it("skips a file the candidate has unticked", () => {
        const step = nextStep({
            kit: KIT,
            included: ["photo", "thumb"],
            prepared: [],
            current: "photo",
        });
        expect(step).toMatchObject({ kind: "file", requirementId: "thumb" });
    });

    it("skips a file that is already prepared", () => {
        const step = nextStep({
            kit: KIT,
            included: all,
            prepared: ["sign"],
            current: "photo",
        });
        expect(step).toMatchObject({ kind: "file", requirementId: "thumb" });
    });

    it("comes back to an earlier file left undone", () => {
        const step = nextStep({
            kit: KIT,
            included: all,
            prepared: ["sign"],
            current: "thumb",
        });
        expect(step).toMatchObject({ kind: "file", requirementId: "photo" });
    });

    it("says nothing at all from a file that is not in the kit", () => {
        expect(
            nextStep({
                kit: KIT,
                included: ["sign", "thumb"],
                prepared: [],
                current: "photo",
            }),
        ).toEqual({ kind: "none" });
    });

    it("says nothing when this is the only file still waiting", () => {
        expect(
            nextStep({
                kit: KIT,
                included: all,
                prepared: ["sign", "thumb"],
                current: "photo",
            }),
        ).toEqual({ kind: "none" });
    });

    it("asks for payment once every file in the kit is prepared", () => {
        expect(
            nextStep({
                kit: KIT,
                included: all,
                prepared: all,
                current: "sign",
            }),
        ).toEqual({ kind: "review", total: 3 });
    });

    it("counts only the kit, not the whole application", () => {
        expect(
            nextStep({
                kit: KIT,
                included: ["photo", "sign"],
                prepared: ["photo", "sign"],
                current: "photo",
            }),
        ).toEqual({ kind: "review", total: 2 });
    });
});
