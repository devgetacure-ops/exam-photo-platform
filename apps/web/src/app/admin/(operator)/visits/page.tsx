import type { Metadata } from "next";
import Link from "next/link";
import { Sheet, SheetSection, Timeline } from "../../../../components/console/sheet";
import { VisitsTable } from "../../../../components/console/tables";
import { Facts, PageHeader, Problem, StateBadge, cn } from "../../../../components/console/ui";
import type { VisitDetail, VisitRow, VisitStage } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { stay, when } from "../../../../lib/operator/format";
import { requireOperator } from "../../../../lib/operator/guard";

export const metadata: Metadata = { title: "Visits" };

const PERIODS: [number, string][] = [
    [1, "Today"],
    [7, "7 days"],
    [30, "30 days"],
    [365, "1 year"],
];

/** Furthest first, as the engine ranks them (DEC-124). */
const STAGES: { value: VisitStage; label: string; tone?: "bad" | "warn" }[] = [
    { value: "downloaded", label: "Downloaded" },
    { value: "paid", label: "Paid" },
    { value: "payment", label: "Reached payment, didn't pay", tone: "warn" },
    { value: "uploaded", label: "Uploaded" },
    { value: "clicked", label: "Clicked" },
    { value: "browsed", label: "Browsed" },
    { value: "looked", label: "Just looked" },
];

function rupees(paise: number) {
    return `₹${(paise / 100).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
}

export default async function VisitsPage({ searchParams }: { searchParams: Promise<{ days?: string; stage?: string; open?: string }> }) {
    await requireOperator();
    const { days: rawDays, stage = "", open } = await searchParams;
    const days = PERIODS.some(([d]) => d === Number(rawDays)) ? Number(rawDays) : 7;
    const loaded = await engineJson<{ visits: VisitRow[] }>(`/v1/operator/visits?days=${days}`);
    if (!loaded.ok) return <Problem what="visits" error={loaded.error} />;
    const all = loaded.value.visits;
    const shown = stage ? all.filter((v) => v.stage === stage) : all;
    const chips = [{ value: "", label: "All", count: all.length }, ...STAGES.map((s) => ({ ...s, count: all.filter((v) => v.stage === s.value).length }))];
    const valid = open && /^[A-Za-z0-9_-]{8,64}$/.test(open);
    const detail = valid ? await engineJson<VisitDetail>(`/v1/operator/visits/${open}`) : null;
    const period = (value: number) => `/admin/visits?${new URLSearchParams({ days: String(value), ...(stage ? { stage } : {}) })}`;

    return (
        <>
            <PageHeader
                title="Visits"
                description="Every visit to the site and how far it got: the pages opened, every button and link tapped, uploads, payment and download."
                actions={
                    <div className="flex rounded-lg bg-[var(--op-muted-bg)] p-0.5">
                        {PERIODS.map(([value, label]) => (
                            <Link
                                key={value}
                                href={period(value)}
                                aria-current={value === days ? "page" : undefined}
                                className={cn("rounded-md px-3 py-1.5 text-[13px]", value === days ? "bg-[var(--op-card)] font-semibold shadow-[var(--op-shadow)]" : "text-[var(--op-muted)]")}
                            >
                                {label}
                            </Link>
                        ))}
                    </div>
                }
            />
            <VisitsTable visits={shown} chips={chips} selected={open} />
            {valid && detail?.ok && <VisitSheet visit={detail.value} />}
        </>
    );
}

function VisitSheet({ visit }: { visit: VisitDetail }) {
    const where = [visit.source, visit.device, visit.browser].filter(Boolean).join(" · ");
    return (
        <Sheet title={where || "Visit"} subtitle={`${when(visit.first_at)} · ${visit.session_id}`} badge={<StateBadge state={`visit-${visit.stage}`} />}>
            <Facts
                rows={[
                    ["Arrived", when(visit.first_at)],
                    ["Last seen", when(visit.last_at)],
                    ["Time on screen", stay(visit.active_seconds)],
                    ["Pages", String(visit.pages)],
                    ["Landed on", visit.landing ?? "/"],
                    ["Came from", visit.referrer_host ?? visit.source],
                    ["Campaign", visit.utm_campaign],
                    ["Connection", visit.connection],
                    ["Customer", visit.email],
                    ["Paid", visit.revenue_paise ? rupees(visit.revenue_paise) : null],
                ]}
            />
            <SheetSection title="What they did">
                {visit.events.length > 0 ? (
                    <Timeline events={visit.events.map((event) => ({ at: when(event.at), what: event.what, tone: event.tone ?? undefined }))} />
                ) : (
                    <p className="m-0 text-sm text-[var(--op-muted)]">Nothing recorded beyond the arrival.</p>
                )}
            </SheetSection>
        </Sheet>
    );
}
