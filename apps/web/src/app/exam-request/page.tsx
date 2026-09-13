import type { Metadata } from "next";
import Link from "next/link";
import { SiteHeader } from "../../components/site-header";
import { SiteFooter } from "../../components/site-footer";
import { RequestForm } from "../../components/request-form";
import { ExamSearch } from "../../components/exam-search";
import { Reveal } from "../../components/euk/reveal";
import {
    Chevron,
    EnvelopeDrawing,
    ListDrawing,
    NoticeDrawing,
} from "../../components/euk/doodles";
import { loadSearchIndex } from "../../lib/catalogue.server";
import { rankEntries } from "../../lib/search-rank";
import type { SearchEntry } from "../../lib/types";

export const metadata: Metadata = {
    title: "Request an examination",
    description:
        "Your examination isn’t on examuploadkit yet? Tell us which one and leave your email. We read its published upload rules, prepare to them, and write to you when it’s ready.",
    alternates: { canonical: "/exam-request" },
};

/**
 * Where a search that found nothing lands.
 *
 * The candidate arrives having just learned we do not have their examination,
 * usually close to a deadline. The page has three jobs, in this order: say so
 * plainly, check the search didn't simply miss it under another spelling, and
 * take their request in under a minute. What happens after they ask is told
 * underneath, with no promised date, because there isn't one to promise.
 */

/** A near match must be at least a word-start hit to be worth suggesting. */
const NEAR_MATCH = 45;

/**
 * Why a listed examination can't be prepared yet, in the candidate's terms.
 * Built from the catalogue's own record, never a generic "coming soon".
 */
function whyNotYet(entry: SearchEntry): string {
    const record = entry.unavailable;
    if (record?.reason === "live capture only") {
        return "Its portal photographs you itself, so there is no photograph for us to prepare.";
    }
    const parts = (record?.detail ?? "").split(/\s+and\s+/);
    if (
        record?.reason === "incomplete evidence" &&
        parts.length > 0 &&
        parts.every((part) => /^no\s+\S/.test(part))
    ) {
        const missing = parts
            .map((part) => `the ${part.replace(/^no\s+/, "")}`)
            .join(" or ");
        return `Its published notice doesn’t give ${missing}, and we don’t prepare to a rule we would have to guess.`;
    }
    return "We haven’t confirmed its published rules yet, and we don’t prepare to a rule we would have to guess.";
}

const AFTER = [
    {
        Drawing: ListDrawing,
        title: "It goes on the list.",
        body: "We take on examinations in order of how many candidates apply to them, so the largest come first.",
    },
    {
        Drawing: NoticeDrawing,
        title: "We read its notice.",
        body: "Photograph, signature and document rules come from the notice the examination published. Where the notice leaves a size or a format out, we don’t fill the gap with a guess.",
    },
    {
        Drawing: EnvelopeDrawing,
        title: "We write to you, once.",
        body: "When it’s ready, you get one email with the link. Nothing else goes to that address, and your request is deleted after 30 days whether it’s ready or not.",
    },
];

export default async function ExamRequest({
    searchParams,
}: {
    searchParams: Promise<{ exam?: string | string[] }>;
}) {
    const { exam } = await searchParams;
    const asked = typeof exam === "string" ? exam.trim().slice(0, 200) : "";
    const { exams, unavailable } = await loadSearchIndex();

    const nearby = asked
        ? rankEntries(exams, asked)
              .filter((row) => row.score >= NEAR_MATCH)
              .slice(0, 3)
        : [];
    // Only an exact name or alias counts as already here. A prefix like "ssc"
    // matches dozens of examinations and proves nothing.
    const found = nearby[0] && nearby[0].score >= 100 ? nearby[0].entry : null;
    const others = found ? nearby.slice(1) : nearby;
    const listed = asked && !found
        ? rankEntries(unavailable, asked)
              .filter((row) => row.score >= NEAR_MATCH)
              .slice(0, 2)
        : [];

    return (
        <>
            <SiteHeader />
            <main id="main-content" className="euk euk-request">
                <section className="euk-request-top">
                    <div className="euk-wrap euk-request-grid">
                        <div className="euk-request-copy">
                            {asked && (
                                <p className="euk-asked">
                                    <span className="euk-asked-query">
                                        <svg
                                            viewBox="0 0 24 24"
                                            fill="none"
                                            stroke="currentColor"
                                            strokeWidth="2.2"
                                            strokeLinecap="round"
                                            aria-hidden="true"
                                        >
                                            <circle cx="11" cy="11" r="7" />
                                            <path d="m20.5 20.5-4.2-4.2" />
                                        </svg>
                                        <span>
                                            <span className="sr-only">
                                                You searched for{" "}
                                            </span>
                                            {asked}
                                        </span>
                                    </span>
                                    <span
                                        className={`euk-asked-stamp${found ? " euk-asked-stamp--ok" : ""}`}
                                    >
                                        {found ? "Already here" : "Not here yet"}
                                    </span>
                                </p>
                            )}

                            {found ? (
                                <>
                                    <h1 className="euk-display euk-request-title">
                                        Good news.
                                        <br />
                                        It&rsquo;s{" "}
                                        <span className="euk-mark">
                                            already here.
                                        </span>
                                    </h1>
                                    <p className="euk-lede">
                                        We prepare {found.prepares} file
                                        {found.prepares === 1 ? "" : "s"} for{" "}
                                        <strong className="euk-request-name">
                                            {found.name}
                                        </strong>
                                        , set by {found.body}. Open it, add
                                        your photograph, and we prepare the
                                        rest.
                                    </p>
                                    <Link
                                        href={`/exam/${found.id}`}
                                        className="primary-button euk-request-open"
                                    >
                                        Go to its upload kit
                                    </Link>
                                    <p className="euk-request-else">
                                        If you meant a different examination,
                                        put that one on our list instead.
                                    </p>
                                </>
                            ) : (
                                <>
                                    <h1 className="euk-display euk-request-title">
                                        {asked
                                            ? "We don’t have it yet."
                                            : "Missing an examination?"}
                                        <br />
                                        Put it on{" "}
                                        <span className="euk-mark">our list.</span>
                                    </h1>
                                    <p className="euk-lede">
                                        {asked ? (
                                            <>
                                                We haven&rsquo;t prepared files
                                                for{" "}
                                                <strong className="euk-request-name">
                                                    {asked}
                                                </strong>{" "}
                                                so far. Tell us you need it and
                                                it goes on our list. We read its
                                                published upload rules, prepare
                                                to them, and email you when
                                                it&rsquo;s ready.
                                            </>
                                        ) : (
                                            <>
                                                We prepare files for{" "}
                                                {exams.length} examinations so
                                                far, and add more as we read
                                                their published rules. Tell us
                                                which one you need and
                                                we&rsquo;ll email you when
                                                it&rsquo;s ready.
                                            </>
                                        )}
                                    </p>
                                </>
                            )}

                            {others.length > 0 && (
                                <div className="euk-nearby">
                                    <p className="euk-nearby-title">
                                        {found
                                            ? "Or one of these."
                                            : "Before you ask, one of these might be the one you mean."}
                                    </p>
                                    <ul>
                                        {others.map(({ entry }) => (
                                            <li key={entry.id}>
                                                <Link href={`/exam/${entry.id}`}>
                                                    <span className="min-w-0">
                                                        <span className="euk-nearby-name">
                                                            {entry.name}
                                                        </span>
                                                        <span className="euk-nearby-meta">
                                                            {entry.body} ·{" "}
                                                            {entry.prepares} file
                                                            {entry.prepares === 1
                                                                ? ""
                                                                : "s"}{" "}
                                                            prepared
                                                        </span>
                                                    </span>
                                                    <Chevron className="euk-chevron--end" />
                                                </Link>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {listed.map(({ entry }) => (
                                <div key={entry.name} className="euk-listed">
                                    <p className="euk-listed-name">
                                        {entry.name} is already on our list.
                                    </p>
                                    <p>{whyNotYet(entry)}</p>
                                    <p>
                                        Ask anyway, and you&rsquo;ll hear from
                                        us when that changes.
                                    </p>
                                </div>
                            ))}
                        </div>

                        <div className="euk-request-slip">
                            <RequestForm
                                kind="exam"
                                initialExam={asked}
                                examCount={exams.length}
                            />
                        </div>

                        <div className="euk-request-search">
                            <p>
                                Or search again. Short forms work too, like SSC
                                CGL or IBPS PO.
                            </p>
                            <ExamSearch exams={exams} unavailable={unavailable} />
                        </div>
                    </div>
                </section>

                <section
                    className="euk-section euk-section--alt"
                    aria-labelledby="after-you-ask"
                >
                    <div className="euk-wrap">
                        <h2 id="after-you-ask" className="euk-display euk-h2">
                            What happens
                            <br />
                            after you ask.
                        </h2>
                        <ol className="euk-after">
                            {AFTER.map(({ Drawing, title, body }, index) => (
                                <li key={title} className="euk-after-step">
                                    <Reveal delay={index * 120}>
                                        <div className="euk-after-head">
                                            <Drawing className="euk-after-drawing" />
                                            <h3>{title}</h3>
                                        </div>
                                        <p>{body}</p>
                                    </Reveal>
                                </li>
                            ))}
                        </ol>
                    </div>
                </section>
            </main>
            <SiteFooter />
        </>
    );
}
