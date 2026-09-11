"use client";
import Link from "next/link";
export default function ErrorPage({
    reset,
}: {
    error: Error;
    reset: () => void;
}) {
    return (
        <main className="euk content-page state-page" id="main-content">
            <div className="paper-symbol" aria-hidden="true">
                ↻
            </div>
            <h1>
                Let’s give that
                <br />
                another try.
            </h1>
            <p>
                This page couldn’t finish loading. You can retry or return to
                the exam catalogue.
            </p>
            <button className="primary-button" onClick={reset}>
                Try again
            </button>
            <Link className="quiet-link" href="/exams">
                Browse exams ↗
            </Link>
            <Link className="quiet-link" href="/support">
                Get help
            </Link>
        </main>
    );
}
