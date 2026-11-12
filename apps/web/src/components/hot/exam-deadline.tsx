"use client";

import Link from "next/link";

import { deadlineStatus, shortDate } from "../../lib/deadlines";
import { useToday } from "../../lib/use-today";
import { useDeadlines } from "../../lib/use-deadlines";
import { DeadlineStamp } from "./deadline-stamp";

/**
 * The application dates on an examination's own page (DEC-135): a stamp, the
 * last date and the exam date, and a link to every deadline. Nothing when
 * the examination is not on the list or its dates have all passed.
 */
export function ExamDeadline({
    examId,
    builtOn,
    locale = "en",
}: {
    examId: string;
    builtOn: string;
    locale?: "en" | "hi";
}) {
    const today = useToday(builtOn);
    const entries = useDeadlines();
    const entry = entries.find((item) => item.examId === examId);
    if (!entry) return null;
    const status = deadlineStatus(entry, today);
    if (status.state === "past") return null;
    const hi = locale === "hi";
    const date = (iso: string) => shortDate(iso, today, locale);
    // "Open · till 25 Nov" and "Extended · to 2 Dec" already carry the date.
    const lastDate =
        status.state === "open" || status.state === "extended" ? null : status.lastDate;
    return (
        <p className="euk-examdl">
            <DeadlineStamp entry={entry} today={today} locale={locale} />
            <span>
                {lastDate && (
                    <>
                        {hi ? "आख़िरी तारीख़" : "Last date"} {date(lastDate)}
                    </>
                )}
                {entry.examDate && (
                    <>
                        {lastDate ? " · " : ""}
                        {hi ? "परीक्षा" : "Exam"} {date(entry.examDate)}
                    </>
                )}
            </span>
            <Link href={hi ? "/hi/deadlines" : "/deadlines"}>{hi ? "सभी तारीख़ें" : "All deadlines"}</Link>
        </p>
    );
}
