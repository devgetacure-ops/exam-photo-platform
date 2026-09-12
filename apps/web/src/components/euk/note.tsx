/**
 * The pointing hand, which is now a mark in the margin rather than a drawn
 * arrow. An arrow has to point at something; these notes sit beside the thing
 * they concern, so the arrow was always aimed at whatever happened to be next
 * to it. A rule down the edge marks the line the way a reader marks a form,
 * and it cannot be pointed the wrong way.
 *
 * The italic is still reserved for this and nothing else: it is how the page
 * indicates a thing rather than how it speaks in general.
 */
export function Note({
    children,
    className = "",
}: {
    children: React.ReactNode;
    className?: string;
}) {
    return <p className={`euk-note ${className}`}>{children}</p>;
}
