"use client";

import Link from "next/link";

import { byUrgency, deadlineStatus, isOpen, opensSoon } from "../../lib/deadlines";
import { useDeadlines } from "../../lib/use-deadlines";
import { useToday } from "../../lib/use-today";
import { DeadlineStamp } from "./deadline-stamp";

/**
 * The one most urgent deadline, under the header (DEC-135, option B).
 *
 * An open examination closing soonest; if none is open, the one opening
 * soonest. Nothing at all when the list holds neither, so the banner never
 * advertises a date that has passed.
 */
export function ClosingSoonBanner({ builtOn }: { builtOn: string }) {
    const today = useToday(builtOn);
    const entries = useDeadlines();
    const pick = [...entries]
        .filter((entry) => {
            const status = deadlineStatus(entry, today);
            return isOpen(status) || opensSoon(status);
        })
        .sort(byUrgency(today))[0];
    if (!pick) return null;
    const status = deadlineStatus(pick, today);
    const name = pick.shortName ?? pick.examName;
    return (
        <aside className="euk euk-invert euk-dbanner" aria-label="Application deadline">
            <div className="euk-wrap euk-dbanner-inner">
                <DeadlineStamp entry={pick} today={today} />
                <p className="euk-dbanner-text">
                    <strong>{name}</strong>
                    {status.state === "opening"
                        ? " applications open soon. Get your photo and signature ready."
                        : " is taking applications. Get your photo and signature ready."}
                </p>
                <Link className="euk-dbanner-go" href={`/exam/${pick.examId}`}>
                    Prepare files <span aria-hidden="true">→</span>
                </Link>
            </div>
        </aside>
    );
}
