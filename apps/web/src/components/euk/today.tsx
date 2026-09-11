"use client";

import { useEffect, useState } from "react";

/**
 * Today's date, written into the boxes a form gives you for it.
 *
 * Rendered after mount rather than at build time: every page here is generated
 * statically, so a server-rendered date would freeze on the day of the build
 * and be wrong on every day after. Until the browser supplies the real date
 * the boxes hold the form's own placeholders, which is what an unfilled form
 * looks like anyway.
 */
export function Today() {
    const [date, setDate] = useState<Date | null>(null);

    useEffect(() => {
        const t = setTimeout(() => setDate(new Date()), 0);
        return () => clearTimeout(t);
    }, []);

    const dd = date ? String(date.getDate()).padStart(2, "0") : "DD";
    const mm = date ? String(date.getMonth() + 1).padStart(2, "0") : "MM";
    const yyyy = date ? String(date.getFullYear()) : "YYYY";
    const groups = [dd, mm, yyyy];

    return (
        <span
            className="euk-date"
            role="img"
            aria-label={
                date
                    ? date.toLocaleDateString("en-IN", {
                          day: "numeric",
                          month: "long",
                          year: "numeric",
                      })
                    : "Date"
            }
        >
            {groups.map((group, g) => (
                <span className="euk-date-group" key={g} aria-hidden="true">
                    {group.split("").map((ch, i) => (
                        <span className="euk-date-cell" key={i}>
                            {ch}
                        </span>
                    ))}
                </span>
            ))}
        </span>
    );
}
