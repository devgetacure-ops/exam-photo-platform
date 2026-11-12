import { DeadlinesList } from "../../components/hot/deadlines-list";
import { JsonLd } from "../../components/json-ld";
import { SiteFooter } from "../../components/site-footer";
import { SiteHeader } from "../../components/site-header";
import { todayKey } from "../../lib/deadlines";
import { loadDeadlines } from "../../lib/deadlines.server";
import { languageAlternates } from "../../lib/i18n";
import { absoluteUrl, breadcrumbs, pageMetadata } from "../../lib/site";

// DEC-136: re-rendered every 5 minutes, and at once after a console edit,
// so the owner's changes to records and dates reach this page.
export const revalidate = 300;

/** Application deadlines, with every last date and exam date (DEC-135). */
export function generateMetadata() {
    return pageMetadata({
        title: "Exam application last dates: open now and closing soon",
        description:
            "Last dates to apply for SSC, UPSC, banking, railway, teaching and entrance exams, with exam dates and extensions. Prepare the photo and signature each one asks for, free.",
        path: "/deadlines",
        languages: languageAlternates("/deadlines"),
    });
}

export default async function DeadlinesPage() {
    const builtOn = todayKey();
    const deadlines = await loadDeadlines();
    return (
        <>
            <SiteHeader />
            <main className="euk euk-deadlines-page" id="main-content">
                <JsonLd
                    data={{
                        "@context": "https://schema.org",
                        "@type": "ItemList",
                        name: "Examination application deadlines",
                        numberOfItems: deadlines.length,
                        itemListElement: deadlines.map((entry, index) => ({
                            "@type": "ListItem",
                            position: index + 1,
                            name: entry.examName,
                            url: absoluteUrl(`/exam/${entry.examId}`),
                        })),
                    }}
                />
                <JsonLd
                    data={breadcrumbs([
                        { name: "Home", path: "/" },
                        { name: "Application deadlines", path: "/deadlines" },
                    ])}
                />
                <div className="euk-wrap">
                    <h1 className="euk-display euk-deadlines-title">Application deadlines</h1>
                    <p className="euk-deadlines-lede">
                        Last dates to apply, extensions and exam dates. Check the official notice before you apply.
                    </p>
                    <DeadlinesList builtOn={builtOn} initial={deadlines} />
                </div>
            </main>
            <SiteFooter />
        </>
    );
}
