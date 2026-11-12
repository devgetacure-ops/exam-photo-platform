"use client";

import { deadlineFor, deadlineStatus, isOpen, opensSoon, todayKey } from "../../lib/deadlines";
import { useToday } from "../../lib/use-today";
import { DeadlineStamp } from "./deadline-stamp";

/**
 * A small stamp beside an examination's name wherever it is listed: search
 * results, the A to Z (DEC-135, option D). Only while applications are open
 * or about to open; otherwise nothing.
 */
export function OpenTag({ examId, builtOn }: { examId: string; builtOn?: string }) {
    const today = useToday(builtOn ?? todayKey());
    const entry = deadlineFor(examId);
    if (!entry) return null;
    const status = deadlineStatus(entry, today);
    if (!isOpen(status) && !opensSoon(status)) return null;
    return <DeadlineStamp entry={entry} today={today} small />;
}
