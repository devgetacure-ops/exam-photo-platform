import type { RequirementSummary } from "./types";

/**
 * What the kit costs, for display.
 *
 * The server decides the amount (DEC-070): `api/pricing.py` prices the kit
 * from the prepared jobs and the order is created at that figure. This mirrors
 * its ladder only so the price can move as the candidate ticks and unticks
 * files, before anything has been prepared. The review always shows the
 * server's quote, and that is what is paid.
 *
 * Kept in step with `CHARGEABLE_REQUIREMENT_TYPES`, `PRICE_LADDER_PAISE` and
 * `LIST_LADDER_PAISE` there.
 */
export const CHARGEABLE_TYPES: ReadonlySet<string> = new Set([
    "photograph",
    "signature",
    "thumb_impression",
    "handwritten_declaration",
]);

const PRICE_LADDER = [300, 500, 800];
const LIST_LADDER = [400, 800, 1000];

export function tier(count: number, ladder: readonly number[] = PRICE_LADDER): number {
    if (count <= 0) return 0;
    return ladder[Math.min(count, ladder.length) - 1];
}

export function rupees(paise: number): string {
    return `₹${Math.round(paise) / 100}`;
}

/** A requirement the platform prepares a file for (DEC-056: never a boolean elsewhere). */
export function isOurs(requirement: RequirementSummary): boolean {
    return (
        requirement.platform_support === "supported" ||
        requirement.platform_support === "partially_supported"
    );
}

export interface KitPrice {
    /** Files we prepare that are in the selection. */
    chosen: number;
    chargeable: number;
    free: number;
    amount: number;
    list: number;
    /** The same figures for every file we prepare. */
    kitFiles: number;
    kitChargeable: number;
    kitFree: number;
    kitAmount: number;
    kitList: number;
}

export function kitPrice(
    requirements: RequirementSummary[],
    included: readonly string[],
): KitPrice {
    const ours = requirements.filter(isOurs);
    const chosen = ours.filter((r) => included.includes(r.requirement_id));
    const charged = (rows: RequirementSummary[]) =>
        rows.filter((r) => CHARGEABLE_TYPES.has(r.requirement_type)).length;

    const chargeable = charged(chosen);
    const kitChargeable = charged(ours);
    return {
        chosen: chosen.length,
        chargeable,
        free: chosen.length - chargeable,
        amount: tier(chargeable),
        list: tier(chargeable, LIST_LADDER),
        kitFiles: ours.length,
        kitChargeable,
        kitFree: ours.length - kitChargeable,
        kitAmount: tier(kitChargeable),
        kitList: tier(kitChargeable, LIST_LADDER),
    };
}
