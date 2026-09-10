import Link from "next/link";
export function SiteFooter() {
    return (
        <footer className="journey-footer">
            <div className="footer-invitation">
                <p className="footer-note">
                    For the application. And everything after.
                </p>
                <h2>
                    A little less admin.
                    <br />
                    <span>A little more possibility.</span>
                </h2>
                <Link className="primary-button" href="/#find-exam">
                    Find your exam <span aria-hidden="true">↗</span>
                </Link>
            </div>
            <div className="footer-flight" aria-hidden="true">
                ↗
            </div>
            <div className="footer-bottom">
                <Link href="/" className="wordmark">
                    UploadReady.
                </Link>
                <nav aria-label="Footer">
                    <Link href="/#how-it-works">How it works</Link>
                    <Link href="/#pricing">Pricing</Link>
                    <Link href="/#questions">Good to know</Link>
                    <Link href="/exams">All exams</Link>
                    <Link href="/support">Support</Link>
                    <Link href="/privacy">Privacy</Link>
                    <Link href="/terms">Terms</Link>
                    <Link href="/refund-policy">Refunds</Link>
                </nav>
                <p>
                    Prepared to stored rules.
                    <br />
                    Final acceptance rests with your exam authority.
                </p>
            </div>
        </footer>
    );
}
