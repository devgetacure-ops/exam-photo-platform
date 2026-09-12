import Link from "next/link";
import { ThemeToggle } from "./theme-toggle";
import { Wordmark } from "./euk/wordmark";
import { HeaderSearch } from "./header-search";

/**
 * One header for every route, and it stays.
 *
 * It runs the full width of the screen rather than the page's measure: the
 * wordmark sits hard left, everything you can do sits hard right, and the
 * space between them is not decoration — it is where the search goes once the
 * page's own search has scrolled away. On an examination page there is no
 * search on the page at all, so the bar carries it from the start, wearing
 * that examination's name.
 *
 * It is sticky rather than absolutely fixed: same result, and the page below
 * needs no compensating padding that could fall out of step with the bar's
 * real height.
 */
export function SiteHeader({
    /** An examination page: its name, shown in the bar and in the search. */
    mobileTitle,
    examName,
    /** Id of the page's own search, which this one takes over from. */
    takesOverFrom,
}: {
    mobileTitle?: string;
    examName?: string;
    takesOverFrom?: string;
}) {
    const onExam = Boolean(mobileTitle);

    return (
        <header className="euk euk-top">
            <div className="euk-top-row">
                <Link
                    href="/"
                    aria-label="examuploadkit home"
                    className="euk-top-mark"
                >
                    <Wordmark />
                </Link>

                <div className="euk-top-mid">
                    <HeaderSearch
                        examName={examName}
                        takesOverFrom={takesOverFrom}
                    />
                </div>

                <nav className="euk-label euk-top-nav">
                    {!onExam && (
                        <>
                            <Link href="/#how" className="hidden sm:inline">
                                How it works
                            </Link>
                            <Link href="/pdf" className="hidden md:inline">
                                PDF tools
                            </Link>
                            <Link href="/#pricing" className="hidden lg:inline">
                                Pricing
                            </Link>
                        </>
                    )}
                    <Link href="/exams" className="euk-top-exams">
                        Exams
                    </Link>
                    <ThemeToggle />
                </nav>
            </div>

            {mobileTitle && (
                <p className="euk-label euk-top-title sm:hidden">
                    {mobileTitle}
                </p>
            )}
        </header>
    );
}
