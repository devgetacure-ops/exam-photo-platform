import { ExamDeadline } from "../hot/exam-deadline";
import { todayKey } from "../../lib/deadlines";
import Link from "next/link";
import type { ExamDetail } from "../../lib/types";
import type { LiveCaptureStance } from "../../lib/appearance-rules";
import { isOurs } from "../../lib/requirement-support";
import { COPY, type Locale } from "../../lib/i18n";
import { ExamAnswer } from "./exam-answer";
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

function lede(total: number, ours: number, locale: Locale): string {
    if (locale === "hi") return ledeHindi(total, ours);
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

function ledeHindi(total: number, ours: number): string {
    if (total === 0) {
        return "यह आवेदन किन फ़ाइलों की माँग करता है, यह हम अभी पढ़ रहे हैं, इसलिए अभी तैयार करने को कुछ नहीं है।";
    }
    const files = total === 1 ? "एक फ़ाइल" : `${total} फ़ाइलें`;
    if (ours === total) {
        return total === 1
            ? "इस आवेदन में एक फ़ाइल चाहिए, और उसे हम तैयार करते हैं।"
            : `इस आवेदन में ${files} चाहिए। हम सभी तैयार करते हैं।`;
    }
    if (ours === 0) {
        return `इस आवेदन में ${files} चाहिए, पर इनमें से कोई भी हम अभी तैयार नहीं कर सकते। हर एक नीचे समझाई गई है।`;
    }
    const rest = total - ours;
    return `इस आवेदन में ${files} चाहिए। ${ours} हम तैयार करते हैं; बाकी ${rest} आपको खुद करनी होंगी, जो नीचे समझाई गई हैं।`;
}

export function ExamHero({
    exam,
    facts,
    liveCapture,
    locale = "en",
}: {
    exam: ExamDetail;
    facts: ExamFact[];
    liveCapture: LiveCaptureStance;
    locale?: Locale;
}) {
    const copy = COPY[locale];
    const requirements = exam.requirements ?? [];
    const ours = requirements.filter(isOurs);
    const groups = new Map<string, number>();
    for (const r of ours) {
        groups.set(r.requirement_type, (groups.get(r.requirement_type) ?? 0) + 1);
    }

    return (
        <section className="euk-exam-hero" aria-labelledby="exam-title">
            <div
                className={`euk-wrap euk-exam-hero-grid${facts.length && locale === "en" ? "" : " euk-exam-hero-grid--solo"}`}
            >
                <div className="min-w-0">
                    <p className="euk-exam-meta">
                        {copy.setBy(exam.conducting_body)}
                        <Link
                            className="euk-exam-lang"
                            href={locale === "hi" ? `/exam/${exam.exam_id}` : `/hi/exam/${exam.exam_id}`}
                            hrefLang={locale === "hi" ? "en" : "hi"}
                            lang={locale === "hi" ? "en" : "hi"}
                        >
                            {locale === "hi" ? "Read in English" : "हिंदी में पढ़ें"}
                        </Link>
                    </p>
                    <h1 id="exam-title" className="euk-display euk-exam-title">
                        {exam.exam_name}
                    </h1>
                    {/* DEC-135: application dates, when the list has them. */}
                    <ExamDeadline examId={exam.exam_id} builtOn={todayKey()} locale={locale} />
                    <p className="euk-exam-lede">
                        {lede(requirements.length, ours.length, locale)}
                    </p>
                    <ExamAnswer exam={exam} locale={locale} />
                    {groups.size > 0 && (
                        <ul className="euk-exam-files" aria-label="Files we prepare for it">
                            {[...groups].map(([type, count]) => {
                                const [one, many] = copy.fileNames[type] ?? copy.fileNames.other;
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
                            {locale === "hi"
                                ? "यह परीक्षा पोर्टल पर आपकी फ़ोटो भी खींचती है। यह यहाँ अपलोड की जाने वाली फ़ोटो के अलावा है, उसकी जगह नहीं।"
                                : "This examination also photographs you on the portal. That is in addition to the photograph you upload here, not instead of it."}
                        </p>
                    )}
                    {liveCapture === "instead" && (
                        <p className="euk-exam-live">
                            {locale === "hi"
                                ? "यह परीक्षा आपकी फ़ोटो खुद खींचती है, इसलिए अपलोड करने के लिए कोई फ़ोटो नहीं है।"
                                : "This examination photographs you itself, so there is no photograph to upload."}
                        </p>
                    )}
                </div>
                {facts.length > 0 && locale === "en" && (
                    <div className="euk-exam-tip">
                        <ExamFacts facts={facts} examName={exam.exam_name} />
                    </div>
                )}
            </div>
        </section>
    );
}
