import { CONTACT_EMAILS, readBusiness } from "../lib/business";

/**
 * How to reach the service: shown on the terms, the privacy policy and
 * support. No personal name and no home address, ever (owner, 2026-09-14).
 * One address for everything (DEC-127): support answers privacy and
 * complaints too. Renders nothing
 * until the phone and hours are set in the environment.
 */
export function BusinessContact() {
    const business = readBusiness();
    if (!business) return null;
    const tel = business.phone.replace(/[^\d+]/g, "");

    return (
        <address className="euk-business" aria-label="How to reach ExamUploadKit">
            <p className="euk-business-title">How to reach ExamUploadKit</p>
            <dl>
                {business.address && (
                    <div>
                        <dt>Address</dt>
                        <dd>{business.address}</dd>
                    </div>
                )}
                <div>
                    <dt>Phone</dt>
                    <dd>
                        <a href={`tel:${tel}`}>{business.phone}</a>
                    </dd>
                </div>
                <div>
                    <dt>Hours</dt>
                    <dd>{business.hours}</dd>
                </div>
                <div>
                    <dt>Email</dt>
                    <dd>
                        <a href={`mailto:${CONTACT_EMAILS.support}`}>{CONTACT_EMAILS.support}</a>
                    </dd>
                </div>
            </dl>
        </address>
    );
}
