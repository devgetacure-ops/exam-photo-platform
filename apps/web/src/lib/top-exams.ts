/**
 * The examinations offered as shortcuts under the hero.
 *
 * A hand-picked list, not a ranking: there is no traffic yet, and a "most
 * popular" claim with nothing behind it is the kind of invented figure this
 * product does not make. Edit this list freely — the labels are the short
 * forms candidates actually type, and any id that no longer exists in the
 * catalogue is dropped at build time rather than shipped as a dead link.
 *
 * When the site has real traffic, this is the thing to replace with what
 * candidates actually open.
 */
export interface TopExam {
    /** Must match an `exam_id` in the catalogue. */
    id: string;
    /** The short form, for a chip. The full name is read from the record. */
    label: string;
}

export const TOP_EXAMS: TopExam[] = [
    { id: "ssc-combined-graduate-level-examination-2026-live-capture", label: "SSC CGL" },
    { id: "ibps-crp-po-mt-xvi", label: "IBPS PO" },
    { id: "neet-ug-2026", label: "NEET UG" },
    { id: "cuet-ug-2026", label: "CUET UG" },
    { id: "rrb-ntpc-graduate-cen-05-2024", label: "RRB NTPC" },
    { id: "ctet-september-2026", label: "CTET" },
    { id: "sbi-probationary-officers-2025", label: "SBI PO" },
    { id: "common-admission-test-2025", label: "CAT" },
];
