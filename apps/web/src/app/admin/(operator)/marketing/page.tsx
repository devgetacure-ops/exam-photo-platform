import Link from "next/link";
import { ActionForm, Badge, Failure } from "../../../../components/operator/ui";
import { when } from "../../../../lib/operator/data";
import { engineJson, enginePost } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

interface Campaign {
    id: string;
    created_at: string;
    actor: string;
    segment: string;
    subject: string;
    status: string;
    total: number;
    sent: number;
    failed: number;
}

interface CampaignsData {
    campaigns: Campaign[];
    segments: Record<string, string>;
    exams: { exam_id: string; exam_name: string }[];
    asked_exams: string[];
    unsubscribed: number;
    links_signed: boolean;
}

const NEEDS_TARGET = new Set(["paid_exam", "asked_exam"]);

export default async function MarketingPage({
    searchParams,
}: {
    searchParams: Promise<{ segment?: string; target?: string; subject?: string; body?: string; tested?: string }>;
}) {
    const operator = await requireOperator();
    const draft = await searchParams;
    const campaigns = await engineJson<CampaignsData>("/v1/operator/campaigns");
    if (!campaigns.ok) return <Failure what="campaigns" error={campaigns.error} />;
    const segment = draft.segment && draft.segment in campaigns.value.segments ? draft.segment : "";
    let preview: { count: number; sample: string[] } | null = null;
    if (segment) {
        const response = await enginePost("/v1/operator/campaigns/preview", { segment, target: draft.target ?? "" }).catch(() => null);
        preview = response?.ok ? ((await response.json()) as { count: number; sample: string[] }) : { count: 0, sample: [] };
    }

    return (
        <>
            <h1>Marketing</h1>

            <section className="euk-op-section">
                <h2>Send an email</h2>
                {!campaigns.value.links_signed && (
                    <p className="euk-op-failure">Sending is off: set EXAM_PHOTO_LINK_SECRET (or the operator token) so unsubscribe links can be signed.</p>
                )}
                <p className="euk-op-quiet">
                    Every email carries a one-click unsubscribe. {campaigns.value.unsubscribed} address
                    {campaigns.value.unsubscribed === 1 ? " has" : "es have"} unsubscribed and are never sent a campaign.
                </p>
                <form method="get" className="euk-op-form">
                    <label>
                        <span className="euk-label">Who</span>
                        <select name="segment" defaultValue={segment}>
                            <option value="">Choose…</option>
                            {Object.entries(campaigns.value.segments).map(([value, label]) => (
                                <option key={value} value={value}>
                                    {label}
                                </option>
                            ))}
                        </select>
                    </label>
                    <label>
                        <span className="euk-label">Examination (for the two per-examination groups)</span>
                        <select name="target" defaultValue={draft.target ?? ""}>
                            <option value="">—</option>
                            <optgroup label="Paid for">
                                {campaigns.value.exams.map((exam) => (
                                    <option key={exam.exam_id} value={exam.exam_id}>
                                        {exam.exam_name}
                                    </option>
                                ))}
                            </optgroup>
                            <optgroup label="Asked for">
                                {campaigns.value.asked_exams.map((exam) => (
                                    <option key={exam} value={exam}>
                                        {exam}
                                    </option>
                                ))}
                            </optgroup>
                        </select>
                    </label>
                    <input type="hidden" name="subject" value={draft.subject ?? ""} />
                    <input type="hidden" name="body" value={draft.body ?? ""} />
                    <button type="submit" className="euk-op-button">
                        Count them
                    </button>
                </form>
                {preview && (
                    <p>
                        <strong>{preview.count}</strong> recipient{preview.count === 1 ? "" : "s"}
                        {preview.sample.length > 0 ? `: ${preview.sample.slice(0, 5).join(", ")}${preview.count > 5 ? "…" : ""}` : ""}
                        {NEEDS_TARGET.has(segment) && !draft.target ? " (choose an examination)" : ""}
                    </p>
                )}
                {draft.tested && <p role="status">Test sent. Check your inbox, then send it below.</p>}
                {segment && (
                    <>
                        <ActionForm action="/admin/actions/campaign-test" back={`/admin/marketing?segment=${segment}&target=${encodeURIComponent(draft.target ?? "")}`}>
                            <input type="hidden" name="keep_draft" value="yes" />
                            <Compose subject={draft.subject} body={draft.body} />
                            <label>
                                <span className="euk-label">Send a test to</span>
                                <input name="to" type="email" defaultValue={operator.includes("@") ? operator : ""} required />
                            </label>
                            <button type="submit" className="euk-op-button">
                                Send me a test
                            </button>
                        </ActionForm>
                        <ActionForm action="/admin/actions/campaign" back="/admin/marketing">
                            <input type="hidden" name="segment" value={segment} />
                            <input type="hidden" name="target" value={draft.target ?? ""} />
                            <Compose subject={draft.subject} body={draft.body} />
                            <label className="euk-op-check">
                                <input type="checkbox" name="confirm" value="yes" required /> Send this to {preview?.count ?? 0} people now
                            </label>
                            <button type="submit" className="euk-op-button" disabled={!preview?.count || !campaigns.value.links_signed}>
                                Send
                            </button>
                        </ActionForm>
                    </>
                )}
            </section>

            <section className="euk-op-section">
                <h2>Sent</h2>
                {campaigns.value.campaigns.length === 0 && <p className="euk-op-quiet">Nothing sent yet.</p>}
                <ul className="euk-op-list">
                    {campaigns.value.campaigns.map((campaign) => (
                        <li key={campaign.id} className="euk-op-card">
                            <p className="euk-op-row">
                                <strong>{campaign.subject}</strong>
                                <Badge state={campaign.status === "finished" ? "resolved" : "answered"} />
                            </p>
                            <p className="euk-op-quiet">
                                {when(campaign.created_at)} · {campaign.segment} · {campaign.sent} of {campaign.total} sent
                                {campaign.failed ? ` · ${campaign.failed} failed` : ""} · by {campaign.actor}
                            </p>
                        </li>
                    ))}
                </ul>
            </section>

            <p className="euk-op-quiet">
                Coupon codes and the review offer are on <Link href="/admin/coupons">Coupons</Link>; reviews on{" "}
                <Link href="/admin/reviews">Reviews</Link>.
            </p>
        </>
    );
}

function Compose({ subject, body }: { subject?: string; body?: string }) {
    return (
        <>
            <label>
                <span className="euk-label">Subject</span>
                <input name="subject" maxLength={200} required defaultValue={subject ?? ""} />
            </label>
            <label>
                <span className="euk-label">Message (plain text; a blank line starts a paragraph)</span>
                <textarea name="body" rows={8} maxLength={20000} required defaultValue={body ?? ""} />
            </label>
        </>
    );
}
