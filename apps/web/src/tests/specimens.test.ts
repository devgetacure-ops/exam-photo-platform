import { describe, expect, test } from "vitest";
import { specimensFor } from "../lib/specimens";
import type { ExamDetail, RequirementSummary } from "../lib/types";

function exam(appearance: Record<string, unknown> = {}): ExamDetail {
    return {
        exam_id: "e",
        exam_name: "E",
        conducting_body: "Body",
        examination_year: 2026,
        application_cycle: "2026",
        aliases: [],
        status: "active",
        rule_id: "r",
        rule_version: "1",
        requirement_counts: {},
        image_requirements: { appearance },
        provenance: {},
        source_evidence: [],
        verification_status: "verified",
        application_rejection_conditions: [],
    };
}

function requirement(
    type: RequirementSummary["requirement_type"],
    said: Partial<RequirementSummary> = {},
): RequirementSummary {
    return {
        requirement_id: type,
        requirement_name: type,
        requirement_type: type,
        submission_method: "file_upload",
        requirement_status: "mandatory",
        platform_support: "supported",
        rejection_conditions: [],
        ...said,
    };
}

const ids = (list: { id: string }[]) => list.map((s) => s.id);

describe("specimens come from the record, never from habit", () => {
    test("every sheet leads with the accepted example", () => {
        for (const type of ["photograph", "signature", "thumb_impression", "handwritten_declaration", "certificate_scan"] as const) {
            const list = specimensFor(requirement(type), exam());
            expect(list[0].ok).toBe(true);
            expect(list.slice(1).every((s) => !s.ok)).toBe(true);
        }
    });

    test("no cap specimen where headwear is permitted, one where it is not", () => {
        const photo = requirement("photograph");
        expect(ids(specimensFor(photo, exam({ headwear: { policy: "permitted" } })))).not.toContain("portrait-cap");
        expect(ids(specimensFor(photo, exam({ headwear: { policy: "prohibited" } })))).toContain("portrait-cap");
    });

    test("spectacles: prohibited shows the frames, conditional shows the glare", () => {
        const photo = requirement("photograph");
        expect(ids(specimensFor(photo, exam({ spectacles: { policy: "prohibited" } })))).toContain("portrait-spectacles");
        const conditional = ids(specimensFor(photo, exam({ spectacles: { policy: "conditional" } })));
        expect(conditional).toContain("portrait-glare");
        expect(conditional).not.toContain("portrait-spectacles");
    });

    test("capitals appear only when the notice forbids them", () => {
        expect(ids(specimensFor(requirement("signature"), exam()))).not.toContain("signature-capitals");
        const banking = requirement("signature", {
            rejection_conditions: ["Signature in capital letters is not accepted."],
        });
        expect(ids(specimensFor(banking, exam()))).toContain("signature-capitals");
    });
});
