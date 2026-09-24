import { Download } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { NotesSection } from "../../../../components/console/notes";
import { Sheet, SheetSection } from "../../../../components/console/sheet";
import { UploadsTable } from "../../../../components/console/tables";
import { when } from "../../../../lib/operator/format";
import { Facts, PageHeader, Problem, StateBadge, buttonStyles, cn } from "../../../../components/console/ui";
import { bytes, pictureFiles, type Note, type OperatorJob, type UploadRow } from "../../../../lib/operator/data";
import { engineJson, enginePost } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

export const metadata: Metadata = { title: "Uploads" };

const PERIODS: [number, string][] = [
    [1, "Today"],
    [7, "7 days"],
    [30, "30 days"],
    [365, "1 year"],
];

export default async function UploadsPage({ searchParams }: { searchParams: Promise<{ q?: string; days?: string; status?: string; open?: string }> }) {
    const operator = await requireOperator();
    const { q = "", days: rawDays, status = "", open } = await searchParams;
    const days = PERIODS.some(([d]) => d === Number(rawDays)) ? Number(rawDays) : 7;
    const loaded = await engineJson<{ uploads: UploadRow[] }>(`/v1/operator/uploads?q=${encodeURIComponent(q)}&days=${days}`);
    if (!loaded.ok) return <Problem what="uploads" error={loaded.error} />;
    const all = loaded.value.uploads;
    const pick = (value: string) => (value === "live" ? all.filter((u) => u.live) : value === "error" ? all.filter((u) => u.status === "error" || u.status === "failed") : all.filter((u) => u.status === value));
    const shown = status ? pick(status) : all;
    const chips = [
        { value: "", label: "All", count: all.length },
        { value: "live", label: "Photo still held", count: pick("live").length },
        { value: "succeeded", label: "Prepared", count: pick("succeeded").length },
        { value: "error", label: "Errors", count: pick("error").length, tone: "bad" as const },
        { value: "busy", label: "Refused, busy", count: pick("busy").length, tone: "warn" as const },
    ];
    const valid = open && /^job_[A-Za-z0-9_-]+$/.test(open);
    const [live, history] = valid
        ? await Promise.all([engineJson<OperatorJob>(`/v1/operator/jobs/${open}`), engineJson<UploadRow & { notes: Note[] }>(`/v1/operator/history/${open}`)])
        : [null, null];
    if (valid && (live?.ok || history?.ok)) {
        await enginePost("/v1/operator/activity", { actor: operator, action: "viewed upload", target: `upload:${open}` }).catch(() => null);
    }
    const period = (value: number) => `/admin/uploads?${new URLSearchParams({ ...(q ? { q } : {}), days: String(value), ...(status ? { status } : {}) })}`;

    return (
        <>
            <PageHeader
                title="Uploads"
                description="Every preparation, kept after the photograph is erased. The photograph shows only while it is still held."
                actions={
                    <>
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
                        <a href="/admin/export/uploads" download className={buttonStyles({ variant: "secondary" })}>
                            <Download size={15} aria-hidden="true" />
                            CSV
                        </a>
                    </>
                }
            />
            <UploadsTable uploads={shown} chips={chips} selected={open} />
            {valid && (live?.ok || history?.ok) && (
                <UploadSheet
                    jobId={open}
                    job={live?.ok ? live.value : null}
                    row={history?.ok ? history.value : null}
                    back={`/admin/uploads?${new URLSearchParams({ days: String(days), ...(status ? { status } : {}), open })}`}
                />
            )}
        </>
    );
}

function UploadSheet({ jobId, job, row, back }: { jobId: string; job: OperatorJob | null; row: (UploadRow & { notes: Note[] }) | null; back: string }) {
    const pictures = job ? pictureFiles(job) : [];
    const exam = job?.exam_name ?? row?.exam_name ?? job?.exam_id ?? row?.exam_id ?? "Upload";
    return (
        <Sheet
            title={`${exam} · ${row?.requirement_name ?? job?.requirement_name ?? "file"}`}
            subtitle={jobId}
            badge={row ? <StateBadge state={row.status} /> : undefined}
        >
            {job ? (
                <div className="grid grid-cols-2 gap-3">
                    {pictures.map((name) => (
                        <a key={name} href={`/admin/files/${jobId}/${name}`} target="_blank" rel="noreferrer" className="flex flex-col gap-1.5">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img src={`/admin/files/${jobId}/${name}`} alt={name} className="aspect-[3/4] w-full rounded-lg border border-[var(--op-border)] bg-[var(--op-muted-bg)] object-contain" />
                            <span className="text-xs text-[var(--op-muted)]">
                                {name.startsWith("input") ? "What they uploaded" : name === job.output_filename ? "Prepared file" : name}
                            </span>
                        </a>
                    ))}
                    {pictures.length === 0 && <p className="m-0 text-sm text-[var(--op-muted)]">No pictures in this upload.</p>}
                </div>
            ) : (
                <p className="m-0 rounded-lg bg-[var(--op-muted-bg)] px-3 py-2.5 text-sm text-[var(--op-muted)]">The photograph has been erased. Its record stays below.</p>
            )}
            {job && <p className="m-0 text-xs text-[var(--op-muted)]">Held until {when(job.expires_at)}. Opening it here is recorded in Activity.</p>}
            {row && (
                <Facts
                    rows={[
                        ["Uploaded", when(row.started_at)],
                        ["Took", row.processing_seconds != null ? `${row.processing_seconds.toFixed(1)} s` : null],
                        ["Outcome", row.outcome ?? row.status],
                        ["Uploaded size", bytes(row.input_bytes)],
                        ["Output", row.output_width ? `${row.output_width}×${row.output_height} px · ${bytes(row.output_bytes)}` : null],
                        ["Findings", (row.findings ?? []).join(", ").replace(/_/g, " ") || "none"],
                        ["Error", row.error],
                        ["Session", row.kit_id ? <code key="k" className="text-xs">{row.kit_id}</code> : null],
                    ]}
                />
            )}
            {row?.stage_ms && Object.keys(row.stage_ms).length > 0 && (
                <SheetSection title="Time per step">
                    <ul className="m-0 flex list-none flex-col gap-1.5 p-0 text-sm">
                        {Object.entries(row.stage_ms)
                            .sort(([, a], [, b]) => b - a)
                            .map(([stage, ms]) => (
                                <li key={stage} className="flex justify-between gap-3">
                                    <span>{stage.replace(/_/g, " ")}</span>
                                    <span className="op-num text-[var(--op-muted)]">{(ms / 1000).toFixed(2)} s</span>
                                </li>
                            ))}
                    </ul>
                </SheetSection>
            )}
            {job && (
                <details className="text-sm">
                    <summary className="cursor-pointer text-[13px] font-semibold uppercase tracking-wide text-[var(--op-muted)]">Everything the engine recorded</summary>
                    <pre className="op-scroll mt-2 max-h-96 overflow-auto rounded-lg bg-[var(--op-muted-bg)] p-3 text-xs">{JSON.stringify({ ...job, report: undefined }, null, 2)}</pre>
                    {job.report != null && <pre className="op-scroll mt-2 max-h-96 overflow-auto rounded-lg bg-[var(--op-muted-bg)] p-3 text-xs">{JSON.stringify(job.report, null, 2)}</pre>}
                </details>
            )}
            <NotesSection target={`upload:${jobId}`} back={back} notes={row?.notes ?? []} />
        </Sheet>
    );
}
