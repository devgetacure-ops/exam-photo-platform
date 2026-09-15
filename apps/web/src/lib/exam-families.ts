/**
 * The examination families: one hub page each, and the same grouping the
 * keyword map targets, so the two can never disagree (DEC-096).
 *
 * Grouped by the record's `category`, which the research writes in 29
 * inconsistent spellings; every one of them is placed here deliberately. A
 * category nobody has placed returns no family, and a test fails, so a new
 * examination is never quietly left out of its hub.
 *
 * Three examinations belong to no family on purpose: ICAI's and ICSI's
 * portals (professional bodies) and CBSE's Class IX/XI registration (a school
 * board). Putting them in "entrance exams" would say something untrue.
 */

export interface ExamFamily {
    slug: string;
    /** As a heading: "Banking and insurance". */
    name: string;
    /** As it reads mid-sentence: "banking and insurance". */
    phrase: string;
    /** One factual line on who sets these examinations. */
    blurb: string;
    /** The words candidates search the family by, for the keyword map. */
    searchWords: readonly string[];
    categories: readonly string[];
}

export const EXAM_FAMILIES: readonly ExamFamily[] = [
    {
        slug: "ssc-and-upsc",
        name: "SSC and UPSC",
        phrase: "SSC and UPSC",
        blurb: "Central government recruitment by the Staff Selection Commission and the Union Public Service Commission.",
        searchWords: ["ssc", "ssc exam", "upsc", "upsc exam"],
        categories: ["central_recruitment"],
    },
    {
        slug: "banking-and-insurance",
        name: "Banking and insurance",
        phrase: "banking and insurance",
        blurb: "Recruitment by IBPS, SBI, RBI, NABARD and the public insurance companies.",
        searchWords: ["bank exam", "banking exam", "ibps", "bank po", "insurance exam", "lic exam"],
        categories: ["banking", "insurance"],
    },
    {
        slug: "railways",
        name: "Railways",
        phrase: "railway",
        blurb: "Recruitment by the Railway Recruitment Boards and the Railway Protection Force.",
        searchWords: ["railway exam", "rrb", "railway"],
        categories: ["railway_recruitment", "railway_security", "railways"],
    },
    {
        slug: "police",
        name: "Police",
        phrase: "police",
        blurb: "Constable and sub-inspector recruitment by state police boards and selection commissions.",
        searchWords: ["police exam", "police constable", "police recruitment"],
        categories: ["police_recruitment"],
    },
    {
        slug: "defence",
        name: "Defence",
        phrase: "defence",
        blurb: "Agniveer intakes and the UPSC defence examinations.",
        searchWords: ["defence exam", "agniveer", "army exam"],
        categories: ["defence", "defence_recruitment"],
    },
    {
        slug: "teaching",
        name: "Teaching",
        phrase: "teaching",
        blurb: "Teacher eligibility tests, teacher recruitment, teacher-education entrances and the national eligibility tests for lecturers.",
        searchWords: ["tet", "teacher exam", "teacher recruitment"],
        categories: [
            "teacher_eligibility",
            "teacher_recruitment",
            "teacher_education_entrance",
            "teaching_eligibility",
            "teaching_research_eligibility",
            "teaching_and_non_teaching_recruitment",
        ],
    },
    {
        slug: "state-commissions",
        name: "State commissions",
        phrase: "state commission",
        blurb: "State public service commissions, staff selection boards and common eligibility tests.",
        searchWords: ["psc exam", "state psc"],
        categories: [
            "state_psc",
            "state_psc_recruitment",
            "state_recruitment",
            "state_recruitment_family",
            "state_common_eligibility",
            "state_recruitment_common_eligibility",
        ],
    },
    {
        slug: "entrance-exams",
        name: "Entrance exams",
        phrase: "entrance",
        blurb: "Admission tests for engineering, medicine, management, polytechnics and schools.",
        searchWords: ["entrance exam", "engineering entrance", "medical entrance"],
        categories: [
            "entrance",
            "state_entrance",
            "management_entrance",
            "medical_entrance",
            "private_entrance",
            "school_admission_entrance",
        ],
    },
];

/** Categories deliberately in no family, and why. */
export const UNGROUPED_CATEGORIES: Readonly<Record<string, string>> = {
    professional_body: "ICAI and ICSI are professional bodies, not a recruitment or entrance family.",
    board_registration: "CBSE's registration is a school board process, not an examination family.",
};

const BY_CATEGORY = new Map<string, ExamFamily>(
    EXAM_FAMILIES.flatMap((family) =>
        family.categories.map((category) => [category, family] as const),
    ),
);

/** The family an examination's category belongs to, or null. */
export function familyOf(category: string | null | undefined): ExamFamily | null {
    return category ? (BY_CATEGORY.get(category) ?? null) : null;
}

export function familyBySlug(slug: string): ExamFamily | null {
    return EXAM_FAMILIES.find((family) => family.slug === slug) ?? null;
}
