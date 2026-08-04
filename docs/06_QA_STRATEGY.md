# Quality Assurance Strategy (06_QA_STRATEGY.md)

This document specifies the QA methodology, test categories, visual-regression workflows, and test fixture rules.

> **Revised 2026-08-04.** The original strategy assumed pixel-by-pixel golden
> images would carry visual verification. In practice they cannot: matting and
> crop output varies with model version and platform, and a pixel diff either
> fails on every rebuild or is set so loose it detects nothing. Visual quality
> is instead verified by **measuring the output and comparing the measurements
> against approved reference material**, which is what the sections below now
> describe.

---

## 1. Test Categories & Execution

- **Unit Tests**: Test single functions (e.g., coordinate scaling, rotation calculations).
- **Contract Tests**: Validate API data boundaries and models using JSON schema.
- **Schema-Validation Tests**: Verify JSON rule files parse correctly, including the `if`/`then` constraints on conditional appearance policies.
- **Pipeline-Stage Tests**: Individually test each processing block (orientation, crop, resize).
- **Integration Tests**: Execute processing on sample rules and mock files from beginning to end.
- **End-to-End Tests**: Run user simulation flows from landing page search to output file download.
- **Marker-Gated Model Suites**: Eleven `mandatory_*` markers covering segmentation, refinement, both crop modes, background, output preparation, compression, the rule pipeline, the API, the rule admin console, and engine quality. These require real model assets and checksum environment variables; `.github/workflows/image-engine-ci.yml` is the source of truth for the per-marker invocation. Skipping one without the model present fails the session.
- **Reference-Pair Benchmark**: `scripts/benchmark_reference_pairs.py` measures each engine output against its matched approved ideal -- crop dimensions, negative space left and right, headspace above the hair, space below the chin, and regional edge behaviour at hair, ears, beard line, chin and neck. Numeric only; no images enter version control.
- **Disposition Accuracy Gate**: `tests/fixtures/adversarial_label_map.json` records human labels for a 40-photograph adversarial set across eleven defect classes. Accuracy is scored against those labels, and the fixture also records where the engine deliberately disagrees with a label so the disagreement is not silently "fixed" later.
- **Policy Tests Without Models**: The disposition policy and enhancement planner consume measurements rather than pixels, so their thresholds are tested with no model present. This keeps the rules fast to test and lets measurement change without touching policy.
- **Compression Boundary Tests**: Assert output sizes are close to but under maximum limits.
- **Crop-Geometry Validation**: Verify head height, side margins, and centering ratios.
- **Filename/Format Validation**: Verify naming strings match regulations.
- **Privacy Lifecycle Tests**: Audit deletion timelines and verify files are completely removed.
- **Windows 64-bit Development Checks**: Ensure library compatibility under Windows environments.
- **Cross-Platform Checks**: Validate APIs and pipelines under Linux containers and MacOS.
- **Mobile Usability & Accessibility**: Enforce WCAG 2.1 compliance and responsive web interfaces.
- **Manual Quality Review**: Human inspection of segmentation edges and clothing blends. Retained deliberately: reviewer labels have twice caught defects every automated measure passed, including a frame-based exposure rule that flagged two correctly exposed night portraits as underexposed.

---

## 2. Calibration Discipline

Thresholds are calibrated against approved reference material, never against
values derived from first principles. Three rules follow from defects this
project has already shipped and had to correct:

1. **State the separation, not just the value.** A threshold comment must record
   what was measured on each side of it, so a later reader can tell whether a
   change moves a boundary or crosses a measurement.
2. **A label set is only evidence for what it labelled.** Photographs labelled
   for pose and compliance say nothing about their lighting, and must not be
   used to derive a photometric target.
3. **A signal is not shipped until its reliability is measured.** Eye-blink
   scoring and a chroma-noise guard were both written, measured, found not to
   separate, and removed rather than shipped as dead constants.

---

## 3. Privacy-Safe Fixture Policy

> [!CAUTION]
> **No real candidate photographs or outputs containing personal details may be committed to Git.**

The repository test suite must exclusively use:
1. **Synthetic Images**: Programmatically generated solid colors, grids, or geometric shapes.
2. **Public-Domain Images**: High-resolution portraits from public sources (e.g., CC0).
3. **Properly Licensed Images**: Stock photography with explicit licensing documentation.
4. **Explicitly Consented Test Images**: Team portraits with signed consent records.

Reference and adversarial photograph sets supplied by the product owner stay
**outside version control**. The repository may hold their measurements and
their labels -- numbers and defect classes referenced by filename -- but never
the images, alpha masks, or any facial embedding derived from them.
