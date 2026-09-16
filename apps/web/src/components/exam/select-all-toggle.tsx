"use client";

/**
 * One control for the whole selection, on the desktop kit and the phone flow.
 *
 * "Clear all" while anything is ticked; once nothing is, the same place says
 * "Select all", so a candidate who cleared by mistake gets the kit back with
 * one tap rather than ticking every row again. Unticking discards nothing: a
 * prepared file keeps its result and comes back with its row.
 */
export function SelectAllToggle({
    selected,
    onClear,
    onSelectAll,
    disabled = false,
    className,
}: {
    selected: number;
    onClear: () => void;
    onSelectAll: () => void;
    disabled?: boolean;
    className: string;
}) {
    const clearing = selected > 0;
    return (
        <button
            type="button"
            className={className}
            disabled={disabled}
            onClick={clearing ? onClear : onSelectAll}
        >
            {clearing ? "Clear all" : "Select all"}
        </button>
    );
}
