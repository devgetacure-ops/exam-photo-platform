import { describe, expect, test } from "vitest";
import { kitPrice, rupees, tier } from "../lib/kit-pricing";
import type { RequirementSummary } from "../lib/types";

function requirement(
    id: string,
    type: RequirementSummary["requirement_type"],
    support: RequirementSummary["platform_support"] = "supported",
): RequirementSummary {
    return {
        requirement_id: id,
        requirement_name: id,
        requirement_type: type,
        submission_method: "file_upload",
        requirement_status: "mandatory",
        platform_support: support,
        rejection_conditions: [],
    };
}

const kit = [
    requirement("photo", "photograph"),
    requirement("sign", "signature"),
    requirement("thumb", "thumb_impression"),
    requirement("cert", "certificate_scan"),
    requirement("live", "photograph", "guidance_only"),
];

describe("kit price display", () => {
    test("mirrors the server ladder, with five rupees as the ceiling", () => {
        expect([0, 1, 2, 3, 6].map((n) => tier(n))).toEqual([0, 300, 500, 500, 500]);
        expect(rupees(500)).toBe("₹5");
    });

    test("documents are free and never move the price", () => {
        const price = kitPrice(kit, ["photo", "sign", "cert"]);
        expect(price.chargeable).toBe(2);
        expect(price.free).toBe(1);
        expect(price.amount).toBe(500);
        expect(price.list).toBe(1000);
    });

    test("the whole kit counts only files we prepare", () => {
        const price = kitPrice(kit, []);
        expect(price.kitFiles).toBe(4);
        expect(price.kitChargeable).toBe(3);
        expect(price.kitAmount).toBe(500);
        expect(price.amount).toBe(0);
    });

    test("a selection of documents alone costs nothing", () => {
        expect(kitPrice(kit, ["cert"]).amount).toBe(0);
    });
});
