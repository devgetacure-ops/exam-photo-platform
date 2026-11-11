"use client";

import Link from "next/link";

import type { ExamDetail } from "../../lib/types";
import { BILLING_ENABLED } from "../../billing/config";
import { kitPrice, rupees } from "../../billing/kit-pricing";
import { isOurs } from "../../lib/requirement-support";
import { ActionBar } from "./action-bar";
import { useLocale, useTr } from "../locale-context";
import { localePath } from "../../lib/i18n";

/**
 * What the examination page offers a phone: the count, the price (billing
 * only, DEC-127; free otherwise), and one way
 * in. The workspace itself is a desktop arrangement and is not shown here —
 * the flow at `/exam/[examId]/prepare` does that job a screen at a time.
 *
 * Everything else on the page stays: a candidate who wants to read the
 * specifications and the sources before starting still can, and a crawler
 * still gets the whole thing.
 */
export function PrepareCta({ exam }: { exam: ExamDetail }) {
    const requirements = exam.requirements ?? [];
    const ours = requirements.filter(isOurs);
    const price = kitPrice(
        requirements,
        ours.map((r) => r.requirement_id),
    );

    const tr = useTr();
    const locale = useLocale();
    if (ours.length === 0) return null;

    return (
        <div className="euk-m-only">
            <ActionBar
                note={
                    <>
                        <strong>
                            {BILLING_ENABLED && price.kitChargeable > 0
                                ? rupees(price.kitAmount)
                                : tr("Free", "मुफ़्त")}
                        </strong>
                        {tr(`${price.kitFiles} file${price.kitFiles === 1 ? "" : "s"}`, `${price.kitFiles} फ़ाइल`)}
                        {BILLING_ENABLED && price.kitFree > 0 ? `, ${price.kitFree} free` : ""}
                    </>
                }
            >
                <Link href={localePath(locale, `/exam/${exam.exam_id}/prepare`)} className="primary-button">
                    {tr("Prepare my files", "मेरी फ़ाइलें तैयार करें")}
                </Link>
            </ActionBar>
        </div>
    );
}
