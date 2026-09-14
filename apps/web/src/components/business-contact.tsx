import { CONTACT_EMAILS, GRIEVANCE_DESIGNATION, readBusiness } from "../lib/business";

/**
 * How to reach the service: shown on the terms, the privacy policy and
 * support. No personal name and no home address, ever (owner, 2026-09-14);
 * the grievance officer is the designation and its address. Renders nothing
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
                    <dt>Support</dt>
                    <dd>
                        <a href={`mailto:${CONTACT_EMAILS.support}`}>{CONTACT_EMAILS.support}</a>
                    </dd>
                </div>
                <div>
                    <dt>Grievance Officer</dt>
                    <dd>
                        {GRIEVANCE_DESIGNATION}
                        <br />
                        <a href={`mailto:${CONTACT_EMAILS.grievance}`}>{CONTACT_EMAILS.grievance}</a>
                    </dd>
                </div>
                <div>
                    <dt>Privacy</dt>
                    <dd>
                        <a href={`mailto:${CONTACT_EMAILS.privacy}`}>{CONTACT_EMAILS.privacy}</a>
                    </dd>
                </div>
                <div>
                    <dt>Legal notices</dt>
                    <dd>
                        <a href={`mailto:${CONTACT_EMAILS.legal}`}>{CONTACT_EMAILS.legal}</a>
                    </dd>
                </div>
            </dl>
        </address>
    );
}
