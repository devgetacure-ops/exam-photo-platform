"use client";

import { useId, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { SearchEntry } from "./types";
import { rankEntries, type Ranked } from "./search-rank";

/**
 * The picker's behaviour, once, for both places it appears.
 *
 * The page's search and the one in the top bar are the same interaction in two
 * shapes: same ranking, same keys, same rule that an unavailable examination is
 * shown but never selected. Keeping the logic here means the bar cannot quietly
 * drift into a second, slightly different search.
 *
 * The whole index is in memory, so matching costs no round trip and results
 * appear as fast as a candidate can type.
 */
export interface ExamPicker {
    query: string;
    type: (value: string) => void;
    clear: () => void;
    active: number;
    setActive: (index: number) => void;
    available: Ranked[];
    blocked: Ranked[];
    hasResults: boolean;
    /** True once the candidate has typed something worth matching. */
    asking: boolean;
    requestHref: string;
    listId: string;
    go: (entry: SearchEntry) => void;
    onKeyDown: (event: React.KeyboardEvent<HTMLInputElement>) => void;
}

export function useExamPicker(
    exams: SearchEntry[],
    unavailable: SearchEntry[],
    /** Called when the candidate picks a row or gives up — the bar closes on it. */
    onLeave?: () => void,
): ExamPicker {
    const router = useRouter();
    const [query, setQuery] = useState("");
    const [active, setActive] = useState(0);
    const listId = useId();

    const { available, blocked } = useMemo(() => {
        if (!query.trim()) return { available: [], blocked: [] };
        return {
            available: rankEntries(exams, query).slice(0, 7),
            blocked: rankEntries(unavailable, query).slice(0, 4),
        };
    }, [query, exams, unavailable]);

    // Only selectable rows take part in keyboard navigation. An unavailable
    // examination is shown, never selected — arrowing onto it and pressing
    // Enter would imply it leads somewhere (DEC-056).
    const navigable = available;
    const hasResults = available.length > 0 || blocked.length > 0;
    const requestHref = `/exam-request?exam=${encodeURIComponent(query.trim())}`;

    const go = (entry: SearchEntry) => {
        onLeave?.();
        router.push(`/exam/${entry.id}`);
    };

    const onKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === "ArrowDown") {
            event.preventDefault();
            setActive((i) => Math.max(0, Math.min(i + 1, navigable.length - 1)));
        } else if (event.key === "ArrowUp") {
            event.preventDefault();
            setActive((i) => Math.max(i - 1, 0));
        } else if (event.key === "Enter") {
            const chosen = navigable[active];
            if (chosen) {
                event.preventDefault();
                go(chosen.entry);
            } else if (query.trim() && !hasResults) {
                // Nothing to select, so Enter does the one useful thing left.
                event.preventDefault();
                onLeave?.();
                router.push(requestHref);
            }
        } else if (event.key === "Escape") {
            setQuery("");
            onLeave?.();
        }
    };

    return {
        query,
        type: (value: string) => {
            setQuery(value);
            setActive(0);
        },
        clear: () => {
            setQuery("");
            setActive(0);
        },
        active,
        setActive,
        available,
        blocked,
        hasResults,
        asking: query.trim().length > 0,
        requestHref,
        listId,
        go,
        onKeyDown,
    };
}
