"use client";

import Link from "next/link";

import { byVolume, deadlineStatus, isOpen, shortDate } from "../../lib/deadlines";
import { useDeadlines } from "../../lib/use-deadlines";
import { useToday } from "../../lib/use-today";
import { DeadlineStamp } from "./deadline-stamp";

/**
 * "Applications open now" on the home page (DEC-135, option A), and the way
 * into the full deadlines page (option C's teaser). Up to six, most urgent
 * first; a stack on a phone, a grid on a desktop, never a sideways strip.
 */
export function OpenNow({ builtOn, limit = 6 }: { builtOn: string; limit?: number }) {
    const today = useToday(builtOn);
    const entries = useDeadlines();
    const open = [...entries]
        .filter((entry) => isOpen(deadlineStatus(entry, today)))
        .sort(byVolume(today))
        .slice(0, limit);
    if (open.length === 0) return null;
    return (
        <section className="euk euk-opennow" aria-labelledby="opennow-title" data-phone-keep>
            <div className="euk-wrap">
                <h2 id="opennow-title" className="euk-display euk-opennow-title">
                    Applications open now
                </h2>
                <ul className="euk-opennow-list">
                    {open.map((entry) => {
                        const status = deadlineStatus(entry, today);
                        return (
                            <li key={entry.examId}>
                                <Link className="euk-opennow-card" href={`/exam/${entry.examId}`}>
                                    <DeadlineStamp entry={entry} today={today} />
                                    <strong className="euk-opennow-name">
                                        {entry.shortName ?? entry.examName}
                                    </strong>
                                    <span className="euk-opennow-dates">
                                        {status.state === "closing" && status.lastDate && (
                                            <>Last date {shortDate(status.lastDate, today)}</>
                                        )}
                                        {status.state === "closing" && status.lastDate && entry.examDate && " · "}
                                        {entry.examDate && <>Exam {shortDate(entry.examDate, today)}</>}
                                    </span>
                                    <span className="euk-opennow-go">
                                        Prepare files <span aria-hidden="true">→</span>
                                    </span>
                                </Link>
                            </li>
                        );
                    })}
                </ul>
                <p className="euk-opennow-more">
                    <Link href="/deadlines">All application deadlines →</Link>
                </p>
            </div>
        </section>
    );
}
