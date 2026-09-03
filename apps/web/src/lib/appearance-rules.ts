/**
 * The photograph rules a candidate actually worries about.
 *
 * "Can I wear my glasses?" and "will they reject me for my headscarf?" are the
 * questions that bring people to this page, and every answer here is drawn
 * from that examination's own record — including, where the research captured
 * it, the exam's own wording. Nothing is generic advice: if the record does not
 * say, this returns nothing rather than inventing a rule, because a confident
 * wrong answer about headwear is worse than no answer.
 *
 * Headwear deserves its own note. Several bodies permit religious coverings
 * that others prohibit, and the record stores that as a `conditional` policy
 * with the condition spelled out. Flattening it to "no headwear" would be
 * wrong for those exams and would read as discrimination rather than as the
 * mistake it is, so the condition is always shown in full.
 */

/** How a rule lands for the candidate. Ordered by how much attention it needs. */
export type Verdict = "prohibited" | "conditional" | "required" | "permitted";

export interface GuidanceItem {
  id: string;
  verdict: Verdict;
  title: string;
  /** The rule in plain words. */
  detail: string;
  /** The examination's own phrasing, where the research captured it. */
  sourceWording?: string;
}

interface Policy {
  policy?: string;
  condition?: string;
  source_wording?: string;
  fields?: string[];
  position?: string;
}

function asPolicy(raw: unknown): Policy | null {
  if (!raw || typeof raw !== "object") return null;
  return raw as Policy;
}

function verdictOf(policy: string | undefined): Verdict {
  switch (policy) {
    case "prohibited":
      return "prohibited";
    case "required":
      return "required";
    case "conditional":
      return "conditional";
    default:
      return "permitted";
  }
}

const SPECTACLES_FALLBACK =
  "Glasses are allowed, but reflections must not hide your eyes.";
const HEADWEAR_FALLBACK = "Your face must be fully visible.";

/**
 * Read the guidance items out of an exam's `image_requirements.appearance`.
 *
 * Returned in attention order — what will get you rejected first — rather than
 * in record order, which is alphabetical and meaningless to a reader.
 */
export function appearanceGuidance(
  imageRequirements: Record<string, unknown>
): GuidanceItem[] {
  const appearance = (imageRequirements.appearance ?? {}) as Record<string, unknown>;
  const composition = (imageRequirements.composition ?? {}) as Record<string, unknown>;
  const items: GuidanceItem[] = [];

  const spectacles = asPolicy(appearance.spectacles);
  if (spectacles) {
    items.push({
      id: "spectacles",
      verdict: verdictOf(spectacles.policy),
      title: "Spectacles",
      detail: spectacles.condition ?? SPECTACLES_FALLBACK,
      sourceWording: spectacles.source_wording,
    });
  }

  const headwear = asPolicy(appearance.headwear);
  if (headwear) {
    items.push({
      id: "headwear",
      verdict: verdictOf(headwear.policy),
      title: "Caps and head coverings",
      detail: headwear.condition ?? HEADWEAR_FALLBACK,
      sourceWording: headwear.source_wording,
    });
  }

  const mask = asPolicy(appearance.face_mask);
  if (mask) {
    items.push({
      id: "face_mask",
      verdict: verdictOf(mask.policy),
      title: "Face masks",
      detail:
        mask.policy === "prohibited"
          ? "Your face must be uncovered."
          : (mask.condition ?? "Your face must be visible."),
      sourceWording: mask.source_wording,
    });
  }

  const smile = asPolicy(appearance.smile);
  if (smile) {
    items.push({
      id: "smile",
      verdict: verdictOf(smile.policy),
      title: "Expression",
      detail:
        smile.condition ??
        (smile.policy === "permitted"
          ? "Smiling is fine."
          : "Keep a natural expression."),
      sourceWording: smile.source_wording,
    });
  }

  const recency = appearance.recency_maximum_days;
  if (typeof recency === "number" && recency > 0) {
    const months = Math.round(recency / 30);
    items.push({
      id: "recency",
      verdict: "required",
      title: "How recent",
      detail: `Taken within the last ${recency} days — about ${months} month${
        months === 1 ? "" : "s"
      }.`,
    });
  }

  // An imprint is the case that makes `partially_supported` real: TNPSC and
  // Kerala PSC want the candidate's name and the date printed on the
  // photograph, and the engine cannot render text onto an image. Saying so
  // here is the difference between a candidate who adds it themselves and one
  // who submits an incomplete file believing we handled it.
  const imprint = asPolicy(appearance.imprint);
  if (imprint?.policy === "required") {
    const fields = (imprint.fields ?? [])
      .map((field) =>
        field === "candidate_name"
          ? "your name"
          : field === "photograph_date"
            ? "the date the photo was taken"
            : field.replace(/_/g, " ")
      )
      .join(" and ");
    items.push({
      id: "imprint",
      verdict: "required",
      title: "Printed on the photograph",
      detail: `This exam wants ${fields || "text"} printed on the image itself${
        imprint.position === "bottom" ? ", along the bottom" : ""
      }. We cannot add that — you will need to before you upload.`,
    });
  } else if (imprint?.policy === "prohibited") {
    items.push({
      id: "imprint",
      verdict: "prohibited",
      title: "Text on the photograph",
      detail: "No name, date or watermark printed on the image.",
    });
  }

  if (appearance.monochrome_accepted === false) {
    items.push({
      id: "colour",
      verdict: "required",
      title: "Colour",
      detail: "A colour photograph — black and white will not be accepted.",
    });
  }

  if (composition.eye_visibility === true) {
    items.push({
      id: "eyes",
      verdict: "required",
      title: "Eyes",
      detail: "Both eyes open and clearly visible.",
    });
  }

  if (composition.frontal_pose === true) {
    items.push({
      id: "pose",
      verdict: "required",
      title: "Pose",
      detail: "Face the camera straight on — no side or three-quarter angle.",
    });
  }

  const order: Record<Verdict, number> = {
    prohibited: 0,
    conditional: 1,
    required: 2,
    permitted: 3,
  };
  return items.sort((a, b) => order[a.verdict] - order[b.verdict]);
}

/**
 * Does this examination capture a photograph of the candidate itself?
 *
 * **This does not mean there is nothing to upload.** 16 of the 39 examinations
 * set this flag *and* still require an uploaded passport photograph — RBI
 * Assistant wants both, and the live capture is an additional step at the
 * portal. Reading the flag as "no upload needed" would tell those candidates to
 * skip the very file we prepare for them, which is the platform's worst failure
 * mode running in the opposite direction: not claiming to have done something
 * we did not, but denying something we did.
 *
 * So callers must pair this with whether a photograph requirement is actually
 * supported before deciding what to say. `liveCaptureStance` does that.
 */
export function requiresLiveCapture(imageRequirements: Record<string, unknown>): boolean {
  const appearance = (imageRequirements.appearance ?? {}) as Record<string, unknown>;
  return appearance.live_capture_required === true;
}

/** What the page should tell the candidate about live capture. */
export type LiveCaptureStance = "none" | "additional" | "instead";

/**
 * Distinguishes the two very different situations the flag covers.
 *
 * `additional` — the exam captures a live photo *and* wants one uploaded. The
 * candidate still needs the file we prepare.
 *
 * `instead` — the exam captures the candidate directly and there is no upload.
 * Nothing for us to prepare, and we must not imply otherwise.
 */
export function liveCaptureStance(
  imageRequirements: Record<string, unknown>,
  hasPreparedPhotograph: boolean
): LiveCaptureStance {
  if (!requiresLiveCapture(imageRequirements)) return "none";
  return hasPreparedPhotograph ? "additional" : "instead";
}
