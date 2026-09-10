import Link from "next/link";
import { loadSearchIndex } from "../../lib/catalogue.server";
import { ExamSearch } from "../../components/exam-search";
import { SiteHeader } from "../../components/site-header";
import { SiteFooter } from "../../components/site-footer";

export const metadata = {
    title: "Find your exam · UploadReady",
    description:
        "Browse exam upload requirements, signatures, photographs and documents with their sources.",
};
export default async function ExamsPage() {
    const { exams, unavailable } = await loadSearchIndex();
    return (
        <>
            <SiteHeader />
            <main className="content-page" id="main-content">
                <div className="content-intro">
                    <h1>
                        Your exam.
                        <br />
                        <span>Your starting point.</span>
                    </h1>
                    <p>
                        Browse {exams.length} examinations. Each checklist
                        separates the files we prepare from the steps you
                        complete with your exam authority.
                    </p>
                    <ExamSearch exams={exams} unavailable={unavailable} />
                </div>
                <div className="exam-directory">
                    {exams.map((exam) => (
                        <Link href={`/exam/${exam.id}`} key={exam.id}>
                            <div>
                                <h2>{exam.name}</h2>
                                <p>
                                    {exam.body} · {exam.year}
                                </p>
                            </div>
                            <span>{exam.prepares} files we prepare ↗</span>
                        </Link>
                    ))}
                </div>
                <div className="support-invitation">
                    <h2>Not on the list?</h2>
                    <p>
                        Tell us which exam you need. We’ll record it for
                        research.
                    </p>
                    <Link className="secondary-button" href="/exam-request">
                        Request an exam ↗
                    </Link>
                </div>
            </main>
            <SiteFooter />
        </>
    );
}
