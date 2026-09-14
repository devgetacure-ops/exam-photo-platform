/**
 * What a candidate agrees to before the first file leaves their device.
 *
 * One agreement, asked once and remembered in this browser: the terms and the
 * privacy policy, both linked. The owner ruled on 2026-09-14 that three boxes
 * were friction, so everything the others said -- that a candidate under 18
 * has a parent's or guardian's agreement, and that a thumb impression is
 * processed only to prepare the file -- is written into those two pages and
 * confirmed by this one tick (DEC-086, amended).
 *
 * Unticking takes the agreement back, and the next upload asks again.
 */

/** Moves when the terms or the privacy policy change in substance. */
export const TERMS_VERSION = "2026-09-14";

const TERMS_KEY = "uploadready:terms-accepted";
const EVENT = "euk:consent";

export function readTermsAccepted(): boolean {
    try {
        return localStorage.getItem(TERMS_KEY) === TERMS_VERSION;
    } catch {
        // Storage blocked: ask again rather than assume.
        return false;
    }
}

export function giveTermsConsent(value: boolean): void {
    try {
        if (value) localStorage.setItem(TERMS_KEY, TERMS_VERSION);
        else localStorage.removeItem(TERMS_KEY);
    } catch {
        // Storage blocked: the box cannot stay ticked, so the upload keeps asking.
    }
    window.dispatchEvent(new Event(EVENT));
}

export function subscribeConsent(onChange: () => void): () => void {
    window.addEventListener(EVENT, onChange);
    window.addEventListener("storage", onChange);
    return () => {
        window.removeEventListener(EVENT, onChange);
        window.removeEventListener("storage", onChange);
    };
}
