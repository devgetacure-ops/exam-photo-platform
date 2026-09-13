import Link from "next/link";
import { SiteHeader } from "./site-header";
import { SiteFooter } from "./site-footer";
import { PolicyTabs } from "./policy-tabs";
import { ActionBar } from "./m/action-bar";
import { PhonePolicy } from "./m/policy-phone";
import { BusinessContact } from "./business-contact";

/**
 * Privacy, terms and refunds.
 *
 * These are read by a candidate with a specific worry — what happens to my
 * photograph, will I get my money back — so the page is built for finding one
 * answer rather than reading top to bottom: the three policies are one strip
 * apart, every section is linked from a list that stays in view on a desktop,
 * and the text runs at a reading size and measure. It ends on a way to ask,
 * because a policy that doesn't answer the question should hand over to
 * someone who can.
 */

function slug(title: string): string {
    return title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-|-$/g, "");
}

export function PolicyPage({
    title,
    intro,
    sections,
}: {
    title: string;
    intro: string;
    sections: { title: string; text: string }[];
}) {
    return (
        <>
            <SiteHeader />
            <main className="euk euk-policy" id="main-content">
                <div className="euk-policy-top">
                    <div className="euk-wrap">
                        <PolicyTabs />
                        <h1 className="euk-display euk-policy-title">{title}</h1>
                        <p className="euk-lede">{intro}</p>
                    </div>
                </div>

                <div className="euk-policy-main">
                    {/* A phone reads the same sections collapsed, with a
                        search; the grid below steps aside for it. */}
                    <PhonePolicy sections={sections} after={<BusinessContact />} />
                    <div className="euk-wrap euk-policy-grid">
                        <nav className="euk-policy-toc" aria-label="On this page">
                            <p className="euk-policy-toc-title">On this page</p>
                            <ul>
                                {sections.map((section) => (
                                    <li key={section.title}>
                                        <a href={`#${slug(section.title)}`}>
                                            {section.title}
                                        </a>
                                    </li>
                                ))}
                            </ul>
                        </nav>

                        <div className="min-w-0">
                            {sections.map((section) => (
                                <section
                                    key={section.title}
                                    id={slug(section.title)}
                                    className="euk-policy-section"
                                >
                                    <h2>{section.title}</h2>
                                    <p>{section.text}</p>
                                </section>
                            ))}

                            <BusinessContact />

                            <div className="euk-policy-close">
                                <p>Not covered here, or not clear enough?</p>
                                <Link className="primary-button" href="/support">
                                    Ask us
                                </Link>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
            <SiteFooter />
            <div className="euk euk-m-only">
                <ActionBar
                    note={
                        <>
                            <strong>Not covered?</strong>
                            Ask, privately
                        </>
                    }
                >
                    <Link href="/support" className="primary-button">
                        Ask us
                    </Link>
                </ActionBar>
            </div>
        </>
    );
}
