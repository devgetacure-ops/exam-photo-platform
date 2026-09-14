import { describe, expect, test, vi } from "vitest";

vi.mock("server-only", () => ({}));

import { loadExam, loadExams } from "../lib/catalogue.server";
import { examAnswers, examDescription, examSpecs } from "../lib/exam-answers";
import { breadcrumbs, pageMetadata, serializeJsonLd } from "../lib/site";
import { GET as sitemap } from "../app/sitemap.xml/route";
import { GET as llms } from "../app/llms.txt/route";

// Reading all 132 records takes several seconds, over the default 5 s timeout.

/**
 * Search, answer engines and link previews (DEC-087).
 *
 * The refusals lead: structured data cannot close its script tag, an answer
 * never states a figure the record does not hold, and an estimate is never
 * presented as published. Then that every examination is reachable from the
 * sitemap and from llms.txt.
 */

describe("what search and answer engines are told", () => {
    test("structured data cannot close its own script tag", () => {
        const out = serializeJsonLd({ name: "</script><script>alert(1)</script>" });
        expect(out).not.toContain("<");
        expect(JSON.parse(out).name).toBe("</script><script>alert(1)</script>");
    });

    test("no answer or description, for any examination, carries an empty or missing value", async () => {
        const exams = await loadExams();
        for (const summary of exams) {
            const exam = await loadExam(summary.exam_id);
            if (!exam) continue;
            const text = [...examAnswers(exam).map((a) => `${a.question} ${a.answer}`), examDescription(exam)].join(" ");
            expect(text, summary.exam_id).not.toMatch(/undefined|null|NaN|: ;|: \./);
        }
    }, 60_000);

    test("a figure that is our estimate is marked, in the answer and in the description", async () => {
        const exams = await loadExams();
        let checked = 0;
        for (const summary of exams) {
            const exam = await loadExam(summary.exam_id);
            if (!exam) continue;
            for (const spec of examSpecs(exam)) {
                const answer = examAnswers(exam).find((a) => a.question.startsWith(`What is the ${spec.label} size`));
                expect(answer, summary.exam_id).toBeDefined();
                const estimated = spec.rows.some((row) => row.estimated);
                expect(answer!.answer.includes("(est.)"), `${summary.exam_id} ${spec.label}`).toBe(estimated);
                checked += 1;
            }
        }
        expect(checked).toBeGreaterThan(100);
    }, 60_000);

    test("a file with no published figures gets no size question", async () => {
        const exams = await loadExams();
        for (const summary of exams) {
            const exam = await loadExam(summary.exam_id);
            if (!exam) continue;
            const labels = examSpecs(exam).map((spec) => spec.label);
            for (const answer of examAnswers(exam).filter((a) => a.question.includes(" size for "))) {
                expect(labels.some((label) => answer.question.startsWith(`What is the ${label} size`))).toBe(true);
            }
        }
    }, 60_000);

    test("a page that duplicates another is kept out of the index but still followed", () => {
        expect(pageMetadata({ title: "t", description: "d", path: "/x", index: false }).robots).toEqual({
            index: false,
            follow: true,
        });
        expect(pageMetadata({ title: "t", description: "d", path: "/x" }).robots).toBeUndefined();
    });

    test("breadcrumbs are absolute and in order", () => {
        const list = breadcrumbs([
            { name: "Home", path: "/" },
            { name: "All examinations", path: "/exams" },
        ]);
        expect(list.itemListElement.map((item) => item.position)).toEqual([1, 2]);
        expect(list.itemListElement[1].item).toMatch(/^https:\/\/.+\/exams$/);
    });

    test("the sitemap lists every examination, its rules and the PDF page", async () => {
        const xml = await (await sitemap()).text();
        const exams = await loadExams();
        expect(xml).toContain("/pdf</loc>");
        for (const exam of exams) expect(xml).toContain(`/exam/${encodeURIComponent(exam.exam_id)}/rules</loc>`);
    });

    test("llms.txt links every examination's rules", async () => {
        const text = await (await llms()).text();
        const exams = await loadExams();
        expect(text.startsWith("# ExamUploadKit")).toBe(true);
        for (const exam of exams) expect(text).toContain(`/exam/${encodeURIComponent(exam.exam_id)}/rules)`);
    });
});
