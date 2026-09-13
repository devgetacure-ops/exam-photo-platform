/**
 * What a candidate agrees to before the first file leaves their device.
 *
 * Three agreements, asked once and remembered in this browser (DEC-086):
 *
 * - **The terms and the privacy policy**, for every examination. One tick,
 *   with both pages linked, and nothing else written into the flow: the
 *   limits, the disclaimers and who is responsible for what live on those
 *   pages, not in front of a candidate who is trying to upload (the owner's
 *   call).
 * - **A parent or guardian**, where the examination's candidates are, or can
 *   be, under 18. A child's personal data needs a parent's agreement under the
 *   Digital Personal Data Protection Act, 2023.
 * - **The thumb impression**, where the file being prepared is one. A
 *   fingerprint is biometric information, which needs explicit agreement
 *   before it is collected.
 *
 * Everything is kept in this browser only. Unticking a box takes the
 * agreement back, and the next upload asks again.
 */

/** `child`: every candidate is under 18. `maybe`: a candidate can be. */
export type Minority = "child" | "maybe";

/**
 * Examinations whose candidates are, or can be, under 18 when they apply,
 * from each examination's published eligibility. Recorded in DEC-086 with the
 * basis for each; an examination added to the catalogue is not on this list
 * until someone has read its eligibility.
 */
export const UNDER_18: Readonly<Record<string, Minority>> = {
    // Every candidate is a child.
    "all-india-sainik-schools-entrance-examination": "child", // entry to Classes VI and IX
    "jawahar-navodaya-vidyalaya-selection-test-class-vi": "child", // entry to Class VI
    "cbse-classes-ix-xi-registration-2025-26": "child", // Class IX and XI students

    // Open after Class 10.
    "ap-polycet": "maybe",
    "tg-ts-polycet": "maybe",
    "joint-entrance-examination-council-uttar-pradesh-polytechnic-entrance": "maybe",
    "icai-examination-portal-photograph-current-portal-scope": "maybe", // Foundation registration

    // Open to Class 12 students, or with a minimum age under 18.
    "jee-main-2026": "maybe",
    "jee-advanced-2026": "maybe",
    "neet-ug-2026": "maybe", // minimum age 17
    "cuet-ug-2026": "maybe",
    "bits-admission-test": "maybe",
    "gujcet": "maybe",
    "karnataka-common-entrance-test-2026": "maybe",
    "kerala-engineering-architecture-medical-entrance-examination": "maybe",
    "mht-cet-2026": "maybe",
    "tg-eapcet": "maybe",
    "wbjee-2026": "maybe",
    "odisha-joint-entrance-examination-ojee": "maybe", // B.Pharm and integrated MBA after Class 12
    "icsi-student-registration-examination-account-photograph": "maybe", // CSEET
    "bihar-d-el-ed-joint-entrance-examination": "maybe", // minimum age 17
    "rajasthan-pre-d-el-ed-examination-bstc": "maybe", // after Class 12
    "rajasthan-pre-teacher-education-test": "maybe", // four-year course after Class 12
    "upsc-nda-na-examination-ii-2026": "maybe", // from 16½
    "indian-air-force-agniveervayu-recruitment": "maybe", // from 17½
    "indian-army-agniveer-recruitment": "maybe", // from 17½
    "indian-army-agniveer-cee-2025-26-online-upload": "maybe", // from 17½
};

/** Moves when the terms or the privacy policy change in substance. */
export const TERMS_VERSION = "2026-09-13";

const TERMS_KEY = "uploadready:terms-accepted";
const EVENT = "euk:consent";

function examKey(examId: string): string {
    return `uploadready:consent:${examId}`;
}

export interface ConsentNeeds {
    guardian: Minority | null;
    thumb: boolean;
}

export interface ConsentState {
    terms: boolean;
    guardian: boolean;
    thumb: boolean;
}

export function consentNeeds(examId: string, requirementType: string): ConsentNeeds {
    return {
        guardian: UNDER_18[examId] ?? null,
        thumb: requirementType === "thumb_impression",
    };
}

export function readConsent(examId: string): ConsentState {
    try {
        const terms = localStorage.getItem(TERMS_KEY) === TERMS_VERSION;
        const raw = localStorage.getItem(examKey(examId));
        const value: unknown = raw ? JSON.parse(raw) : null;
        const record = typeof value === "object" && value !== null ? (value as Record<string, unknown>) : {};
        return { terms, guardian: record.guardian === true, thumb: record.thumb === true };
    } catch {
        // Storage blocked or the value damaged: ask again rather than assume.
        return { terms: false, guardian: false, thumb: false };
    }
}

export function giveConsent(examId: string, part: keyof ConsentState, value: boolean): void {
    try {
        if (part === "terms") {
            if (value) localStorage.setItem(TERMS_KEY, TERMS_VERSION);
            else localStorage.removeItem(TERMS_KEY);
        } else {
            const current = readConsent(examId);
            localStorage.setItem(
                examKey(examId),
                JSON.stringify({ guardian: current.guardian, thumb: current.thumb, [part]: value }),
            );
        }
    } catch {
        // Storage blocked: the box cannot stay ticked, so the upload keeps asking.
    }
    window.dispatchEvent(new Event(EVENT));
}

export function consentReady(state: ConsentState, needs: ConsentNeeds): boolean {
    return state.terms && (!needs.guardian || state.guardian) && (!needs.thumb || state.thumb);
}

export function subscribeConsent(onChange: () => void): () => void {
    window.addEventListener(EVENT, onChange);
    window.addEventListener("storage", onChange);
    return () => {
        window.removeEventListener(EVENT, onChange);
        window.removeEventListener("storage", onChange);
    };
}
