import "server-only";

/**
 * How to reach the service, for the pages that have to say so.
 *
 * The owner's name and home address are never shown (owner, 2026-09-14): the
 * grievance officer is named by designation only, and the address block stays
 * empty until a business address, separate from the one on their identity
 * documents, is set. So this reads only the phone, the hours and that public
 * address -- never a name -- and never from the code.
 *
 * Set in `apps/web/.env.local` (git-ignored) or the host's environment:
 * EUK_BUSINESS_PHONE, EUK_BUSINESS_HOURS, and optionally
 * EUK_BUSINESS_PUBLIC_ADDRESS. The older EUK_BUSINESS_NAME and
 * EUK_BUSINESS_ADDRESS are deliberately not read.
 */

export { CONTACT_EMAILS } from "./site";

export const GRIEVANCE_DESIGNATION = "Proprietor and Grievance Officer";

export interface Business {
    phone: string;
    hours: string;
    /** A business address chosen for publication; null until one is set. */
    address: string | null;
}

export function readBusiness(): Business | null {
    const phone = process.env.EUK_BUSINESS_PHONE?.trim();
    const hours = process.env.EUK_BUSINESS_HOURS?.trim();
    const address = process.env.EUK_BUSINESS_PUBLIC_ADDRESS?.trim() || null;
    // Both or nothing: a phone without its hours reads as a mistake.
    if (!phone || !hours) return null;
    return { phone, hours, address };
}
