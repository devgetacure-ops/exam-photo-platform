/**
 * The examinations this browser opened from the phone search, newest first.
 *
 * A candidate comes back to the same examination several times — to read the
 * rules, to prepare, to pay — and typing its name again on a phone keyboard
 * each time is the friction this removes. Only the examination's id and name
 * are kept, never anything the candidate typed or uploaded, and only in this
 * browser.
 */
export interface RecentExam {
    id: string;
    name: string;
}

const KEY = "uploadready:recent-exams";
const MAX = 5;

export function readRecent(): RecentExam[] {
    try {
        const raw = localStorage.getItem(KEY);
        if (!raw) return [];
        const value: unknown = JSON.parse(raw);
        if (!Array.isArray(value)) return [];
        return value
            .filter(
                (row): row is RecentExam =>
                    typeof row === "object" &&
                    row !== null &&
                    typeof (row as RecentExam).id === "string" &&
                    typeof (row as RecentExam).name === "string",
            )
            .slice(0, MAX);
    } catch {
        // Storage blocked or the value damaged: no recents, not a crash.
        return [];
    }
}

export function rememberExam(exam: RecentExam): RecentExam[] {
    const next = [
        { id: exam.id, name: exam.name },
        ...readRecent().filter((row) => row.id !== exam.id),
    ].slice(0, MAX);
    try {
        localStorage.setItem(KEY, JSON.stringify(next));
    } catch {
        // Remembered for this visit only.
    }
    return next;
}
