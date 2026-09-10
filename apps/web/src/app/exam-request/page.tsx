import Link from "next/link";
import { SiteHeader } from "../../components/site-header";
import { SiteFooter } from "../../components/site-footer";
import { RequestForm } from "../../components/request-form";

export const metadata = { title: "Request an exam · UploadReady" };
export default async function ExamRequest({
    searchParams,
}: {
    searchParams: Promise<{ exam?: string }>;
}) {
    const { exam } = await searchParams;
    return (
        <>
            <SiteHeader />
            <main className="content-page request-page" id="main-content">
                <div className="content-intro">
                    <div className="paper-symbol" aria-hidden="true">
                        ↗
                    </div>
                    <h1>
                        Let’s put your exam
                        <br />
                        <span>on the list.</span>
                    </h1>
                    <p>
                        Not every exam is ready here yet. Share its name and, if
                        you have it, the official notification. We’ll record
                        your request for research.
                    </p>
                    <p>
                        We can’t promise an addition date. Please keep following
                        your exam’s official application instructions.
                    </p>
                    <Link className="quiet-link" href="/exams">
                        Browse available exams ↗
                    </Link>
                </div>
                <RequestForm
                    kind="exam"
                    initialExam={
                        typeof exam === "string" ? exam.slice(0, 200) : ""
                    }
                />
            </main>
            <SiteFooter />
        </>
    );
}
