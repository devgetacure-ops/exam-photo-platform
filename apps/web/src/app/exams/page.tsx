import Link from "next/link";
import { loadSearchIndex } from "../../lib/catalogue.server";
import { ExamSearch } from "../../components/exam-search";
import { SiteHeader } from "../../components/site-header";
import { SiteFooter } from "../../components/site-footer";

export const metadata = {
    title: "Find your exam · examuploadkit",
    description:
        "Browse exam upload requirements, signatures, photographs and documents with their sources.",
};

/**
 * The directory has to stay usable as the catalogue grows, and it is already
 * at 132.
 *
 * Grouping by conducting body was the obvious move and is the wrong one: the
 * tail is long, so it produces roughly sixty groups, most of them holding a
 * single examination. That is harder to scan than the flat list it replaced.
 *
 * A–Z with a jump bar is the pattern that holds at this size and keeps holding
 * at five hundred. It is also entirely server-rendered anchors, so it works
 * with JavaScript off and gives the crawler 132 real links from one page —
 * which is the reason these pages are generated at build time at all.
 */
function initial(name: string): string {
    const first = name.trim().charAt(0).toUpperCase();
    return /[A-Z]/.test(first) ? first : "#";
}

export default async function ExamsPage() {
    const { exams, unavailable } = await loadSearchIndex();

    const groups = new Map<string, typeof exams>();
    for (const exam of [...exams].sort((a, b) => a.name.localeCompare(b.name))) {
        const key = initial(exam.name);
        const bucket = groups.get(key);
        if (bucket) bucket.push(exam);
        else groups.set(key, [exam]);
    }
    const letters = [...groups.keys()].sort();

    return (
        <>
            <SiteHeader />
            <main className="euk content-page" id="main-content">
                <div className="content-intro">
                    <h1>
                        Your exam.
                        <br />
                        <span>Your starting point.</span>
                    </h1>
                    <p>
                        All {exams.length} examinations. Each one separates the
                        files we prepare from the steps you complete with your
                        exam authority.
                    </p>
                    <ExamSearch
                        exams={exams}
                        unavailable={unavailable}
                        showBrowseLink={false}
                    />
                </div>

                <nav
                    aria-label="Jump to a letter"
                    className="flex flex-wrap gap-1.5 border-y-[3px] border-[var(--ink)] py-4"
                >
                    {letters.map((letter) => (
                        <Link
                            key={letter}
                            href={`#letter-${letter}`}
                            className="euk-label euk-lift flex h-9 w-9 items-center justify-center border-2 border-[var(--ink)] text-[12px]"
                        >
                            {letter}
                        </Link>
                    ))}
                </nav>

                {letters.map((letter) => (
                    <section key={letter} id={`letter-${letter}`}>
                        <h2 className="euk-display sticky top-0 z-10 border-b-[3px] border-[var(--ink)] bg-[var(--paper)] py-3 text-[34px]">
                            {letter}
                        </h2>
                        <ul className="grid gap-0 md:grid-cols-2 md:gap-x-10">
                            {groups.get(letter)!.map((exam) => (
                                <li
                                    key={exam.id}
                                    className="border-b-2 border-[var(--hairline)]"
                                >
                                    <Link
                                        href={`/exam/${exam.id}`}
                                        className="group flex items-baseline justify-between gap-4 py-3"
                                    >
                                        <span className="min-w-0">
                                            <span className="block text-[15px] font-medium leading-snug group-hover:underline group-hover:decoration-[var(--signal)] group-hover:underline-offset-4">
                                                {exam.name}
                                            </span>
                                            <span className="euk-label block pt-1 text-[10px] text-[var(--ink-55)]">
                                                {exam.body}
                                                {exam.year ? ` · ${exam.year}` : ""}
                                            </span>
                                        </span>
                                        <span className="euk-label shrink-0 text-[10px] text-[var(--signal-deep)]">
                                            {exam.prepares} we prepare
                                        </span>
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </section>
                ))}

                <div className="support-invitation">
                    <h2>Not on the list?</h2>
                    <p>
                        Tell us which exam you need. We&rsquo;ll record it for
                        research.
                    </p>
                    <Link className="secondary-button" href="/exam-request">
                        Request an exam ↗
                    </Link>
                </div>
            </main>
            <SiteFooter />
        </>
    );
}
