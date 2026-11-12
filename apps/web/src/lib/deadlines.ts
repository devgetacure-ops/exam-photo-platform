/**
 * Application deadlines and what they mean today (DEC-135).
 *
 * The list is `data/deadlines.json`, written by `scripts/build_deadlines.py`
 * from the hand-edited sheet `packages/exam-rules/research/deadlines.csv`.
 * Pages are built ahead of time, so every status here is worked out again in
 * the browser from the visitor's own date: a banner built last week must not
 * still say "closes in 2 days".
 */
import data from "../data/deadlines.json";

export interface Deadline {
    examId: string;
    examName: string;
    shortName: string | null;
    conductingBody: string | null;
    opens: string | null;
    closes: string | null;
    extendedTo: string | null;
    examDate: string | null;
    examDateNote: string | null;
    sourceUrl: string | null;
    lastVerified: string | null;
    /** How many sat it in the last cycle (DEC-137): bigger exams come first. */
    candidates?: number | null;
}

export const DEADLINES: readonly Deadline[] = (data as { entries: Deadline[] }).entries;

export type DeadlineState =
    /** Registration has not opened yet. */
    | "opening"
    /** Open, more than a week to go. */
    | "open"
    /** Open, a week or less to go. */
    | "closing"
    /** Open on an extended last date. */
    | "extended"
    /** Registration over, the examination still ahead. */
    | "exam-ahead"
    /** Everything is in the past. */
    | "past";

export interface DeadlineStatus {
    state: DeadlineState;
    /** Days until the date that matters for the state: opening, last date or exam. */
    days: number | null;
    /** The last date in force: the extension if there is one. */
    lastDate: string | null;
}

const DAY = 24 * 60 * 60 * 1000;

/** A YYYY-MM-DD date as local midnight, so "today" is the visitor's day. */
function localDay(iso: string): number {
    const [y, m, d] = iso.split("-").map(Number);
    return new Date(y, m - 1, d).getTime();
}

export function todayKey(now: Date = new Date()): string {
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, "0");
    const d = String(now.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
}

export function deadlineStatus(entry: Deadline, today: string): DeadlineStatus {
    const now = localDay(today);
    const lastDate = entry.extendedTo ?? entry.closes;
    const days = (iso: string) => Math.round((localDay(iso) - now) / DAY);
    if (entry.opens && now < localDay(entry.opens)) {
        return { state: "opening", days: days(entry.opens), lastDate };
    }
    if (lastDate && now <= localDay(lastDate)) {
        const left = days(lastDate);
        if (entry.extendedTo) return { state: "extended", days: left, lastDate };
        return { state: left <= 7 ? "closing" : "open", days: left, lastDate };
    }
    if (entry.examDate && now <= localDay(entry.examDate)) {
        return { state: "exam-ahead", days: days(entry.examDate), lastDate };
    }
    return { state: "past", days: null, lastDate };
}

/** Openings further off than this are not "hot": they wait for the full list. */
export const SOON_DAYS = 30;

/** Opening within SOON_DAYS. */
export function opensSoon(status: DeadlineStatus): boolean {
    return status.state === "opening" && (status.days ?? Infinity) <= SOON_DAYS;
}

/** Taking applications today, in any form. */
export function isOpen(status: DeadlineStatus): boolean {
    return status.state === "open" || status.state === "closing" || status.state === "extended";
}

/** Most urgent first: fewest days to the last date; then opening soonest. */
export function byUrgency(today: string) {
    const rank: Record<DeadlineState, number> = {
        closing: 0,
        extended: 0,
        open: 1,
        opening: 2,
        "exam-ahead": 3,
        past: 4,
    };
    return (a: Deadline, b: Deadline): number => {
        const sa = deadlineStatus(a, today);
        const sb = deadlineStatus(b, today);
        return rank[sa.state] - rank[sb.state] || (sa.days ?? 9999) - (sb.days ?? 9999);
    };
}

/**
 * Largest first (DEC-137), most urgent among equals; an examination with no
 * figure goes after every one that has one.
 */
export function byVolume(today: string) {
    const urgency = byUrgency(today);
    return (a: Deadline, b: Deadline): number =>
        (b.candidates ?? -1) - (a.candidates ?? -1) || urgency(a, b);
}

export function deadlineFor(examId: string): Deadline | undefined {
    return DEADLINES.find((entry) => entry.examId === examId);
}

/** "25 Nov" or "25 Nov 2027", in English or Hindi. */
export function shortDate(iso: string, today: string, locale: "en" | "hi" = "en"): string {
    const date = new Date(localDay(iso));
    const sameYear = iso.slice(0, 4) === today.slice(0, 4);
    return date.toLocaleDateString(locale === "hi" ? "hi-IN" : "en-IN", {
        day: "numeric",
        month: "short",
        ...(sameYear ? {} : { year: "numeric" }),
    });
}

/** The short label a stamp carries, e.g. "Closes in 2 days". */
export function stampText(status: DeadlineStatus, today: string, locale: "en" | "hi" = "en"): string {
    const hi = locale === "hi";
    const n = status.days ?? 0;
    const date = status.lastDate ? shortDate(status.lastDate, today, locale) : "";
    switch (status.state) {
        case "opening":
            return hi ? `${n} दिन में खुलेगा` : n === 1 ? "Opens tomorrow" : `Opens in ${n} days`;
        case "closing":
            if (n === 0) return hi ? "आज आख़िरी दिन" : "Last day today";
            if (n === 1) return hi ? "कल आख़िरी दिन" : "Closes tomorrow";
            return hi ? `${n} दिन बाकी` : `Closes in ${n} days`;
        case "extended":
            return hi ? `तारीख़ बढ़ी · ${date} तक` : `Extended · to ${date}`;
        case "open":
            return hi ? `खुला है · ${date} तक` : `Open · till ${date}`;
        case "exam-ahead":
            return hi ? "आवेदन बंद" : "Applications closed";
        default:
            return "";
    }
}
