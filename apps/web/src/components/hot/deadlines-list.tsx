"use client";

import Link from "next/link";

import {
    DEADLINES,
    byUrgency,
    deadlineStatus,
    shortDate,
    type Deadline,
    type DeadlineState,
} from "../../lib/deadlines";
import { useToday } from "../../lib/use-today";
import { DeadlineStamp } from "./deadline-stamp";

/**
 * Every deadline on the list, grouped by what it means today (DEC-135,
 * option C). Rendered on the server with the build date, so the page has its
 * content for search engines; re-grouped in the browser with the real date.
 */

const GROUPS: { id: string; states: DeadlineState[]; en: string; hi: string }[] = [
    { id: "closing", states: ["closing", "extended"], en: "Closing this week", hi: "इस हफ़्ते बंद हो रहे" },
    { id: "open", states: ["open"], en: "Open now", hi: "अभी खुले हैं" },
    { id: "opening", states: ["opening"], en: "Opening soon", hi: "जल्द खुलेंगे" },
    { id: "exam", states: ["exam-ahead"], en: "Applications closed, exam ahead", hi: "आवेदन बंद, परीक्षा आगे" },
];

export function DeadlinesList({ builtOn, locale = "en" }: { builtOn: string; locale?: "en" | "hi" }) {
    const today = useToday(builtOn);
    const hi = locale === "hi";
    const prefix = hi ? "/hi" : "";
    const sorted = [...DEADLINES].sort(byUrgency(today));
    const groups = GROUPS.map((group) => ({
        ...group,
        entries: sorted.filter((entry) => group.states.includes(deadlineStatus(entry, today).state)),
    })).filter((group) => group.entries.length > 0);

    if (groups.length === 0) {
        return (
            <p className="euk-deadlines-empty">
                {hi
                    ? "अभी सूची में कोई आने वाली तारीख़ नहीं है।"
                    : "No upcoming dates on the list right now."}
            </p>
        );
    }

    return (
        <div className="euk-deadlines">
            {groups.map((group) => (
                <section key={group.id} className="euk-deadlines-group" aria-labelledby={`dl-${group.id}`}>
                    <h2 id={`dl-${group.id}`} className="euk-label euk-deadlines-head">
                        {hi ? group.hi : group.en}
                    </h2>
                    <ul className="euk-deadlines-rows">
                        {group.entries.map((entry) => (
                            <Row key={entry.examId} entry={entry} today={today} hi={hi} prefix={prefix} />
                        ))}
                    </ul>
                </section>
            ))}
        </div>
    );
}

function Row({ entry, today, hi, prefix }: { entry: Deadline; today: string; hi: boolean; prefix: string }) {
    const locale = hi ? "hi" : "en";
    const date = (iso: string) => shortDate(iso, today, locale);
    return (
        <li className="euk-deadlines-row">
            <div className="euk-deadlines-main">
                <DeadlineStamp entry={entry} today={today} locale={locale} />
                <Link className="euk-deadlines-name" href={`${prefix}/exam/${entry.examId}`}>
                    {entry.examName}
                </Link>
                {entry.conductingBody && <span className="euk-deadlines-body">{entry.conductingBody}</span>}
            </div>
            <dl className="euk-deadlines-dates">
                {entry.opens && (
                    <div>
                        <dt>{hi ? "आवेदन शुरू" : "Applications open"}</dt>
                        <dd>{date(entry.opens)}</dd>
                    </div>
                )}
                {entry.closes && (
                    <div>
                        <dt>{hi ? "आख़िरी तारीख़" : "Last date"}</dt>
                        <dd>
                            {entry.extendedTo ? (
                                <>
                                    <s>{date(entry.closes)}</s> {date(entry.extendedTo)}{" "}
                                    <span className="euk-deadlines-ext">{hi ? "(बढ़ाई गई)" : "(extended)"}</span>
                                </>
                            ) : (
                                date(entry.closes)
                            )}
                        </dd>
                    </div>
                )}
                <div>
                    <dt>{hi ? "परीक्षा" : "Exam"}</dt>
                    <dd>
                        {entry.examDate ? date(entry.examDate) : hi ? "घोषित नहीं" : "Not announced"}
                        {entry.examDateNote ? ` · ${entry.examDateNote}` : ""}
                    </dd>
                </div>
            </dl>
            <p className="euk-deadlines-foot">
                <Link href={`${prefix}/exam/${entry.examId}`}>
                    {hi ? "फ़ोटो और हस्ताक्षर तैयार करें →" : "Prepare photo and signature →"}
                </Link>
                {entry.sourceUrl && (
                    <a href={entry.sourceUrl} target="_blank" rel="noreferrer nofollow">
                        {hi ? "स्रोत" : "Source"}
                        {entry.lastVerified ? ` · ${hi ? "जाँचा" : "checked"} ${date(entry.lastVerified)}` : ""} ↗
                    </a>
                )}
            </p>
        </li>
    );
}
