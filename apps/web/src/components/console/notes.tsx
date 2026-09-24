import type { Note } from "../../lib/operator/data";
import { SheetSection } from "./sheet";
import { ActionForm, Button, Textarea } from "./ui";

/** Notes on anything (DEC-109): who wrote what, when, and a box to add one. */
export function NotesSection({ target, back, notes }: { target: string; back: string; notes: Note[] }) {
    return (
        <SheetSection title="Notes">
            {notes.length > 0 && (
                <ul className="m-0 flex list-none flex-col gap-2 p-0">
                    {notes.map((note, index) => (
                        <li key={index} className="rounded-lg bg-[var(--op-muted-bg)] px-3 py-2 text-sm">
                            <p className="m-0 whitespace-pre-wrap">{note.text}</p>
                            <p className="m-0 mt-1 text-xs text-[var(--op-muted)]">
                                {note.actor} · {new Date(note.at).toLocaleString("en-IN", { timeZone: "Asia/Kolkata", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
                            </p>
                        </li>
                    ))}
                </ul>
            )}
            <ActionForm action="/admin/actions/note" back={back} className="flex flex-col gap-2">
                <input type="hidden" name="target" value={target} />
                <Textarea name="text" rows={2} maxLength={4000} required placeholder="Add a note only you will see" aria-label="New note" />
                <Button type="submit" size="sm" className="self-start">
                    Save note
                </Button>
            </ActionForm>
        </SheetSection>
    );
}
