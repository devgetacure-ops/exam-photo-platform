import { SiteHeader } from "../../components/site-header";
import { SiteFooter } from "../../components/site-footer";
import { RequestForm } from "../../components/request-form";

export const metadata = { title: "A little help · UploadReady" };
export default async function SupportPage({
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
                        ↳
                    </div>
                    <h1>
                        Something not right?
                        <br />
                        <span>Start here.</span>
                    </h1>
                    <p>
                        A file issue, a payment question, a rule that needs
                        another look. Tell us what happened and keep your
                        request reference.
                    </p>
                    <details>
                        <summary>Paid, but no download?</summary>
                        <p>
                            Return to your exam in the same browser and refresh
                            your kit status. Payment confirmation may still be
                            arriving. Avoid paying again while it is pending,
                            and include the order reference in your request.
                        </p>
                    </details>
                    <details>
                        <summary>Files have expired?</summary>
                        <p>
                            Temporary files cannot be restored after deletion.
                            If you paid and did not receive your files, include
                            the order reference so delivery can be checked.
                        </p>
                    </details>
                    <p>
                        This is a private request, not a public forum. Never
                        include sensitive identity documents or payment
                        credentials.
                    </p>
                </div>
                <RequestForm
                    kind="support"
                    initialExam={
                        typeof exam === "string" ? exam.slice(0, 200) : ""
                    }
                />
            </main>
            <SiteFooter />
        </>
    );
}
