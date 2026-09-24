import { Star } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { ActionForm, Badge, Button, Card, Empty, PageHeader, Problem, cn } from "../../../../components/console/ui";
import { when } from "../../../../lib/operator/format";
import { rupees } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

export const metadata: Metadata = { title: "Reviews" };

interface Review {
    order_id: string;
    at: string;
    rating: number | null;
    tags: string[];
    comment: string | null;
    name: string | null;
    may_publish: number;
    status: string;
    reviewed_by: string | null;
    reward_code: string | null;
    source: string | null;
    exam_names: string[];
    emails: string[];
    amount_paise: number | null;
}

interface Reviews {
    reviews: Review[];
    summary: { count: number; average: number | null; by_star: Record<string, number>; pending: number; approved: number };
    offer_on: boolean;
}

const TABS: [string, string][] = [
    ["pending", "To approve"],
    ["approved", "Approved"],
    ["rejected", "Rejected"],
    ["", "All"],
];

function Stars({ rating, size = 18 }: { rating: number; size?: number }) {
    return (
        <span className="inline-flex" aria-label={`${rating} out of 5 stars`}>
            {[1, 2, 3, 4, 5].map((n) => (
                <Star key={n} size={size} aria-hidden="true" fill={n <= rating ? "var(--op-accent)" : "none"} stroke={n <= rating ? "var(--op-accent)" : "var(--op-border-strong)"} />
            ))}
        </span>
    );
}

export default async function ReviewsPage({ searchParams }: { searchParams: Promise<{ status?: string }> }) {
    await requireOperator();
    const requested = (await searchParams).status;
    const status = requested === undefined ? "pending" : requested;
    const [loaded, all] = await Promise.all([
        engineJson<Reviews>(`/v1/operator/reviews?status=${encodeURIComponent(status)}`),
        engineJson<Reviews>("/v1/operator/reviews"),
    ]);
    if (!loaded.ok) return <Problem what="reviews" error={loaded.error} />;
    const { reviews, summary, offer_on: offerOn } = loaded.value;
    const counts: Record<string, number> = { "": all.ok ? all.value.reviews.length : 0 };
    for (const review of all.ok ? all.value.reviews : []) counts[review.status] = (counts[review.status] ?? 0) + 1;
    const back = `/admin/reviews?status=${status}`;
    const total = Math.max(1, summary.count);

    return (
        <>
            <PageHeader
                title="Reviews"
                description="Nothing appears on the site unless the candidate allowed it and you approve it."
                actions={
                    <Link href="/admin/coupons" className="flex items-center gap-2 rounded-lg border border-[var(--op-border)] bg-[var(--op-card)] px-3 py-2 text-sm hover:bg-[var(--op-hover)]">
                        <span className={cn("h-2 w-2 rounded-full", offerOn ? "bg-[var(--op-good)]" : "bg-[var(--op-faint)]")} />
                        Free-files offer is <strong>{offerOn ? "running" : "off"}</strong>
                    </Link>
                }
            />
            <div className="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
                <Card className="flex h-fit flex-col gap-3 p-5">
                    <div className="flex items-baseline gap-2">
                        <span className="op-num text-4xl font-semibold">{summary.average ?? "—"}</span>
                        {summary.average != null && <Stars rating={Math.round(summary.average)} />}
                    </div>
                    <span className="text-[13px] text-[var(--op-muted)]">
                        from {summary.count} review{summary.count === 1 ? "" : "s"}
                    </span>
                    {[5, 4, 3, 2, 1].map((star) => {
                        const n = summary.by_star[String(star)] ?? 0;
                        return (
                            <div key={star} className="flex items-center gap-2 text-[13px]">
                                <span className="w-6">{star}★</span>
                                <div className="h-2 flex-1 rounded-full bg-[var(--op-muted-bg)]">
                                    <div className="h-2 rounded-full bg-[var(--op-accent)]" style={{ width: `${(n / total) * 100}%` }} />
                                </div>
                                <span className="op-num w-8 text-right text-[var(--op-muted)]">{n}</span>
                            </div>
                        );
                    })}
                </Card>
                <div className="flex flex-col gap-3">
                    <div className="flex self-start rounded-lg bg-[var(--op-muted-bg)] p-0.5">
                        {TABS.map(([value, label]) => (
                            <Link
                                key={value || "all"}
                                href={`/admin/reviews?status=${value}`}
                                aria-current={status === value ? "page" : undefined}
                                className={cn("rounded-md px-3 py-1.5 text-[13px]", status === value ? "bg-[var(--op-card)] font-semibold shadow-[var(--op-shadow)]" : "text-[var(--op-muted)]")}
                            >
                                {label} <span className="op-num">{counts[value] ?? 0}</span>
                            </Link>
                        ))}
                    </div>
                    {reviews.length === 0 && (
                        <Card>
                            <Empty title={status === "pending" ? "Nothing to approve" : "No reviews here"}>Reviews arrive from the downloads screen and the delivery email.</Empty>
                        </Card>
                    )}
                    {reviews.map((review) => {
                        const low = (review.rating ?? 5) <= 2;
                        return (
                            <Card key={review.order_id} className={cn("flex flex-col gap-3 p-5", low && "border-[var(--op-bad)]")}>
                                <div className="flex flex-wrap items-center gap-2">
                                    <Stars rating={review.rating ?? 0} />
                                    <span className="flex-1 text-[13px] text-[var(--op-muted)]">
                                        {review.name || "No name"} · {review.exam_names.join(", ") || "exam not recorded"} · {when(review.at)} ·{" "}
                                        {review.source === "email" ? "email link" : "downloads screen"}
                                    </span>
                                    <Badge tone={review.may_publish ? "good" : "neutral"}>{review.may_publish ? "May be shown" : "Private"}</Badge>
                                </div>
                                {review.comment && <p className="m-0 text-base leading-relaxed">&ldquo;{review.comment}&rdquo;</p>}
                                {review.tags.length > 0 && (
                                    <div className="flex flex-wrap gap-1.5">
                                        {review.tags.map((tag) => (
                                            <Badge key={tag} tone={low ? "bad" : "neutral"}>
                                                {tag}
                                            </Badge>
                                        ))}
                                    </div>
                                )}
                                <div className="flex flex-wrap items-center gap-2">
                                    {review.status !== "approved" && (
                                        <ActionForm action={`/admin/actions/review/${review.order_id}`} back={back}>
                                            <input type="hidden" name="status" value="approved" />
                                            <Button type="submit" variant="primary" size="lg">
                                                Approve
                                            </Button>
                                        </ActionForm>
                                    )}
                                    {review.status !== "rejected" && (
                                        <ActionForm action={`/admin/actions/review/${review.order_id}`} back={back}>
                                            <input type="hidden" name="status" value="rejected" />
                                            <Button type="submit" size="lg">
                                                Reject
                                            </Button>
                                        </ActionForm>
                                    )}
                                    <span className="flex-1" />
                                    <span className="text-xs text-[var(--op-muted)]">
                                        {review.amount_paise != null ? rupees(review.amount_paise) : ""}
                                        {review.reward_code ? ` · earned ${review.reward_code}` : ""}
                                        {review.reviewed_by ? ` · ${review.status} by ${review.reviewed_by}` : ""}
                                    </span>
                                    <Link href={`/admin/orders?open=${review.order_id}`} className="text-[13px] text-[var(--op-muted)] underline">
                                        Open order
                                    </Link>
                                </div>
                            </Card>
                        );
                    })}
                </div>
            </div>
        </>
    );
}
