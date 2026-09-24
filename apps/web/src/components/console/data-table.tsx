"use client";

import {
    columnFilteringFeature,
    createFilteredRowModel,
    createPaginatedRowModel,
    createSortedRowModel,
    filterFns,
    globalFilteringFeature,
    rowPaginationFeature,
    rowSortingFeature,
    tableFeatures,
    useTable,
    type RowData,
} from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight, Search } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useMemo, type ReactNode } from "react";
import { cn } from "./ui";

/**
 * Every list in the console (DEC-113): sort by any column, filter as you type,
 * page through, and open a row in the side panel. On a phone each row becomes
 * a compact card from `mobile(row)`.
 */

export const features = tableFeatures({
    rowSortingFeature,
    sortedRowModel: createSortedRowModel(),
    columnFilteringFeature,
    globalFilteringFeature,
    filteredRowModel: createFilteredRowModel(),
    filterFns: { includesString: filterFns.includesString },
    rowPaginationFeature,
    paginatedRowModel: createPaginatedRowModel(),
});

export interface Column<T> {
    id: string;
    header: string;
    /** What sorting and filtering compare. */
    value: (row: T) => string | number | null | undefined;
    cell?: (row: T) => ReactNode;
    className?: string;
    align?: "right";
}

export interface Chip {
    label: string;
    value: string;
    count?: number;
    tone?: "bad" | "warn";
}

export function DataTable<T extends RowData>({
    rows,
    columns,
    rowId,
    mobile,
    searchPlaceholder = "Filter…",
    chips,
    chipParam = "state",
    selected,
    initialSort,
    pageSize = 25,
    empty,
    toolbar,
}: {
    rows: T[];
    columns: Column<T>[];
    rowId: (row: T) => string;
    mobile: (row: T) => ReactNode;
    searchPlaceholder?: string;
    chips?: Chip[];
    chipParam?: string;
    selected?: string | null;
    initialSort?: { id: string; desc: boolean };
    pageSize?: number;
    empty?: ReactNode;
    toolbar?: ReactNode;
}) {
    const router = useRouter();
    const pathname = usePathname();
    const params = useSearchParams();
    const activeChip = params.get(chipParam) ?? "";

    const defs = useMemo(
        () =>
            columns.map((column) => ({
                id: column.id,
                header: column.header,
                accessorFn: (row: T) => column.value(row) ?? "",
                enableSorting: true,
            })),
        [columns],
    );

    const table = useTable({
        features,
        data: rows,
        columns: defs,
        getRowId: (row: T) => rowId(row),
        initialState: {
            sorting: initialSort ? [initialSort] : [],
            pagination: { pageIndex: 0, pageSize },
            globalFilter: "",
        },
        globalFilterFn: "includesString",
    });

    const go = (update: Record<string, string | null>) => {
        const next = new URLSearchParams(params.toString());
        for (const [key, value] of Object.entries(update)) {
            if (value) next.set(key, value);
            else next.delete(key);
        }
        const query = next.toString();
        router.push(query ? `${pathname}?${query}` : pathname, { scroll: false });
    };
    const open = (id: string) => go({ open: id });

    const pageRows = table.getRowModel().rows;
    const filtered = table.getFilteredRowModel().rows.length;
    const { pageIndex } = table.state.pagination;
    const byId = new Map(columns.map((column) => [column.id, column]));

    return (
        <div className="flex flex-col gap-3">
            <div className="flex flex-wrap items-center gap-2">
                <label className="flex h-9 w-full items-center gap-2 rounded-lg border border-[var(--op-border)] bg-[var(--op-card)] px-3 sm:w-80">
                    <Search size={15} className="text-[var(--op-muted)]" aria-hidden="true" />
                    <input
                        aria-label={searchPlaceholder}
                        placeholder={searchPlaceholder}
                        value={String(table.state.globalFilter ?? "")}
                        onChange={(event) => table.setGlobalFilter(event.target.value)}
                        className="h-full flex-1 bg-transparent text-sm outline-none placeholder:text-[var(--op-faint)]"
                    />
                </label>
                {chips && (
                    <div className="op-scroll -mx-1 flex max-w-full gap-1.5 overflow-x-auto px-1">
                        {chips.map((chip) => {
                            const on = activeChip === chip.value;
                            return (
                                <button
                                    key={chip.value || "all"}
                                    type="button"
                                    onClick={() => go({ [chipParam]: chip.value || null, open: null })}
                                    aria-pressed={on}
                                    className={cn(
                                        "flex h-8 shrink-0 cursor-pointer items-center gap-1.5 rounded-full border px-3 text-[13px]",
                                        on
                                            ? "border-[var(--op-primary)] bg-[var(--op-primary)] text-[var(--op-primary-text)]"
                                            : "border-[var(--op-border)] bg-[var(--op-card)] hover:bg-[var(--op-hover)]",
                                    )}
                                >
                                    {chip.label}
                                    {chip.count !== undefined && (
                                        <span
                                            className={cn(
                                                "op-num font-semibold",
                                                !on && chip.tone === "bad" && chip.count > 0 && "text-[var(--op-bad)]",
                                                !on && chip.tone === "warn" && chip.count > 0 && "text-[var(--op-warn)]",
                                            )}
                                        >
                                            {chip.count}
                                        </span>
                                    )}
                                </button>
                            );
                        })}
                    </div>
                )}
                {toolbar && <div className="ml-auto flex items-center gap-2">{toolbar}</div>}
            </div>

            <div className="overflow-hidden rounded-xl border border-[var(--op-border)] bg-[var(--op-card)] shadow-[var(--op-shadow)]">
                {filtered === 0 ? (
                    empty ?? <p className="m-0 px-6 py-12 text-center text-[var(--op-muted)]">Nothing here.</p>
                ) : (
                    <>
                        <table className="hidden w-full border-collapse text-sm md:table">
                            <thead>
                                {table.getHeaderGroups().map((group) => (
                                    <tr key={group.id} className="border-b border-[var(--op-border)] bg-[var(--op-muted-bg)]">
                                        {group.headers.map((header) => {
                                            const column = byId.get(header.column.id);
                                            const sorted = header.column.getIsSorted();
                                            return (
                                                <th
                                                    key={header.id}
                                                    scope="col"
                                                    aria-sort={sorted === "asc" ? "ascending" : sorted === "desc" ? "descending" : undefined}
                                                    className={cn("px-4 py-2.5 text-left text-xs font-medium text-[var(--op-muted)]", column?.align === "right" && "text-right")}
                                                >
                                                    <button
                                                        type="button"
                                                        onClick={header.column.getToggleSortingHandler()}
                                                        className="inline-flex cursor-pointer items-center gap-1 hover:text-[var(--op-text)]"
                                                    >
                                                        {column?.header}
                                                        {sorted === "asc" && <ArrowUp size={12} aria-hidden="true" />}
                                                        {sorted === "desc" && <ArrowDown size={12} aria-hidden="true" />}
                                                    </button>
                                                </th>
                                            );
                                        })}
                                    </tr>
                                ))}
                            </thead>
                            <tbody>
                                {pageRows.map((row) => {
                                    const id = row.id;
                                    return (
                                        <tr
                                            key={id}
                                            onClick={() => open(id)}
                                            className={cn(
                                                "cursor-pointer border-b border-[var(--op-border)] last:border-0 hover:bg-[var(--op-hover)]",
                                                selected === id && "bg-[var(--op-accent-soft)] shadow-[inset_3px_0_0_var(--op-accent)]",
                                            )}
                                        >
                                            {columns.map((column, index) => (
                                                <td key={column.id} className={cn("px-4 py-3 align-middle", column.align === "right" && "text-right", column.className)}>
                                                    {index === 0 ? (
                                                        <button
                                                            type="button"
                                                            onClick={(event) => {
                                                                event.stopPropagation();
                                                                open(id);
                                                            }}
                                                            className="cursor-pointer text-left"
                                                        >
                                                            {column.cell ? column.cell(row.original) : String(column.value(row.original) ?? "—")}
                                                        </button>
                                                    ) : column.cell ? (
                                                        column.cell(row.original)
                                                    ) : (
                                                        String(column.value(row.original) ?? "—")
                                                    )}
                                                </td>
                                            ))}
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                        <ul className="m-0 list-none divide-y divide-[var(--op-border)] p-0 md:hidden">
                            {pageRows.map((row) => (
                                <li key={row.id}>
                                    <button
                                        type="button"
                                        onClick={() => open(row.id)}
                                        className={cn("block w-full cursor-pointer px-4 py-3 text-left active:bg-[var(--op-hover)]", selected === row.id && "bg-[var(--op-accent-soft)]")}
                                    >
                                        {mobile(row.original)}
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </>
                )}
                {filtered > 0 && (
                    <div className="flex items-center gap-2 border-t border-[var(--op-border)] px-4 py-2.5 text-[13px] text-[var(--op-muted)]">
                        <span className="op-num flex-1">
                            {pageIndex * pageSize + 1}–{Math.min((pageIndex + 1) * pageSize, filtered)} of {filtered}
                        </span>
                        <button
                            type="button"
                            aria-label="Previous page"
                            onClick={() => table.previousPage()}
                            disabled={!table.getCanPreviousPage()}
                            className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-lg border border-[var(--op-border)] disabled:opacity-40"
                        >
                            <ChevronLeft size={16} />
                        </button>
                        <button
                            type="button"
                            aria-label="Next page"
                            onClick={() => table.nextPage()}
                            disabled={!table.getCanNextPage()}
                            className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-lg border border-[var(--op-border)] disabled:opacity-40"
                        >
                            <ChevronRight size={16} />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
