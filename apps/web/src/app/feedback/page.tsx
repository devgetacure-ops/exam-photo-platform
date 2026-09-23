import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Did it work?",
    robots: { index: false, follow: false },
};

/**
 * Where the delivery email's "did it work?" links land (DEC-111).
 *
 * Nothing is recorded on opening the page: mail scanners open links on their
 * own, and an answer they gave would be worth nothing. The candidate's answer
 * is saved only when they press Send.
 */
export default async function FeedbackPage({
    searchParams,
}: {
    searchParams: Promise<{ o?: string; t?: string; a?: string; sent?: string }>;
}) {
    const { o = "", t = "", a = "yes", sent } = await searchParams;
    const valid = /^order_[A-Za-z0-9_-]{1,64}$/.test(o) && /^[a-f0-9]{32}$/.test(t);

    return (
        <main id="main-content" className="euk euk-feedback">
            <h1 className="euk-display">{sent ? "Thank you." : "Did your file work?"}</h1>
            {!valid && <p>This link is incomplete. Reply to the email that brought you here and tell us how it went.</p>}
            {valid && sent && <p>We read every answer. If something went wrong, we will write to you.</p>}
            {valid && !sent && (
                <form method="post" action="/api/feedback" className="euk-feedback-form">
                    <input type="hidden" name="order_id" value={o} />
                    <input type="hidden" name="token" value={t} />
                    <fieldset>
                        <legend className="euk-label">Your answer</legend>
                        <label>
                            <input type="radio" name="worked" value="yes" defaultChecked={a !== "no"} /> Yes, the portal accepted it
                        </label>
                        <label>
                            <input type="radio" name="worked" value="no" defaultChecked={a === "no"} /> No, there was a problem
                        </label>
                    </fieldset>
                    <label>
                        <span className="euk-label">Anything to add? (optional)</span>
                        <textarea name="comment" rows={4} maxLength={1000} />
                    </label>
                    <label className="euk-consent">
                        <input type="checkbox" name="may_publish" value="yes" />
                        <span>You may show my comment on the site, without my name or email.</span>
                    </label>
                    <button type="submit" className="primary-button">
                        Send
                    </button>
                </form>
            )}
        </main>
    );
}
