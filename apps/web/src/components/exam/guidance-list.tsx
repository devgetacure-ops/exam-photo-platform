import type { GuidanceItem, Verdict } from "../../lib/appearance-rules";

/**
 * The photograph rules, as a candidate needs to read them.
 *
 * Ordered by what will get you rejected first, not alphabetically. Each rule
 * carries a verdict word as well as a colour, because "prohibited" and
 * "allowed" must not depend on hue to be distinguishable — and because a rule
 * about religious headwear read the wrong way is not a small mistake.
 *
 * Where the research captured the examination's own phrasing it is quoted
 * beneath. That is the honest form of "cite your sources": not a badge
 * claiming officialness, but the words the body actually used, so a candidate
 * can match them against the notification in front of them.
 */

const STYLES: Record<Verdict, { chip: string; word: string }> = {
  prohibited: { chip: "bg-blocked-soft text-blocked", word: "Not allowed" },
  conditional: { chip: "bg-caveat-soft text-caveat", word: "Conditions apply" },
  required: { chip: "bg-accent-soft text-accent-ink", word: "Required" },
  permitted: { chip: "bg-ready-soft text-ready", word: "Allowed" },
};

export function GuidanceList({ items }: { items: GuidanceItem[] }) {
  if (items.length === 0) return null;

  return (
    <ul className="mt-5 grid gap-3 sm:grid-cols-2">
      {items.map((item) => {
        const style = STYLES[item.verdict];
        return (
          <li
            key={item.id}
            className="rounded-xl border border-line bg-surface p-4"
          >
            <div className="flex items-start justify-between gap-3">
              <h3 className="font-medium text-ink">{item.title}</h3>
              <span
                className={`label shrink-0 rounded px-2 py-0.5 ${style.chip}`}
              >
                {style.word}
              </span>
            </div>
            <p className="mt-2 text-sm leading-relaxed text-ink-soft">
              {item.detail}
            </p>
            {item.sourceWording && (
              <p className="mt-2 border-l-2 border-line-strong pl-3 text-sm text-muted italic">
                &ldquo;{item.sourceWording}&rdquo;
              </p>
            )}
          </li>
        );
      })}
    </ul>
  );
}
