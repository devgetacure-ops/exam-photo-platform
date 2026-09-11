import Link from "next/link";
import { SiteHeader } from "../components/site-header";
import { SiteFooter } from "../components/site-footer";
export default function NotFound() {
    return (
        <>
            <SiteHeader />
            <main className="euk content-page state-page" id="main-content">
                <div className="paper-symbol" aria-hidden="true">
                    ↪
                </div>
                <h1>
                    A small detour.
                    <br />
                    Your application can wait here.
                </h1>
                <p>
                    We couldn’t find that page. Let’s get you back to the right
                    exam.
                </p>
                <Link className="primary-button" href="/exams">
                    Find your exam ↗
                </Link>
                <Link className="quiet-link" href="/exam-request">
                    Request a missing exam
                </Link>
            </main>
            <SiteFooter />
        </>
    );
}
