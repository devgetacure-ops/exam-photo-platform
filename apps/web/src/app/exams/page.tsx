import Link from "next/link";
import { loadSearchIndex } from "../../lib/catalogue.server";
import { ExamSearch } from "../../components/exam-search";
import { SiteHeader } from "../../components/site-header";
import { SiteFooter } from "../../components/site-footer";
import { Chevron } from "../../components/euk/doodles";
import { JsonLd } from "../../components/json-ld";
import { absoluteUrl, breadcrumbs, pageMetadata } from "../../lib/site";

export async function generateMetadata() {
    const { exams } = await loadSearchIndex();
    return pageMetadata({
        title: `Photo and signature size for all ${exams.length} exams, A to Z`,
        description:
            "Every examination we prepare upload files for, A to Z: SSC, UPSC, banking, railways, police, teaching, state commissions and entrances, with the photograph, signature and documents each one asks for.",
        path: "/exams",
    });
}

/**
 * The directory has to stay usable as the catalogue grows, and it is already
 * at 132.
 *
 * Grouping by conducting body was the obvious move and is the wrong one: the
 * tail is long, so it produces roughly sixty groups, most of them holding a
 * single examination. That is harder to scan than the flat list it replaced.
 *
 * A–Z with a jump bar is the pattern that holds at this size and keeps holding
 * at five hundred. It is set like the index at the back of a book: the letter
 * large in the margin, the entries beside it. Entirely server-rendered anchors,
 * so it works with JavaScript off and gives the crawler every examination as
 * a real link from one page.
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
            <SiteHeader takesOverFrom="directory-search" />
            <main className="euk euk-directory" id="main-content">
                <JsonLd
                    data={{
                        "@context": "https://schema.org",
                        "@type": "ItemList",
                        name: "Examinations",
                        numberOfItems: exams.length,
                        itemListElement: [...exams]
                            .sort((a, b) => a.name.localeCompare(b.name))
                            .map((exam, index) => ({
                                "@type": "ListItem",
                                position: index + 1,
                                name: exam.name,
                                url: absoluteUrl(`/exam/${exam.id}`),
                            })),
                    }}
                />
                <JsonLd
                    data={breadcrumbs([
                        { name: "Home", path: "/" },
                        { name: "All examinations", path: "/exams" },
                    ])}
                />
                <section className="euk-directory-top">
                    <div className="euk-wrap">
                        <h1 className="euk-display euk-directory-title">
                            Your examination,
                            <br />
                            <span className="euk-mark">and every file it asks for.</span>
                        </h1>
                        <p className="euk-lede">
                            {exams.length} examinations, A to Z. Each one opens on
                            the files we prepare and the steps you take yourself.
                        </p>
                        <div className="euk-directory-search" id="directory-search">
                            <ExamSearch
                                exams={exams}
                                unavailable={unavailable}
                                showBrowseLink={false}
                            />
                        </div>
                    </div>
                </section>

                <nav aria-label="Jump to a letter" className="euk-az">
                    <div className="euk-wrap euk-az-row">
                        {letters.map((letter) => (
                            <Link key={letter} href={`#letter-${letter}`}>
                                {letter}
                            </Link>
                        ))}
                    </div>
                </nav>

                <div className="euk-directory-index">
                <div className="euk-wrap">
                    {letters.map((letter) => (
                        <section
                            key={letter}
                            id={`letter-${letter}`}
                            className="euk-letter"
                            aria-labelledby={`letter-${letter}-title`}
                        >
                            <h2 id={`letter-${letter}-title`} className="euk-display euk-letter-mark">
                                {letter}
                            </h2>
                            <ul className="euk-letter-list">
                                {groups.get(letter)!.map((exam) => (
                                    <li key={exam.id}>
                                        <Link href={`/exam/${exam.id}`} className="euk-dir-item">
                                            <span className="min-w-0">
                                                <span className="euk-dir-name">{exam.name}</span>
                                                <span className="euk-dir-meta">
                                                    {exam.body}
                                                    {exam.year ? ` · ${exam.year}` : ""}
                                                </span>
                                            </span>
                                            <span className="euk-dir-count">
                                                {exam.prepares === 0
                                                    ? "Guidance only"
                                                    : `${exam.prepares} file${exam.prepares === 1 ? "" : "s"}`}
                                            </span>
                                        </Link>
                                    </li>
                                ))}
                            </ul>
                        </section>
                    ))}

                    <div className="euk-dir-invite">
                        <div className="min-w-0">
                            <h2 className="euk-display">Not on the list?</h2>
                            <p>
                                Tell us which examination you need. It goes on our
                                list, and we write to you when it&rsquo;s ready.
                            </p>
                        </div>
                        <Link className="primary-button euk-dir-invite-link" href="/exam-request">
                            Ask us to add it
                            <Chevron />
                        </Link>
                    </div>
                </div>
                </div>
            </main>
            <SiteFooter />
        </>
    );
}
