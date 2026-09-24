import { cva, type VariantProps } from "class-variance-authority";
import { clsx, type ClassValue } from "clsx";
import type { ComponentProps, ReactNode } from "react";
import { twMerge } from "tailwind-merge";

/**
 * The console's building blocks (DEC-113), in the shadcn/ui pattern: plain
 * elements styled with Tailwind over the `--op-*` tokens in console.css.
 * Server-safe: nothing here holds state.
 */

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export const buttonStyles = cva(
    "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg font-medium transition-colors disabled:pointer-events-none disabled:opacity-50 cursor-pointer select-none",
    {
        variants: {
            variant: {
                primary: "bg-[var(--op-primary)] text-[var(--op-primary-text)] hover:opacity-90",
                secondary:
                    "border border-[var(--op-border)] bg-[var(--op-card)] text-[var(--op-text)] hover:bg-[var(--op-hover)]",
                ghost: "text-[var(--op-text)] hover:bg-[var(--op-hover)]",
                danger: "bg-[var(--op-bad)] text-white hover:opacity-90",
                accent: "bg-[var(--op-accent)] text-white hover:opacity-90",
            },
            size: {
                sm: "h-8 px-3 text-[13px]",
                md: "h-9 px-3.5 text-sm",
                lg: "h-11 px-5 text-[15px]",
                icon: "h-9 w-9",
            },
        },
        defaultVariants: { variant: "secondary", size: "md" },
    },
);

export function Button({
    className,
    variant,
    size,
    type = "button",
    ...props
}: ComponentProps<"button"> & VariantProps<typeof buttonStyles>) {
    return <button type={type} className={cn(buttonStyles({ variant, size }), className)} {...props} />;
}

const TONES = {
    neutral: "bg-[var(--op-muted-bg)] text-[var(--op-muted)]",
    good: "bg-[var(--op-good-bg)] text-[var(--op-good)]",
    warn: "bg-[var(--op-warn-bg)] text-[var(--op-warn)]",
    bad: "bg-[var(--op-bad-bg)] text-[var(--op-bad)]",
    info: "bg-[var(--op-info-bg)] text-[var(--op-info)]",
    accent: "bg-[var(--op-accent-soft)] text-[var(--op-accent-text)]",
} as const;

export type Tone = keyof typeof TONES;

export function Badge({ tone = "neutral", children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
    return (
        <span className={cn("inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-semibold", TONES[tone], className)}>
            {children}
        </span>
    );
}

/** Every state the console names, in words, with the colour that repeats it. */
export const STATE: Record<string, { label: string; tone: Tone }> = {
    "refund-due": { label: "Refund due", tone: "bad" },
    delivered: { label: "Delivered", tone: "good" },
    paid: { label: "Paid", tone: "warn" },
    unpaid: { label: "Not paid", tone: "neutral" },
    "payment-failed": { label: "Payment failed", tone: "warn" },
    refunded: { label: "Refunded", tone: "info" },
    free: { label: "Free · code", tone: "info" },
    open: { label: "Open", tone: "bad" },
    answered: { label: "Answered", tone: "info" },
    resolved: { label: "Resolved", tone: "good" },
    pending: { label: "To approve", tone: "warn" },
    approved: { label: "Approved", tone: "good" },
    rejected: { label: "Rejected", tone: "neutral" },
    succeeded: { label: "Prepared", tone: "good" },
    processing: { label: "Processing", tone: "info" },
    error: { label: "Error", tone: "bad" },
    busy: { label: "Refused: busy", tone: "warn" },
    failed: { label: "Failed", tone: "bad" },
};

export function StateBadge({ state }: { state: string }) {
    const known = STATE[state] ?? { label: state, tone: "neutral" as Tone };
    return <Badge tone={known.tone}>{known.label}</Badge>;
}

export function Card({ className, ...props }: ComponentProps<"div">) {
    return <div className={cn("rounded-xl border border-[var(--op-border)] bg-[var(--op-card)] shadow-[var(--op-shadow)]", className)} {...props} />;
}

export function CardHeader({ title, action, description }: { title: ReactNode; action?: ReactNode; description?: ReactNode }) {
    return (
        <div className="flex items-start gap-3 border-b border-[var(--op-border)] px-5 py-3.5">
            <div className="min-w-0 flex-1">
                <h2 className="m-0 text-[15px] font-semibold">{title}</h2>
                {description && <p className="m-0 mt-0.5 text-[13px] text-[var(--op-muted)]">{description}</p>}
            </div>
            {action}
        </div>
    );
}

export function PageHeader({ title, description, actions }: { title: ReactNode; description?: ReactNode; actions?: ReactNode }) {
    return (
        <div className="flex flex-wrap items-end gap-3">
            <div className="min-w-[min(100%,20rem)] flex-1">
                <h1 className="m-0 text-2xl font-semibold tracking-tight">{title}</h1>
                {description && <p className="m-0 mt-1 text-[var(--op-muted)]">{description}</p>}
            </div>
            {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
        </div>
    );
}

const fieldBase =
    "w-full rounded-lg border border-[var(--op-border)] bg-[var(--op-card)] px-3 text-sm text-[var(--op-text)] placeholder:text-[var(--op-faint)] focus:border-[var(--op-border-strong)] focus:outline-none";

export function Input({ className, ...props }: ComponentProps<"input">) {
    return <input className={cn(fieldBase, "h-10", className)} {...props} />;
}

export function Textarea({ className, ...props }: ComponentProps<"textarea">) {
    return <textarea className={cn(fieldBase, "min-h-24 py-2 leading-relaxed", className)} {...props} />;
}

export function Select({ className, ...props }: ComponentProps<"select">) {
    return <select className={cn(fieldBase, "h-10 cursor-pointer pr-8", className)} {...props} />;
}

export function Field({ label, hint, children, className }: { label: string; hint?: ReactNode; children: ReactNode; className?: string }) {
    return (
        <label className={cn("flex flex-col gap-1.5", className)}>
            <span className="text-[13px] font-medium">{label}</span>
            {children}
            {hint && <span className="text-xs text-[var(--op-muted)]">{hint}</span>}
        </label>
    );
}

export function Check({ children, className, ...props }: ComponentProps<"input"> & { children: ReactNode }) {
    return (
        <label className={cn("flex min-h-10 cursor-pointer items-center gap-2.5 text-sm", className)}>
            <input type="checkbox" className="h-4 w-4 accent-[var(--op-accent)]" {...props} />
            <span>{children}</span>
        </label>
    );
}

/** A small trend line for a number card; the points are whatever the series is. */
export function Sparkline({ values, tone = "text" }: { values: number[]; tone?: "text" | "accent" }) {
    if (values.length < 2) return <div className="h-9" />;
    const max = Math.max(...values, 1);
    const min = Math.min(...values, 0);
    const span = max - min || 1;
    const points = values
        .map((value, index) => `${((index / (values.length - 1)) * 200).toFixed(1)},${(34 - ((value - min) / span) * 30).toFixed(1)}`)
        .join(" ");
    return (
        <svg viewBox="0 0 200 36" preserveAspectRatio="none" className="h-9 w-full" aria-hidden="true">
            <polyline
                points={points}
                fill="none"
                stroke={tone === "accent" ? "var(--op-accent)" : "var(--op-text)"}
                strokeWidth="2"
                vectorEffect="non-scaling-stroke"
                strokeLinejoin="round"
            />
        </svg>
    );
}

export function Stat({
    label,
    value,
    delta,
    good,
    foot,
    spark,
    href,
}: {
    label: string;
    value: ReactNode;
    delta?: string | null;
    good?: boolean;
    foot?: ReactNode;
    spark?: number[];
    href?: string;
}) {
    const body = (
        <>
            <span className="text-[13px] text-[var(--op-muted)]">{label}</span>
            <div className="flex items-baseline gap-2">
                <span className="op-num text-[26px] font-semibold tracking-tight">{value}</span>
                {delta && <span className={cn("text-xs font-semibold", good ? "text-[var(--op-good)]" : "text-[var(--op-bad)]")}>{delta}</span>}
            </div>
            {spark && <Sparkline values={spark} tone={label === "Revenue" ? "accent" : "text"} />}
            {foot && <span className="text-xs text-[var(--op-muted)]">{foot}</span>}
        </>
    );
    const style = "flex flex-col gap-1.5 p-4 sm:p-5";
    return href ? (
        <a href={href} className={cn("rounded-xl border border-[var(--op-border)] bg-[var(--op-card)] shadow-[var(--op-shadow)] hover:border-[var(--op-border-strong)]", style)}>
            {body}
        </a>
    ) : (
        <Card className={style}>{body}</Card>
    );
}

export function Empty({ title, children, icon }: { title: string; children?: ReactNode; icon?: ReactNode }) {
    return (
        <div className="flex flex-col items-center gap-2 px-6 py-12 text-center">
            {icon && <div className="text-[var(--op-faint)]">{icon}</div>}
            <p className="m-0 font-semibold">{title}</p>
            {children && <p className="m-0 max-w-md text-[13px] text-[var(--op-muted)]">{children}</p>}
        </div>
    );
}

export function Problem({ what, error }: { what: string; error: string }) {
    return (
        <Card className="border-[var(--op-bad)] bg-[var(--op-bad-bg)] p-4 text-[var(--op-bad)]" role="alert">
            Could not load {what}. {error}
        </Card>
    );
}

export function Facts({ rows }: { rows: [string, ReactNode][] }) {
    return (
        <dl className="m-0 grid grid-cols-[120px_minmax(0,1fr)] gap-x-3 gap-y-2.5 text-sm">
            {rows.filter(([, value]) => value !== null && value !== undefined && value !== "").map(([label, value]) => (
                <div key={label} className="contents">
                    <dt className="text-[var(--op-muted)]">{label}</dt>
                    <dd className="m-0 break-words">{value ?? "—"}</dd>
                </div>
            ))}
        </dl>
    );
}

/** A POST to an operator action, returning to `back` with a confirmation. */
export function ActionForm({ action, back, children, className }: { action: string; back: string; children: ReactNode; className?: string }) {
    return (
        <form method="post" action={action} className={className}>
            <input type="hidden" name="back" value={back} />
            {children}
        </form>
    );
}
