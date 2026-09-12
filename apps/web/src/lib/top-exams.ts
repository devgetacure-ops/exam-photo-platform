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
    { id: "ssc-combined-higher-secondary-10-2-level-examination-2025-live-capture", label: "SSC CHSL" },
    { id: "ssc-multi-tasking-staff-and-havaldar-examination-2025-live-capture", label: "SSC MTS" },
    { id: "ibps-crp-po-mt-xvi", label: "IBPS PO" },
    { id: "ibps-crp-customer-service-associates-xv", label: "IBPS Clerk" },
    { id: "sbi-probationary-officers-2025", label: "SBI PO" },
    { id: "sbi-junior-associates-2025", label: "SBI Clerk" },
    { id: "rrb-ntpc-graduate-cen-05-2024", label: "RRB NTPC" },
    { id: "rrb-level-1-posts-cen-08-2024", label: "RRB Group D" },
    { id: "upsc-civil-services-examination-2026", label: "UPSC CSE" },
    { id: "upsc-nda-na-examination-ii-2026", label: "NDA" },
    { id: "uttar-pradesh-police-constable-recruitment", label: "UP Police" },
    { id: "neet-ug-2026", label: "NEET UG" },
    { id: "jee-main-2026", label: "JEE Main" },
    { id: "cuet-ug-2026", label: "CUET UG" },
    { id: "gate-2026", label: "GATE" },
    { id: "ctet-september-2026", label: "CTET" },
    { id: "common-admission-test-2025", label: "CAT" },
];
