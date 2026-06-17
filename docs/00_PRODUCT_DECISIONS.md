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
- **75–80% Face Coverage expected outcome**: Correct natural cropping should ordinarily yield ~75–80% face coverage. This is a visual guideline and diagnostic metric, not a hard rejection threshold. Differences in hair, beards, and face shape will not cause rejection.
- **Identity Preservation**: No AI changes to facial geometry, eyes, nose, lips, expressions, or skin tones are allowed. Only restrained corrections (exposure, contrast, white balance, mild noise reduction, sharpening) are permitted.
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
- **Client-Side Pre-Checks**: Perform initial face count and file size checks in the user's browser before uploading to save bandwidth and compute cost.
- **Metadata Stripping**: Recommended to strip all personal EXIF metadata (GPS location, device details) while preserving orientation tags to ensure privacy.
- **Diagnostic Logging**: Store calculated ratios (e.g., face-height ratio, side-margin ratio) in debug logs for pipeline tuning.

---

## 3. Unresolved Decisions

These issues represent ambiguities that must be settled in Phase 0:

- **Specific Launch Exam Inventory**: The exact list of Indian exam cycles (e.g., UPSC, SSC, JEE, NEET) to include in the launch dataset is undetermined.
- **Image Deletion Retention Window**: The exact time limit (e.g., 30 minutes, 2 hours, 24 hours) for retaining uploaded and processed images before automated deletion is not set.
- **File-Size Safety Margin**: The safety buffer size (e.g., 2 KB or 5% below maximum) to prevent rejection due to differences in filesystem byte calculation is not specified.

---

## 4. Explicit Future Features

Planned enhancements deferred to post-MVP releases:

- **Payment Gateway**: Monetization paths, paid downloads, and bundle credits.
- **Advanced Interactive Editors**: Manual adjustments, brush controls, and background restore tools.
- **Operational Dashboards**: Analytics on failure clusters and rule-correction frequency.
- **History Logs**: Candidate profiles and past processing history (subject to separate privacy guidelines).
