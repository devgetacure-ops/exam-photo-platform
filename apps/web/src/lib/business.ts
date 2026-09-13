import "server-only";

/**
 * Who runs the service, for the pages that have to say so.
 *
 * The consumer rules for selling online ask for the seller's name, address,
 * a contact number and email, and a grievance officer's name, designation and
 * contact. For a one-person business all of those are the owner's own, and
 * the owner does not want them public before launch (DEC-086). So the personal
 * details are read from the environment at build time and never committed;
 * with them unset, nothing about the business renders anywhere.
 *
 * Set in `apps/web/.env.local` (git-ignored) or the host's environment:
 * EUK_BUSINESS_NAME, EUK_BUSINESS_ADDRESS, EUK_BUSINESS_PHONE,
 * EUK_BUSINESS_HOURS.
 */

export const CONTACT_EMAILS = {
    support: "support@examuploadkit.com",
    privacy: "privacy@examuploadkit.com",
    grievance: "grievance@examuploadkit.com",
    legal: "legal@examuploadkit.com",
} as const;

export const GRIEVANCE_DESIGNATION = "Proprietor and Grievance Officer";

export interface Business {
    name: string;
    address: string;
    phone: string;
    hours: string;
}

export function readBusiness(): Business | null {
    const name = process.env.EUK_BUSINESS_NAME?.trim();
    const address = process.env.EUK_BUSINESS_ADDRESS?.trim();
    const phone = process.env.EUK_BUSINESS_PHONE?.trim();
    const hours = process.env.EUK_BUSINESS_HOURS?.trim();
    // All or nothing: half a set of business details reads as a mistake.
    if (!name || !address || !phone || !hours) return null;
    return { name, address, phone, hours };
}
