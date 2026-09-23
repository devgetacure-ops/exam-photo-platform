import Link from "next/link";
import { Badge, Failure } from "../../../../components/operator/ui";
import { bytes, seconds, when, type UploadRow } from "../../../../lib/operator/data";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

const PERIODS = [1, 7, 30, 365];

export default async function UploadsPage({
    searchParams,
}: {
    searchParams: Promise<{ q?: string; days?: string; status?: string }>;
}) {
    await requireOperator();
    const { q = "", days: rawDays, status = "" } = await searchParams;
    const days = PERIODS.includes(Number(rawDays)) ? Number(rawDays) : 7;
    const loaded = await engineJson<{ uploads: UploadRow[] }>(
        `/v1/operator/uploads?q=${encodeURIComponent(q)}&days=${days}`,
    );
    if (!loaded.ok) return <Failure what="uploads" error={loaded.error} />;
    const all = loaded.value.uploads;
    const shown = status === "live" ? all.filter((row) => row.live) : status ? all.filter((row) => row.status === status) : all;
    const link = (next: Record<string, string>) =>
        `/admin/uploads?${new URLSearchParams({ ...(q ? { q } : {}), days: String(days), ...(status ? { status } : {}), ...next })}`;

    return (
        <>
            <h1>Uploads</h1>
            <p className="euk-op-quiet">
                Every preparation, kept after the photograph is erased. A picture shows only while the file is still held.
            </p>
            <form method="get" className="euk-op-search">
                <input name="q" type="search" defaultValue={q} placeholder="Exam, session or upload id" aria-label="Filter uploads" />
                <input type="hidden" name="days" value={days} />
                <button type="submit" className="euk-op-button">
                    Filter
                </button>
            </form>
            <p className="euk-op-filter">
                {PERIODS.map((period) => (
                    <Link key={period} href={link({ days: String(period) })} aria-current={period === days}>
                        {period === 1 ? "Today" : period === 365 ? "1 year" : `${period} days`}
                    </Link>
                ))}
            </p>
            <p className="euk-op-filter">
                {[
                    ["", `All (${all.length})`],
                    ["live", `Photo still held (${all.filter((r) => r.live).length})`],
                    ["succeeded", "Prepared"],
                    ["error", "Errors"],
                    ["busy", "Refused, busy"],
                ].map(([value, label]) => (
                    <Link key={value} href={link({ status: value })} aria-current={status === value}>
                        {label}
                    </Link>
                ))}
            </p>
            {shown.length === 0 && <p className="euk-op-quiet">None.</p>}
            <ul className="euk-op-uploads">
                {shown.map((row) => (
                    <li key={row.job_id}>
                        <Link href={`/admin/uploads/${row.job_id}`} className="euk-op-upload">
                            {row.live ? (
                                // eslint-disable-next-line @next/next/no-img-element
                                <img src={`/admin/files/${row.job_id}/input.jpg`} alt="" loading="lazy" />
                            ) : (
                                <span className="euk-op-erased" aria-hidden="true">
                                    erased
                                </span>
                            )}
                            <span>
                                <strong>{row.exam_name ?? row.exam_id ?? "No examination"}</strong> <Badge state={row.status} />
                                <br />
                                {row.requirement_name ?? row.requirement_type ?? "—"} · {seconds(row.processing_seconds)} · {bytes(row.input_bytes)} in
                                <br />
                                <span className="euk-op-quiet">
                                    {when(row.started_at)}
                                    {row.outcome ? ` · ${row.outcome}` : ""}
                                    {row.error ? ` · ${row.error}` : ""}
                                </span>
                            </span>
                        </Link>
                    </li>
                ))}
            </ul>
        </>
    );
}
