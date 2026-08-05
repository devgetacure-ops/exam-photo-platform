# Product Decisions (00_PRODUCT_DECISIONS.md)

This document records the foundational product decisions, recommendations, open issues, and planned future expansions.

---

## 1. Confirmed Product Decisions

These items represent confirmed capabilities and behaviors derived from the product foundation:

- **Examination-Specific Processing**: The platform is built around structured, cycle-specific exam guidelines rather than a generic passport photo tool. Selecting an exam is the mandatory first step.
- **Two Crop Modes**:
  - **Crop Mode A**: Executed when exact dimensions or aspect ratios are specified.
  - **Crop Mode B**: Executed when dimensions are omitted or specified as ranges.
- **Natural Framing Objective**: The primary composition goal is natural framing. Preserving visible hair volume, both ears (where visible in the source), the chin, and final beard lines is mandatory.
- **75–80% Face Coverage expected outcome**: Correct natural cropping should ordinarily yield ~75–80% face coverage. This is a visual guideline and diagnostic metric, not a hard rejection threshold. Differences in hair, beards, and face shape will not cause rejection. **Confirmed by measurement (2026-08-04)**: across 60 approved reference outputs the delivered head height runs 0.665 to 0.918 with a median of 0.855, so four of the approved outputs sit *below* 75%. Treating 75% as a floor would reject compositions the reviewer had already approved.
- **Identity Preservation**: No AI changes to facial geometry, eyes, nose, lips, expressions, or skin tones are allowed. Only restrained corrections (exposure, contrast, white balance, mild noise reduction, sharpening) are permitted. **This extends to lighting correction (DEC-043)**: any adjustment driving faces toward an absolute target luminance would lighten dark skin, so corrections are triggered by capture defects -- clipping, compressed tonal range, non-neutral illuminant, softness -- and never by how light or dark a subject is. A correctly exposed dark-skinned face is left untouched.
- **Accept, Warn or Block (DEC-041)**: The engine blocks only when it cannot produce a truthful output: an undecodable file, no detectable face, or a genuinely ambiguous subject. **Appearance is never a blocking reason.** Anything else produces a photograph together with findings at one of two severities, and deterrence is delivered by the interface rather than by refusing to process.
- **Published Rejection Criteria**: The platform will publish an upload manual stating what is rejected. Every published criterion must trace to a cited official source, and every rejection the engine makes must be defensible, because the two are the same promise.
- **Appearance Rules Are Per-Exam (DEC-042)**: Conducting bodies contradict each other on background colour, spectacles, smiling, printed name and date, and colour versus monochrome. No majority default is safe, so these are carried per exam with a three-state `permitted`/`prohibited`/`conditional` policy. An unspecified rule is neither permission nor prohibition.
- **Quality-Aware Compression**: The file size must approach but never exceed the official maximum allowed limit to maintain optimal quality. No fake byte padding or empty metadata padding is allowed.
- **Rule Provenance**: Stored rules must log rule cycle provenance (official source PDF/URL, page, section, text) and record status (`official`, `inferred`, or `platform default`).
- **Rule Versioning**: Rules are structured, reviewable, and versioned. Changes must keep older rule versions for reproducibility.
- **No Guaranteed Acceptance Claims**: The platform guarantees processing to match stored guidelines, but explicitly states it does *not* guarantee final acceptance by any external authority or portal.
- **Privacy-First Handling**: Photos are sensitive biometric data. The platform uses temporary storage with automated deletions, restricts staff access, and prohibits use of uploads for model training.
- **Exclusion of Payments in MVP**: The initial release does not include a payment gateway.
- **Exclusion of Advanced Editing in MVP**: Manual crop adjustments, background brush tools, and retouch tools are excluded from the MVP.

---

## 2. Implementation Recommendations

These items represent recommended technical approaches that are not yet binding:

- **Asynchronous Processing**: Introduce a message queue (e.g., Celery/Redis) if background segmentation or image rendering latency exceeds 1.5 seconds.
- **Client-Side Pre-Checks**: File size and format may be checked in the browser before upload to save bandwidth. **Face counting must not be**, and this recommendation is revised for that reason: a browser-side face check would reject uploads before the disposition policy ever sees them, which is the blocking behaviour DEC-041 exists to prevent. Server-side face counting also depends on a confidence ladder and a second-face size ratio that a lightweight client model cannot reproduce.
- **Metadata Stripping**: Recommended to strip all personal EXIF metadata (GPS location, device details) while preserving orientation tags to ensure privacy.
- **Diagnostic Logging**: Store calculated ratios (e.g., face-height ratio, side-margin ratio) in debug logs for pipeline tuning.

---

## 3. Unresolved Decisions

These issues represent ambiguities that must be settled in Phase 0:

- **Specific Launch Exam Inventory**: **Partially resolved (2026-08-04).** Input-side rules are researched for 48 examinations, and 11 are encoded from official sources: UPSC CSE, SSC CGL, IBPS PO, SBI PO, LIC AAO, JEE Main, NEET UG, GATE, RRB Level-1, TNPSC CTSE and CBSE registration. All 11 remain `provisional` because their **output specifications -- pixel dimensions, file size, DPI, filename -- are still unverified**, which is Milestone 19. The launch count beyond these 11 is Milestone 27.
- **Image Deletion Retention Window**: The exact time limit (e.g., 30 minutes, 2 hours, 24 hours) for retaining uploaded and processed images before automated deletion is not set.
- **File-Size Safety Margin**: The safety buffer size (e.g., 2 KB or 5% below maximum) to prevent rejection due to differences in filesystem byte calculation is not specified.

---

## 4. Explicit Future Features

Planned enhancements deferred to post-MVP releases:

- **Payment Gateway**: Monetization paths, paid downloads, and bundle credits.
- **Advanced Interactive Editors**: Manual adjustments, brush controls, and background restore tools.
- **Operational Dashboards**: Analytics on failure clusters and rule-correction frequency.
- **History Logs**: Candidate profiles and past processing history (subject to separate privacy guidelines).
