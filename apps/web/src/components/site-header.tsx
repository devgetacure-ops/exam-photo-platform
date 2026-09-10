import Link from "next/link";
import { ThemeToggle } from "./theme-toggle";

export function SiteHeader({ mobileTitle }: { mobileTitle?: string }) {
    return (
        <header className={`site-header ${mobileTitle ? "exam-header" : ""}`}>
            {mobileTitle && (
                <Link className="mobile-back" href="/">
                    Back
                </Link>
            )}
            <Link href="/" className="wordmark" aria-label="UploadReady home">
                UploadReady<span className="brand-period">.</span>
            </Link>
            <span className="header-caption">
                Indian exam upload preparation
            </span>
            {mobileTitle && (
                <strong className="mobile-title">{mobileTitle}</strong>
            )}
            <Link className="quiet-link" href="/#how-it-works">
                {mobileTitle ? "Help" : "How it works"}
            </Link>
            {!mobileTitle && (
                <Link className="quiet-link header-pricing" href="/#pricing">
                    Pricing
                </Link>
            )}
            <ThemeToggle />
        </header>
    );
}
