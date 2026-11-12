"use client";

import { useEffect, useState } from "react";
import { todayKey } from "./deadlines";

/**
 * Today's date as YYYY-MM-DD (DEC-135). The first render uses the date the
 * page was built, so the server's HTML and the first client render agree;
 * straight after, the visitor's own date takes over.
 */
export function useToday(builtOn: string): string {
    const [today, setToday] = useState(builtOn);
    useEffect(() => {
        const now = todayKey();
        if (now !== builtOn) {
            const timer = setTimeout(() => setToday(now), 0);
            return () => clearTimeout(timer);
        }
        return undefined;
    }, [builtOn]);
    return today;
}
