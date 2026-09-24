import Link from "next/link";
import { ActionForm, Badge, Failure, Fact } from "../../../../components/operator/ui";
import { rupees, when } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

interface Review {
    order_id: string;
    at: string;
    rating: number | null;
    tags: string[];
    comment: string | null;
    name: string | null;
    may_publish: number;
    status: string;
    reviewed_at: string | null;
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
    ["pending", "Waiting"],
    ["approved", "Approved"],
    ["rejected", "Rejected"],
    ["", "All"],
];

const STATE_BADGE: Record<string, string> = { pending: "open", approved: "resolved", rejected: "unpaid" };

export default async function ReviewsPage({ searchParams }: { searchParams: Promise<{ status?: string }> }) {
    await requireOperator();
    const requested = (await searchParams).status;
    const status = requested === undefined ? "pending" : requested;
    const loaded = await engineJson<Reviews>(`/v1/operator/reviews?status=${encodeURIComponent(status)}`);
    if (!loaded.ok) return <Failure what="reviews" error={loaded.error} />;
    const { reviews, summary, offer_on: offerOn } = loaded.value;
    const back = `/admin/reviews?status=${status}`;

    return (
        <>
            <h1>Reviews</h1>
            <p className="euk-op-quiet">
                Nothing appears on the site unless the candidate allowed it and you approve it. The free-files offer is{" "}
                <Link href="/admin/coupons">{offerOn ? "running" : "off"}</Link>.
            </p>
            <dl className="euk-op-facts">
                <Fact label="Average rating" value={summary.average == null ? "—" : `${summary.average} ★ from ${summary.count}`} />
                <Fact
                    label="By stars"
                    value={Object.entries(summary.by_star)
                        .sort(([a], [b]) => Number(b) - Number(a))
                        .map(([star, count]) => `${star}★ ${count}`)
                        .join(" · ")}
                />
                <Fact label="Waiting for you" value={summary.pending} alarm={summary.pending > 0} />
                <Fact label="Approved" value={summary.approved} />
            </dl>
            <p className="euk-op-filter">
                {TABS.map(([value, label]) => (
                    <Link key={value || "all"} href={`/admin/reviews?status=${value}`} aria-current={status === value}>
                        {label}
                    </Link>
                ))}
            </p>
            {reviews.length === 0 && <p className="euk-op-quiet">None.</p>}
            <ul className="euk-op-list">
                {reviews.map((review) => (
                    <li key={review.order_id} className="euk-op-card" data-state={(review.rating ?? 5) <= 2 ? "refund-due" : undefined}>
                        <p className="euk-op-row">
                            <strong aria-label={`${review.rating ?? "no"} stars`}>
                                {"★".repeat(review.rating ?? 0)}
                                <span className="euk-op-quiet">{"★".repeat(5 - (review.rating ?? 0))}</span>
                            </strong>
                            <Badge state={STATE_BADGE[review.status] ?? review.status} />
                        </p>
                        {review.tags.length > 0 && <p>{review.tags.join(" · ")}</p>}
                        {review.comment && <p className="euk-op-message">&ldquo;{review.comment}&rdquo;</p>}
                        <p className="euk-op-quiet">
                            {review.name || "No name"} · {review.may_publish ? "may be shown on the site" : "private: never shown"} ·{" "}
                            {when(review.at)} · from {review.source === "email" ? "the email link" : "the downloads screen"}
                        </p>
                        <p className="euk-op-quiet">
                            <Link href={`/admin/orders/${review.order_id}`}>{review.exam_names.join(", ") || review.order_id}</Link>
                            {review.amount_paise != null ? ` · ${rupees(review.amount_paise)}` : ""} · {review.emails.join(", ") || "no email"}
                            {review.reward_code ? ` · earned ${review.reward_code}` : ""}
                            {review.reviewed_by ? ` · ${review.status} by ${review.reviewed_by}` : ""}
                        </p>
                        <p className="euk-op-filter">
                            {review.status !== "approved" && (
                                <ActionForm action={`/admin/actions/review/${review.order_id}`} back={back} className="euk-op-inline">
                                    <input type="hidden" name="status" value="approved" />
                                    <button type="submit" className="euk-op-button">
                                        Approve
                                    </button>
                                </ActionForm>
                            )}
                            {review.status !== "rejected" && (
                                <ActionForm action={`/admin/actions/review/${review.order_id}`} back={back} className="euk-op-inline">
                                    <input type="hidden" name="status" value="rejected" />
                                    <button type="submit" className="euk-op-button">
                                        Reject
                                    </button>
                                </ActionForm>
                            )}
                        </p>
                    </li>
                ))}
            </ul>
        </>
    );
}
