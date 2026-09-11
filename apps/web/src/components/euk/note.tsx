/**
 * The pointing hand. The italic is reserved for this and nothing else — it is
 * how the page indicates a thing rather than how it speaks in general, so the
 * arrow is part of the component and not an optional decoration.
 */
export function Note({
    children,
    className = "",
}: {
    children: React.ReactNode;
    className?: string;
}) {
    return (
        <p className={`euk-note ${className}`}>
            <svg
                width="34"
                height="20"
                viewBox="0 0 34 20"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
                aria-hidden="true"
            >
                <path d="M2 4 C 12 2, 26 6, 31 16" />
                <path d="M31 10 L31 16.5 L25 16.5" />
            </svg>
            <span>{children}</span>
        </p>
    );
}
