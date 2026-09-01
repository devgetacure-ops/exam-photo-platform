/**
 * The kit lives in the browser, and is lost with it (DEC-058).
 *
 * A kit is one examination's inventory in progress: which requirements have
 * been prepared, and which job on the server holds each result. Requirements
 * are completed in arbitrary order and potentially across several sittings, so
 * the mapping has to survive a page reload — but it is deliberately not a
 * server record. Candidate photographs are sensitive personal data under the
 * DPDP Act, where every additional retention surface is a liability to reason
 * about separately; the artifacts already sit under the job TTL and deletion
 * machinery, and putting the index here adds no new surface.
 *
 * Consequence, recorded rather than hidden: a candidate who switches device,
 * clears their browser data or opens the app in a private window loses their
 * kit, and the artifacts on the server become unreachable until the TTL
 * removes them. This is judged acceptable for a guest purchase with no
 * account. It stops being acceptable the moment the product grows accounts.
 */

import type { ApiJobStatus, PreparationOutcome, PrepareRequirementResponse } from "./types";

const STORAGE_KEY = "exam-photo:kits:v1";

/** Matches the server's `KIT_ID_REGEX` (`^kit_[A-Za-z0-9_-]{1,64}$`). */
export function isValidKitId(value: string): boolean {
  return /^kit_[A-Za-z0-9_-]{1,64}$/.test(value);
}

function mintKitId(): string {
  const random =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID().replace(/-/g, "")
      : Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2);
  return `kit_${random}`.slice(0, 68);
}

function nowIso(): string {
  return new Date().toISOString();
}

/** What one prepared requirement leaves in the kit. Enough to render a row without a refetch. */
export interface KitEntry {
  jobId: string;
  requirementId: string;
  requirementType: string;
  status: ApiJobStatus;
  outcome: PreparationOutcome;
  outputFilename?: string | null;
  outputMediaType?: string | null;
  /** Relative to the API base — resolve with `jobOutputUrl(jobId)`. */
  outputUrl?: string | null;
  reportUrl?: string | null;
  expiresAt?: string | null;
  findings: string[];
  updatedAt: string;
}

export interface KitState {
  kitId: string;
  examId: string;
  examName?: string;
  createdAt: string;
  updatedAt: string;
  /** requirement_id → the job that prepared it. */
  requirements: Record<string, KitEntry>;
}

type KitStore = Record<string, KitState>;

function readStore(): KitStore {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object") return {};
    return parsed as KitStore;
  } catch {
    // Private window, disabled storage, or corrupt JSON. A kit that cannot be
    // read is a kit that does not exist — the caller starts a fresh one.
    return {};
  }
}

function writeStore(store: KitStore): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  } catch {
    // Quota exceeded or storage blocked. The in-memory value the caller holds
    // is still correct for this session; nothing else we can do.
  }
}

/** Every kit currently held in this browser, most-recently-touched first. */
export function listKits(): KitState[] {
  return Object.values(readStore()).sort((a, b) =>
    b.updatedAt.localeCompare(a.updatedAt)
  );
}

/** The kit for one examination, or `null` if none has been started here. */
export function getKit(examId: string): KitState | null {
  return readStore()[examId] ?? null;
}

/**
 * The kit for one examination, creating it if this browser has never seen it.
 * Selecting an examination is what starts a kit — there is no separate step.
 */
export function startKit(examId: string, examName?: string): KitState {
  const store = readStore();
  const existing = store[examId];
  if (existing && isValidKitId(existing.kitId)) {
    if (examName && existing.examName !== examName) {
      existing.examName = examName;
      existing.updatedAt = nowIso();
      writeStore(store);
    }
    return existing;
  }
  const created: KitState = {
    kitId: mintKitId(),
    examId,
    examName,
    createdAt: nowIso(),
    updatedAt: nowIso(),
    requirements: {},
  };
  store[examId] = created;
  writeStore(store);
  return created;
}

/**
 * Record the result of a preparation against its requirement. Overwrites any
 * previous attempt for that requirement — the latest job is the one the kit
 * carries, and the earlier one falls to the server TTL.
 */
export function recordPreparation(
  examId: string,
  response: PrepareRequirementResponse,
  examName?: string
): KitState {
  const store = readStore();
  const kit = store[examId] ?? startKit(examId, examName);
  // `startKit` may have written; re-read so we extend the persisted copy.
  const current = readStore()[examId] ?? kit;

  current.requirements[response.requirement_id] = {
    jobId: response.job_id,
    requirementId: response.requirement_id,
    requirementType: response.requirement_type,
    status: response.status,
    outcome: response.outcome,
    outputFilename: response.output_filename ?? null,
    outputMediaType: response.output_media_type ?? null,
    outputUrl: response.output_url ?? null,
    reportUrl: response.report_url ?? null,
    expiresAt: response.expires_at ?? null,
    findings: response.findings ?? [],
    updatedAt: nowIso(),
  };
  current.updatedAt = nowIso();
  if (examName) current.examName = examName;

  const next = readStore();
  next[examId] = current;
  writeStore(next);
  return current;
}

/** Forget one requirement's result. Does not delete the server job — the caller does that. */
export function forgetRequirement(examId: string, requirementId: string): KitState | null {
  const store = readStore();
  const kit = store[examId];
  if (!kit) return null;
  delete kit.requirements[requirementId];
  kit.updatedAt = nowIso();
  writeStore(store);
  return kit;
}

/** Drop the whole kit from this browser. */
export function clearKit(examId: string): void {
  const store = readStore();
  if (!(examId in store)) return;
  delete store[examId];
  writeStore(store);
}
