import Link from "next/link";
import { SiteHeader } from "../components/site-header";
import { SiteFooter } from "../components/site-footer";
import { ExamSearch } from "../components/exam-search";
import { MissingPageDrawing, StatePage } from "../components/state-page";
import { loadSearchIndex } from "../lib/catalogue.server";

/**
 * A page that isn't there.
 *
 * Most people who land here followed an old exam link or mistyped one, and
 * what they want is their examination, not an apology. So the page leads
 * with the search, the fastest way back, and keeps the other two ways out
 * beside it.
 */
export default async function NotFound() {
    const { exams, unavailable } = await loadSearchIndex();
    return (
        <>
            <SiteHeader />
            <StatePage
                art={<MissingPageDrawing />}
                title="This page isn’t on file."
                mark="Your examination probably is."
                lede="The link may be an old one, or a letter slipped. Search for your examination and you’re straight back."
            >
                <div className="euk-state-search">
                    <ExamSearch
                        exams={exams}
                        unavailable={unavailable}
                        showBrowseLink={false}
                    />
                </div>
                <p className="euk-state-links">
                    <Link className="euk-link" href="/exams">
                        All examinations
                    </Link>
                    <Link className="euk-link" href="/exam-request">
                        Request an examination
                    </Link>
                    <Link className="euk-link" href="/support">
                        Support
                    </Link>
                </p>
            </StatePage>
            <SiteFooter />
        </>
    );
}
