/**
 * The wordmark is thirteen cells sharing 1px dividers inside one outer border —
 * the construction a real application form uses, where the boxes you write one
 * character into are joined rather than floating apart.
 *
 * It is one component at every size because a logo built two different ways is
 * two logos. Only the cell metrics change, and they change in CSS rather than
 * here, so a breakpoint never needs a second element in the tree.
 */
const LETTERS = "EXAMUPLOADKIT".split("");

export function Wordmark({ label = "ExamUploadKit" }: { label?: string }) {
    return (
        <span className="euk-lock" role="img" aria-label={label}>
            {LETTERS.map((letter, i) => (
                <span className="euk-cell" aria-hidden="true" key={`${letter}-${i}`}>
                    {letter}
                </span>
            ))}
        </span>
    );
}
