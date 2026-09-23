import Link from "next/link";
import { notFound } from "next/navigation";
import { Badge, Fact, NotesBlock } from "../../../../../components/operator/ui";
import { bytes, pictureFiles, seconds, when, type Note, type OperatorJob, type UploadRow } from "../../../../../lib/operator/data";
import { engineJson, enginePost } from "../../../../../lib/operator/engine";
import { requireOperator } from "../../../../../lib/operator/guard";

export default async function UploadPage({ params }: { params: Promise<{ jobId: string }> }) {
    const operator = await requireOperator();
    const { jobId } = await params;
    if (!/^job_[A-Za-z0-9_-]+$/.test(jobId)) notFound();
    const [live, history] = await Promise.all([
        engineJson<OperatorJob>(`/v1/operator/jobs/${jobId}`),
        engineJson<UploadRow & { notes: Note[] }>(`/v1/operator/history/${jobId}`),
    ]);
    if (!live.ok && !history.ok) notFound();
    // Recorded, so the activity log shows who looked at a candidate's upload.
    await enginePost("/v1/operator/activity", { actor: operator, action: "viewed upload", target: `upload:${jobId}` }).catch(() => null);

    const job = live.ok ? live.value : null;
    const row = history.ok ? history.value : null;
    const pictures = job ? pictureFiles(job) : [];
    const exam = job?.exam_name ?? row?.exam_name ?? job?.exam_id ?? row?.exam_id ?? "Upload";
    const hidden = new Set(["files", "report"]);
    const rest = job ? Object.entries(job).filter(([key]) => !hidden.has(key)) : [];

    return (
        <>
            <p>
                <Link href="/admin/uploads">← Uploads</Link>
            </p>
            <h1>{exam}</h1>
            <p className="euk-op-quiet">
                {jobId} · {job ? `photo held until ${when(job.expires_at)}` : "photograph erased"}
            </p>

            {job && (
                <section className="euk-op-pictures" aria-label="Pictures">
                    {pictures.map((name) => (
                        <figure key={name}>
                            <a href={`/admin/files/${jobId}/${name}`} target="_blank" rel="noreferrer">
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img src={`/admin/files/${jobId}/${name}`} alt={name} />
                            </a>
                            <figcaption>
                                {name.startsWith("input") ? "What the candidate uploaded" : name === job.output_filename ? "Prepared file" : name}
                            </figcaption>
                        </figure>
                    ))}
                    {pictures.length === 0 && <p className="euk-op-quiet">No pictures in this upload.</p>}
                </section>
            )}

            {row && (
                <section className="euk-op-section">
                    <h2>
                        Preparation <Badge state={row.status} />
                    </h2>
                    <dl className="euk-op-facts">
                        <Fact label="File" value={row.requirement_name ?? row.requirement_type} />
                        <Fact label="Uploaded" value={when(row.started_at)} />
                        <Fact label="Finished" value={when(row.finished_at)} />
                        <Fact label="Time to prepare" value={seconds(row.processing_seconds)} />
                        <Fact label="Outcome" value={row.outcome} />
                        <Fact label="Uploaded size" value={bytes(row.input_bytes)} />
                        <Fact
                            label="Output"
                            value={row.output_width ? `${row.output_width} × ${row.output_height} px · ${bytes(row.output_bytes)}` : "—"}
                        />
                        <Fact label="Findings" value={(row.findings ?? []).join(", ") || "none"} />
                        <Fact label="Issue codes" value={(row.issue_codes ?? []).join(", ") || "none"} />
                        {row.error && <Fact label="Error" value={row.error} alarm />}
                        <Fact
                            label="Session"
                            value={row.kit_id ? <Link href={`/admin/search?q=${encodeURIComponent(row.kit_id)}`}>{row.kit_id}</Link> : "—"}
                        />
                    </dl>
                    {row.stage_ms && Object.keys(row.stage_ms).length > 0 && (
                        <details>
                            <summary>Time per pipeline stage</summary>
                            <table className="euk-op-table">
                                <tbody>
                                    {Object.entries(row.stage_ms).map(([stage, ms]) => (
                                        <tr key={stage}>
                                            <th scope="row">{stage}</th>
                                            <td>{(ms / 1000).toFixed(2)} s</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </details>
                    )}
                </section>
            )}

            {job && (
                <>
                    {(job.email_attempts ?? []).length > 0 && (
                        <section className="euk-op-section">
                            <h2>Emails</h2>
                            <ul className="euk-op-plain">
                                {(job.email_attempts ?? []).map((attempt, index) => (
                                    <li key={index}>
                                        {when(attempt.at)} to {attempt.masked_address} ·{" "}
                                        {attempt.succeeded ? "sent" : `failed: ${attempt.error ?? "unknown"}`}
                                    </li>
                                ))}
                            </ul>
                        </section>
                    )}
                    <section className="euk-op-section">
                        <h2>Files on disk</h2>
                        <ul className="euk-op-plain">
                            {(job.files ?? []).map((file) => (
                                <li key={file.name}>
                                    <a href={`/admin/files/${jobId}/${file.name}`} target="_blank" rel="noreferrer">
                                        {file.name}
                                    </a>{" "}
                                    · {bytes(file.bytes)}
                                </li>
                            ))}
                        </ul>
                    </section>
                    <section className="euk-op-section">
                        <h2>Everything the engine recorded</h2>
                        <dl className="euk-op-facts">
                            {rest.map(([key, value]) => (
                                <Fact key={key} label={key.replace(/_/g, " ")} value={show(key, value)} />
                            ))}
                        </dl>
                    </section>
                    {job.report != null && (
                        <section className="euk-op-section">
                            <h2>Pipeline report</h2>
                            <pre className="euk-op-pre">{JSON.stringify(job.report, null, 2)}</pre>
                        </section>
                    )}
                </>
            )}

            <NotesBlock target={`upload:${jobId}`} back={`/admin/uploads/${jobId}`} notes={row?.notes ?? []} />
        </>
    );
}

function show(key: string, value: unknown): string {
    if (value == null || value === "") return "—";
    if (typeof value === "boolean") return value ? "yes" : "no";
    if (typeof value === "string" && /_at$/.test(key)) return when(value);
    if (Array.isArray(value))
        return value.length ? value.map((v) => (typeof v === "object" ? JSON.stringify(v) : String(v))).join(", ") : "—";
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
}
