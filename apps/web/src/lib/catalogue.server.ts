/**
 * Build-time reader for the encoded examination catalogue.
 *
 * The catalogue is 39 generated JSON records that change only when
 * `scripts/encode_exam_rules.py` re-runs, which is a deliberate, versioned
 * event. So the read path does not belong on the network at all: these are read
 * from disk while the site builds, and the exam pages ship as real HTML.
 *
 * Three things follow from that, all of them wanted.
 *
 * **Exam pages are indexable.** The pricing strategy puts SEO first among
 * distribution channels and names exam requirement pages as the acquisition
 * asset. A page whose content arrives by client-side `fetch` is an empty
 * document to a crawler, and would forfeit that.
 *
 * **The catalogue survives the API being down.** Search, requirements and
 * specifications are static. The FastAPI service is needed only to *prepare* a
 * file, which is the one thing that genuinely cannot be precomputed.
 *
 * **Search is instant.** 39 records with their aliases is a few KB, so the
 * whole index ships with the page and predictive search costs no round trip.
 *
 * This module is server-only: it touches `fs` and must never be imported from a
 * client component. `api-client.ts` remains the browser's route to the service.
 */

import "server-only";

import { readFile, readdir } from "node:fs/promises";
import path from "node:path";

import type {
  ExamDetail,
  ExamSummary,
  PlatformSupport,
  RequirementCounts,
  RequirementSummary,
  SearchEntry,
  UnavailableExam,
} from "./types";

export type { SearchEntry } from "./types";

/**
 * The generated catalogue, relative to this file. Still named `examples/rules`
 * while holding the real records — renaming it touches the encoder, the gap
 * register and every documented path, so DEC-055 carries the name rather than
 * changing it.
 */
const CATALOGUE_DIR = path.join(process.cwd(), "..", "..", "examples", "rules");

const UNAVAILABLE_FILE = "unavailable_examinations.json";

/** Every `platform_support` value, so a count is never sparse (DEC-056). */
const SUPPORT_VALUES: PlatformSupport[] = [
  "supported",
  "partially_supported",
  "guidance_only",
  "physical_stage",
  "not_yet_supported",
];

interface RawRule {
  rule_id?: string;
  rule_version?: string;
  status?: string;
  fictional_example?: boolean;
  notes?: string;
  exam?: Record<string, unknown>;
  image_requirements?: Record<string, unknown>;
  requirements?: Record<string, unknown>[];
  provenance?: Record<string, { type?: string; [k: string]: unknown }>;
}

function countSupport(requirements: RequirementSummary[]): RequirementCounts {
  const counts: RequirementCounts = {};
  for (const value of SUPPORT_VALUES) counts[value] = 0;
  for (const requirement of requirements) {
    counts[requirement.platform_support] =
      (counts[requirement.platform_support] ?? 0) + 1;
  }
  return counts;
}

function toRequirement(raw: Record<string, unknown>): RequirementSummary {
  return {
    requirement_id: String(raw.requirement_id ?? ""),
    requirement_name: String(raw.requirement_name ?? ""),
    requirement_type: raw.requirement_type as RequirementSummary["requirement_type"],
    submission_method: raw.submission_method as RequirementSummary["submission_method"],
    requirement_status: raw.requirement_status as RequirementSummary["requirement_status"],
    platform_support: raw.platform_support as PlatformSupport,
    applicability: (raw.applicability as string) ?? null,
    content_instructions: (raw.content_instructions as string) ?? null,
    rejection_conditions: Array.isArray(raw.rejection_conditions)
      ? (raw.rejection_conditions as string[])
      : [],
    notes: (raw.notes as string) ?? null,
    file_spec: (raw.file_spec as Record<string, unknown>) ?? null,
  };
}

function toDetail(raw: RawRule): ExamDetail | null {
  const exam = raw.exam;
  if (!exam || typeof exam !== "object") return null;
  const examId = exam.exam_id;
  if (typeof examId !== "string" || examId.length === 0) return null;

  const requirements = Array.isArray(raw.requirements)
    ? raw.requirements.map(toRequirement)
    : null;

  return {
    exam_id: examId,
    exam_name: String(exam.exam_name ?? ""),
    conducting_body: String(exam.conducting_body ?? ""),
    examination_year: Number(exam.examination_year ?? 0),
    application_cycle: String(exam.application_cycle ?? ""),
    application_stage: (exam.application_stage as string) ?? null,
    jurisdiction: (exam.jurisdiction as string) ?? null,
    category: (exam.category as string) ?? null,
    aliases: Array.isArray(exam.aliases) ? (exam.aliases as string[]) : [],
    status: String(raw.status ?? ""),
    rule_id: String(raw.rule_id ?? ""),
    rule_version: String(raw.rule_version ?? ""),
    notes: raw.notes ?? null,
    requirements,
    requirement_counts: countSupport(requirements ?? []),
    image_requirements: raw.image_requirements ?? {},
    provenance: raw.provenance ?? {},
  };
}

/**
 * Every real examination record, ordered by name.
 *
 * Fictional records are excluded by their own `fictional_example` flag rather
 * than by filename, matching `rule_catalogue.py`: a benchmark fixture renamed
 * for any reason must not become an examination a candidate can select.
 *
 * A record that will not parse is skipped rather than thrown, for the same
 * reason the Python reader skips it — one malformed regeneration should cost
 * its own examination, not the entire catalogue. At build time a throw would
 * take down the whole site.
 */
export async function loadExams(): Promise<ExamDetail[]> {
  let names: string[];
  try {
    names = await readdir(CATALOGUE_DIR);
  } catch {
    return [];
  }

  const exams: ExamDetail[] = [];
  for (const name of names.sort()) {
    if (!name.endsWith(".json") || name === UNAVAILABLE_FILE) continue;
    let raw: RawRule;
    try {
      raw = JSON.parse(await readFile(path.join(CATALOGUE_DIR, name), "utf-8"));
    } catch {
      continue;
    }
    if (raw.fictional_example !== false) continue;
    const detail = toDetail(raw);
    if (detail) exams.push(detail);
  }

  return exams.sort((a, b) => a.exam_name.localeCompare(b.exam_name));
}

/** One examination, or `null` when the catalogue does not encode it. */
export async function loadExam(examId: string): Promise<ExamDetail | null> {
  const exams = await loadExams();
  return exams.find((exam) => exam.exam_id === examId) ?? null;
}

/**
 * The examinations the research covers that no rule record encodes.
 *
 * Shown in the picker rather than omitted (DEC-056): a candidate searching
 * SSC CGL and finding nothing concludes the platform does not cover it, and an
 * absence discovered at the portal is worse than one admitted here.
 */
export async function loadUnavailable(): Promise<UnavailableExam[]> {
  let payload: { examinations?: unknown };
  try {
    payload = JSON.parse(
      await readFile(path.join(CATALOGUE_DIR, UNAVAILABLE_FILE), "utf-8")
    );
  } catch {
    return [];
  }
  if (!Array.isArray(payload.examinations)) return [];

  return (payload.examinations as Record<string, unknown>[])
    .filter((item) => item && typeof item.exam_name === "string")
    .map((item) => ({
      exam_name: String(item.exam_name),
      reason: String(item.reason ?? ""),
      detail: String(item.detail ?? ""),
      non_photograph_deliverables: Number(item.non_photograph_deliverables ?? 0),
    }))
    .sort((a, b) => a.exam_name.localeCompare(b.exam_name));
}

/**
 * The whole picker's data, both halves, in one payload.
 *
 * Selectable and unavailable examinations stay in separate arrays rather than
 * one list with a flag — one is selectable and the other is not, and a single
 * list with a flag is how that distinction gets lost (DEC-056).
 */
export async function loadSearchIndex(): Promise<{
  exams: SearchEntry[];
  unavailable: SearchEntry[];
}> {
  const [exams, unavailable] = await Promise.all([loadExams(), loadUnavailable()]);

  return {
    exams: exams.map((exam) => ({
      id: exam.exam_id,
      name: exam.exam_name,
      body: exam.conducting_body,
      year: exam.examination_year,
      aliases: exam.aliases,
      prepares:
        (exam.requirement_counts.supported ?? 0) +
        (exam.requirement_counts.partially_supported ?? 0),
      total: exam.requirements?.length ?? 0,
    })),
    unavailable: unavailable.map((item) => ({
      id: "",
      name: item.exam_name,
      body: "",
      year: 0,
      aliases: [],
      prepares: 0,
      total: 0,
      unavailable: {
        reason: item.reason,
        detail: item.detail,
        deliverables: item.non_photograph_deliverables,
      },
    })),
  };
}

/** Summary rows for any surface that lists examinations without their inventory. */
export async function loadExamSummaries(): Promise<ExamSummary[]> {
  const exams = await loadExams();
  return exams.map((exam) => ({
    exam_id: exam.exam_id,
    exam_name: exam.exam_name,
    conducting_body: exam.conducting_body,
    examination_year: exam.examination_year,
    application_cycle: exam.application_cycle,
    application_stage: exam.application_stage,
    category: exam.category,
    aliases: exam.aliases,
    status: exam.status,
    requirement_counts: exam.requirement_counts,
    requirement_total: exam.requirements?.length ?? 0,
  }));
}
