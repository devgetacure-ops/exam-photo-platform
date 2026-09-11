import type { ExamDetail, RequirementSummary } from "./types";

/**
 * The do and don't specimens for one file.
 *
 * Examination notices teach by specimen: SSC prints a sheet of photographs
 * that will not be accepted, each captioned with its fault, and the banking
 * notices set a signature in capitals beside the rule forbidding it. The page
 * adapts that sheet, with two constraints.
 *
 * Each specimen is a drawing, not a photograph. A photographed stranger in a
 * cap would be a real face with no provenance on a page that sells exactly
 * that care; a line drawing shows the fault and nothing else.
 *
 * And no specimen appears without a reason. A "don't" is either something this
 * examination's own record rules out (a cap where headwear is not permitted,
 * capitals where the notice forbids them) or something we check every upload
 * for and cannot fix (a blurred photograph, a signature cut off at the edge).
 * An examination that permits spectacles gets no spectacles specimen.
 */

export type SpecimenId =
    | "portrait-ok"
    | "portrait-cap"
    | "portrait-dark-glasses"
    | "portrait-spectacles"
    | "portrait-glare"
    | "portrait-mask"
    | "portrait-shadow"
    | "portrait-side"
    | "portrait-eyes-closed"
    | "portrait-far"
    | "portrait-clipped"
    | "portrait-blur"
    | "portrait-dark"
    | "signature-ok"
    | "signature-capitals"
    | "signature-clipped"
    | "signature-faint"
    | "thumb-ok"
    | "thumb-smudged"
    | "declaration-ok"
    | "declaration-capitals"
    | "declaration-cropped"
    | "document-ok"
    | "document-cut";

export interface Specimen {
    id: SpecimenId;
    ok: boolean;
    caption: string;
}

interface Policy {
    policy?: string;
    condition?: string;
}

function policyOf(raw: unknown): Policy | null {
    return raw && typeof raw === "object" ? (raw as Policy) : null;
}

/** Everything the record says about this file, as one searchable string. */
function recordText(requirement: RequirementSummary): string {
    return [
        ...requirement.rejection_conditions,
        requirement.content_instructions ?? "",
        requirement.notes ?? "",
    ].join(" ");
}

export function specimensFor(
    requirement: RequirementSummary,
    exam: ExamDetail,
): Specimen[] {
    const said = recordText(requirement);
    switch (requirement.requirement_type) {
        case "photograph":
            return photograph(exam, said);
        case "signature":
            return signature(said);
        case "thumb_impression":
            return thumb(said);
        case "handwritten_declaration":
            return declaration(said);
        case "certificate_scan":
        case "identity_document":
            return document();
        default:
            return [];
    }
}

function photograph(exam: ExamDetail, said: string): Specimen[] {
    const image = (exam.image_requirements ?? {}) as Record<string, unknown>;
    const appearance = (image.appearance ?? {}) as Record<string, unknown>;
    const headwear = policyOf(appearance.headwear);
    const spectacles = policyOf(appearance.spectacles);
    const mask = policyOf(appearance.face_mask);
    const conditions = `${headwear?.condition ?? ""} ${spectacles?.condition ?? ""} ${said}`;

    const out: Specimen[] = [
        {
            id: "portrait-ok",
            ok: true,
            caption: "Straight on, eyes open, the whole face visible",
        },
    ];

    // What this examination's own rules rule out.
    if (headwear && headwear.policy !== "permitted") {
        out.push({ id: "portrait-cap", ok: false, caption: "A cap or hat" });
    }
    if (/dark glasses|sunglasses|tinted/i.test(conditions)) {
        out.push({
            id: "portrait-dark-glasses",
            ok: false,
            caption: "Dark glasses",
        });
    }
    if (spectacles?.policy === "prohibited") {
        out.push({
            id: "portrait-spectacles",
            ok: false,
            caption: "Spectacles",
        });
    } else if (
        spectacles?.policy === "conditional" ||
        /reflection|glare/i.test(said)
    ) {
        out.push({
            id: "portrait-glare",
            ok: false,
            caption: "Glare hiding the eyes",
        });
    }
    if (mask?.policy === "prohibited") {
        out.push({ id: "portrait-mask", ok: false, caption: "A face mask" });
    }
    if (/shadow/i.test(said)) {
        out.push({
            id: "portrait-shadow",
            ok: false,
            caption: "Shadow across the face",
        });
    }

    // What we check every photograph for, whatever the notice says.
    out.push(
        { id: "portrait-side", ok: false, caption: "Turned from the camera" },
        { id: "portrait-eyes-closed", ok: false, caption: "Eyes closed" },
        { id: "portrait-far", ok: false, caption: "Taken too far away" },
        {
            id: "portrait-clipped",
            ok: false,
            caption: "Top of the head cut off",
        },
        { id: "portrait-blur", ok: false, caption: "Blurred" },
        { id: "portrait-dark", ok: false, caption: "Too dark" },
    );
    return out;
}

function signature(said: string): Specimen[] {
    const blackInk = /black ink/i.test(said);
    const out: Specimen[] = [
        {
            id: "signature-ok",
            ok: true,
            caption: blackInk
                ? "Your full signature, black ink, white paper"
                : "Your full signature, dark ink, plain paper",
        },
    ];
    if (/capital/i.test(said)) {
        out.push({
            id: "signature-capitals",
            ok: false,
            caption: "In capital letters",
        });
    }
    out.push({
        id: "signature-clipped",
        ok: false,
        caption: "Strokes cut off at the edge",
    });
    if (/ink|pen/i.test(said)) {
        out.push({
            id: "signature-faint",
            ok: false,
            caption: "Pencil, or ink too faint",
        });
    }
    return out;
}

function thumb(said: string): Specimen[] {
    const out: Specimen[] = [
        {
            id: "thumb-ok",
            ok: true,
            caption: "The whole impression, ridges clear",
        },
    ];
    if (/smudg|unclear|blot/i.test(said)) {
        out.push({
            id: "thumb-smudged",
            ok: false,
            caption: "Smudged or blotted",
        });
    }
    return out;
}

function declaration(said: string): Specimen[] {
    const out: Specimen[] = [
        {
            id: "declaration-ok",
            ok: true,
            caption: "The whole page, written clearly",
        },
    ];
    if (/capital/i.test(said)) {
        out.push({
            id: "declaration-capitals",
            ok: false,
            caption: "In capital letters",
        });
    }
    out.push({
        id: "declaration-cropped",
        ok: false,
        caption: "Page cut off at the edges",
    });
    return out;
}

function document(): Specimen[] {
    return [
        {
            id: "document-ok",
            ok: true,
            caption: "Every page whole and readable",
        },
        {
            id: "document-cut",
            ok: false,
            caption: "Corners cut off, or shot at an angle",
        },
    ];
}
