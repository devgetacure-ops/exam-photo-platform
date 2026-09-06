import Image from "next/image";
import Link from "next/link";
import { ExamSearch } from "../components/exam-search";
import { SiteHeader } from "../components/site-header";
import { loadSearchIndex } from "../lib/catalogue.server";

export default async function Home() {
    const { exams, unavailable } = await loadSearchIndex();
    const popular = [
        { label: "IBPS PO", exam: exams.find((e) => e.name.includes("IBPS CRP PO")) },
        { label: "NEET UG", exam: exams.find((e) => e.name.includes("NEET")) },
        { label: "GATE", exam: exams.find((e) => e.name.includes("GATE")) },
    ].filter((item) => item.exam);
    return (
        <main className="landing">
            <SiteHeader />
            <section className="landing-hero">
                <div className="arrival-copy">
                    <p className="eyebrow">
                        Less file fixing. More getting ahead.
                    </p>
                    <h1>
                        Your exam is a big deal.
                        <br />
                        <span>Your uploads shouldn’t be.</span>
                    </h1>
                    <p className="hero-description">
                        Photograph, signature, documents. Get the files your
                        application needs, prepared to your exam’s stored rules.
                    </p>
                    <div className="search-section">
                        <p className="search-label">
                            Which exam are you applying for?
                        </p>
                        <ExamSearch exams={exams} unavailable={unavailable} />
                        <div className="popular-exams">
                            <span>Popular</span>
                        {popular.map(({ label, exam }) => (
                            <Link key={exam!.id} href={`/exam/${exam!.id}`}>
                                {label}
                                </Link>
                            ))}
                        </div>
                    </div>
                    <div className="landing-assurance">
                        <span>₹4 a file · ₹8 the kit</span>
                        <span>No account needed</span>
                        <span>{exams.length} exams covered</span>
                    </div>
                </div>
                <div className="landing-visual">
                    <div className="sample-label">
                        One less thing on your list.
                    </div>
                    <Image
                        width={1086}
                        height={1448}
                        priority
                        src="/examples/portrait-studio.png"
                        alt="Fictional example of a clearly framed application photograph"
                        className="landing-portrait"
                    />
                    <div className="sample-spec">
                        <span>Your photograph</span>
                        <strong>Cropped. Sized. Prepared.</strong>
                    </div>
                    <p>Example only · Your exam sets the specifications</p>
                </div>
            </section>
            <section className="how-section" id="how-it-works">
                <div>
                    <p className="eyebrow">A small task, taken care of.</p>
                    <h2>
                        From “what size?”
                        <br />
                        to ready for your application.
                    </h2>
                </div>
                <ol>
                    <li>
                        <span>01</span>
                        <div>
                            <h3>Find your exam</h3>
                            <p>
                                See the files it asks for, with visual guidance
                                and sources.
                            </p>
                        </div>
                    </li>
                    <li>
                        <span>02</span>
                        <div>
                            <h3>Add your files</h3>
                            <p>
                                We handle the sizing and formatting. Review
                                anything that needs attention.
                            </p>
                        </div>
                    </li>
                    <li>
                        <span>03</span>
                        <div>
                            <h3>Review before you buy</h3>
                            <p>
                                Choose an individual file or your complete
                                prepared kit.
                            </p>
                        </div>
                    </li>
                </ol>
            </section>
            <footer className="site-footer">
                <span>UploadReady · Made for the application ahead.</span>
                <span>
                    Prepared to stored rules. Final acceptance is decided by
                    your exam authority.
                </span>
            </footer>
        </main>
    );
}
