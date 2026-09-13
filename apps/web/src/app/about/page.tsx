import type { Metadata } from "next";

import { HomeStory } from "../../components/home-story";
import { SiteFooter } from "../../components/site-footer";
import { SiteHeader } from "../../components/site-header";
import { loadSearchIndex } from "../../lib/catalogue.server";

export const metadata: Metadata = {
    title: "How it works and what it costs",
    description:
        "What we prepare, how, what it costs, and the decisions behind it: your face is never changed, no rule is guessed, and your files are deleted.",
    // The same sections are on the landing page, which is the page to rank.
    robots: { index: false, follow: true },
    alternates: { canonical: "/" },
};

/**
 * The long argument, one link from the phone home.
 *
 * A phone's home is kept short (the owner's call) and this is where the rest
 * went. On a desktop the same sections already follow the hero, so the page
 * exists for the phone and says nothing the landing page does not.
 */
export default async function About() {
    const { exams } = await loadSearchIndex();

    return (
        <div className="euk euk-about">
            <SiteHeader />
            <main id="main-content">
                <section className="euk-about-top">
                    <div className="euk-wrap">
                        <h1 className="euk-display euk-about-title">
                            How it works, what it costs, and why it exists.
                        </h1>
                    </div>
                </section>
                <HomeStory examCount={exams.length} />
            </main>
            <SiteFooter />
        </div>
    );
}
