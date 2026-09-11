import Link from "next/link";
import { ThemeToggle } from "./theme-toggle";
import { Wordmark } from "./euk/wordmark";

/**
 * One header for every route. On an exam page it also carries that
 * examination's name and a way back, because a candidate deep in a kit needs
 * to know which form they are filling before they need anything else.
 */
export function SiteHeader({ mobileTitle }: { mobileTitle?: string }) {
    return (
        <header className="euk border-b-[3px] border-[var(--ink)] bg-[var(--paper)]">
            <div className="flex items-center justify-between gap-4 px-5 py-4 md:px-12">
                <div className="flex min-w-0 items-center gap-4">
                    <Link href="/" aria-label="examuploadkit home">
                        <Wordmark />
                    </Link>
                    {mobileTitle && (
                        <span className="euk-label hidden min-w-0 truncate border-l-2 border-[var(--hairline)] pl-4 text-[10px] text-[var(--ink-55)] sm:inline">
                            {mobileTitle}
                        </span>
                    )}
                </div>

                <nav className="euk-label flex items-center gap-4 text-[10px] md:gap-6 md:text-[11px]">
                    {mobileTitle ? (
                        <Link href="/exams" className="hidden sm:inline">
                            Change exam
                        </Link>
                    ) : (
                        <>
                            <Link href="/#how" className="hidden sm:inline">
                                How it works
                            </Link>
                            <Link href="/#pricing" className="hidden sm:inline">
                                Pricing
                            </Link>
                        </>
                    )}
                    <Link
                        href="/exams"
                        className="border-2 border-[var(--ink)] px-2 py-1.5 md:px-3"
                    >
                        Exams
                    </Link>
                    <ThemeToggle />
                </nav>
            </div>

            {mobileTitle && (
                <p className="euk-label truncate border-t-2 border-[var(--hairline)] px-5 py-2 text-[10px] text-[var(--ink-55)] sm:hidden">
                    {mobileTitle}
                </p>
            )}
        </header>
    );
}
