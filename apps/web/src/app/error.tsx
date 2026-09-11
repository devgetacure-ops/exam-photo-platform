"use client";

import Link from "next/link";
import { SiteHeader } from "../components/site-header";
import { SiteFooter } from "../components/site-footer";
import { StatePage, TornPageDrawing } from "../components/state-page";

/**
 * A page that failed to render.
 *
 * The candidate's first worry is their files, so that is answered first and
 * truthfully: a page failing to load touches neither the kit held in this
 * browser nor the files on our side, which keep their own deletion time. The
 * error's digest is shown as a reference, because it is what matches this
 * failure to the server's log if they write to support.
 */
export default function ErrorPage({
    error,
    unstable_retry,
}: {
    error: Error & { digest?: string };
    unstable_retry: () => void;
}) {
    return (
        <>
            <SiteHeader />
            <StatePage
                art={<TornPageDrawing />}
                title="Something broke on our side."
                mark="Your kit didn’t."
                lede="The files you prepared are still in this browser, and still with us until their deletion time. Try the page again. If it keeps happening, tell us what you were doing."
            >
                <div className="euk-state-actions">
                    <button
                        type="button"
                        className="primary-button"
                        onClick={() => unstable_retry()}
                    >
                        Try again
                    </button>
                    <Link className="secondary-button" href="/exams">
                        Back to examinations
                    </Link>
                    <Link className="euk-link" href="/support">
                        Tell support
                    </Link>
                </div>
                {error.digest && (
                    <p className="euk-state-ref">
                        Reference for support: <span>{error.digest}</span>
                    </p>
                )}
            </StatePage>
            <SiteFooter />
        </>
    );
}
