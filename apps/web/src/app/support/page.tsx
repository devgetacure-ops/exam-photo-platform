import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";
import { SiteHeader } from "../../components/site-header";
import { SiteFooter } from "../../components/site-footer";
import { RequestForm } from "../../components/request-form";
import { Note } from "../../components/euk/note";
import { ActionBar } from "../../components/m/action-bar";
import { AnswerSearch } from "../../components/m/answer-search";

export const metadata: Metadata = {
    title: "Support and grievances · examuploadkit",
    description:
        "Paid but no files, a file the portal rejected, an email that didn’t arrive. The known ways out, and a private form for anything else.",
    alternates: { canonical: "/support" },
};

/**
 * Support, redressal and requests.
 *
 * The brief asks for a forum. What a forum gives a candidate is the chance to
 * find that someone else hit the same problem and what fixed it; what it costs
 * them is posting their problem in public, and a candidate's problem is very
 * often a photograph of their own face or signature. So the page does the
 * first half in public and the second in private: every known problem is
 * answered here for anyone to read, and a case of their own goes through the
 * slip, with a reference, where nobody else sees it.
 *
 * Every answer is written against how the product actually behaves — the
 * payment confirmation wait, the deletion deadline, the download record — so
 * none of them promise a refund, a timeline or an outcome it can't keep.
 */

interface Answer {
    q: string;
    a: ReactNode;
}

const GROUPS: { title: string; answers: Answer[] }[] = [
    {
        title: "About a payment",
        answers: [
            {
                q: "I paid, but my files haven’t been released.",
                a: (
                    <>
                        <p>
                            Confirmation reaches us from the payment provider,
                            and it can land a little after the checkout window
                            closes. Go back to your examination in the same
                            browser and press <strong>Refresh status</strong>.
                        </p>
                        <p>
                            Please don&rsquo;t pay a second time while it&rsquo;s
                            confirming. If the files still aren&rsquo;t
                            released, write to us with the UPI reference or
                            payment ID from your payment app.
                        </p>
                    </>
                ),
            },
            {
                q: "Money left my account, but checkout said the payment failed.",
                a: (
                    <>
                        <p>
                            Check the transaction in your UPI or banking app
                            first. A payment that failed is reversed by your
                            bank or UPI app, on their timeline rather than ours.
                        </p>
                        <p>
                            If the app shows it as successful and you have no
                            files, write to us with its reference.
                        </p>
                    </>
                ),
            },
            {
                q: "I was charged twice.",
                a: (
                    <>
                        <p>
                            Write to us with both references and we check each
                            one against the payment record.
                        </p>
                        <p>
                            Reporting it doesn&rsquo;t issue a refund by itself.
                            A refund is confirmed once the payment provider
                            processes it, as the{" "}
                            <Link className="euk-link" href="/refund-policy">
                                refund policy
                            </Link>{" "}
                            explains.
                        </p>
                    </>
                ),
            },
        ],
    },
    {
        title: "About your files",
        answers: [
            {
                q: "My files were deleted before I downloaded them.",
                a: (
                    <>
                        <p>
                            Files are deleted within 30 minutes, or within an
                            hour if you asked us to keep them, and a deleted
                            file can&rsquo;t be brought back. That is what
                            deleting them means.
                        </p>
                        <p>
                            If you paid and never got to download, write to us
                            with the payment reference. We keep a record of
                            downloads and of emails sent, and that record is
                            what we check.
                        </p>
                    </>
                ),
            },
            {
                q: "The portal rejected a file you prepared.",
                a: (
                    <>
                        <p>
                            Tell us the examination, which file it was, and the
                            exact words of the message the portal showed. We
                            check the file against the rule we prepared it to.
                        </p>
                        <p>
                            Whether a file is accepted is always the
                            authority&rsquo;s decision. If we read a rule
                            wrong, we want to know, because every candidate
                            after you would get the same file.
                        </p>
                    </>
                ),
            },
            {
                q: "The rules on your page don’t match my notice.",
                a: (
                    <p>
                        Notices change between application cycles. Send us a
                        link to the one you&rsquo;re reading and we read it
                        again.
                    </p>
                ),
            },
            {
                q: "The email with my files didn’t arrive.",
                a: (
                    <p>
                        Look in spam and promotions first. While you wait,
                        download the files straight from the page. They stay
                        there until the deletion time it shows.
                    </p>
                ),
            },
        ],
    },
    {
        title: "Anything else",
        answers: [
            {
                q: "My examination isn’t listed.",
                a: (
                    <p>
                        Tell us which one on the{" "}
                        <Link className="euk-link" href="/exam-request">
                            request page
                        </Link>
                        , and we&rsquo;ll email you when it&rsquo;s ready.
                    </p>
                ),
            },
            {
                q: "I want my request, or the email on it, deleted.",
                a: (
                    <p>
                        Requests and the email address on them are deleted
                        after 30 days on their own. To remove one sooner, write
                        to us with its reference.
                    </p>
                ),
            },
        ],
    },
];

function Toggle() {
    return (
        <svg
            className="euk-answer-mark"
            viewBox="0 0 22 22"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.4"
            strokeLinecap="round"
            aria-hidden="true"
        >
            <rect x="1.5" y="1.5" width="19" height="19" />
            <path d="M6.5 11 H15.5" />
            <path className="euk-answer-v" d="M11 6.5 V15.5" />
        </svg>
    );
}

export default async function SupportPage({
    searchParams,
}: {
    searchParams: Promise<{ exam?: string | string[] }>;
}) {
    const { exam } = await searchParams;
    const about = typeof exam === "string" ? exam.trim().slice(0, 200) : "";

    return (
        <>
            <SiteHeader />
            <main id="main-content" className="euk euk-support">
                <section className="euk-request-top">
                    <div className="euk-wrap euk-support-grid">
                        <div className="euk-request-copy">
                            <h1 className="euk-display euk-request-title">
                                Something went wrong?{" "}
                                <br />
                                We{" "}
                                <span className="euk-mark">planned for it.</span>
                            </h1>
                            <p className="euk-lede">
                                A payment that hasn&rsquo;t confirmed, a file
                                the portal turned down, an email that
                                didn&rsquo;t come. Each of these has a known way
                                out, and it&rsquo;s written below. If yours
                                isn&rsquo;t there, write to us. It stays
                                private.
                            </p>
                            <Note className="euk-support-note">
                                Look for yours first. Most of these you can sort
                                out right now.
                            </Note>
                            <a href="#write" className="euk-link euk-jump">
                                Or write to us now
                            </a>
                            <AnswerSearch scope=".euk-support" />

                            {GROUPS.map((group) => (
                                <section
                                    key={group.title}
                                    className="euk-answers"
                                    aria-label={group.title}
                                >
                                    <h2 className="euk-answers-title">
                                        {group.title}
                                    </h2>
                                    {group.answers.map((answer) => (
                                        <details
                                            key={answer.q}
                                            className="euk-answer"
                                        >
                                            <summary>
                                                <span>{answer.q}</span>
                                                <Toggle />
                                            </summary>
                                            <div className="euk-answer-body">
                                                {answer.a}
                                            </div>
                                        </details>
                                    ))}
                                </section>
                            ))}

                            <div className="euk-escalate">
                                <h2 className="euk-display">
                                    If our reply doesn&rsquo;t settle it
                                </h2>
                                <p>
                                    Write again, quote your reference, and begin
                                    the message with the word Grievance, so it
                                    is read as one. Every reply comes by email,
                                    to the address you gave.
                                </p>
                            </div>
                        </div>

                        <div id="write" className="euk-request-slip">
                            <h2 className="euk-display euk-support-slip-title">
                                Not here?{" "}
                                <br />
                                Write to us.
                            </h2>
                            <p className="euk-support-slip-note">
                                Nothing you send is shown to anyone else.
                            </p>
                            <RequestForm kind="support" initialExam={about} />
                        </div>
                    </div>
                </section>
            </main>
            <SiteFooter />
            {/* A phone's one action here. Last in the document, so its spacer
                is the end of it. */}
            <div className="euk euk-m-only">
                <ActionBar
                    note={
                        <>
                            <strong>Private</strong>
                            Replies by email
                        </>
                    }
                >
                    <a href="#write" className="primary-button">
                        Write to us
                    </a>
                </ActionBar>
            </div>
        </>
    );
}
