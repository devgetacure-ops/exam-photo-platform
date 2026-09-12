/**
 * What to do when the file you are looking at is done.
 *
 * The kit page used to offer whatever row came next in the list, always, with
 * an arrow beside it — including files the candidate had unticked, files they
 * had already prepared, and rows they complete themselves. That is a prompt
 * pointing at work nobody asked for.
 *
 * The rule here: a step is only offered from a file that is in the kit, it is
 * only ever a file that is also in the kit and still waiting, and once nothing
 * is waiting the only thing left to do is look at the lot and pay for it.
 */
export interface KitFile {
    requirementId: string;
    name: string;
}

export type NextStep =
    | { kind: "none" }
    | {
          kind: "file";
          requirementId: string;
          name: string;
          prepared: number;
          total: number;
      }
    | { kind: "review"; total: number };

export function nextStep({
    kit,
    included,
    prepared,
    current,
}: {
    /** Files we prepare, in the order the page lists them. */
    kit: KitFile[];
    /** The ids the candidate has ticked. */
    included: readonly string[];
    /** The ids that already have a prepared file. */
    prepared: readonly string[];
    /** The file being worked on. */
    current: string;
}): NextStep {
    const inKit = kit.filter((file) => included.includes(file.requirementId));
    if (!inKit.some((file) => file.requirementId === current)) {
        return { kind: "none" };
    }

    const isDone = (file: KitFile) => prepared.includes(file.requirementId);
    if (inKit.every(isDone)) return { kind: "review", total: inKit.length };

    const waiting = inKit.filter(
        (file) => file.requirementId !== current && !isDone(file),
    );
    if (waiting.length === 0) return { kind: "none" };

    const here = inKit.findIndex((file) => file.requirementId === current);
    const pick =
        waiting.find((file) => inKit.indexOf(file) > here) ?? waiting[0];

    return {
        kind: "file",
        requirementId: pick.requirementId,
        name: pick.name,
        prepared: inKit.filter(isDone).length,
        total: inKit.length,
    };
}
