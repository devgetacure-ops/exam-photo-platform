"use client";

import "./system.css";
import "./app.css";
import "./states.css";
import { StatePage, TornPageDrawing } from "../components/state-page";

/**
 * The last line: the root layout itself failed, so nothing it provides is
 * here, no header, no footer, no fonts. This page brings its own document and
 * its own styles, and still answers the first question a candidate has.
 */
export default function GlobalError({
    error,
    unstable_retry,
}: {
    error: Error & { digest?: string };
    unstable_retry: () => void;
}) {
    return (
        <html lang="en" data-theme="light">
            <body>
                <title>Something broke · ExamUploadKit</title>
                <StatePage
                    art={<TornPageDrawing />}
                    title="The site hit a problem loading."
                    mark="Your kit is still safe."
                    lede="The files you prepared are still in this browser, and still with us until their deletion time. Try again in a moment."
                >
                    <div className="euk-state-actions">
                        <button
                            type="button"
                            className="primary-button"
                            onClick={() => unstable_retry()}
                        >
                            Try again
                        </button>
                        {/* A plain anchor: client navigation may be what failed. */}
                        {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
                        <a className="euk-link" href="/">
                            Go to the home page
                        </a>
                    </div>
                    {error.digest && (
                        <p className="euk-state-ref">
                            Reference for support: <span>{error.digest}</span>
                        </p>
                    )}
                </StatePage>
            </body>
        </html>
    );
}
