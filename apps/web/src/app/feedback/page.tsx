import type { Metadata } from "next";
import { ReviewPanel } from "../../components/exam/review-panel";

export const metadata: Metadata = {
    title: "How did we do?",
    robots: { index: false, follow: false },
};

/**
 * Where the delivery email's "did it work?" links land (DEC-111, DEC-112):
 * the same review box as the downloads screen, proven by the link's
 * signature instead of the kit. Opening the page records nothing, because
 * mail scanners open links; only pressing Send does.
 */
export default async function FeedbackPage({ searchParams }: { searchParams: Promise<{ o?: string; t?: string }> }) {
    const { o = "", t = "" } = await searchParams;
    const valid = /^order_[A-Za-z0-9_-]{1,64}$/.test(o) && /^[a-f0-9]{32}$/.test(t);
    return (
        <main id="main-content" className="euk euk-feedback">
            {valid ? (
                <ReviewPanel orderId={o} token={t} />
            ) : (
                <>
                    <h1 className="euk-display">How did we do?</h1>
                    <p>This link is incomplete. Reply to the email that brought you here and tell us how it went.</p>
                </>
            )}
        </main>
    );
}
