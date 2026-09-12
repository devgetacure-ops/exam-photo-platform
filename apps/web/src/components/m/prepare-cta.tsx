"use client";

import Link from "next/link";

import type { ExamDetail } from "../../lib/types";
import { isOurs, kitPrice, rupees } from "../../lib/kit-pricing";
import { ActionBar } from "./action-bar";

/**
 * What the examination page offers a phone: the count, the price, and one way
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

    if (ours.length === 0) return null;

    return (
        <div className="euk-m-only">
            <ActionBar
                note={
                    <>
                        <strong>
                            {price.kitChargeable > 0 ? rupees(price.kitAmount) : "Free"}
                        </strong>
                        {price.kitFiles} file{price.kitFiles === 1 ? "" : "s"}
                        {price.kitFree > 0 ? `, ${price.kitFree} free` : ""}
                    </>
                }
            >
                <Link href={`/exam/${exam.exam_id}/prepare`} className="primary-button">
                    Prepare my files
                </Link>
            </ActionBar>
        </div>
    );
}
