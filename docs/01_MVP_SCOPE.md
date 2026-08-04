# MVP Scope Specification (01_MVP_SCOPE.md)

This document defines the functional scope of the Minimum Viable Product (MVP) and distinguishes it from deferred post-MVP capabilities.

> **Revised 2026-08-04.** The original scope described a one-click compliance
> pipeline. It is now larger in one specific way: the platform will **publish
> which photographs are rejected**, as a candidate-facing upload manual. That
> commitment changes what the minimum product is, because every published
> rejection criterion has to be defensible and every rejection the engine makes
> has to be correct. The disposition rules below (DEC-041) and the per-exam
> appearance rules (DEC-042) follow from it.

---

## 1. Included in the MVP

The MVP delivers a complete, automated compliance pipeline:

- **Curated Exam Selection**: A searchable, version-controlled library of top Indian exam rules.
- **Structured Examination Rules**: Schema-compliant rule records capturing dimensions, file sizes, format, filenames, **and per-exam candidate-appearance rules** (spectacles, headwear, expression, colour-vs-monochrome, printed name/date), carried per exam because conducting bodies contradict each other (DEC-042).
- **Secure Photo Upload**: Secure endpoints handling standard image formats (JPEG, PNG, WebP) with EXIF orientation normalizations.
- **File Validation**: Input sanitization verifying magic bytes and preventing exploits.
- **Source-Photo Disposition**: Every upload is classified **accept**, **warn** or **block** (DEC-041). The engine blocks only when it cannot produce a truthful output -- an undecodable file, no detectable face, or a genuinely ambiguous subject. **Appearance is never a blocking reason.** Everything else produces a photograph plus findings.
- **Candidate-Facing Findings**: Two severities. `likely_rejection` presents an acknowledgement step with retaking as the primary action and downloading as a quiet secondary; `possible_issue` is an inline notice. Download stays enabled in every non-blocked state.
- **Background Cleaning**: Portrait matting and replacement with the background colour the exam requires, recomputed on the planned crop region so the head receives the model's full resolution (DEC-040).
- **Intelligent Cropping**: Automatically handles Crop Mode A (exact aspect/dimensions) and Crop Mode B (head-centered with natural margins), with composition calibrated against approved reference outputs (DEC-037).
- **Natural Enhancement**: Corrections applied only where a capture defect is measured, and disclosed to the candidate (DEC-043). Corrects the capture -- flat tonal range, clipping, colour cast, softness -- never the subject.
- **Dimensions Handling**: Exact target sizing and aspect ratio enforcement.
- **Format Handling**: Outputs formatted strictly as required (typically JPEG).
- **Quality-Aware Compression**: Smart iteratively-optimized compression landing just below the maximum size limit.
- **Filename Handling**: Applies target naming schemas (e.g., `photograph.jpg` or `candidate_photo.jpg`).
- **Printed Name and Date Imprint**: Applied where the exam requires it (TNPSC, Kerala PSC, CBSE) and never where it is prohibited (Railways).
- **Final Validation**: Independent verification of the final output file format, dimensions, size, integrity, and crop ratios before delivery.
- **Preview & Download**: Clear side-by-side presentation and instant download link.
- **Published Upload Manual**: Candidate-facing guidance on the landing page covering how to photograph and upload, and what will be rejected. Every stated rule traces to a cited official source.
- **Re-upload & Reprocess**: Clear user guidance on failure with retry flows.
- **Temporary Storage & Deletion Lifecycle**: Files stored in private storage and purged automatically on window expiration.

---

## 2. Excluded from the MVP

These capabilities are explicitly excluded from the MVP baseline. They must not be implemented during initial development:

- **Commercial Payments**: Payment gateways, credits, subscriptions, or paid downloads.
- **Manual Composition Editors**: Interactive crop sliders, rotation dials, or manual adjustment panels.
- **Background Brush Tools**: Fine-grained pixel-level background erasure, restore brushes, or manual masking.
- **Cosmetic Retouching**: Skin smoothing, blemish removal, tooth whitening, or eye size scaling. **Also excluded: any enhancement targeting an absolute skin luminance**, which would lighten dark skin and breaches identity preservation (DEC-043).
- **Sunglasses, Headwear and Eye-Closure Detection**: Measured as unreliable with the shipped models and deferred to Milestone 23. Until a classifier is scored against the labelled fixture, these remain advisory text in the upload manual rather than engine findings.
- **Provenance and Recency Checks**: Whether a photograph is recent, live-captured, or the candidate's own cannot be established from pixels. These appear as guidance only, never as findings.
- **User Accounts & History**: Saved candidate profiles, photo history, or past download records.
- **Native Mobile Apps**: Android/iOS wrapper apps (mobile-responsiveness is required, but native wrappers are excluded).
- **Bulk Processing Tools**: Operational interfaces for batch processing uploads for multiple candidates.
- **Universal Exam Coverage**: Not supporting every Indian exam cycle on day one; only a vetted curated inventory.
- **Guaranteed Acceptance Claims**: The platform will never make claims guaranteeing acceptance by government portals.

---

## 3. Why blocking is deliberately narrow

Candidates come to the platform to receive a compliant photograph, not to be
assessed. A refusal and a silent failure are the same outcome to them, and both
lose the user. Blocking and warning demand the same corrective action -- retake
the photograph -- so blocking buys no additional protection while removing the
deliverable.

The error costs are asymmetric: a wrong warning is an annoyance, a wrong block
loses a user on a false premise. That asymmetry decides the design wherever a
detector can be wrong, which is most of them.

Deterrence is delivered by the interface, not the engine. "The engine refuses"
and "the interface asks you to confirm" are different guarantees, and only the
second is safe when a signal is imperfect.
