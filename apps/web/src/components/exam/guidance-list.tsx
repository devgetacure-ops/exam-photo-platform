import type { GuidanceItem, Verdict } from "../../lib/appearance-rules";
import { Cross, Tick } from "./specimen-sheet";

/**
 * The photograph rules, as a candidate needs to read them.
 *
 * Ordered by what will get you rejected first, not alphabetically. Each rule
 * carries a verdict word and a mark as well as a colour, because "prohibited"
 * and "allowed" must not depend on hue to be distinguishable — and because a
 * rule about religious headwear read the wrong way is not a small mistake.
 *
 * Where the research captured the examination's own phrasing it is quoted
 * beneath: not a badge claiming officialness, but the words the body used, so
 * a candidate can match them against the notification in front of them.
 */

const WORD: Record<Verdict, string> = {
    prohibited: "Not allowed",
    conditional: "Conditions apply",
    required: "Required",
    permitted: "Allowed",
};

export function GuidanceList({ items }: { items: GuidanceItem[] }) {
    if (items.length === 0) return null;

    return (
        <ul className="euk-verdicts euk-guidance">
            {items.map((item) => (
                <li key={item.id} className={`euk-verdict euk-verdict--${item.verdict}`}>
                    <span className="euk-verdict-mark" aria-hidden="true">
                        {item.verdict === "prohibited" ? (
                            <Cross />
                        ) : item.verdict === "conditional" ? (
                            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.8" strokeLinecap="round">
                                <path d="M3 11 C 6 6, 9 6, 10 10 C 11 14, 14 14, 17 9" />
                            </svg>
                        ) : (
                            <Tick />
                        )}
                    </span>
                    <div className="min-w-0">
                        <p className="euk-verdict-title">
                            {item.title}{" "}
                            <span className="euk-verdict-word">{WORD[item.verdict]}</span>
                        </p>
                        <p>{item.detail}</p>
                        {item.sourceWording && (
                            <p className="euk-verdict-quote">
                                The notice: &ldquo;{item.sourceWording}&rdquo;
                            </p>
                        )}
                    </div>
                </li>
            ))}
        </ul>
    );
}
