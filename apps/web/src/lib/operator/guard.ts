import "server-only";
import { headers } from "next/headers";
import { notFound } from "next/navigation";
import { operatorFromHeaders } from "./access";

/** Every operator page starts here; anyone else gets the ordinary 404. */
export async function requireOperator(): Promise<string> {
    const operator = await operatorFromHeaders(await headers());
    if (!operator) notFound();
    return operator;
}
