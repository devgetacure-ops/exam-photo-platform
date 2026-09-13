import Link from "next/link";
import { ExamSearch } from "../components/exam-search";
import { HomeStory } from "../components/home-story";
import { PhoneHome } from "../components/m/home";
import { HomeAction } from "../components/m/home-actions";
import { SiteFooter } from "../components/site-footer";
import { SiteHeader } from "../components/site-header";
import { loadSearchIndex } from "../lib/catalogue.server";
import { TOP_EXAMS } from "../lib/top-exams";
import type { Metadata } from "next";
import { JsonLd } from "../components/json-ld";
import { rupees, tier } from "../lib/kit-pricing";
import { ORGANIZATION_ID, SITE_URL, pageMetadata } from "../lib/site";

/**
 * The landing page, in the order the brief sets: the hero, then what we do,
 * how we do it, the problem, why we built it, pricing, and our story.
 *
 * Everything below the hero reveals as it scrolls in. The hero does not: it is
 * the largest contentful paint on a slow phone, and holding it back for an
 * animation would cost the one metric that decides whether a candidate stays.
 *
 * A phone gets a different home (`components/m/home.tsx`): short, the search
 * and the before-and-after, with this long argument moved to `/about`. Both
 * are in the document; which one shows is decided by width alone, so every
 * page stays statically rendered.
 */

export async function generateMetadata(): Promise<Metadata> {
    const { exams } = await loadSearchIndex();
    return pageMetadata({
        title: `Exam photo and signature resizer for ${exams.length} Indian exams | examuploadkit`,
        description: `Your photograph, signature, thumb impression and documents at the exact size, KB and format your examination publishes: SSC, UPSC, IBPS, NEET, JEE and more. ${rupees(tier(1))} a file, no account, previewed before you pay.`,
        path: "/",
    });
}

const OFFERS = [
    { name: "One file", files: 1 },
    { name: "Two files", files: 2 },
    { name: "Three files or more", files: 3 },
];

export default async function Home() {
    const { exams, unavailable } = await loadSearchIndex();

    // Shortcuts under the hero. An id that has left the catalogue drops out
    // here rather than shipping as a link to nothing.
    const shortcuts = TOP_EXAMS.map((pick) => {
        const exam = exams.find((row) => row.id === pick.id);
        return exam ? { ...pick, name: exam.name } : null;
    }).filter((row): row is { id: string; label: string; name: string } => row !== null);

    return (
        <div className="euk euk-home">
            <JsonLd
                data={{
                    "@context": "https://schema.org",
                    "@type": "Service",
                    name: "Exam upload file preparation",
                    serviceType:
                        "Photograph, signature, thumb impression and document preparation for examination applications",
                    provider: { "@id": ORGANIZATION_ID },
                    areaServed: { "@type": "Country", name: "India" },
                    url: SITE_URL,
                    offers: OFFERS.map((offer) => ({
                        "@type": "Offer",
                        name: offer.name,
                        price: String(tier(offer.files) / 100),
                        priceCurrency: "INR",
                    })),
                }}
            />
            <SiteHeader takesOverFrom="hero-search" />
            <main id="main-content">
                <PhoneHome examCount={exams.length} shortcuts={shortcuts} />

                {/* ---- hero ------------------------------------------------ */}
                <section className="euk-hero">
                    <div className="euk-wrap">
                        <h1 className="euk-display euk-hero-title">
                            You prepare for the exam.
                            <br />
                            We&rsquo;ll prepare{" "}
                            <span className="euk-mark">the files.</span>
                        </h1>
                        <p className="euk-hero-sub">
                            Your photograph, signature, thumb impression, declaration and certificates. Each one made to the rules your examination published.
                        </p>
                        <div className="euk-hero-search" id="hero-search">
                            <ExamSearch exams={exams} unavailable={unavailable} />
                        </div>
                        <p className="euk-hero-facts">
                            <span>No account</span>
                            <span>From ₹3, PDF work free</span>
                            <Link href="/exam-request">
                                Not on the list? Tell us which one
                            </Link>
                        </p>

                        {shortcuts.length > 0 && (
                            <div className="euk-jumps">
                                <p className="euk-jumps-lead">Straight to one of these</p>
                                <ul>
                                    {shortcuts.map((exam) => (
                                        <li key={exam.id}>
                                            <Link href={`/exam/${exam.id}`}>
                                                {exam.label}
                                                <span className="sr-only"> — {exam.name}</span>
                                            </Link>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </section>

                <HomeStory examCount={exams.length} />
            </main>
            <SiteFooter />
            {/* Last in the document, so its spacer is the document's end. */}
            <HomeAction />
        </div>
    );
}
