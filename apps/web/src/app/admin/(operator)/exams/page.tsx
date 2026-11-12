import type { Metadata } from "next";
import Link from "next/link";

import { ExamsTable } from "../../../../components/console/exams-table";
import { asDeadline, hasDates, type ExamRow } from "../../../../lib/operator/exam-rows";
import { Sheet, SheetSection } from "../../../../components/console/sheet";
import { ActionForm, Badge, Button, Check, Field, Input, PageHeader, Problem, buttonStyles } from "../../../../components/console/ui";
import { DEADLINES, deadlineStatus, todayKey } from "../../../../lib/deadlines";
import { engineJson } from "../../../../lib/operator/engine";
import { requireOperator } from "../../../../lib/operator/guard";

export const metadata: Metadata = { title: "Exams" };

/**
 * Every examination, its dates and whether its record was edited (DEC-136).
 * A row opens the dates in the side panel; the full record is edited on the
 * examination's own page. Replaces the Calendar, which it contains.
 */
export default async function ExamsPage({ searchParams }: { searchParams: Promise<{ show?: string; open?: string }> }) {
    await requireOperator();
    const { show = "", open } = await searchParams;
    const loaded = await engineJson<{ exams: ExamRow[] }>("/v1/operator/exams");
    if (!loaded.ok) return <Problem what="the examinations" error={loaded.error} />;
    const all = loaded.value.exams;
    const today = todayKey();
    const soon = (row: ExamRow) => {
        if (!hasDates(row)) return false;
        const status = deadlineStatus(asDeadline(row), today);
        return (status.state === "closing" || status.state === "extended" || status.state === "open") && (status.days ?? 99) <= 14;
    };
    const filters: Record<string, (row: ExamRow) => boolean> = {
        dates: hasDates,
        soon,
        none: (row) => !hasDates(row),
        edited: (row) => row.edited,
    };
    const shown = filters[show] ? all.filter(filters[show]) : all;
    const chips = [
        { value: "", label: "All", count: all.length },
        { value: "soon", label: "Closing in 14 days", count: all.filter(soon).length, tone: "warn" as const },
        { value: "dates", label: "With dates", count: all.filter(hasDates).length },
        { value: "none", label: "No dates", count: all.filter((r) => !hasDates(r)).length },
        { value: "edited", label: "Edited", count: all.filter((r) => r.edited).length },
    ];
    const selected = open ? all.find((row) => row.exam_id === open) : undefined;
    const back = `/admin/exams?${new URLSearchParams({ ...(show ? { show } : {}), ...(open ? { open } : {}) })}`;
    // Bundled rows that would fill a gap: dates where the console has none,
    // or a candidate count where one is missing (DEC-137).
    const notInEngine = DEADLINES.filter((entry) => {
        const row = all.find((r) => r.exam_id === entry.examId);
        if (!row) return false;
        return !hasDates(row) || (row.dates.candidates == null && entry.candidates != null);
    });

    return (
        <>
            <PageHeader
                title="Exams"
                description="All examinations. Open one to set its dates; edit its names, photograph, signature and documents on its own page. Changes reach the site within minutes."
                actions={
                    notInEngine.length > 0 ? (
                        <ActionForm action="/admin/actions/dates-import" back="/admin/exams?show=dates">
                            <input type="hidden" name="entries" value={JSON.stringify(notInEngine)} />
                            <Button type="submit">Fill {notInEngine.length} gaps from the bundled list</Button>
                        </ActionForm>
                    ) : null
                }
            />
            <ExamsTable exams={shown} chips={chips} selected={open ?? null} />

            {selected && (
                <Sheet
                    title={selected.exam_name}
                    subtitle={selected.conducting_body ?? undefined}
                    badge={selected.edited ? <Badge tone="warn">Edited record</Badge> : undefined}
                    actions={
                        <Link href={`/admin/exams/${selected.exam_id}`} className={buttonStyles({ variant: "primary", size: "sm" })}>
                            Edit the record
                        </Link>
                    }
                >
                    <SheetSection title="Dates">
                        <ActionForm action={`/admin/actions/exam-dates/${selected.exam_id}`} back={back} className="flex flex-col gap-3">
                            <div className="grid grid-cols-2 gap-3">
                                <Field label="Applications open">
                                    <Input type="date" name="opens_on" defaultValue={selected.dates.opens_on ?? ""} />
                                </Field>
                                <Field label="Last date">
                                    <Input type="date" name="closes_on" defaultValue={selected.dates.closes_on ?? ""} />
                                </Field>
                                <Field label="Extended to" hint="Only if the last date was extended">
                                    <Input type="date" name="extended_to" defaultValue={selected.dates.extended_to ?? ""} />
                                </Field>
                                <Field label="Exam date">
                                    <Input type="date" name="exam_date" defaultValue={selected.dates.exam_date ?? ""} />
                                </Field>
                            </div>
                            <Field label="Candidates" hint="How many sat it last time; bigger exams are shown first">
                                <Input inputMode="numeric" name="candidates" defaultValue={selected.dates.candidates ?? ""} placeholder="e.g. 1400000" />
                            </Field>
                            <Field label="Exam date note" hint="e.g. Prelims, or To be announced">
                                <Input name="exam_date_note" maxLength={120} defaultValue={selected.dates.exam_date_note ?? ""} />
                            </Field>
                            <Field label="Source" hint="The official notice the dates came from">
                                <Input type="url" name="source_url" maxLength={500} defaultValue={selected.dates.source_url ?? ""} placeholder="https://" />
                            </Field>
                            <div className="grid grid-cols-2 gap-3">
                                <Field label="Checked on">
                                    <Input type="date" name="last_verified" defaultValue={selected.dates.last_verified ?? today} />
                                </Field>
                                <Field label="Private note">
                                    <Input name="note" maxLength={300} defaultValue={selected.dates.note ?? ""} />
                                </Field>
                            </div>
                            <Check name="auto_remind" value="yes" defaultChecked={selected.dates.auto_remind}>
                                Email everyone who prepared files for it, 3 days before the last date
                            </Check>
                            <div className="flex gap-2">
                                <Button type="submit" variant="primary" size="sm">
                                    Save dates
                                </Button>
                            </div>
                            <p className="m-0 text-xs text-[var(--op-muted)]">Clear every date and save to take it off the site.</p>
                        </ActionForm>
                    </SheetSection>
                    <SheetSection title="On the site">
                        <div className="flex flex-col gap-1.5 text-sm">
                            <a className="underline" href={`/exam/${selected.exam_id}`} target="_blank" rel="noreferrer">
                                The examination&rsquo;s page ↗
                            </a>
                            <a className="underline" href="/deadlines" target="_blank" rel="noreferrer">
                                Application deadlines ↗
                            </a>
                        </div>
                    </SheetSection>
                </Sheet>
            )}
        </>
    );
}
