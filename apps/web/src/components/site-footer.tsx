import Link from "next/link";
import { Wordmark } from "./euk/wordmark";
import { Reveal } from "./euk/reveal";
import { SignatureStroke } from "./euk/doodles";
import { Today } from "./euk/today";

/**
 * The back of the form.
 *
 * Every Indian application ends the same way: a declaration, a line for the
 * candidate's signature, a box for the date, and a list of what is enclosed.
 * The footer is that page. The declaration is the standard wording candidates
 * have signed a hundred times; the signature writes itself as it scrolls into
 * view; the date is today's, in the boxes the form gives you for it; and the
 * site's routes are the enclosures, ticked.
 *
 * It is the one place on the site where the form metaphor is played straight,
 * because it is the one place a candidate expects to find it.
 */
const ENCLOSURES: {
    group: string;
    links: { href: string; label: string }[];
}[] = [
    {
        group: "For your application",
        links: [
            { href: "/exams", label: "All examinations" },
            { href: "/#how", label: "How it works" },
            { href: "/#pricing", label: "Pricing" },
            { href: "/exam-request", label: "Request an examination" },
        ],
    },
    {
        group: "If something goes wrong",
        links: [
            { href: "/support", label: "Support and grievances" },
            { href: "/refund-policy", label: "Refunds" },
        ],
    },
    {
        group: "The fine print",
        links: [
            { href: "/privacy", label: "Privacy" },
            { href: "/terms", label: "Terms" },
        ],
    },
];

function Tick() {
    return (
        <svg
            viewBox="0 0 16 16"
            className="euk-enc-box"
            aria-hidden="true"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <rect x="1.5" y="1.5" width="13" height="13" />
            <path className="euk-enc-tick" d="M4.5 8.2 L7 10.7 L11.8 5.4" />
        </svg>
    );
}

export function SiteFooter() {
    return (
        <footer className="euk euk-foot">
            <div className="euk-invert px-5 py-14 md:px-12 md:py-20">
                <div className="euk-wrap">
                    <Reveal className="euk-light euk-declaration">
                        <p className="euk-declaration-bar">Declaration</p>
                        <p className="euk-declaration-text">
                            I declare that the particulars in my application are
                            true, and that the photograph, signature and
                            documents I upload are my own.
                        </p>
                        <div className="euk-declaration-sign">
                            <div className="min-w-0">
                                <div className="euk-sign-line">
                                    <SignatureStroke />
                                </div>
                                <p className="euk-sign-caption">
                                    Signature of the candidate
                                </p>
                            </div>
                            <div>
                                <Today />
                                <p className="euk-sign-caption">Date</p>
                            </div>
                        </div>
                    </Reveal>

                    <div className="euk-foot-cta">
                        <h2 className="euk-display">
                            You sign the form.
                            <br />
                            <span className="euk-mark">
                                We prepare what it asks for.
                            </span>
                        </h2>
                        <Link href="/exams" className="primary-button">
                            Find your examination
                        </Link>
                    </div>
                </div>
            </div>

            <div className="bg-[var(--paper)] px-5 py-12 md:px-12 md:py-14">
                <div className="euk-wrap euk-enclosures">
                    <div className="flex flex-col gap-4">
                        <Link href="/" aria-label="examuploadkit home">
                            <Wordmark />
                        </Link>
                        <p className="text-[14px] leading-relaxed text-[var(--ink-70)]">
                            Every file prepared to the rules your examination
                            published. Acceptance is always the authority&rsquo;s
                            decision, never ours.
                        </p>
                    </div>

                    {ENCLOSURES.map((group) => (
                        <nav key={group.group} aria-label={group.group}>
                            <p className="euk-enc-group">{group.group}</p>
                            <ul className="euk-enc-list">
                                {group.links.map((link) => (
                                    <li key={link.href}>
                                        <Link href={link.href}>
                                            <Tick />
                                            <span>{link.label}</span>
                                        </Link>
                                    </li>
                                ))}
                            </ul>
                        </nav>
                    ))}
                </div>

                <p className="euk-wrap euk-foot-last">
                    Files are deleted within 30 minutes, or within an hour if you
                    ask us to keep them.
                </p>
            </div>
        </footer>
    );
}
