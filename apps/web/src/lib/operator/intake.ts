import "server-only";
import type { CandidateRequest } from "../request-store";
import { enginePost } from "./engine";

/**
 * Put a saved form request into the operator's inbox (DEC-109).
 *
 * Best effort: the candidate's request is already saved to the requests
 * volume and has its reference, so a missing token or a busy engine must not
 * turn their receipt into an error. `euk-watch` still forwards it by email.
 */
export async function forwardToInbox(
    value: CandidateRequest,
    reference: string,
    env: Record<string, string | undefined> = process.env,
): Promise<boolean> {
    if (!env.EXAM_PHOTO_OPERATOR_TOKEN) return false;
    try {
        const response = await enginePost("/v1/operator/tickets", {
            kind: value.kind === "exam" ? "exam" : (value.topic ?? "support"),
            email: value.email,
            exam: value.exam,
            message: value.message,
            reference,
            payment_reference: value.payment_reference ?? null,
        });
        return response.ok;
    } catch {
        return false;
    }
}
