import type { Metadata } from "next";
import Link from "next/link";
import { when } from "../../../../lib/operator/format";
import { ActionForm, Badge, Button, Card, CardHeader, Check, Empty, Field, Input, PageHeader, Problem, Select, Textarea } from "../../../../components/console/ui";
import { engineJson, enginePost } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

export const metadata: Metadata = { title: "Marketing" };

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

export default async function MarketingPage({ searchParams }: { searchParams: Promise<{ segment?: string; target?: string; subject?: string; body?: string }> }) {
    const operator = await requireOperator();
    const draft = await searchParams;
    const loaded = await engineJson<CampaignsData>("/v1/operator/campaigns");
    if (!loaded.ok) return <Problem what="campaigns" error={loaded.error} />;
    const data = loaded.value;
    const segment = draft.segment && draft.segment in data.segments ? draft.segment : "";
    const target = draft.target ?? "";
    let preview: { count: number; sample: string[] } | null = null;
    if (segment && (!NEEDS_TARGET.has(segment) || target)) {
        const response = await enginePost("/v1/operator/campaigns/preview", { segment, target }).catch(() => null);
        preview = response?.ok ? ((await response.json()) as { count: number; sample: string[] }) : { count: 0, sample: [] };
    }
    const here = `/admin/marketing?${new URLSearchParams({ ...(segment ? { segment } : {}), ...(target ? { target } : {}) })}`;

    return (
        <>
            <PageHeader title="Marketing" description={`Email a group of customers. Every email has a one-click unsubscribe; ${data.unsubscribed} have unsubscribed and are never sent one.`} />
            {!data.links_signed && <Problem what="sending" error="Unsubscribe links cannot be signed: set EXAM_PHOTO_LINK_SECRET on the server." />}

            <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
                <Card>
                    <CardHeader title="1. Who" description="Choose a group, then count it." />
                    <form method="get" className="flex flex-col gap-4 p-5">
                        <Field label="Group">
                            <Select name="segment" defaultValue={segment}>
                                <option value="">Choose…</option>
                                {Object.entries(data.segments).map(([value, label]) => (
                                    <option key={value} value={value}>
                                        {label}
                                    </option>
                                ))}
                            </Select>
                        </Field>
                        <Field label="Examination" hint="Only for “paid for” and “asked for” one examination.">
                            <Select name="target" defaultValue={target}>
                                <option value="">—</option>
                                <optgroup label="Paid for">
                                    {data.exams.map((exam) => (
                                        <option key={exam.exam_id} value={exam.exam_id}>
                                            {exam.exam_name}
                                        </option>
                                    ))}
                                </optgroup>
                                <optgroup label="Asked for">
                                    {data.asked_exams.map((exam) => (
                                        <option key={exam} value={exam}>
                                            {exam}
                                        </option>
                                    ))}
                                </optgroup>
                            </Select>
                        </Field>
                        <input type="hidden" name="subject" value={draft.subject ?? ""} />
                        <input type="hidden" name="body" value={draft.body ?? ""} />
                        <Button type="submit" className="self-start">
                            Count them
                        </Button>
                        {preview && (
                            <div className="rounded-lg bg-[var(--op-muted-bg)] px-4 py-3 text-sm">
                                <strong className="op-num text-lg">{preview.count}</strong> {preview.count === 1 ? "person" : "people"}
                                {preview.sample.length > 0 && <div className="mt-1 truncate text-xs text-[var(--op-muted)]">{preview.sample.slice(0, 4).join(", ")}{preview.count > 4 ? "…" : ""}</div>}
                            </div>
                        )}
                        {segment && NEEDS_TARGET.has(segment) && !target && <p className="m-0 text-sm text-[var(--op-warn)]">Choose an examination for this group.</p>}
                    </form>
                </Card>

                <Card>
                    <CardHeader title="2. What" description="Plain text. A blank line starts a new paragraph." />
                    {!preview ? (
                        <Empty title="Choose who first">Count a group, then write the email here.</Empty>
                    ) : (
                        <div className="flex flex-col gap-4 p-5">
                            <ActionForm action="/admin/actions/campaign-test" back={here} className="flex flex-col gap-4">
                                <input type="hidden" name="keep_draft" value="yes" />
                                <Field label="Subject">
                                    <Input name="subject" maxLength={200} required defaultValue={draft.subject ?? ""} />
                                </Field>
                                <Field label="Message">
                                    <Textarea name="body" rows={8} maxLength={20000} required defaultValue={draft.body ?? ""} />
                                </Field>
                                <div className="flex flex-wrap items-end gap-2">
                                    <Field label="Send a test to" className="min-w-0 flex-1">
                                        <Input name="to" type="email" defaultValue={operator.includes("@") ? operator : ""} required />
                                    </Field>
                                    <Button type="submit">Send me a test</Button>
                                </div>
                            </ActionForm>
                            {draft.subject && draft.body && (
                                <ActionForm action="/admin/actions/campaign" back="/admin/marketing" className="flex flex-col gap-3 rounded-lg border border-[var(--op-border)] p-4">
                                    <input type="hidden" name="segment" value={segment} />
                                    <input type="hidden" name="target" value={target} />
                                    <input type="hidden" name="subject" value={draft.subject} />
                                    <input type="hidden" name="body" value={draft.body} />
                                    <p className="m-0 text-sm">
                                        Ready: <strong>{draft.subject}</strong> to <strong className="op-num">{preview.count}</strong> {preview.count === 1 ? "person" : "people"}.
                                    </p>
                                    <Check name="confirm" value="yes" required>
                                        Send it to all {preview.count} now
                                    </Check>
                                    <Button type="submit" variant="accent" size="lg" disabled={!preview.count || !data.links_signed} className="self-start">
                                        Send
                                    </Button>
                                </ActionForm>
                            )}
                            {!(draft.subject && draft.body) && <p className="m-0 text-xs text-[var(--op-muted)]">Send yourself a test first; the Send button appears after it.</p>}
                        </div>
                    )}
                </Card>
            </div>

            <Card>
                <CardHeader title="Sent" action={<Link href="/admin/coupons" className="text-[13px] text-[var(--op-muted)]">Coupons →</Link>} />
                {data.campaigns.length === 0 ? (
                    <Empty title="Nothing sent yet" />
                ) : (
                    <div className="op-scroll overflow-x-auto">
                        <table className="w-full min-w-[640px] border-collapse text-sm">
                            <thead>
                                <tr className="border-b border-[var(--op-border)] bg-[var(--op-muted-bg)] text-left text-xs text-[var(--op-muted)]">
                                    <th scope="col" className="px-5 py-2.5 font-medium">Subject</th>
                                    <th scope="col" className="px-3 py-2.5 font-medium">Group</th>
                                    <th scope="col" className="px-3 py-2.5 text-right font-medium">Sent</th>
                                    <th scope="col" className="px-3 py-2.5 font-medium">When</th>
                                    <th scope="col" className="px-5 py-2.5 font-medium">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.campaigns.map((campaign) => (
                                    <tr key={campaign.id} className="border-b border-[var(--op-border)] last:border-0">
                                        <td className="px-5 py-3 font-medium">{campaign.subject}</td>
                                        <td className="px-3 py-3 text-[var(--op-muted)]">{campaign.segment.replace(/_/g, " ")}</td>
                                        <td className="op-num px-3 py-3 text-right">
                                            {campaign.sent}/{campaign.total}
                                            {campaign.failed ? <span className="text-[var(--op-bad)]"> · {campaign.failed} failed</span> : null}
                                        </td>
                                        <td className="px-3 py-3 text-[var(--op-muted)]">{when(campaign.created_at)}</td>
                                        <td className="px-5 py-3">
                                            <Badge tone={campaign.status === "finished" ? "good" : "info"}>{campaign.status === "finished" ? "Finished" : "Sending"}</Badge>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </Card>
        </>
    );
}
