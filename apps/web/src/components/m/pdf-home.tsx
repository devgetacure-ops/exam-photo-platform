"use client";

import Link from "next/link";
import { useState } from "react";

import { PDF_JOBS, PDF_LIMITS } from "../../lib/pdf-work";
import { ActionBar } from "./action-bar";
import { Sheet } from "./sheet";

/**
 * The PDF work, on a phone.
 *
 * One thing here is a tool anybody can use right now: a PDF page saved as an
 * image, in the candidate's own browser. It gets its own screen, one tap
 * away. The rest of the work is real but not a tool on its own — it runs
 * alongside a file we prepare — so it is listed under exactly that heading,
 * and each row opens a sheet saying what it does and how to get it, rather
 * than a screen that would pretend to be something a candidate can start.
 */

function Chevron() {
    return (
        <svg width="9" height="15" viewBox="0 0 9 15" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M1.5 1 L7.5 7.5 L1.5 14" />
        </svg>
    );
}

export function PhonePdf() {
    const [open, setOpen] = useState<string | null>(null);
    const job = PDF_JOBS.find((item) => item.title === open);

    return (
        <section className="euk-m-only euk-mpdf" aria-labelledby="mpdf-title">
            <h1 id="mpdf-title" className="euk-display euk-mpdf-title">
                Your form wants one PDF.
            </h1>
            <p className="euk-mpdf-lede">
                Portals rarely take what you already have. One PDF of four
                certificates. An image of a page that came to you as a PDF. Under
                500 KB, named their way.
            </p>

            <p className="euk-mpdf-label">Free for anybody, right now</p>
            <Link href="/pdf/to-image" className="euk-mpdf-tool">
                <span>
                    <strong>A PDF page as an image</strong>
                    <span>Runs on your phone. Nothing is uploaded or charged.</span>
                </span>
                <Chevron />
            </Link>

            <p className="euk-mpdf-label">Free with any file we prepare</p>
            <ul className="euk-mpdf-jobs">
                {PDF_JOBS.map((item) => (
                    <li key={item.title}>
                        <button
                            type="button"
                            className="euk-mpdf-job"
                            onClick={() => setOpen(item.title)}
                        >
                            <span>{item.title}</span>
                            <Chevron />
                        </button>
                    </li>
                ))}
            </ul>

            <button type="button" className="euk-mpdf-limits" onClick={() => setOpen("limits")}>
                What this doesn&rsquo;t do
            </button>

            <p className="euk-mpdf-note">
                Files you send us are deleted within 30 minutes, or within an hour
                if you ask us to keep them. A PDF you turn into an image never
                reaches us at all.
            </p>

            <Sheet open={Boolean(job)} title={job?.title ?? ""} onClose={() => setOpen(null)}>
                {job && (
                    <div className="euk-mpdf-sheet">
                        <p>{job.body}</p>
                        <p>
                            It runs alongside the file we prepare, so it follows your
                            examination&rsquo;s own rules for the page, the byte limit
                            and the filename. One prepared file is ₹3, and the PDF work
                            comes with it.
                        </p>
                        <Link href="/exams" className="primary-button">
                            Find your examination
                        </Link>
                    </div>
                )}
            </Sheet>

            <Sheet
                open={open === "limits"}
                title="What this doesn’t do"
                onClose={() => setOpen(null)}
            >
                <div className="euk-mpdf-sheet">
                    <ul>
                        {PDF_LIMITS.map((limit) => (
                            <li key={limit}>{limit}</li>
                        ))}
                    </ul>
                    <p>Said plainly, so you don&rsquo;t spend the evening uploading in hope.</p>
                </div>
            </Sheet>
        </section>
    );
}

/** The bottom bar for /pdf. Last in the document, so its spacer is the end. */
export function PdfAction() {
    return (
        <div className="euk euk-m-only">
            <ActionBar
                note={
                    <>
                        <strong>Free</strong>
                        Nothing uploaded
                    </>
                }
            >
                <Link href="/pdf/to-image" className="primary-button">
                    Convert a PDF page
                </Link>
            </ActionBar>
        </div>
    );
}
