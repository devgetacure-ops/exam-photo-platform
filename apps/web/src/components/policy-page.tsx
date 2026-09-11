import Link from "next/link";
import { SiteHeader } from "./site-header";
import { SiteFooter } from "./site-footer";

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
            <main className="euk content-page policy-page" id="main-content">
                <div className="content-intro">
                    <h1>{title}</h1>
                    <p>{intro}</p>
                </div>
                {sections.map((section) => (
                    <section key={section.title}>
                        <h2>{section.title}</h2>
                        <p>{section.text}</p>
                    </section>
                ))}
                <Link className="secondary-button" href="/support">
                    Ask a question ↗
                </Link>
            </main>
            <SiteFooter />
        </>
    );
}
