/**
 * Diagrams of what a compliant upload looks like.
 *
 * Drawn rather than photographed, for four reasons that all point the same
 * way. We may never ship real candidate photographs, so a photo set would have
 * to be commissioned. A diagram shows the *rule* — where the head sits, how
 * much margin there is — which a photograph can only imply. These weigh a
 * couple of hundred bytes each on a connection the candidate is paying for.
 * And they follow the theme, so they are legible on both grounds.
 *
 * Every diagram is decorative in the accessibility sense: the rule it depicts
 * is always stated in text beside it, so nothing here is the only carrier of
 * information.
 */

interface DiagramProps {
  /** Draw the compliant version, or the mistake. */
  variant?: "good" | "bad";
  className?: string;
}

const GOOD = "var(--ready)";
const BAD = "var(--blocked)";
const SUBJECT = "var(--muted)";
const FRAME = "var(--line-strong)";

/**
 * Head-and-shoulders framing: the single thing candidates get wrong most
 * often, in both directions — a distant full-body shot, or a face cropped so
 * tightly the hair and chin are cut.
 */
export function PortraitFraming({ variant = "good", className }: DiagramProps) {
  const stroke = variant === "good" ? GOOD : BAD;
  return (
    <svg
      viewBox="0 0 80 100"
      className={className}
      role="presentation"
      aria-hidden="true"
    >
      <rect
        x="1"
        y="1"
        width="78"
        height="98"
        rx="3"
        fill="var(--sunk)"
        stroke={FRAME}
        strokeWidth="1.5"
      />
      {variant === "good" ? (
        <>
          {/* Head occupying the upper-middle band, with air above the hair
              and the shoulders entering at the base. */}
          <circle cx="40" cy="42" r="19" fill={SUBJECT} opacity="0.35" />
          <path
            d="M14 100c0-14 12-23 26-23s26 9 26 23"
            fill={SUBJECT}
            opacity="0.35"
          />
          <line x1="40" y1="8" x2="40" y2="21" stroke={stroke} strokeWidth="1.5" />
          <line x1="36" y1="8" x2="44" y2="8" stroke={stroke} strokeWidth="1.5" />
          <line x1="36" y1="21" x2="44" y2="21" stroke={stroke} strokeWidth="1.5" />
        </>
      ) : (
        <>
          {/* Too far away: the head is a fraction of the frame. */}
          <circle cx="40" cy="34" r="8" fill={SUBJECT} opacity="0.3" />
          <path d="M28 62c0-7 5-12 12-12s12 5 12 12" fill={SUBJECT} opacity="0.3" />
          <line
            x1="16"
            y1="84"
            x2="64"
            y2="84"
            stroke={stroke}
            strokeWidth="1.5"
            strokeDasharray="3 3"
          />
        </>
      )}
    </svg>
  );
}

/** A signature on paper: full strokes inside the frame, versus clipped. */
export function SignatureFraming({ variant = "good", className }: DiagramProps) {
  const stroke = variant === "good" ? GOOD : BAD;
  return (
    <svg
      viewBox="0 0 120 60"
      className={className}
      role="presentation"
      aria-hidden="true"
    >
      <rect
        x="1"
        y="1"
        width="118"
        height="58"
        rx="3"
        fill="var(--sunk)"
        stroke={FRAME}
        strokeWidth="1.5"
      />
      {variant === "good" ? (
        <path
          d="M20 40c8-16 14 6 20-6s12 10 20-2 14 8 22-4"
          fill="none"
          stroke={SUBJECT}
          strokeWidth="2.5"
          strokeLinecap="round"
        />
      ) : (
        <>
          {/* Running off the edge — the stroke is cut, so the signature is
              not the candidate's signature any more. */}
          <path
            d="M2 40c10-16 16 6 22-6s12 10 20-2 16 8 24-6"
            fill="none"
            stroke={SUBJECT}
            strokeWidth="2.5"
            strokeLinecap="round"
          />
          <line x1="1" y1="1" x2="1" y2="59" stroke={stroke} strokeWidth="3" />
          <line x1="119" y1="1" x2="119" y2="59" stroke={stroke} strokeWidth="3" />
        </>
      )}
    </svg>
  );
}

/** A whole sheet, all four corners present, versus a page with corners lost. */
export function PageFraming({ variant = "good", className }: DiagramProps) {
  const stroke = variant === "good" ? GOOD : BAD;
  return (
    <svg
      viewBox="0 0 80 100"
      className={className}
      role="presentation"
      aria-hidden="true"
    >
      {variant === "good" ? (
        <>
          <rect
            x="8"
            y="6"
            width="64"
            height="88"
            rx="2"
            fill="var(--surface)"
            stroke={stroke}
            strokeWidth="1.5"
          />
          {[22, 34, 46, 58, 70].map((y) => (
            <line
              key={y}
              x1="18"
              y1={y}
              x2={y === 70 ? 48 : 62}
              y2={y}
              stroke={SUBJECT}
              strokeWidth="2"
              opacity="0.4"
            />
          ))}
        </>
      ) : (
        <>
          <rect
            x="8"
            y="6"
            width="64"
            height="88"
            rx="2"
            fill="var(--surface)"
            stroke={FRAME}
            strokeWidth="1.5"
          />
          {[22, 34, 46, 58, 70].map((y) => (
            <line
              key={y}
              x1="18"
              y1={y}
              x2={y === 70 ? 48 : 62}
              y2={y}
              stroke={SUBJECT}
              strokeWidth="2"
              opacity="0.4"
            />
          ))}
          {/* A corner outside the capture. */}
          <path
            d="M52 0 L80 0 L80 28 Z"
            fill="var(--paper)"
            stroke={stroke}
            strokeWidth="1.5"
            strokeDasharray="3 2"
          />
        </>
      )}
    </svg>
  );
}

/** A thumb impression: full ridge pattern versus a partial press. */
export function ThumbFraming({ variant = "good", className }: DiagramProps) {
  const stroke = variant === "good" ? GOOD : BAD;
  return (
    <svg
      viewBox="0 0 80 100"
      className={className}
      role="presentation"
      aria-hidden="true"
    >
      <rect
        x="1"
        y="1"
        width="78"
        height="98"
        rx="3"
        fill="var(--sunk)"
        stroke={FRAME}
        strokeWidth="1.5"
      />
      <g
        fill="none"
        stroke={variant === "good" ? SUBJECT : stroke}
        strokeWidth="2"
        opacity={variant === "good" ? 0.55 : 0.4}
      >
        {(variant === "good" ? [10, 16, 22, 28] : [10, 16]).map((r) => (
          <ellipse key={r} cx="40" cy="52" rx={r} ry={r * 1.25} />
        ))}
      </g>
      {variant === "bad" && (
        <path
          d="M14 74h52"
          stroke={stroke}
          strokeWidth="2.5"
          strokeDasharray="4 3"
          fill="none"
        />
      )}
    </svg>
  );
}

/** The right diagram for a requirement type, in the requested variant. */
export function DiagramFor({
  requirementType,
  variant = "good",
  className,
}: DiagramProps & { requirementType: string }) {
  switch (requirementType) {
    case "photograph":
      return <PortraitFraming variant={variant} className={className} />;
    case "signature":
      return <SignatureFraming variant={variant} className={className} />;
    case "thumb_impression":
      return <ThumbFraming variant={variant} className={className} />;
    default:
      return <PageFraming variant={variant} className={className} />;
  }
}
