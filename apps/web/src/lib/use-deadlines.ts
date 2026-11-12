"use client";

import { useEffect, useState } from "react";

import { getApiBaseUrl } from "./api-client";
import { DEADLINES, type Deadline } from "./deadlines";

/**
 * The application dates, live from the engine (DEC-136).
 *
 * The owner sets dates in the console; the engine serves them at
 * `/v1/deadlines`. The page renders first with the list bundled at build
 * (so the server's HTML and the first render agree), then swaps in the live
 * list. One request per page, shared by every component that asks. With no
 * engine, or none of its dates set yet, the bundled list stands.
 */

let live: Promise<Deadline[] | null> | null = null;

function fetchLive(): Promise<Deadline[] | null> {
    if (!live) {
        live = fetch(`${getApiBaseUrl()}/v1/deadlines`, { cache: "no-store" })
            .then((response) => (response.ok ? response.json() : null))
            .then((body: { entries?: Deadline[] } | null) =>
                body && Array.isArray(body.entries) && body.entries.length > 0 ? body.entries : null,
            )
            .catch(() => null);
    }
    return live;
}

export function useDeadlines(initial: readonly Deadline[] = DEADLINES): readonly Deadline[] {
    const [entries, setEntries] = useState<readonly Deadline[]>(initial);
    useEffect(() => {
        let mounted = true;
        void fetchLive().then((fresh) => {
            if (mounted && fresh) setEntries(fresh);
        });
        return () => {
            mounted = false;
        };
    }, []);
    return entries;
}
