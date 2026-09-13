import { CONTACT_EMAILS, GRIEVANCE_DESIGNATION, readBusiness } from "../lib/business";

/**
 * Who runs the service and how to reach them: the details the consumer rules
 * ask a seller to publish, set once and shown on the terms, the privacy
 * policy and support. Renders nothing until the owner's details are set in
 * the environment (DEC-086).
 */
export function BusinessContact() {
    const business = readBusiness();
    if (!business) return null;
    const tel = business.phone.replace(/[^\d+]/g, "");

    return (
        <address className="euk-business" aria-label="Who runs examuploadkit">
            <p className="euk-business-title">Who runs examuploadkit</p>
            <dl>
                <div>
                    <dt>Proprietor</dt>
                    <dd>{business.name}</dd>
                </div>
                <div>
                    <dt>Address</dt>
                    <dd>{business.address}</dd>
                </div>
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
                        {business.name}, {GRIEVANCE_DESIGNATION}
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
