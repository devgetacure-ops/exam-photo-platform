"use client";

import { useEffect, useState, type ReactNode, type RefObject } from "react";
import { factAttribution, type ExamFact } from "./exam-facts";

/**
 * The wait between paying and receiving.
 *
 * A rubber stamp hovers over the application form, inked and ready, and does
 * not press. Nothing here may say PAID: this screen shows while Razorpay's
 * window is open and while the payment is unconfirmed, and a candidate who
 * sees "PAID" before we know it is true has been told something false. The
 * stamp lands only on the success screen, once the server has released the
 * files. A Pause stops it along with the tips.
 *
 * Beside it, the examination's own facts, one every seven seconds. The wait
 * is often a few seconds, sometimes longer; either way the candidate reads
 * something true about their examination instead of watching a spinner.
 *
 * Motion is transform and opacity on a handful of SVG groups, nothing that
 * lays out or repaints the page. Reduced motion removes the press and the
 * rotation and keeps the page still.
 */
export function PaymentScene({
    examName,
    facts,
    title,
    note,
    headingRef,
    children,
}: {
    examName: string;
    facts: ExamFact[];
    title: string;
    note: string;
    headingRef: RefObject<HTMLHeadingElement | null>;
    children?: ReactNode;
}) {
    const [index, setIndex] = useState(0);
    const [paused, setPaused] = useState(false);

    useEffect(() => {
        if (
            paused ||
            facts.length < 2 ||
            window.matchMedia("(prefers-reduced-motion: reduce)").matches
        )
            return;
        const timer = setInterval(
            () => setIndex((value) => (value + 1) % facts.length),
            7000,
        );
        return () => clearInterval(timer);
    }, [paused, facts.length]);

    const fact = facts.length ? facts[index % facts.length] : null;

    return (
        <section
            className="euk-pay"
            data-paused={paused}
            aria-labelledby="pay-title"
        >
            <div className="euk-pay-art" aria-hidden="true">
                <svg
                    viewBox="0 0 200 170"
                    className="euk-pay-svg"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                >
                    <path className="euk-pay-sheet" d="M28 78 H 172 V 162 H 28 Z" />
                    <path d="M44 96 H 94 M44 110 H 88 M44 124 H 96 M44 138 H 82 M44 150 H 70" />
                    <ellipse className="euk-pay-shadow" cx="132" cy="100" rx="30" ry="5" />
                    <g className="euk-pay-stamp">
                        <circle cx="132" cy="14" r="10" />
                        <path d="M126 24 V 42 H 138 V 24" />
                        <path d="M108 42 H 156 V 58 H 108 Z" />
                        <path className="euk-pay-pad" d="M110 58 H 154 V 64 H 110 Z" />
                    </g>
                </svg>
            </div>

            <div className="euk-pay-copy">
                <h2
                    id="pay-title"
                    ref={headingRef}
                    tabIndex={-1}
                    className="euk-display euk-pay-title"
                >
                    {title}
                </h2>
                <p className="euk-pay-note" role="status">
                    {note}
                </p>
                <div className="euk-pay-dots" aria-hidden="true">
                    <span />
                    <span />
                    <span />
                </div>
                {children}

                {fact && (
                    <aside
                        className="euk-pay-tip"
                        aria-label={`Worth knowing about ${examName}`}
                    >
                        <div className="euk-pay-tip-head">
                            <p>While it confirms, worth knowing</p>
                            <button
                                type="button"
                                className="euk-pay-tip-pause"
                                aria-pressed={paused}
                                onClick={() => setPaused((value) => !value)}
                            >
                                {paused ? "Resume" : "Pause"}
                            </button>
                        </div>
                        <p key={index} className="euk-pay-tip-text">
                            {fact.text}
                        </p>
                        {/* Named, not linked: a link here would invite a
                            candidate away from a payment still confirming. */}
                        <p className="euk-pay-tip-source">{factAttribution(fact)}</p>
                    </aside>
                )}
            </div>
        </section>
    );
}
