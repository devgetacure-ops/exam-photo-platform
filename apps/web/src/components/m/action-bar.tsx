"use client";

/**
 * The phone's one place for a primary action.
 *
 * Fixed to the foot of the screen inside the home-indicator inset, so the
 * thumb never travels and the address bar can never cut it off — the page is
 * measured in `dvh`, not `vh`. It reserves its own height at the end of the
 * document, so nothing a candidate is reading ends up underneath it.
 *
 * A screen with nothing to do does not get one (the owner's call): content
 * takes the whole display instead.
 */
export function ActionBar({
    note,
    children,
}: {
    /** The running total, the file count — whatever the action costs. */
    note?: React.ReactNode;
    children: React.ReactNode;
}) {
    return (
        <>
            <div className="euk-actionbar-spacer" aria-hidden="true" />
            <div className="euk-actionbar">
                {note ? <div className="euk-actionbar-note">{note}</div> : null}
                <div className="euk-actionbar-action">{children}</div>
            </div>
        </>
    );
}
