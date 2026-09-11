import type { ExamDetail } from "./types";
import { isOurs } from "./kit-pricing";

export interface ReplacedTool {
    id: string;
    label: string;
}

/**
 * The separate tools a candidate would otherwise string together for this
 * application.
 *
 * Read from what this examination's own record asks of each file we prepare:
 * a background tool only when a background is specified, a resizer only when
 * a size is, a PDF merger only when there are documents. The list is never
 * longer than the job it describes, so it can be shown as a fact rather than
 * as a sales line.
 */
export function toolsReplaced(exam: ExamDetail): ReplacedTool[] {
    const tools = new Map<string, string>();
    const add = (id: string, label: string) => {
        if (!tools.has(id)) tools.set(id, label);
    };
    const image = (exam.image_requirements ?? {}) as Record<string, unknown>;

    for (const requirement of (exam.requirements ?? []).filter(isOurs)) {
        const type = requirement.requirement_type;
        const spec = (
            type === "photograph" ? image : (requirement.file_spec ?? {})
        ) as Record<string, unknown>;

        if (type === "certificate_scan" || type === "identity_document") {
            add("pdf", "An image-to-PDF converter");
            add("merge", "A PDF merger");
        } else {
            add("crop", "A photo cropper");
        }
        if (type === "photograph") {
            const background = spec.background as { mode?: string } | undefined;
            if (background?.mode && background.mode !== "unspecified") {
                add("background", "A background remover");
            }
        }
        if (spec.dimensions) add("resize", "An image resizer");
        if (spec.file_size) add("compress", "A file compressor");
        if (spec.formats) add("convert", "A format converter");
    }

    return [...tools].map(([id, label]) => ({ id, label }));
}
