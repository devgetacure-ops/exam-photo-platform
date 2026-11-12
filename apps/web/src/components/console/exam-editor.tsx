"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Badge, Button, Card, Field, Input, Select, Textarea, cn } from "./ui";

/**
 * The whole of one examination's record, edited in the console (DEC-136).
 *
 * Forms for what changes most (names, the photograph's size and limits, each
 * file's limits and support), and the record itself under Advanced for
 * anything else. Nothing is saved until the engine has checked the whole
 * record against the schema; its problems are listed by field.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Rec = Record<string, any>;

const STATUSES = ["mandatory", "conditional", "optional", "portal_dependent"];
const SUPPORT = ["supported", "partially_supported", "guidance_only", "physical_stage", "not_yet_supported"];
const DIM_MODES = ["exact", "range", "unspecified"];
const BG_MODES = ["exact_colour", "plain_light", "plain_background", "unspecified"];
const UNIT_BYTES: Record<string, number> = { kb: 1000, mb: 1_000_000, b: 1 };

function get(obj: Rec, path: string): any {
    return path.split(".").reduce((o, k) => (o == null ? undefined : o[k]), obj);
}

function set(obj: Rec, path: string, value: any): Rec {
    const next: Rec = structuredClone(obj);
    const keys = path.split(".");
    let node = next;
    for (const key of keys.slice(0, -1)) {
        if (node[key] == null || typeof node[key] !== "object") node[key] = {};
        node = node[key];
    }
    const last = keys[keys.length - 1];
    if (value === undefined || value === "" || (Array.isArray(value) && value.length === 0)) delete node[last];
    else node[last] = value;
    return next;
}

const num = (value: string) => (value.trim() === "" ? undefined : Number(value));
const list = (value: string) =>
    value
        .split(/[\n,]/)
        .map((v) => v.trim())
        .filter(Boolean);

/** A size limit in the unit the notice used, kept in step with its bytes. */
function SizeFields({ rec, base, onChange }: { rec: Rec; base: string; onChange: (r: Rec) => void }) {
    const size = get(rec, base) ?? {};
    const unit = String(size.size_unit_as_published ?? "KB");
    const factor = UNIT_BYTES[unit.toLowerCase()] ?? 1000;
    const update = (which: "minimum" | "maximum", value: string) => {
        const n = num(value);
        let next = set(rec, `${base}.published_${which}`, n);
        next = set(next, `${base}.${which}_bytes`, n === undefined ? undefined : Math.round(n * factor));
        if (n !== undefined && !size.size_unit_as_published) next = set(next, `${base}.size_unit_as_published`, "KB");
        onChange(next);
    };
    return (
        <div className="grid grid-cols-2 gap-3">
            <Field label={`Smallest file (${unit})`}>
                <Input type="number" min={0} step="any" value={size.published_minimum ?? ""} onChange={(e) => update("minimum", e.target.value)} />
            </Field>
            <Field label={`Largest file (${unit})`}>
                <Input type="number" min={0} step="any" value={size.published_maximum ?? ""} onChange={(e) => update("maximum", e.target.value)} />
            </Field>
        </div>
    );
}

function DimensionFields({ rec, base, onChange }: { rec: Rec; base: string; onChange: (r: Rec) => void }) {
    const dims = get(rec, base) ?? {};
    const mode = dims.mode ?? "unspecified";
    return (
        <div className="grid grid-cols-3 gap-3">
            <Field label="Size rule">
                <Select value={mode} onChange={(e) => onChange(set(rec, `${base}.mode`, e.target.value))}>
                    {DIM_MODES.map((m) => (
                        <option key={m} value={m}>
                            {m}
                        </option>
                    ))}
                </Select>
            </Field>
            {mode === "exact" && (
                <>
                    <Field label="Width (px)">
                        <Input type="number" min={1} value={dims.width_px ?? ""} onChange={(e) => onChange(set(rec, `${base}.width_px`, num(e.target.value)))} />
                    </Field>
                    <Field label="Height (px)">
                        <Input type="number" min={1} value={dims.height_px ?? ""} onChange={(e) => onChange(set(rec, `${base}.height_px`, num(e.target.value)))} />
                    </Field>
                </>
            )}
            {mode === "range" && (
                <>
                    <Field label="Width from–to (px)">
                        <div className="flex gap-1.5">
                            <Input type="number" min={1} value={dims.min_width_px ?? ""} onChange={(e) => onChange(set(rec, `${base}.min_width_px`, num(e.target.value)))} />
                            <Input type="number" min={1} value={dims.max_width_px ?? ""} onChange={(e) => onChange(set(rec, `${base}.max_width_px`, num(e.target.value)))} />
                        </div>
                    </Field>
                    <Field label="Height from–to (px)">
                        <div className="flex gap-1.5">
                            <Input type="number" min={1} value={dims.min_height_px ?? ""} onChange={(e) => onChange(set(rec, `${base}.min_height_px`, num(e.target.value)))} />
                            <Input type="number" min={1} value={dims.max_height_px ?? ""} onChange={(e) => onChange(set(rec, `${base}.max_height_px`, num(e.target.value)))} />
                        </div>
                    </Field>
                </>
            )}
        </div>
    );
}

function FormatsField({ rec, base, onChange }: { rec: Rec; base: string; onChange: (r: Rec) => void }) {
    const formats: string[] = get(rec, `${base}.allowed_formats`) ?? [];
    return (
        <Field label="File types" hint="Comma-separated, e.g. jpg, jpeg">
            <Input value={formats.join(", ")} onChange={(e) => onChange(set(rec, `${base}.allowed_formats`, list(e.target.value.toLowerCase())))} />
        </Field>
    );
}

type Tab = "exam" | "photo" | "files" | "advanced";

export function ExamEditor({
    examId,
    initial,
    original,
    edited,
    editedAt,
}: {
    examId: string;
    initial: Rec;
    original: Rec | null;
    edited: boolean;
    editedAt: string | null;
}) {
    const [rec, setRec] = useState<Rec>(initial);
    const [saved, setSaved] = useState<Rec>(initial);
    const [isEdited, setIsEdited] = useState(edited);
    const [tab, setTab] = useState<Tab>("exam");
    const [busy, setBusy] = useState(false);
    const [problems, setProblems] = useState<{ field: string; message: string }[]>([]);
    const [json, setJson] = useState<string>(() => JSON.stringify(initial, null, 2));
    const [jsonError, setJsonError] = useState<string | null>(null);
    const dirty = useMemo(() => JSON.stringify(rec) !== JSON.stringify(saved), [rec, saved]);
    const requirements: Rec[] = rec.requirements ?? [];
    const others = requirements.map((r, i) => ({ r, i })).filter(({ r }) => r.requirement_type !== "photograph");
    const photoIndex = requirements.findIndex((r) => r.requirement_type === "photograph");

    const change = (next: Rec) => {
        setRec(next);
        setJson(JSON.stringify(next, null, 2));
        setProblems([]);
    };

    const save = async () => {
        setBusy(true);
        setProblems([]);
        try {
            const response = await fetch(`/admin/api/exams/${examId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ record: rec }),
            });
            const body = (await response.json().catch(() => ({}))) as { detail?: string; problems?: { field: string; message: string }[] };
            if (!response.ok) {
                setProblems(body.problems ?? [{ field: "", message: body.detail ?? `Not saved (${response.status}).` }]);
                toast.error("Not saved. Fix the problems listed and try again.");
                return;
            }
            setSaved(rec);
            setIsEdited(true);
            toast.success("Saved. Preparation uses it now; the site shows it within minutes.");
        } catch {
            toast.error("The console could not be reached. Nothing was saved.");
        } finally {
            setBusy(false);
        }
    };

    const revert = async () => {
        if (!window.confirm("Go back to the original record? Your edits to this examination are set aside.")) return;
        setBusy(true);
        try {
            const response = await fetch(`/admin/api/exams/${examId}`, { method: "DELETE" });
            if (!response.ok) {
                toast.error("Not reverted.");
                return;
            }
            const back = original ?? initial;
            setRec(back);
            setSaved(back);
            setJson(JSON.stringify(back, null, 2));
            setIsEdited(false);
            toast.success("Back to the original record.");
        } finally {
            setBusy(false);
        }
    };

    const applyJson = () => {
        try {
            const parsed = JSON.parse(json) as Rec;
            setRec(parsed);
            setJsonError(null);
            setProblems([]);
        } catch (error) {
            setJsonError(error instanceof Error ? error.message : "Not valid JSON");
        }
    };

    const TABS: [Tab, string][] = [
        ["exam", "Exam"],
        ["photo", "Photograph"],
        ["files", `Other files (${others.length})`],
        ["advanced", "Advanced"],
    ];

    return (
        <div className="flex flex-col gap-4">
            <div className="flex flex-wrap items-center gap-2">
                {isEdited ? <Badge tone="warn">Edited{editedAt ? ` · ${editedAt.slice(0, 10)}` : ""}</Badge> : <Badge>Original record</Badge>}
                {dirty && <Badge tone="info">Unsaved changes</Badge>}
                <div className="ml-auto flex flex-wrap gap-2">
                    {dirty && (
                        <Button type="button" onClick={() => change(saved)} disabled={busy}>
                            Discard
                        </Button>
                    )}
                    {isEdited && (
                        <Button type="button" onClick={revert} disabled={busy}>
                            Revert to original
                        </Button>
                    )}
                    <Button type="button" variant="primary" onClick={save} disabled={busy || !dirty}>
                        {busy ? "Saving…" : "Save"}
                    </Button>
                </div>
            </div>

            {problems.length > 0 && (
                <Card className="border-[var(--op-bad)] p-4">
                    <p className="m-0 mb-2 font-semibold text-[var(--op-bad)]">Not saved. The engine found:</p>
                    <ul className="m-0 flex list-none flex-col gap-1 p-0 text-sm">
                        {problems.map((p, i) => (
                            <li key={i}>
                                {p.field && <code className="mr-1.5 text-xs">{p.field}</code>}
                                {p.message}
                            </li>
                        ))}
                    </ul>
                </Card>
            )}

            <div className="flex gap-1 overflow-x-auto border-b border-[var(--op-border)]" role="tablist">
                {TABS.map(([id, label]) => (
                    <button
                        key={id}
                        type="button"
                        role="tab"
                        aria-selected={tab === id}
                        onClick={() => setTab(id)}
                        className={cn(
                            "whitespace-nowrap border-b-2 px-3 py-2 text-sm",
                            tab === id ? "border-[var(--op-accent)] font-semibold" : "border-transparent text-[var(--op-muted)]",
                        )}
                    >
                        {label}
                    </button>
                ))}
            </div>

            {tab === "exam" && (
                <Card className="flex flex-col gap-3 p-5">
                    <Field label="Name">
                        <Input value={get(rec, "exam.exam_name") ?? ""} onChange={(e) => change(set(rec, "exam.exam_name", e.target.value))} />
                    </Field>
                    <Field label="Short names" hint="One per line; the first is shown on cards and stamps. Searches match all of them.">
                        <Textarea rows={4} value={(get(rec, "exam.aliases") ?? []).join("\n")} onChange={(e) => change(set(rec, "exam.aliases", list(e.target.value)))} />
                    </Field>
                    <Field label="Conducting body">
                        <Input value={get(rec, "exam.conducting_body") ?? ""} onChange={(e) => change(set(rec, "exam.conducting_body", e.target.value))} />
                    </Field>
                    <div className="grid grid-cols-2 gap-3">
                        <Field label="Exam year">
                            <Input type="number" value={get(rec, "exam.examination_year") ?? ""} onChange={(e) => change(set(rec, "exam.examination_year", num(e.target.value)))} />
                        </Field>
                        <Field label="Application cycle">
                            <Input value={get(rec, "exam.application_cycle") ?? ""} onChange={(e) => change(set(rec, "exam.application_cycle", e.target.value))} />
                        </Field>
                    </div>
                    <p className="m-0 text-xs text-[var(--op-muted)]">The page address ({examId}) never changes, so links keep working.</p>
                </Card>
            )}

            {tab === "photo" &&
                (rec.image_requirements ? (
                    <Card className="flex flex-col gap-4 p-5">
                        <DimensionFields rec={rec} base="image_requirements.dimensions" onChange={change} />
                        <SizeFields rec={rec} base="image_requirements.file_size" onChange={change} />
                        <FormatsField rec={rec} base="image_requirements.formats" onChange={change} />
                        <div className="grid grid-cols-2 gap-3">
                            <Field label="Background">
                                <Select value={get(rec, "image_requirements.background.mode") ?? "unspecified"} onChange={(e) => change(set(rec, "image_requirements.background.mode", e.target.value))}>
                                    {BG_MODES.map((m) => (
                                        <option key={m} value={m}>
                                            {m}
                                        </option>
                                    ))}
                                </Select>
                            </Field>
                            <Field label="Colour" hint="When the background is an exact colour, e.g. white">
                                <Input value={get(rec, "image_requirements.background.required_colour") ?? ""} onChange={(e) => change(set(rec, "image_requirements.background.required_colour", e.target.value))} />
                            </Field>
                        </div>
                        <Field label="Face coverage target (%)" hint="As published, e.g. 80">
                            <Input type="number" min={0} max={100} value={get(rec, "image_requirements.composition.face_coverage_target") ?? ""} onChange={(e) => change(set(rec, "image_requirements.composition.face_coverage_target", num(e.target.value)))} />
                        </Field>
                        {photoIndex >= 0 && (
                            <Field label="Instructions as published" hint="Quoted on the page as the notice's own words; keep it matching the figures above">
                                <Textarea rows={3} value={requirements[photoIndex].content_instructions ?? ""} onChange={(e) => change(set(rec, `requirements.${photoIndex}.content_instructions`, e.target.value))} />
                            </Field>
                        )}
                    </Card>
                ) : (
                    <Card className="p-5 text-sm text-[var(--op-muted)]">This examination asks for no photograph.</Card>
                ))}

            {tab === "files" && (
                <div className="flex flex-col gap-3">
                    {others.length === 0 && <Card className="p-5 text-sm text-[var(--op-muted)]">No other files.</Card>}
                    {others.map(({ r, i }) => {
                        const base = `requirements.${i}`;
                        return (
                            <Card key={r.requirement_id ?? i} className="flex flex-col gap-3 p-5">
                                <div className="flex items-center gap-2">
                                    <strong>{r.requirement_name}</strong>
                                    <Badge>{r.requirement_type}</Badge>
                                </div>
                                <Field label="Name">
                                    <Input value={r.requirement_name ?? ""} onChange={(e) => change(set(rec, `${base}.requirement_name`, e.target.value))} />
                                </Field>
                                <div className="grid grid-cols-2 gap-3">
                                    <Field label="Required">
                                        <Select value={r.requirement_status ?? "mandatory"} onChange={(e) => change(set(rec, `${base}.requirement_status`, e.target.value))}>
                                            {STATUSES.map((s) => (
                                                <option key={s} value={s}>
                                                    {s}
                                                </option>
                                            ))}
                                        </Select>
                                    </Field>
                                    <Field label="We prepare it">
                                        <Select value={r.platform_support ?? "supported"} onChange={(e) => change(set(rec, `${base}.platform_support`, e.target.value))}>
                                            {SUPPORT.map((s) => (
                                                <option key={s} value={s}>
                                                    {s}
                                                </option>
                                            ))}
                                        </Select>
                                    </Field>
                                </div>
                                <Field label="Who it applies to">
                                    <Input value={r.applicability ?? ""} onChange={(e) => change(set(rec, `${base}.applicability`, e.target.value))} />
                                </Field>
                                <SizeFields rec={rec} base={`${base}.file_spec.file_size`} onChange={change} />
                                <FormatsField rec={rec} base={`${base}.file_spec.formats`} onChange={change} />
                                {get(rec, `${base}.file_spec.dimensions`) && <DimensionFields rec={rec} base={`${base}.file_spec.dimensions`} onChange={change} />}
                                <Field label="Instructions as published">
                                    <Textarea rows={3} value={r.content_instructions ?? ""} onChange={(e) => change(set(rec, `${base}.content_instructions`, e.target.value))} />
                                </Field>
                            </Card>
                        );
                    })}
                </div>
            )}

            {tab === "advanced" && (
                <Card className="flex flex-col gap-3 p-5">
                    <p className="m-0 text-sm text-[var(--op-muted)]">
                        The whole record. Edit anything here, then Apply and Save; the engine checks it against the schema before it is used.
                    </p>
                    <Textarea rows={28} spellCheck={false} className="font-mono text-xs" value={json} onChange={(e) => setJson(e.target.value)} />
                    {jsonError && <p className="m-0 text-sm text-[var(--op-bad)]">{jsonError}</p>}
                    <div>
                        <Button type="button" onClick={applyJson}>
                            Apply
                        </Button>
                    </div>
                </Card>
            )}
        </div>
    );
}
