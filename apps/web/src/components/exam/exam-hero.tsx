import type { ExamDetail } from "../../lib/types";
import type { LiveCaptureStance } from "../../lib/appearance-rules";
import { isOurs } from "../../lib/kit-pricing";
import { FileTypeDrawing } from "../euk/doodles";
import { ExamFacts, type ExamFact } from "./exam-facts";

/**
 * The top of an examination's page: which examination, what it asks for, and
 * the one thing worth knowing about it.
 *
 * The tip sits beside the title rather than under the kit. It is not what the
 * candidate came for, so it never pushes the kit down; but it is the part of
 * the page no other site has, so it is set where the eye lands second.
 */

const NAMES: Record<string, [string, string]> = {
    photograph: ["Photograph", "photographs"],
    signature: ["Signature", "signatures"],
    thumb_impression: ["Thumb impression", "thumb impressions"],
    handwritten_declaration: ["Declaration", "declarations"],
    portal_declaration: ["Declaration", "declarations"],
    certificate_scan: ["Certificate", "certificates"],
    identity_document: ["ID document", "ID documents"],
    other: ["Other file", "other files"],
};

function lede(total: number, ours: number): string {
    if (total === 0) {
        return "We haven’t finished reading what this application asks for, so there is nothing to prepare yet.";
    }
    const files = `${total} file${total === 1 ? "" : "s"}`;
    if (ours === total) {
        return total === 1
            ? "This application asks for one file, and we prepare it."
            : `This application asks for ${files}. We prepare every one of them.`;
    }
    if (ours === 0) {
        return `This application asks for ${files}, and we can’t prepare any of them yet. Each one is explained below, with what the notice asks.`;
    }
    const rest = total - ours;
    return `This application asks for ${files}. We prepare ${ours}; the other ${rest} ${rest === 1 ? "is a step" : "are steps"} you take yourself, explained below.`;
}

export function ExamHero({
    exam,
    facts,
    liveCapture,
}: {
    exam: ExamDetail;
    facts: ExamFact[];
    liveCapture: LiveCaptureStance;
}) {
    const requirements = exam.requirements ?? [];
    const ours = requirements.filter(isOurs);
    const groups = new Map<string, number>();
    for (const r of ours) {
        groups.set(r.requirement_type, (groups.get(r.requirement_type) ?? 0) + 1);
    }

    return (
        <section className="euk-exam-hero" aria-labelledby="exam-title">
            <div
                className={`euk-wrap euk-exam-hero-grid${facts.length ? "" : " euk-exam-hero-grid--solo"}`}
            >
                <div className="min-w-0">
                    <p className="euk-exam-meta">Set by {exam.conducting_body}</p>
                    <h1 id="exam-title" className="euk-display euk-exam-title">
                        {exam.exam_name}
                    </h1>
                    <p className="euk-exam-lede">
                        {lede(requirements.length, ours.length)}
                    </p>
                    {groups.size > 0 && (
                        <ul className="euk-exam-files" aria-label="Files we prepare for it">
                            {[...groups].map(([type, count]) => {
                                const [one, many] = NAMES[type] ?? NAMES.other;
                                return (
                                    <li key={type}>
                                        <FileTypeDrawing type={type} />
                                        <span>{count > 1 ? `${count} ${many}` : one}</span>
                                    </li>
                                );
                            })}
                        </ul>
                    )}
                    {/*
                        Live capture changes what the candidate has to do rather
                        than how, and "the exam takes a photo too" is the
                        opposite of "so skip the upload" on the examinations
                        that want both.
                    */}
                    {liveCapture === "additional" && (
                        <p className="euk-exam-live">
                            This examination also photographs you on the portal.
                            That is in addition to the photograph you upload
                            here, not instead of it.
                        </p>
                    )}
                    {liveCapture === "instead" && (
                        <p className="euk-exam-live">
                            This examination photographs you itself, so there is
                            no photograph to upload.
                        </p>
                    )}
                </div>
                {facts.length > 0 && (
                    <div className="euk-exam-tip">
                        <ExamFacts facts={facts} examName={exam.exam_name} />
                    </div>
                )}
            </div>
        </section>
    );
}
