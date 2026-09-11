import Link from "next/link";
import { Wordmark } from "./euk/wordmark";

/**
 * The footer is the last panel of the form, not a link dump: the closing line
 * sits in an inverted band, and the routes below it are grouped the way the
 * document groups them rather than run together in one row.
 */
const LINKS: { heading: string; items: { href: string; label: string }[] }[] = [
    {
        heading: "The kit",
        items: [
            { href: "/exams", label: "All examinations" },
            { href: "/#how", label: "How it works" },
            { href: "/#pricing", label: "Pricing" },
            { href: "/exam-request", label: "Request an exam" },
        ],
    },
    {
        heading: "If something is wrong",
        items: [
            { href: "/support", label: "Support" },
            { href: "/refund-policy", label: "Refunds" },
        ],
    },
    {
        heading: "The small print",
        items: [
            { href: "/privacy", label: "Privacy" },
            { href: "/terms", label: "Terms" },
        ],
    },
];

export function SiteFooter() {
    return (
        <footer className="euk">
            <div className="euk-invert px-5 py-10 md:px-12 md:py-14">
                <h2 className="euk-display text-[42px] md:text-[62px]">
                    A little less admin.
                    <br />
                    <span className="euk-mark">A little more possibility.</span>
                </h2>
                <Link
                    href="/"
                    className="euk-lift mt-7 inline-block border-[3px] border-[var(--ink)] bg-[var(--signal)] px-6 py-3 text-[15px] font-semibold text-[var(--signal-ink)] shadow-[7px_7px_0_var(--ink)]"
                >
                    Find your examination
                </Link>
            </div>

            <div className="border-t-[3px] border-[var(--ink)] bg-[var(--paper)] px-5 py-9 md:px-12 md:py-11">
                <div className="flex flex-col gap-9 md:flex-row md:justify-between md:gap-12">
                    <div className="flex flex-col gap-4">
                        <Link href="/" aria-label="examuploadkit home">
                            <Wordmark />
                        </Link>
                        <p className="max-w-[280px] text-[13px] leading-relaxed text-[var(--ink-55)]">
                            Files are prepared to each examination&rsquo;s own
                            published rules. Final acceptance rests with the
                            authority, never with us.
                        </p>
                    </div>

                    <div className="grid grid-cols-2 gap-7 md:grid-cols-3 md:gap-12">
                        {LINKS.map((group) => (
                            <nav key={group.heading} aria-label={group.heading}>
                                <p className="euk-label pb-3 text-[10px] text-[var(--ink-40)]">
                                    {group.heading}
                                </p>
                                <ul className="flex flex-col gap-2">
                                    {group.items.map((item) => (
                                        <li key={item.href}>
                                            <Link
                                                href={item.href}
                                                className="text-[14px] text-[var(--ink-70)] underline decoration-[var(--hairline)] underline-offset-4 hover:decoration-[var(--signal)]"
                                            >
                                                {item.label}
                                            </Link>
                                        </li>
                                    ))}
                                </ul>
                            </nav>
                        ))}
                    </div>
                </div>

                <p className="euk-label mt-9 border-t-2 border-[var(--hairline)] pt-5 text-[10px] leading-relaxed text-[var(--ink-55)]">
                    Files are deleted within 30 minutes — or within an hour, if
                    you ask us to keep them.
                </p>
            </div>
        </footer>
    );
}
