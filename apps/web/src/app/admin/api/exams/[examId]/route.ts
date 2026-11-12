import { revalidatePath } from "next/cache";

import { operatorFromHeaders } from "../../../../../lib/operator/access";
import { postedFromHere } from "../../../../../lib/operator/actions";
import { engineSend } from "../../../../../lib/operator/engine";

export const runtime = "nodejs";

/**
 * Save or revert one examination's record from the console's editor
 * (DEC-136). JSON in and out, so the editor can show each problem beside its
 * field instead of reloading. Access-checked like every operator route.
 */

const ID = /^[a-z0-9][a-z0-9-]{1,160}$/;

function refresh(examId: string) {
    for (const path of [
        `/exam/${examId}`,
        `/exam/${examId}/rules`,
        `/exam/${examId}/prepare`,
        `/hi/exam/${examId}`,
        `/hi/exam/${examId}/prepare`,
        "/exams",
        "/",
        "/search-index.json",
    ])
        revalidatePath(path);
}

async function guard(request: Request, examId: string): Promise<string | Response> {
    const actor = await operatorFromHeaders(request.headers);
    if (!actor) return new Response("Not found", { status: 404 });
    if (!postedFromHere(request.headers, request.headers.get("host")))
        return Response.json({ detail: "This must be sent from the operator page." }, { status: 403 });
    if (!ID.test(examId)) return Response.json({ detail: "Invalid examination." }, { status: 400 });
    return actor;
}

async function relay(response: Response): Promise<Response> {
    const body = await response.json().catch(() => ({ detail: `The engine answered ${response.status}.` }));
    return Response.json(body, { status: response.status, headers: { "Cache-Control": "private, no-store" } });
}

export async function PUT(request: Request, { params }: { params: Promise<{ examId: string }> }) {
    const { examId } = await params;
    const actor = await guard(request, examId);
    if (actor instanceof Response) return actor;
    let record: unknown;
    try {
        record = ((await request.json()) as { record?: unknown }).record;
    } catch {
        return Response.json({ detail: "Not a record." }, { status: 400 });
    }
    try {
        const response = await engineSend("PUT", `/v1/operator/exams/${examId}/record`, { actor, record });
        if (response.ok) refresh(examId);
        return relay(response);
    } catch {
        return Response.json({ detail: "The engine could not be reached. Nothing was changed." }, { status: 502 });
    }
}

export async function DELETE(request: Request, { params }: { params: Promise<{ examId: string }> }) {
    const { examId } = await params;
    const actor = await guard(request, examId);
    if (actor instanceof Response) return actor;
    try {
        const response = await engineSend(
            "DELETE",
            `/v1/operator/exams/${examId}/record?actor=${encodeURIComponent(actor)}`,
        );
        if (response.ok) refresh(examId);
        return relay(response);
    } catch {
        return Response.json({ detail: "The engine could not be reached. Nothing was changed." }, { status: 502 });
    }
}
