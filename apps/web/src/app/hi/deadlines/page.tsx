import { DeadlinesList } from "../../../components/hot/deadlines-list";
import { SiteFooter } from "../../../components/site-footer";
import { SiteHeader } from "../../../components/site-header";
import { todayKey } from "../../../lib/deadlines";
import { loadDeadlines } from "../../../lib/deadlines.server";
import { languageAlternates } from "../../../lib/i18n";
import { pageMetadata } from "../../../lib/site";

// DEC-136: re-rendered every 5 minutes, and at once after a console edit,
// so the owner's changes to records and dates reach this page.
export const revalidate = 300;

/** The deadlines page in Hindi (DEC-135). */
export function generateMetadata() {
    return pageMetadata({
        title: "परीक्षा आवेदन की आख़िरी तारीख़ें: अभी खुले और जल्द बंद होने वाले",
        description:
            "SSC, UPSC, बैंकिंग, रेलवे, शिक्षक और प्रवेश परीक्षाओं के आवेदन की आख़िरी तारीख़ें, परीक्षा की तारीख़ और बढ़ाई गई तारीख़ें। हर परीक्षा के लिए फ़ोटो और हस्ताक्षर मुफ़्त तैयार करें।",
        path: "/hi/deadlines",
        languages: languageAlternates("/deadlines"),
        locale: "hi_IN",
    });
}

export default async function HindiDeadlinesPage() {
    const deadlines = await loadDeadlines();
    return (
        <>
            <SiteHeader />
            <main className="euk euk-deadlines-page" id="main-content" lang="hi">
                <div className="euk-wrap">
                    <h1 className="euk-display euk-deadlines-title">आवेदन की आख़िरी तारीख़ें</h1>
                    <p className="euk-deadlines-lede">
                        आवेदन की आख़िरी तारीख़, बढ़ाई गई तारीख़ और परीक्षा की तारीख़। आवेदन से पहले आधिकारिक सूचना ज़रूर देखें।
                    </p>
                    <DeadlinesList builtOn={todayKey()} locale="hi" initial={deadlines} />
                </div>
            </main>
            <SiteFooter />
        </>
    );
}
