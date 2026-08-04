# Decision Log (08_DECISION_LOG.md)

This log tracks architectural and product decisions, open questions, and recommended paths.

## These entries are living records, not constraints

An entry records the best decision available when it was written, together with
the evidence behind it. When later measurement or a later product decision
contradicts one, **amend the entry** -- add an `Amended` block stating what
changed, when, and on what evidence, and update `Status` to `Superseded` if the
original decision no longer holds at all. Do not bend an implementation to
preserve a stale entry, and do not silently diverge from one either: an entry
that no longer matches the code is worse than no entry, because it is read as
current.

The evidence in a superseded entry stays valuable -- it records what was tried
and what it measured -- so entries are amended in place rather than deleted.

---

## Reusable Decision Template

```markdown
### [DEC-XXX]: [Decision Title]
- **Date**: YYYY-MM-DD
- **Status**: [Proposed | Under Review | Approved | Rejected]
- **Problem**: Describe the issue or architecture choice.
- **Options Considered**:
  - Option A: Pros and Cons.
  - Option B: Pros and Cons.
- **Decision**: Select one option.
- **Reasoning**: Why this choice was selected.
- **Consequences**: Downstream impacts on speed, security, and dependencies.
- **Affected Modules**: Which directories/packages are affected.
- **Approval Owner**: [Must refer to an official product manager or lead architect - leave empty if not assigned]
```

---

## 1. Initial Confirmed Decisions

### DEC-001: Mandatory Exam-Specific Workflow
- **Date**: 2026-06-17
- **Status**: Approved
- **Problem**: Should the platform allow generic cropping or force exam selection?
- **Decision**: Force exam selection first.
- **Reasoning**: Primary platform value lies in compliance rather than generic editing.
- **Consequences**: Restricts workflow but ensures compliance configurations are retrieved before upload.
- **Affected Modules**: `apps/web`, `packages/exam-rules`.
- **Approval Owner**: Lead Architect

### DEC-002: Revalidation Loop
- **Date**: 2026-06-17
- **Status**: Approved
- **Problem**: Can user adjustments bypass compliance checks?
- **Decision**: Any crop or background change triggers recalculation and compliance checking.
- **Reasoning**: Prevents users from exporting non-compliant images.
- **Consequences**: Slightly increases backend processing load.
- **Affected Modules**: `services/image-engine`.
- **Approval Owner**: Lead Architect

---

## 2. Unresolved Decisions (Requiring Owner Assignee)

### DEC-003: Final Retention Period
- **Date**: 2026-06-17
- **Status**: Under Review
- **Problem**: How long should candidate photographs be stored before automatic deletion?
- **Options Considered**:
  - Option A: Delete immediately after download.
  - Option B: Keep for 1 hour to support retries.
  - Option C: Keep for 24 hours.
- **Decision**: Under Review.
- **Reasoning**: Pending legal audit and user retry volume metrics.
- **Approval Owner**: *Unassigned*

---

## 3. Recommendations Requiring Approval

### DEC-004: Python Processing Toolkit
- **Date**: 2026-06-17
- **Status**: Proposed
- **Problem**: Core framework choice for head detection and background segmentation.
- **Options Considered**:
  - OpenCV + Custom algorithms.
  - MediaPipe for landmarks + ONNX runtime for segmentation.
- **Decision**: Proposed using MediaPipe and ONNX.
- **Reasoning**: MediaPipe offers robust landmark coordinates; ONNX enables decoupled, performant segmentation.
- **Approval Owner**: *Unassigned*

### DEC-005: Canonical Schema Nesting Structure
- **Date**: 2026-06-17
- **Status**: Approved
- **Problem**: Discrepancy between early schema structures in 03_EXAM_RULE_SCHEMA.md and nested layout required for Milestone 2.
- **Decision**: Adopt prompt's nested fields schema structure at root.
- **Reasoning**: Cleans up division of concerns between verification metadata, rules, and identity attributes.
- **Consequences**: Standardizes multi-language implementations.
- **Affected Modules**: `packages/exam-rules`, `services/image-engine`.
- **Approval Owner**: Lead Architect

### DEC-006: Byte Size Unit Normalization
- **Date**: 2026-06-17
- **Status**: Approved
- **Problem**: Whether Kilobyte limits are binary (1024 bytes) or decimal (1000 bytes) standard.
- **Decision**: Normalize values to binary base (1 KB = 1024 bytes) for safety boundary calculations.
- **Reasoning**: Standardizes maximum capacity limits on filesystems safely.
- **Consequences**: Enforces correct safety margins.
- **Affected Modules**: `services/image-engine`.
- **Approval Owner**: Lead Architect

### DEC-007: Canonical Working Image Mode
- **Date**: 2026-06-17
- **Status**: Approved
- **Problem**: Which in-memory colour layout should be used as the working standard?
- **Decision**: Enforce 8-bit RGBA as the canonical layout.
- **Reasoning**: Preserves alpha transparencies and ensures predictable channel layout for downstream segmentation.
- **Affected Modules**: `services/image-engine`.
- **Approval Owner**: Lead Architect

### DEC-008: Extension Mismatch Handling
- **Date**: 2026-06-17
- **Status**: Approved
- **Problem**: Action policy on files whose extension conflicts with true signature.
- **Decision**: Warn by default (using `INPUT_EXTENSION_MISMATCH`), parse the file according to its true bytes, but allow setting policy to "reject" via strict flag configuration.
- **Affected Modules**: `services/image-engine`.
- **Approval Owner**: Lead Architect

### DEC-009: Development Safety Defaults
- **Date**: 2026-06-17
- **Status**: Approved
- **Problem**: Unresolved final limits parameters for candidate uploads.
- **Decision**: Declare temporary safety defaults (maximum 10MB, max 8192x8192 resolution) to shield memory allocations from decompression exploits.
- **Affected Modules**: `services/image-engine`.
- **Approval Owner**: Lead Architect

### DEC-010: Suitability Evaluator Orchestration & Status
- **Date**: 2026-06-17
- **Status**: Approved
- **Problem**: Design of suitability statuses and indeterminate logic when providers are missing.
- **Decision**: Adopt four statuses: suitable, suitable_with_warnings, unsuitable, indeterminate. If required providers are missing, status defaults to indeterminate rather than passing.
- **Affected Modules**: `services/image-engine/suitability`.
- **Approval Owner**: Lead Architect

### DEC-011: Unresolved Suitability Benchmarks (Requiring Owner Assignee)
- **Date**: 2026-06-17
- **Status**: Under Review
- **Problem**: Unresolved final values for thresholds (blur warning/blocking limits, mean luminance limits, pose limits).
- **Options Considered**:
  - Option A: Benchmarking threshold values against candidate upload distributions.
- **Decision**: Logged as unresolved; tuning is deferred to later milestones.
- **Approval Owner**: *Unassigned*

### DEC-012: Face Detection Technology Integration
- **Date**: 2026-06-17
- **Status**: Approved
- **Problem**: Selection and integration of local face detection technology and baseline model variant.
- **Decision**: Select MediaPipe Face Detector (`mediapipe~=0.10.35`) as the provider, and `blaze_face_short_range.tflite` as the baseline model variant. Independent model card license verified as Apache-2.0.
- **Affected Modules**: `services/image-engine`.
- **Approval Owner**: Lead Architect

### DEC-013: Landmark-Assisted Geometric Head-Box Estimation Baseline Selection
- **Date**: 2026-06-17
- **Status**: Approved
- **Problem**: Selection of a local CPU-compatible baseline approach for provisional head-region estimation.
- **Options Considered**:
  - Option A: Landmark-Assisted Geometric Heuristic Expansion. Pros: 0 MB size, < 0.1 ms latency, 100% deterministic, no external dependencies, high privacy. Cons: Heuristic vertical/horizontal bounds (cannot observe actual hairline or chin boundaries).
  - Option B: Dense Face Mesh / 3D Landmark Estimation. Pros: 468+ detailed landmarks. Cons: ~10 MB weights, ~40 ms latency, landmarks do not cover hair or ear boundaries.
  - Option C: Dedicated Head Detection Models. Pros: Encloses hair/ears. Cons: 15–50 MB weights, ~100 ms latency, license complexities, high compute overhead.
- **Decision**: Adopt Option A (Landmark-Assisted Geometric Heuristic Expansion) as the provisional baseline.
- **Reasoning**: It is extremely fast, lightweight, introduces no new runtime dependencies, and is fully deterministic, providing a safe fallback crop frame.
- **Consequences**: Boundary visibility states remain "unknown" or "geometry_inferred" / "landmark_inferred" (cannot report "observed"). Clamping to image bounds reports clipping as "suspected" instead of "confirmed".
- **Affected Modules**: `services/image-engine/providers`, `services/image-engine/suitability`.
- **Approval Owner**: Lead Architect

### DEC-014: Portrait Segmentation Technology and Baseline Selection
- **Date**: 2026-06-18
- **Status**: Approved
- **Problem**: Selection and integration of local CPU-capable portrait segmentation technology and baseline model variant.
- **Options Considered**:
  - Option A: MediaPipe Selfie Multiclass (`selfie_multiclass_256x256.tflite`). Pros: 6-class output (background, hair, body skin, face skin, clothing, accessories) enables precise validation rules. Cons: ~16.4 MB model size, heavy CPU latency (~144ms inference, up to ~1570ms total pipeline resolution).
  - Option B: MediaPipe Selfie Binary (`selfie_segmentation.tflite`). Pros: Highly lightweight (~0.25 MB), fast CPU latency (~7-24ms inference, ~22ms to ~737ms total pipeline duration), robust foreground separation. Cons: Only outputs 2-class binary mask (person vs. background), no class-specific granularity.
- **Decision**: Approve both models behind the `SubjectSegmentationProvider` interface. Use **MediaPipe Selfie Binary** (`selfie_bin_general`) as the default baseline. MediaPipe Selfie Multiclass remains supported as an optional diagnostic variant.
- **Reasoning**: MediaPipe Selfie Binary General executes significantly faster with a tiny footprint, making it the most practical runtime baseline for offline CPU execution.
- **Affected Modules**: `services/image-engine/providers/segmenters`, `services/image-engine/suitability`.
- **Approval Owner**: Lead Architect


### DEC-015: Foreground Refinement Technology Selection
- **Date**: 2026-06-18
- **Status**: Approved
- **Problem**: Selection and integration of local CPU-capable foreground mask refinement technology.
- **Options Considered**:
  - Option A: Deterministic NumPy Morphology + PIL Gaussian Blur. Pros: Zero new dependencies, fully deterministic, 100% CPU-safe, fully auditable, lightweight. Cons: Slightly slower than optimized native C libraries.
  - Option B: SciPy ndimage binary morphology. Pros: Extremely fast. Cons: Adds a large compiled C extension dependency, deployment risks.
  - Option C: Deep learning-based matting (MODNet). Pros: High-quality hair boundaries. Cons: Requires ONNX runtime (~80MB library) and model file, heavy GPU/CPU overhead.
- **Decision**: Adopt Option A (Deterministic NumPy Morphology + PIL Gaussian Blur) as the baseline refiner, implemented by the class `MorphologicalForegroundRefiner`.
- **Reasoning**: Ensures zero new dependencies, preserves 100% CPU portability, and is fully deterministic and auditable.
- **Affected Modules**: `services/image-engine/providers/refiners`, `services/image-engine/providers/foreground_refinement.py`.
- **Approval Owner**: Lead Architect


### DEC-016: Exact-Aspect Crop Planning Pipeline (Crop Mode A) Baseline
- **Date**: 2026-06-19
- **Status**: Approved
- **Problem**: Selection and integration of local deterministic crop planning for Indian Exam requirements needing fixed aspect ratio/dimensions.
- **Options Considered**:
  - Option A: Bounding Box scaling based on the full refined foreground mask. Pros: Simple. Cons: Torso/shoulder features would enlarge the crop and shrink the face.
  - Option B: Head-led positioning with containment interval projection. Pros: Face-centered, head size is preserved correctly, and refined mask containment is verified as a post-check. Cons: Relies on accurate head estimation.
- **Decision**: Adopt Option B (Head-led positioning with containment interval projection).
- **Reasoning**: Ensures that face and head dimensions are prioritized, matching Indian exam standards, while using the refined foreground mask for validation checks.
- **Affected Modules**: `services/image-engine/providers/crop_planners`, `services/image-engine/providers/crop_planning.py`.
- **Approval Owner**: Lead Architect


### DEC-017: Crop Mode B Head-Led Range Crop Planning
- **Date**: 2026-06-19
- **Status**: Approved
- **Problem**: Selection and integration of local deterministic crop planning for rules specifying dimension and aspect ranges, rather than exact dimensions.
- **Options Considered**:
  - Option A: Force exact aspect crop using Crop Mode A planner. Pros: Reuses existing codebase. Cons: Does not allow utilizing flexible aspect and size ranges.
  - Option B: Dedicated head-led range planner with aspect ratio clamping and boundary shifting. Pros: Uses head height ratio target for natural framing, supports range constraints, shifts crop box to prevent padding where possible, allows geometry-only fallback. Cons: More complex mathematically.
- **Decision**: Adopt Option B (DeterministicCropModeBPlanner) with configuration and result schemas separated from Crop Mode A.
- **Reasoning**: It cleanly separates exact aspect planning from range aspect planning, calculates natural head-led crops, validates constraints, and detects padding without synthesizing pixels.
  - *Sizing Range Clarification*: The width/height ranges (min_width/max_width/min_height/max_height) represent final output dimensions after scaling/resizing. However, since image resizing is not implemented in the planning milestone (Milestone 10), these ranges are evaluated as source-pixel crop constraints for compatibility guidance.
- **Affected Modules**: `services/image-engine/providers/crop_planners/deterministic_crop_mode_b_planner.py`, `services/image-engine/providers/crop_planning.py`.
- **Approval Owner**: Lead Architect




### DEC-018: Background Composition Baseline
- **Date**: 2026-06-19
- **Status**: Approved
- **Problem**: Selection and integration of local deterministic background replacement for rules requiring solid backgrounds.
- **Decision**: Adopt SolidBackgroundComposer as the baseline composer.
- **Reasoning**: It ensures safe background composition without altering identity, leverages the refined alpha mask from Milestone 8, and is deterministic.
- **Affected Modules**: services/image-engine/providers/background_composers/solid_background_composer.py
- **Approval Owner**: Lead Architect


### DEC-019: Output Dimensioning and Restrained Enhancement Baseline
- **Date**: 2026-06-20
- **Status**: Approved
- **Problem**: Selection and integration of local deterministic image resizing, output selection priority, and restrained brightness/contrast/sharpness enhancement baseline.
- **Decision**: Adopt DeterministicOutputPreparer. Implement scaling warning limits (1.5x warning, 2.0x strong warning, 3.0x ceiling; 0.05 min downscale error, 0.10/0.20 downscale warnings). Adopt conservative enhancement thresholds (brightness: 0.88-1.12, contrast: 0.88-1.12, sharpness: 0.80-1.20). Fail early on exact aspect mismatch without stretching. Save invalid previews only with diagnostic flags.
- **Reasoning**: Ensures that candidate images are sized accurately to meet exam constraints without introducing identity distortion, artifacts, or silent stretching. Keeps enhancement limited to basic quality correction to avoid biometric alteration.
- **Affected Modules**: services/image-engine/providers/output_preparers, services/image-engine/providers/output_preparation.py.
- **Approval Owner**: Lead Architect

### DEC-020: Quality-Aware Compression Loop Baseline
- **Date**: 2026-06-20
- **Status**: Approved
- **Problem**: Selection and integration of local deterministic image compression and quality factor search to satisfy maximum and minimum file size limits.
- **Decision**: Adopt DeterministicJpegCompressor. Implement integer-based binary search on quality factors `[20, 100]` with an absolute safety quality floor of 20 to preserve biometric details. Enforce safety margins (`safety_margin_bytes`) and ceiling ratios (`target_ceiling_ratio`) strictly during search. Enable metadata stripping (e.g., EXIF) and a mandatory decode-after-encode dimension test. Exclude binary arrays from JSON serialization to prevent leakage. Save invalid output candidates only under diagnostic `--allow-invalid-output` flags.
- **Reasoning**: Ensures that candidate images are optimized for storage and delivery without crossing regulatory size limits or degrading visual quality below biometric legibility thresholds.
- **Affected Modules**: services/image-engine/providers/compression, services/image-engine/providers/output_compression.py, services/image-engine/cli.py.
- **Approval Owner**: Lead Architect


### DEC-021: Rule-Orchestrated Local Processing Pipeline
- **Date**: 2026-06-20
- **Status**: Approved
- **Problem**: Designing a unified processing workflow orchestration that maps structured exam rules to image-engine provider configurations, validates candidates against constraints, strips EXIF, generates safe filenames without PII exposure, and handles invalid execution report outputs.
- **Decision**: Adopt RuleOrchestratedPipeline with a rule resolver setting `allow_subject_clipping=False` by default (to preserve strict portrait boundaries) and relaxed crop height bounds to avoid rigid crop failures. Ensure filename generation is always run to provide `output_filename` even on downstream validation failure. Prefix invalid output filenames with `diagnostic_invalid_` and output corresponding processing reports. Exclude `encoded_bytes` from serialization. Ensure tests pass under the `--require-real` constraint.
- **Reasoning**: Integrates individual engine providers into a single, cohesive rule-driven processing pipeline, ensuring that candidate privacy is preserved (no PII in filenames or serialized logs) and validation constraints are strictly verified on actual encoded bytes.
- **Affected Modules**: services/image-engine/src/exam_photo/orchestration, services/image-engine/src/exam_photo/cli.py.
- **Approval Owner**: Lead Architect


### DEC-022: Local Processing API and Privacy Lifecycle
- **Date**: 2026-06-20
- **Status**: Approved
- **Problem**: Exposing the rule-orchestrated processing pipeline through a safe, local-only API boundary with file management under a privacy-first temporary lifecycle.
- **Decision**: Implement a local-only, synchronous FastAPI service (`serve-api`). Features:
  - Persistent job manifests (`job.json`) written to job-specific folders under `artifact_root` containing job status, metadata, issue codes, and artifact lists.
  - Strict path traversal validation of `job_id` using regex check `^job_[A-Za-z0-9_-]+$`.
  - Enforced upload size limits (`max_upload_bytes + 1`) check on the incoming stream before any processing.
  - Opaque URL routes for reports (`/v1/jobs/{job_id}/report`) and binary outputs (`/v1/jobs/{job_id}/output`) rather than physical path disclosures.
  - Clean manual deletion removing all disk artifacts, with DELETED state remaining in-memory only.
  - Scannable manifest-based TTL cleanup of expired folders.
- **Reasoning**: Creates a clean, isolated backend boundary and storage manager that complies with strict privacy, boundary sandboxing, and validation regulations before introducing a public-facing web interface.
- **Affected Modules**: `services/image-engine/src/exam_photo/api`, `services/image-engine/src/exam_photo/cli.py`, `services/image-engine/tests/api`, `scripts`.
- **Approval Owner**: Lead Architect


### DEC-023: Public Web App MVP and Local API Integration
- **Date**: 2026-06-20
- **Status**: Approved
- **Problem**: Building a public-facing user frontend MVP that enables selection/upload of exam rules, photo uploads, synchronous processing via the local API, status checks, validation report presentation, output download, and manual job deletion under strict privacy-first constraints.
- **Decision**: Build a React/Next.js App Router application in `apps/web/` using TypeScript and Tailwind CSS. Expose a calm, trustworthy user interface. Key requirements implemented:
  - Strict localhost CORS config allowed on backend (`127.0.0.1:3000` and `localhost:3000` origins when enabled).
  - Bundled sample rules duplicated exactly from backend configs (`public/rules/` directory).
  - Client-side validation for image format, size (< 5MB), and JSON rules.
  - Omit binary `encoded_bytes` from report view and raw JSON panels.
  - Complete memory-only local states: no `localStorage` caching of photos/blobs, immediate URL revocation of previews and downloads on deletion or unmounting.
  - Separate JS quality, build, and test steps in the CI runner.
- **Reasoning**: Delivers the first candidate-facing interface that connects directly to the local backend service, respecting privacy-first choices (no browser storage footprint) and verification requirements.
- **Affected Modules**: `apps/web/`, `services/image-engine/src/exam_photo/api/app.py`, `services/image-engine/tests/api/test_api.py`, `.github/workflows/`.
- **Approval Owner**: Lead Architect


### DEC-024: Local Rule Configuration Console and Validation API
- **Date**: 2026-06-20
- **Status**: Approved
- **Problem**: Designing a local rule configuration manager console for developers and operators to create, edit, validate, and export structured rules without manually editing raw files.
- **Decision**: Implement a local-only administration workspace and backend validation route. Key configurations and components:
  - Gated route `/admin/rules` locked behind environment variable `NEXT_PUBLIC_ENABLE_RULE_ADMIN=true` with prominent warnings indicating this is only a local accidental-exposure guard and not a security/authentication mechanism.
  - Form sections and raw JSON editing panels with state management that preserves unknown/advanced nested fields during field-specific edits.
  - Reset/revert behaviors to reset the workspace back to the pristine loaded sample state.
  - Stateless backend validation endpoint `POST /v1/rules/validate` returning standard `422 Unprocessable Entity` for malformed body shapes and 200 `is_valid` validation errors for rules. Enforce that validation does not write any files to disk.
  - Sample-rule sync test comparing backend examples with frontend public rule JSON files to avoid drift.
- **Reasoning**: Provides a robust, local-only developer utility to construct, validate, and check rule schemas without introducing production database dependencies, user auth, or persistent storage mechanisms.
- **Affected Modules**: `apps/web/`, `services/image-engine/src/exam_photo/api/app.py`, `services/image-engine/tests/api/test_rule_validation_api.py`.
- **Approval Owner**: Lead Architect

### DEC-025: Generalized Adaptive Portrait Composition and Edge-Matting Hardening
- **Date**: 2026-06-22
- **Status**: Approved
- **Problem**: Hardening the image compliance engine to produce high-quality, compliant portrait crops and composites across diverse human subjects without overfitting, clipping hair/ears, or introducing grey/white edge halos and color spill.
- **Decision**: Adopt the following comprehensive visual quality and adaptive composition enhancements:
  - **Composition 1.1 Model**: Introduce CropProfile and EarsPolicy schemas with validators mapping default ratio constraints (head size, margins, eye-line, torso limits) dynamically.
  - **Fused Head Refinement**: Implement a post-segmentation fused head refinement using an adaptive head ROI to accurately locate the hair/chin boundary, ignoring the torso.
  - **Grid-Search Cost Minimization**: Generate candidate crops and select the lowest cost crop using multi-objective scoring.
  - **Guided Filter Matting**: Compute a trimap and uncertainty band at reduced resolution, project to native resolution, and refine the alpha mask using Guided Filter on the RGB guidance image.
  - **Edge Color Decontamination**: Restrict background color spill recovery strictly to the boundary region ($0.05 < \alpha < 0.95$) to prevent global biometric color shifts.
  - **Premultiplied Compositing**: Crop, premultiply, resize RGB/alpha together, and composite on white target background to prevent dark/bright edge fringes.
  - **Comprehensive 30-Subject Benchmark**: Freeze baseline metrics (IoU, halo, spill, continuity, uniformity) and enforce visual quality gates on 192 deterministic variants.
- **Reasoning**: Ensures robust, generalized compliance outputs for diverse skin tones, hairstyles, facial hair, clothing, and headwear, while satisfying strict privacy-first constraints and preserving subject identity.
- **Affected Modules**: `services/image-engine/providers/refiners`, `services/image-engine/providers/crop_planners`, `services/image-engine/providers/background_composers`, `services/image-engine/providers/premultiplied_compositing.py`, `services/image-engine/providers/foreground_decontamination.py`, `services/image-engine/providers/fused_head_refinement.py`, `scripts/benchmark_engine_quality.py`.
- **Approval Owner**: Lead Architect

### DEC-026: Preservation-First Arbitrary Source Framing
- **Date**: 2026-07-06
- **Status**: Approved
- **Problem**: Candidate uploads can use arbitrary source dimensions and loose selfie framing, while exam outputs still require exact or rule-selected dimensions, clean white background replacement, target file size, and safe filenames without cutting hair, ears, chin, or beard boundaries.
- **Options Considered**:
  - Reject sources when a tight exact-aspect crop would extend beyond source pixels.
  - Preserve the subject by allowing transparent out-of-source crop regions that become the configured solid background during final composition.
- **Decision**: Use preservation-first framing. Crop Mode A remains selected for exact dimensions, Crop Mode B remains selected for ranges or unspecified dimensions, and rule face-coverage percentages map to target/min/max head-height crop ratios. Rule-orchestrated processing may use background-colour padding to satisfy exact output frames while keeping subject clipping disabled by default.
- **Reasoning**: This matches real candidate-upload behavior and prevents false "not possible" failures when a compliant result can be produced by tight subject framing plus white background composition.
- **Consequences**: Outputs can include white padding outside the original source bounds, but not stretched pixels or clipped subject features. Rules with unspecified dimensions use the documented platform default profile dimensions before compression.
- **Affected Modules**: `services/image-engine/src/exam_photo/orchestration`, `services/image-engine/src/exam_photo/providers/crop_planners`.
- **Approval Owner**: Lead Architect

### DEC-027: Semantic Exam Portrait Composition Boundary
- **Date**: 2026-07-06
- **Status**: Approved
- **Problem**: A single head/foreground geometry was being used for multiple concerns: background removal, head preservation, crop sizing, and torso inclusion. Full-person segmentation can include neck, collar, shoulders, and torso; when that geometry influences crop sizing, tight exam outputs become too loose and face coverage drops even when the face and head were detected correctly.
- **Options Considered**:
  - Tune crop thresholds for individual failing photos.
  - Continue using the refined foreground mask as the crop-preservation source.
  - Add a semantic exam-portrait composition stage between head refinement and crop planning.
- **Decision**: Adopt a semantic `PortraitCompositionResult` produced by `DeterministicPortraitCompositionEstimator`. Crop Mode A and Crop Mode B must use the portrait preservation/framing box for crop geometry and preservation validation. The refined alpha mask remains available for background removal and secondary mask checks, but full foreground bounds must not drive tight crop sizing.
- **Reasoning**: This fixes the engine contract rather than a single output. It generalizes across loose selfies, different source dimensions, hairstyles, beards, collars, and shoulder-heavy foreground masks while preserving the subject identity and preventing hair/ear/chin/beard clipping.
- **Consequences**: Pipeline reports now expose `portrait_composition_box` and lower-body exclusion geometry for debugging. If composition estimation fails, the pipeline falls back to head geometry with a warning, never to full foreground-driven crop geometry.
- **Affected Modules**: `services/image-engine/src/exam_photo/providers/portrait_composition.py`, `services/image-engine/src/exam_photo/providers/crop_planners`, `services/image-engine/src/exam_photo/orchestration/rule_pipeline.py`, `services/image-engine/tests/providers/test_portrait_composition.py`.
- **Approval Owner**: Lead Architect

### DEC-028: Benchmark Dimension Rules and Explicit JPEG DPI
- **Date**: 2026-07-06
- **Status**: Approved
- **Problem**: The benchmark set requires exact pixel dimensions plus 72 DPI, but the existing schema only represented pixel dimensions and did not carry DPI into final encoded output validation.
- **Decision**: Add optional `dimensions.dpi` to the canonical rule schema and Python rule model. Resolve this value into `OutputCompressionConfig.target_dpi`, write it through Pillow JPEG encoding as square DPI density, and validate decoded output DPI in final validation. Create six benchmark exact-dimension rules for the 60-image benchmark categories.
- **Reasoning**: DPI should be a machine-readable, testable rule constraint rather than a note. Keeping it optional preserves existing rules while enabling benchmark and exam rules that specify DPI.
- **Consequences**: Final validation can now return `PIPELINE_FINAL_DPI_INVALID` if an encoded candidate does not match the configured DPI. Metadata stripping remains focused on EXIF/privacy metadata; JFIF DPI density is allowed when explicitly required.
- **Affected Modules**: `packages/exam-rules/schema/exam-rule.schema.json`, `services/image-engine/src/exam_photo/models/exam_rule.py`, `services/image-engine/src/exam_photo/orchestration`, `services/image-engine/src/exam_photo/providers/compression`, `examples/rules/benchmark_exact_*_72dpi_white_bg.json`.
- **Approval Owner**: Lead Architect

### DEC-029: Anatomical Head Span as the Composition Reference
- **Date**: 2026-07-31
- **Status**: Approved
- **Problem**: Measured against a 60-photo reference set (six exact-dimension exam size classes, 10 photos each), engine output was systematically under-cropped: head height 0.60 of frame versus 0.84 in the reference, headroom 0.125 versus 0.048, side space ~2.7x too wide, and face area roughly half. Only 30/60 reference inputs produced any output at all. Two root causes were isolated. First, DEC-026 mapped `face_coverage_*` percentages onto `*_head_height_ratio`; these are different quantities (a correctly composed reference photo measures 0.84 head height but only 0.29 face area and 0.58 face height), and the mapping additionally turned a diagnostic into a hard reject bound, contrary to the AGENTS.md principle that face coverage is "a diagnostic indicator, not a rigid mathematical rejection threshold". Second, DEC-027's preservation box was used as the composition reference, but it deliberately extends past the head (measured 1.140 +/- 0.011 times the crown-to-chin span, and 1.31 times the head width) because it absorbs hair spread, shoulder alpha and a lower-body exclusion band. Enforcing "head height = 0.77" against that inflated box yields a real head height of 0.665, and reaching 0.84 would require a ratio above 1.0, which is unreachable. Requiring the crop to contain the full preservation box width additionally capped achievable head height below the allowed minimum for 23/50 photos, concentrated in tall target aspects (7/8 in the 1200x1800 class).
- **Options Considered**:
  - Raise the configured ratios in preservation-box space. Rejected: the required target exceeds 1.0 for the vertical case, and the horizontal inflation factor is far less stable (sd 0.166) than the vertical one (sd 0.011).
  - Tune per-size-class constants. Rejected as fixture-fitting; it does not correct the underlying unit mismatch.
  - Separate the two roles the single box was serving.
- **Decision**: Split the geometry into a *generous* preservation box (unchanged, used to avoid cutting into the subject casually) and a *mandatory* region — crown to chin-plus-beard-margin, spanning the head core — against which composition ratios, planning constraints and preservation validation are all stated, so the planner cannot produce a crop its own validator then rejects. The crown is read from the observed subject mask rather than the geometric `face_top - 0.6 * face_height` estimate, which overshoots badly when the detector returns an oversized face box. `face_coverage_*` no longer contributes to head-height geometry and remains a reported diagnostic. `TIGHT_EXAM_PORTRAIT` profile ratios, side/bottom margins, mask-preservation threshold and preferred face-centre are recalibrated to the reference distribution. Whether outer hair is given up is decided per photo, not by a profile label: the candidate search scores both a strict variant (keeps the entire preservation box) and a relaxed one (keeps the head core plus the chin/beard margin), and a strict crop always wins when the photo admits one, so no subject area is sacrificed unnecessarily. Only subjects that cannot be composed strictly - voluminous hair, tall target aspects, a head near the source edge - fall back to the relaxed result, which is what reference photos do for those same subjects (the head silhouette touches the left edge in 31/60 and the right edge in 44/60). Preservation validation, reported margins and the mask-retention metric are all judged against whichever region that photo's crop actually promised, and the mask-retention metric is measured over that region rather than a fixed expansion beyond it. The legacy (no-profile) planning branch keeps its original "crop contains the preservation box" contract unchanged.
- **Reasoning**: The reference set shows very low variance in the landmark-derived quantities (eye line 0.486 +/- 0.033, chin 0.888 +/- 0.043, head height 0.840 +/- 0.056), so these are stable engine targets rather than per-photo preferences. Fixing the reference frame corrects the contract instead of compensating for it downstream.
- **Consequences**: Over the 60-photo reference set, pipeline success rose from 30/60 to 56/60 and head height from 0.600 to 0.753 mean / 0.804 median against a 0.840 target, with every measured composition metric moving closer to the reference. Head-height error fell from 0.240 to 0.087 and head-width error from 0.236 to 0.050. Crop-stage validity is 58/58 of photos that reach planning, with head coverage of the mandatory region at exactly 1.000. Face detection gained a confidence-recovery ladder because the short-range BlazeFace model returned no detections at all on 9/60 ordinary half-body submissions; recovery accepts only an unambiguous single face, so genuine multi-person photos still fail. The `full_range` model remains unusable here (the manifest records it as incompatible with the Python Tasks FaceDetector API). The mask-retention metric previously sampled a region 35% wider and taller than anything the planner guaranteed, so a correctly composed crop could fail a bar nothing targeted; aligning it to the guaranteed region fixed both this and a pre-existing CLI test failure. The `case_marie_curie` golden baseline was regenerated because it encoded the old composition; the new output is visually a tighter, better-framed crop. Full suite: 253 passed, 0 failed, with ruff/format/mypy clean. Residual gap: 8 photos remain under-cropped because segmentation retains background objects adjacent to the subject (signboards, gates, wall panels), which inflates the observed subject extent; mask validation and matte validation both pass these, so the blind spot is logged as follow-up work rather than resolved here.
- **Affected Modules**: `services/image-engine/src/exam_photo/providers/crop_planners/deterministic_crop_planner.py`, `services/image-engine/src/exam_photo/orchestration/rule_resolver.py`, `services/image-engine/src/exam_photo/orchestration/rule_pipeline.py`.
- **Approval Owner**: Lead Architect

### DEC-030: Matte Resolution, Band Width and Alpha Contrast Window
- **Date**: 2026-07-31
- **Status**: Approved
- **Problem**: Edge quality was limited by the refinement stage discarding detail the segmenter had already produced. Measured on a reference photo, the raw segmentation probability mask carried genuine partial coverage over 4.64% of the frame; after refinement only 1.22% survived. Three independent causes: (a) `maximum_matting_pixels` (2 MP) demoted an ordinary 10.6 MP phone photo a whole quality tier, pinning matting to a 1024px working resolution; (b) the "unknown" band the guided filter is allowed to write into was computed at a fixed 512px and upsampled with NEAREST, so it arrived quantised into ~8px blocks and the filter could only ever produce a blocky edge regardless of its own resolution; (c) the alpha contrast window (0.18/0.72 followed by a smoothstep) clipped 46% of the alpha range, which is precisely the range that describes hair.
- **Options Considered**:
  - Raise the memory budget. Rejected: peak memory is a real constraint and the budget was not the problem, the policy for spending it was.
  - Widen the matting band aggressively. Measured and rejected: at 0.025 of head height the band exceeded the reach of colour decontamination, so its interior kept background colour; hair detail rose but the halo proxy more than doubled.
  - Replace the segmenter with a portrait matting model. Deferred; see Consequences.
- **Decision**: Derive the working resolution by scaling to the pixel budget instead of dropping a quality tier, keeping ~1.7x the linear resolution at identical peak memory. Build the matting band at the refinement resolution from a smoothly resampled decision rather than a NEAREST-upsampled 512px one. Size the band from estimated head height rather than a fixed pixel count, bounded so it stays within the colour-decontamination reach, and raise that reach to match. Widen the alpha contrast window to 0.05/0.92. Morphology at the refinement resolution uses Pillow's C rank filters applied iteratively, which is linear in radius and adds no dependency beyond Pillow and numpy (OpenCV is only present transitively via the optional `face` extra and must not become a core requirement).
- **Reasoning**: Each cause was isolated by measurement rather than tuned together: retained soft alpha moved 1.22% -> 1.46% (resolution) -> 2.29% (contrast window) -> 3.08% (band width) against a 4.64% ceiling. Re-running with the contrast window reverted showed the halo proxy stayed elevated, which reattributed that cost to the resolution and band work rather than to the window.
- **Consequences**: Over the 60-photo reference set, hard-edge fraction fell from 0.390 to 0.300 (reference photos measure 0.567, so engine output is now materially softer and more natural than the references it was calibrated against, which is the intended direction). Composition is unaffected. The `halo_score` proxy rose from 0.756 to 1.121, but direct pixel inspection shows finer individual hair strands and no grey ring, and background purity is essentially unchanged (`bg_pure_white_frac` 0.868 -> 0.862), so the proxy is partly conflating additional genuine soft-edge detail with contamination; it should not be optimised against on its own. The `case_marie_curie` golden baseline was regenerated (MAE 8.59, matte-only, composition unchanged) and shows visibly finer strand detail. Full suite: 253 passed, 0 failed, ruff/format/mypy clean. This is the limit of what the current selfie segmentation model supports; per-strand hair requires a real portrait matting model (BiRefNet MIT or BEN2 Apache-2.0 via onnxruntime; RMBG-1.4 is non-commercial and unsuitable), which remains the outstanding step change.
- **Affected Modules**: `services/image-engine/src/exam_photo/providers/refiners/morphological_refiner.py`, `services/image-engine/src/exam_photo/providers/foreground_refinement.py`, `services/image-engine/src/exam_photo/providers/foreground_decontamination.py`, `tests/golden-images/case_marie_curie.golden.jpg`.
- **Approval Owner**: Lead Architect

### DEC-031: BiRefNet Subject Matting Backend
- **Date**: 2026-08-01
- **Status**: Approved
- **Problem**: Reviewer assessment of engine output was that roughly 95% of results were unusable, with two specific complaints: a hard line visible around the face/jaw, and crops that were too loose. Inspection of the alpha mask showed the cause was not tuning but the segmentation model itself: MediaPipe selfie segmentation produces a "sticker" matte (flat alpha 1.0 across the subject, hard boundary, faceted straight-line shoulders, transparent holes inside the face box), and absorbs background structures adjacent to the subject (signboards, gates, wall panels) into the subject mask. DEC-030 had already extracted essentially all detail that model produces (3.08% soft alpha against its own 4.64% ceiling), so no further tuning was available.
- **Options Considered**:
  - RMBG-2.0. Rejected: BRIA's model card records it as "developed on the BiRefNet architecture" -- the repository ships `birefnet.py` and `BiRefNet_config.py` -- so it is the same design under CC BY-NC 4.0, gated behind licence acceptance, and it scored *lower* than permissive BiRefNet on 5 of 6 measured images while being visually indistinguishable. Adopting it would cost monetisation rights for no measured gain; BRIA sells a commercial agreement if it is ever wanted.
  - BEN2 (Apache-2.0). Rejected on measurement: lowest edge-alignment score of the four backends (4.04) and slowest (120-167 ms/image at its fixed 1024 input, which its ONNX graph cannot vary), plus one hard failure.
  - Continue tuning MediaPipe. Rejected as exhausted per DEC-030.
- **Decision**: Adopt BiRefNet (MIT) as an opt-in subject segmentation backend at 512px inference, selected via `RuleOrchestratedPipeline(matting_backend="birefnet")` or CLI `--matting-backend birefnet`. The default remains `"mediapipe"` so existing callers, tests and deployments are unchanged. Weights are vendored to `model-assets/birefnet/` by `scripts/download_birefnet.py`, pinned to revision `e2bf8e44` and SHA-256 verified against `model-manifests/birefnet.json`, matching the existing face-detector and segmenter model handling. `torch`/`transformers` are an optional `matting` extra and are imported lazily so the package remains importable without them.
- **Reasoning**: Selection was made on measurement rather than reputation. A new `edge_alignment` signal (gradient magnitude along the matte boundary relative to subject interior) was introduced because three earlier candidate signals failed validation against known-good/known-bad photos -- two pointed the wrong way -- and because the reported defect is a boundary that sits off the true subject edge, which silhouette-shape metrics cannot see. Inference resolution was chosen by sweep: 512 matches 1024's edge-alignment score (4.72 vs 4.80) and is visually indistinguishable while running ~7x faster on CPU (12s vs 85s), and 384 degrades sharply.
- **Consequences**: Over the 60-photo reference set, valid outputs rose from 56/60 to 57/60 and hard-edge fraction fell from 0.390 to 0.337 (reference photos measure 0.567, so output remains materially softer than the set it is calibrated against). Background removal is qualitatively fixed: structures previously absorbed into the mask are now excluded. Composition improved only marginally (head height 0.749 -> 0.754, mean; median 0.784 against a 0.840 target, 8 photos still below 0.70) because **crop geometry is derived from the detector face box, not from the mask** -- so a better matte cannot fix it. Three latent bugs were found and fixed while integrating, all previously masked by the poor segmentation: (a) `preserve_face_core` force-filled the entire inner face-box rectangle to opaque regardless of the segmenter's output, reintroducing background the model had correctly excluded; (b) `_estimate_crown_y` rejected any mask crown reading below `face_box.top`, discarding ground truth precisely when the face box was oversized; (c) the same phantom space remained in `preserve_box`, making crop sizing reserve room for absent subject. Fix (c) initially regressed one photo by trimming `preserve_box` without trimming `composition_box`, so preservation validation judged the crop against a region the planner no longer promised -- the same planner/validator disagreement class as DEC-029, corrected by trimming both. Cost: `torch` is ~2 GB and BiRefNet runs ~12s/image on CPU versus ~4.5s for MediaPipe; the API is already job-based with polling so this is viable, and ONNX export plus int8 quantisation remain available.
- **Residual**: BlazeFace short-range returns no detection on 9/60 reference photos and a poor box on those recovered by the confidence ladder, and its eye keypoints are corrupted by sunglasses, which blocks the eye-line constraint. Since all crop geometry depends on that box, the outstanding work is to derive head geometry (crown, head width, shoulder line) from the now-accurate matte and use face landmarks only for eye line and chin. That is expected to address the ~8 still-loose photos as a class rather than individually.
- **Affected Modules**: `services/image-engine/src/exam_photo/providers/segmenters/birefnet_segmenter.py`, `orchestration/rule_pipeline.py`, `cli.py`, `providers/refiners/morphological_refiner.py`, `providers/crop_planners/deterministic_crop_planner.py`, `scripts/download_birefnet.py`, `model-manifests/birefnet.json`, `pyproject.toml`.
- **Approval Owner**: Lead Architect

### DEC-032: Dense Face Landmark Refinement
- **Date**: 2026-08-01
- **Status**: Approved
- **Problem**: BlazeFace gives coarse eye points and no true chin landmark, so crop height and eye-line placement can be driven by detector-box bottom rather than anatomy.
- **Decision**: Add an optional MediaPipe dense face-landmarker refinement step after BlazeFace face counting. The landmarker runs on a crop around the detected face, updates only chin and eye-line landmarks, and leaves the detector bounding box unchanged.
- **Reasoning**: Face counting remains with BlazeFace because it has better raw-photo coverage, while dense landmarks improve the two crop quantities most sensitive to detector-box error.
- **Consequences**: If the landmarker asset is missing or disagrees strongly with the detector, the pipeline keeps the original detection and proceeds. This is an enhancement, not a hard dependency.
- **Affected Modules**: `services/image-engine/src/exam_photo/providers/mediapipe_face_landmarker.py`, `services/image-engine/src/exam_photo/orchestration/rule_pipeline.py`.
- **Approval Owner**: Lead Architect

### DEC-033: Preserve Trusted BiRefNet Alpha
- **Date**: 2026-08-01
- **Status**: Approved
- **Problem**: Morphological reconstruction was designed for coarse MediaPipe masks. Applied to BiRefNet probability masks, it discards useful soft-edge detail and can reintroduce the hard-cutout behavior the model was selected to avoid.
- **Decision**: Add a trusted-alpha path for BiRefNet output. When the segmenter supplies a high-quality probability mask, skip destructive morphology and pass the alpha through to later composition/decontamination stages.
- **Reasoning**: The product defect is edge realism. BiRefNet already predicts soft foreground probabilities; preserving that signal is safer than forcing it through coarse-mask cleanup.
- **Consequences**: MediaPipe masks still use the existing refinement path. BiRefNet output keeps finer hair and jaw transitions, with tests covering exact alpha preservation.
- **Affected Modules**: `services/image-engine/src/exam_photo/providers/refiners/morphological_refiner.py`, `services/image-engine/tests/providers/test_foreground_refinement.py`.
- **Approval Owner**: Lead Architect

### DEC-034: Landmark-Derived Chin Fallback
- **Date**: 2026-08-01
- **Status**: Approved
- **Problem**: When dense landmarks are unavailable, the detector-box bottom often falls into neck or shirt area, which makes the crop reserve phantom space below the real chin.
- **Decision**: Use an eye/mouth-derived mouth-to-chin fallback before the detector-box bottom when landmarks contain enough stable points.
- **Reasoning**: The fallback is calibrated from reference photos with known chin landmarks and is closer to anatomy than treating the bottom of a coarse detector box as the jaw line.
- **Consequences**: The fallback is intentionally coarse and remains below dense-landmark priority. It reduces systematic loose crops without changing face counting.
- **Affected Modules**: `services/image-engine/src/exam_photo/providers/crop_planners/deterministic_crop_planner.py`.
- **Approval Owner**: Lead Architect

### DEC-035: Preserve Chin, Beard, Hair and Ears Before Chasing Coverage
- **Date**: 2026-08-01
- **Status**: Approved
- **Problem**: Some tight source photos cannot simultaneously satisfy a 75% head-height floor and preserve all hair, ears, chin, and beard boundary.
- **Decision**: Treat the 75% floor as an aggregate diagnostic and exam target, but do not solve impossible photos by clipping identity-bearing regions. Log geometrically impossible cases and keep the crop-fix UI as the later recovery path.
- **Reasoning**: The repository contract says face coverage is an expected result of correct natural cropping, not a rigid mathematical rejection threshold. Hair, ears, chin, beard, and jawline preservation are identity and acceptance requirements.
- **Consequences**: The engine reports no-output or invalid crop reasons for genuinely impossible photos instead of silently producing clipped outputs.
- **Affected Modules**: `services/image-engine/src/exam_photo/providers/crop_planners/deterministic_crop_planner.py`, `scripts/benchmark_reference_pairs.py`.
- **Approval Owner**: Lead Architect

### DEC-036: BiRefNet Default and Reference-Pair Benchmark Loop
- **Date**: 2026-08-01
- **Status**: Approved
- **Problem**: The API selected BiRefNet automatically, but direct callers through `RuleOrchestratedPipeline` and the CLI still defaulted to MediaPipe, producing the old matte. The branch also lacked a repeatable all-60 engine-vs-ideal benchmark, causing tuning to drift toward derived constants instead of the approved reference outputs.
- **Decision**: Make BiRefNet the default backend for `RuleOrchestratedPipeline` and CLI processing, resolving vendored model defaults from `model-manifests/birefnet.json` when callers do not pass explicit BiRefNet arguments. Add `scripts/benchmark_reference_pairs.py` to compare all 60 matched source/ideal pairs and report crop size, margins, 75% floor count, no-output keys, and regional edge behavior.
- **Reasoning**: Product quality depends on realistic portrait edges. MediaPipe remains selectable for legacy diagnostics, but it is no longer the default for product processing. The benchmark treats the ideal outputs as the spec and avoids optimizing against invented thresholds.
- **Consequences**: BiRefNet CPU inference is the dominant runtime cost, measured at roughly 10-26 seconds per produced photo on this Windows CPU environment after thread capping. All-60 baseline after the runtime/refinement fixes: 56/60 produced output, no-output keys `3-3`, `3-9`, `5-1`, `6-7`; 46/56 measurable outputs met the 75% floor; mean margin absolute error was 0.0480. A trial that moved mandatory preservation margins toward ideal-output medians improved margin MAE to 0.0440 but regressed no-output to 10/60, so it was rejected and not retained.
- **Affected Modules**: `services/image-engine/src/exam_photo/orchestration/rule_pipeline.py`, `services/image-engine/src/exam_photo/cli.py`, `services/image-engine/src/exam_photo/providers/segmenters/birefnet_segmenter.py`, `scripts/benchmark_reference_pairs.py`.
- **Approval Owner**: Lead Architect

### DEC-037: Composition Margins Read From the Approved Ideal Outputs
- **Date**: 2026-08-04
- **Status**: Approved
- **Problem**: `_CHIN_BEARD_MARGIN_RATIO` (0.24) and `_TOP_MARGIN_RATIO` (0.08) were sized by feasibility algebra -- "the largest margin still compatible with a 75% coverage floor" -- rather than measured from the approved reference outputs. Because both are *mandatory* floors rather than targets, they did not merely reserve space: together they bounded head height at 1/(1 + 0.08 + 0.24) = 0.758 for every photo, while the ideal outputs have a median head height of 0.855 and a p90 of 0.900. The engine was structurally incapable of reaching the approved composition on any photo. Measured over the 60-photo set, below-chin space exceeded the matching ideal on 50 of 56 produced outputs, by a mean of 0.067 of frame height.
- **Decision**: Set both constants from the measured ideal-output distribution, at the p25 rather than the median, because they are floors and the profile's composition targets are what should choose the framing. Below-chin space as a fraction of the crown-to-chin span measures p10 0.075 / p25 0.091 / median 0.119 / p90 0.217 across the 60 ideals; space above the hair measures p10 0.028 / p25 0.038 / median 0.048. The constants become 0.09 and 0.04. `_SIDE_MARGIN_RATIO` keeps its value of 0.03, which already matches the ideal p25 (0.033 left / 0.029 right); only its justification was rewritten, since the aspect-ratio interaction it describes is real and still binds on tall targets.
- **Reasoning**: The user's stated specification is the approved ideal outputs, not a threshold derived from first principles. A mandatory floor placed near the middle of the reference distribution contradicts half of the approved outputs by construction; placed at the low end it protects the subject without preventing the intended framing. The tightest approved reference output leaves 0.075 of the span below the chin and clips no beard, so the p25 is empirically safe.
- **Consequences**: Median delivered head height rose from 0.798 to 0.833 against an ideal median of 0.855; margin mean absolute error fell from 0.0480 to 0.0422; outputs rose from 56/60 to 57/60 and the 75% floor from 46/56 to 47/57. Photos whose own ideal sits below 0.75 (`6-1` 0.73, `6-2` 0.66, `6-3` 0.67, `6-9` 0.73) confirm that 75% is a target rather than a floor in the reference set itself.
- **Affected Modules**: `services/image-engine/src/exam_photo/providers/crop_planners/deterministic_crop_planner.py`.
- **Approval Owner**: Lead Architect

### DEC-038: Face Containment Anchored on Measured Anatomy
- **Date**: 2026-08-04
- **Status**: Approved
- **Problem**: Crop validation required the crop to contain the raw BlazeFace rectangle, while the candidate search enforced containment of the anatomical `mandatory_box` and knew nothing about that rectangle. The two therefore judged different regions, and the search could select a correctly tight crop that its own validator then rejected as a blocking `CROP_SOURCE_TOO_TIGHT` error. Once the DEC-037 margins were corrected, this alone turned 8 otherwise-valid photos into no-output (4/60 to 12/60). The detector rectangle is additionally a poor proxy for anatomy in both directions: its bottom lands 0.045-0.143 face heights below the true chin, and on low-confidence recovery detections its top sits above the hairline.
- **Decision**: Fold every landmark the detector actually located into `mandatory_box`, and validate containment against that same box -- the exact region the search enforces -- so planner and validator agree by construction. When no landmarks are available, fall back to the detector rectangle's sides and top but cap its bottom at the promised chin/beard line. Critically, the validator applies this only under the same condition the search does: when subject clipping is disallowed. Validating it unconditionally recreated the identical disagreement in the opposite direction, blocking callers that had explicitly passed `allow_subject_clipping=True`.
- **Reasoning**: The recurring defect class in this module is the planner promising one region and the validator judging another (see also DEC-029). The durable fix is a single shared region with a single shared condition, not a better heuristic rectangle. Landmarks and the mask-derived head core are real per-photo measurements; the detector box is a coarse guess.
- **Consequences**: No-output returned to 3/60 while the DEC-037 margin gains were retained. The unconditional first version was caught by `test_pipeline_integration_success`, which passes `allow_subject_clipping=True`; that test is now the regression guard for the condition matching.
- **Affected Modules**: `services/image-engine/src/exam_photo/providers/crop_planners/deterministic_crop_planner.py`.
- **Approval Owner**: Lead Architect

### DEC-039: Minimum Face Coverage as the Last Relaxation Tier
- **Date**: 2026-08-04
- **Status**: Approved
- **Problem**: `head_height_min` was absent from every relaxation tier, on the reasoning that minimum face coverage is the published requirement an output is judged against and so must never be traded away. Measured, that reasoning produced the opposite of its intent. On the 9 photos where no candidate could reach the floor, the search returned nothing and fell through to the geometric projection fallback, which ignores every composition target: those photos delivered 0.41-0.66 head height with 0.15-0.30 of the frame as headroom, worse on the floor itself than candidates the search had already found and discarded.
- **Decision**: Add `head_height_min` as the final tier of `_RELAXATION_TIERS`, surrendered only after torso, eye line, top margin, centring and head width. Tier ranking means a candidate meeting the floor always beats one that does not, so no photo that can comply is affected. `CROP_NO_VALID_COMPOSITION` continues to report the compromise downstream.
- **Reasoning**: A constraint that cannot be relaxed is not thereby enforced; it merely routes the photo to a code path with no constraints at all. Surrendering the floor last, and reporting it, delivers the tightest crop the geometry allows. The approved ideal outputs measure 0.665-0.728 head height on four photos, so a sub-0.75 result is correct framing for those subjects rather than a failure.
- **Consequences**: Subject protection (complete hair, chin/beard boundary, ear visibility, padding limits) remains outside the ladder and is still never waived. The geometric projection fallback becomes close to unreachable, which is intended.
- **Affected Modules**: `services/image-engine/src/exam_photo/providers/crop_planners/deterministic_crop_planner.py`.
- **Approval Owner**: Lead Architect

### DEC-040: Matte the Crop Region, Not the Whole Frame
- **Date**: 2026-08-04
- **Status**: Approved
- **Problem**: Reviewer assessment of output was streaked hair edges, halos and colour bleed spreading into the face and ears. The cause is resolution, not tuning. BiRefNet sees a fixed 512x512 square, so the alpha detail any part of the subject receives is set by how much of the *source frame* it occupies, not by how large it will be in the finished photo. Candidates submit half- and full-body photographs and the exam photo is a tight head crop, so the head is the small part of the input that becomes the whole output. Measured over the 60-photo set: the head arrives with a median of 121 px of alpha detail (worst 42 px) and is magnified by a median 2.1x, worst 17.4x. Every photo with visible streaking or halo sits in the high-magnification group.
- **Decision**: After crop planning, re-run the matting model on the planned crop region plus a 12% margin and splice the resulting alpha back into the full-frame mask, so decontamination and compositing both consume the sharpened matte. Skip when the region is within 1.15x of the full frame, and treat any failure as a warning that degrades edge detail rather than failing the photo. Crop geometry is already decided at that point and is not revisited, so this cannot feed back into planning.
- **Reasoning**: Spending a fixed model resolution budget on the whole frame when only the head survives is the direct cause of the defect; no tuning of band widths or decontamination reach can recover detail the model never produced. Two competing hypotheses were falsified with measurement before this one was adopted: out-of-bounds padding blanking the subject (0 of 57 outputs cut the subject at a padded band) and the crop frame clipping ears (1 of 57 touches a side edge more than its ideal does).
- **Consequences**: One extra inference per photo, roughly doubling matting cost on photos that qualify; the API is job-based so this is acceptable. Spot-checked on `6-9`, `6-5`, `6-6` and `5-2`: effective alpha resolution up 2.5-3.5x and edge quality closer to the matching ideal on 14 of 15 regional measures. It does not close the gap on the 1200x1800 class, where the limit is source resolution rather than matte resolution: that class needs a median 4.41x (worst 6.98x) enlargement of real source detail, while every other size class is downscaling. That is an input-suitability problem and is addressed separately.
- **Affected Modules**: `services/image-engine/src/exam_photo/orchestration/rule_pipeline.py`, `scripts/benchmark_reference_pairs.py`.
- **Approval Owner**: Lead Architect

### DEC-041: Accept, Warn, Block -- the Output Disposition Policy
- **Date**: 2026-08-04
- **Status**: Approved
- **Problem**: A published upload manual will tell candidates which photographs are rejected, so the engine's dispositions become public promises. The tempting reading -- enforce every published exam rule and refuse non-compliant photographs -- fails commercially and factually. Candidates come to the platform to receive a compliant photograph, not to be assessed; a refusal and a silent failure are the same outcome to them, and both lose the user. Research across 48 examinations (see DEC-042) additionally shows that three of the five most commonly published rules -- recency, live capture / own photograph, and identity match at later stages -- cannot be verified from pixels at all, and that several appearance rules are mutually contradictory between bodies.
- **Decision**: Dispositions are decided by one principle: **block only when the engine cannot produce a truthful output; otherwise always produce, and report what is risky.** This yields three buckets. (1) *Auto-fix, silent*: background, crop and face coverage, dimensions, DPI, file size, format, colour space, filename. (2) *Produce and warn*: every detectable appearance defect the engine cannot repair -- blur, non-frontal pose, closed eyes, sunglasses, cap or head covering, mask, spectacle glare, harsh shadow, hidden ears, greyscale where colour is required, source resolution insufficient for the target size. Warnings carry two severities: `likely_rejection` and `possible_issue`. (3) *Block*: only an undecodable file, no detectable face, or more than one detectable face. Appearance is never a blocking reason. Rules that are not checkable from an image are neither blocked nor warned; they appear as static guidance in the upload manual.
- **Reasoning**: Blocking and warning demand the same corrective action from the candidate -- retake the photograph -- so blocking buys no additional protection while removing the deliverable. The error costs are asymmetric: a wrong warning is an annoyance, a wrong block is a lost user on a false premise. That asymmetry is decisive for the appearance signals specifically, because detector reliability is uneven and, for head coverings, the rules themselves conflict: IBPS, GATE and the Navy expressly permit religious headwear that SSC prohibits, so a blanket cap block would wrongly reject candidates on examinations that allow them. Multiple faces is a block rather than a warning because selecting a face would silently produce a photograph of a possibly different person, which is an untruthful output rather than a risky one.
- **Consequences**: The engine's public contract is that it never refuses for appearance reasons. Deterrence is delivered by the web app instead: `likely_rejection` presents an acknowledgement step with retaking as the primary action and downloading as a secondary one, while `possible_issue` is an inline notice. This separation is deliberate -- "the engine refuses" and "the interface asks you to confirm" are different guarantees, and only the second is safe when a detector can be wrong. Detectors will be introduced in confidence order (eye closure first, since the vendored face landmarker already emits blend shapes; sunglasses and head coverings require classifiers that do not yet exist), and no signal may be promoted to `likely_rejection` before its reliability is measured.
- **Affected Modules**: `services/image-engine/src/exam_photo/suitability/`, `services/image-engine/src/exam_photo/orchestration/rule_pipeline.py`, `apps/web/src/components/`.
- **Approval Owner**: Lead Architect
- **Amended 2026-08-04 (no stage may block for composition reasons)**: Wiring the policy into `process_rule` showed the contract was being contradicted from inside the pipeline. Two photographs the policy had already judged acceptable still produced nothing, because background composition treated `BACKGROUND_FOREGROUND_TOO_SMALL` and `BACKGROUND_SUBJECT_CLIPPING_RISK` as hard failures. A subject that fills little of the frame, or whose hair reaches the top edge, is a composition concern rather than an unusable output -- and the approved reference outputs let hair reach or leave the edge on most photographs. Both are now warnings that surface as `possible_issue` findings and still produce a photograph. The rule is therefore stated more strongly than originally written: **no stage anywhere in the pipeline may block for an appearance or composition reason.** Only an undecodable file, no detectable face, or a genuinely ambiguous subject may refuse. Genuinely unusable mattes remain caught by segmentation mask validation, which is a different failure.
- **Amended 2026-08-04 (face counting)**: The original entry left the detector's "exactly one face" requirement in place. That requirement blocked a single candidate photographed in front of a printed banner, whose spurious second face appears only at the lowest confidence tier and carries no landmarks. Face counting is now delegated to the disposition policy, which weighs the second face's size and the tier it was found at, and the pipeline proceeds with the largest face when the subject is unambiguous. A related defect was fixed in the recovery ladder, which failed to record which confidence tier a multi-face recovery had used, making a desperation-tier detection look like a full-confidence one.
- **Amended 2026-08-04 (blend shapes)**: The original entry anticipated eye closure as the first detector to ship, "since the vendored face landmarker already emits blend shapes". Measurement contradicted this: the eye-blink score does not separate closed eyes or sunglasses from narrow or deep-set eyes. Blend shapes are switched off, no consumer exists, and eye closure remains unimplemented pending a real classifier.

### DEC-042: Per-Exam Appearance Rules With Three-State Policies
- **Date**: 2026-08-04
- **Status**: Approved
- **Problem**: Appearance rules were previously treated as platform-wide constants. Research over 48 Indian examinations shows they are exam-specific and frequently contradictory, so any hardcoded majority behaviour is wrong for a known set of examinations. Verified conflicts: background is white or light for most bodies but MPSC prefers solid blue, green or red; spectacles are prohibited during SSC live capture, permitted without reflections by banking bodies, permitted only if regularly used by NTA, and permitted as normal corrective lenses by GATE; smiling is prohibited by UPSC and Railways but expressly allowed by CBSE; a printed name and date is required by TNPSC, Kerala PSC and CBSE and expressly prohibited by Railways; colour is required by most bodies but CUET-PG and UGC-NET accept black and white; verified face-occupancy thresholds are 50%, 60-70%, about 75% and 80%.
- **Decision**: Extend the canonical JSON Schema in `packages/exam-rules` and its Pydantic mirror with an appearance block carried per exam. Policy fields that a boolean cannot express use a three-state enumeration -- `permitted`, `prohibited`, `conditional` -- with a free-text condition string, because "prohibited except for religious reasons" and "permitted only if regularly worn" are neither yes nor no. This applies at minimum to spectacles and headwear. Background colour, face-coverage target, colour-versus-monochrome acceptance, ears visibility, smile permission and the name/date imprint are likewise carried per exam rather than assumed.
- **Reasoning**: This is the "Exam First, Tool Second" principle applied to appearance: the exam rule record drives the pipeline, and the research establishes that no majority default is safe. A two-state flag would force every conditional rule to be recorded as either a false prohibition or a false permission, and the conditional cases are exactly the ones with the highest cost of error, since they cover religious head coverings and prescription eyewear.
- **Consequences**: Warnings become exam-dependent: the same photograph may warn for one examination and pass silently for another, which is correct. The name/date imprint is a rendering capability the engine does not yet have and is scheduled as real work rather than a validation check. Rules recorded as unverifiable in the research are represented as absent rather than as permissive defaults, consistent with the no-silent-assumptions principle. Public guidance must not assert that all examinations require a white background, prohibit smiling, or prohibit spectacles; the verified evidence contradicts each of those claims.
- **Affected Modules**: `packages/exam-rules/schema/exam-rule.schema.json`, `services/image-engine/src/exam_photo/models/exam_rule.py`, `services/image-engine/src/exam_photo/orchestration/rule_resolver.py`, `examples/rules/`.
- **Approval Owner**: Lead Architect

### DEC-043: Natural Enhancement Corrects the Capture, Never the Subject
- **Date**: 2026-08-04
- **Status**: Approved
- **Problem**: The product owner asked for basic, natural enhancement -- lighting, contrast, sharpening, noise reduction -- explicitly bounded as "not unnatural and dramatic or unreal" and "completely optional, only if required". The output preparer already had brightness/contrast/sharpness machinery, but its mode defaulted to `none` and its adjustment factors were caller-supplied constants: nothing measured the photograph, so nothing could decide whether enhancement was required or how much. The obvious implementation -- measure a "good" reference population and drive every photograph toward its mean -- is unsafe, and was rejected before being built.
- **Decision**: Enhancement corrects **capture defects relative to each photograph's own rendering**, and never moves a subject toward a target appearance. Four corrections are planned, each triggered only by its own measured deficit: a compressed tonal range is stretched; clipped shadows or highlights are recovered away from the clipped end; a non-neutral illuminant is partially neutralised; a soft capture is sharpened. Each is capped at the output preparer's existing conservative limits (0.12 brightness, 0.12 contrast, 0.20 sharpness). A photograph with no measured deficit receives a no-op plan, which is the common case. Every adjustment actually applied is disclosed to the candidate rather than performed silently.
- **Reasoning**: An absolute luminance target would lighten dark skin, which the identity-preservation principle prohibits outright -- so the trigger for brightness correction is *clipping*, and the trigger for contrast correction is *compressed range*, neither of which is a property of the subject's complexion. A correctly exposed dark-skinned face has a healthy tonal range and no clipping, and is therefore left completely untouched; `test_a_correctly_exposed_dark_face_is_untouched` asserts exactly that and is the load-bearing test of this module. The colour-cast trigger is likewise a property of the illuminant rather than the subject: human skin under neutral light is red-dominant, measured at 38 to 88 levels of red over blue across all 40 photographs in the adversarial set, so a face where blue approaches or exceeds red is coloured light rather than a complexion. Cast correction is deliberately partial (capped at half the measured excess) because fully neutralising a severe stage-lit cast invents colour the sensor never recorded.
- **Consequences**: A reviewer's "perfect"/"clean" labels record pose, quality and compliance, **not** lighting, and are explicitly barred from being used as a photometric target -- this is recorded in the label fixture so a later reader cannot mistake them for one. One photograph in the set carries a cast severe enough (blue minus red +58.8, against a next-worst +20.1) that correction alone cannot rescue it, so it is both corrected and warned about. Disclosure was chosen over silent application at the product owner's direction. Noise reduction is specified here but not yet implemented; the other three corrections are.
- **Affected Modules**: `services/image-engine/src/exam_photo/suitability/enhancement_planner.py`, `services/image-engine/src/exam_photo/providers/output_preparers/deterministic_output_preparer.py`, `services/image-engine/tests/fixtures/adversarial_label_map.json`.
- **Approval Owner**: Lead Architect

### DEC-044: The Bottom Edge Is Anchored to the Chin, Not Left Over
- **Date**: 2026-08-04
- **Status**: Approved
- **Problem**: The output-invariant sweep failed 224 of 960 generated geometries, every one of them on below-chin space, and 212 of those where the head box reached far above the face box -- voluminous hair. Below-chin space was not constrained anywhere in the engine. It was a residual: whatever head height and top margin happened to leave. On a subject with a high crown that residual is large and systematic. The eye line as a fraction of crop height is `(eye - crown)/span * head_height + top_margin`, and the crown-to-eye distance measures ~0.64 of the crown-to-chin span on such subjects, so the 0.86 head-height target forces the eye line to 0.60 -- past its 0.54 ceiling even at the minimum top margin. Because the eye line was a constraint and below-chin space was not, the search bought the eye line by shrinking head height, and the 0.19 of frame height that freed up drained out below the chin where nothing looked at it. Verified on a real failing case: head height 0.792 against an 0.86 target, top margin pinned at its 0.02 minimum, eye line 0.527, below-chin 0.188.
- **Decision**: State below-chin space as a constraint in the candidate search, bounded at 0.15 of crop height, and rank it **above** the eye line in `_RELAXATION_TIERS` so the eye line is surrendered first. The product rule this encodes, from the product owner, is that the bottom edge is anchored just below the last beard line -- or just below the chin if clean-shaven -- with a small margin, tightened further wherever the target dimensions allow; framing wins, and the eye line lands where the resulting frame puts it. The engine cannot detect a beard line (DEC-035 records three attempts rejected on measured evidence), so the anchor is the existing uniform chin-plus-margin floor, `_CHIN_BEARD_MARGIN_RATIO`.
- **Reasoning**: Below-chin space is not an independent degree of freedom -- `below_chin = 1 - top_margin - head_height` -- so the constraint adds no new axis to the search. What it adds is a *statement* of the rule. Left implicit in head height and top margin, the rule was silently invertible in exactly the case it matters. The bound at 0.15 is read off measurement on both sides: across the 60 approved ideal outputs, chin-to-bottom as a fraction of their own frame height is min 0.054, p25 0.081, median 0.102, p75 0.142, p90 0.179, max 0.247; across the ten engine outputs a reviewer assessed individually, every accepted photograph sat at or below 0.155 and the two rejected as too loose sat at 0.188 and 0.190. 0.15 therefore sits above ordinary approved framing and below both rejections and the 0.175 delivered invariant, leaving room for the candidate grid's integer quantisation, which moves head height ~0.02 per step.
- **Consequences**: The last relaxation tier deliberately does **not** waive `below_chin`, which is the one place the ladder is not cumulative. That tier adds exactly one constraint, `head_height_min`, and below-chin space does not conflict with it: head height is set by the crop's size and below-chin space by its position, so giving up the second buys nothing toward the first. Carrying it down anyway -- purely because the sets nest -- left 12 geometries delivering 0.20-0.21 while a 0.15 candidate sat unchosen at the same tier, the cost function having placed those crops on the padding term alone. Three validation regions moved with the search in the same change, per the defect class in DEC-029 and DEC-038: head-coverage validation and margin reporting are now keyed to `mandatory_box` under the search's own condition (adaptive planning, subject clipping disallowed) rather than to `outer_hair_relaxation_used`, which is only the weaker statement that no candidate happened to keep the whole preservation box. A crop could otherwise be selected as "strict", leaving that flag false, while its bottom edge sat correctly at the chin/beard line and well above the head estimate's bottom -- and validation then reported the planner's intended framing as a blocking `CROP_HEAD_CLIPPED`. Mask retention deliberately stays measured against the generous box: keyed to `mandatory_box` it would return 1.0 by construction on every crop the search can select, and a check that cannot fail is worse than no check. Sweep violations 224 -> 0; delivered below-chin space now measures min 0.082, median 0.110, p90 0.137, max 0.151. Six of the 60 approved ideals themselves exceed the 0.175 invariant, four in the 1200x1800 class where head height is bound by the target's width rather than by composition; the invariant is calibrated on the reviewer's verdicts over engine outputs and remains a report rather than a refusal (DEC-041).
- **Affected Modules**: `services/image-engine/src/exam_photo/providers/crop_planners/deterministic_crop_planner.py`, `services/image-engine/tests/orchestration/test_output_invariants.py`, `services/image-engine/tests/providers/test_crop_mode_a.py`, `services/image-engine/tests/orchestration/test_visual_regression.py`, `HANDOFF-INVARIANTS.md`.
- **Approval Owner**: Lead Architect
- **Amended 2026-08-04 (the preservation box has no bottom)**: The sweep reached zero while photograph 35 -- one the product owner had flagged by eye as too loose below the chin -- did not move a pixel. Instrumenting the candidate search on the owner's own review photographs showed why, and it was a larger defect than the one the entry was written for. The best candidate on every photograph measured was a fully compliant **tier 0** crop, and it was being discarded by the strict/relaxed preference, which prefers a candidate keeping the whole preservation box and applies that preference as an *override* rather than a tie-break -- a strict candidate wins outright whenever one exists, so the preference silently outranked every composition target the search had just scored. The clause responsible was `b_cand < preserve_box.bottom`. That box's bottom is not an observation of the subject: it is a fixed geometric expansion past the jaw, landing in the neck, so requiring the crop to reach it made the bottom edge a consequence of the head estimator's padding rather than of the candidate's anatomy. It is removed. The chin and beard boundary remain protected by `chin_protection_y` -- the landmark chin plus the beard margin -- as a hard constraint, which is the actual promise; the strict preference is about hair, and now covers only the crown and the two sides, as its own comment always claimed. Measured on the ten photographs labelled perfect in the 40-photo adversarial set, below-chin space as a fraction of frame height: photo 4 0.155 -> 0.081, 5 0.124 -> 0.104, 8 0.124 -> 0.105, 13 unchanged 0.117, 17 0.155 -> 0.111, 18 0.151 -> 0.117, 19 0.147 -> 0.098, 27 unchanged 0.111, 31 0.188 -> 0.146, 35 0.190 -> 0.111. Head height rose or held on all ten (35: 0.766 -> 0.857; 19: 0.823 -> 0.877; 4: 0.805 -> 0.862). All ten now satisfy every invariant, where two did not before. Photograph 31 remains the loosest at 0.146 because its subject's hair pins the crop's sides, which is the strict preference doing the job it is actually for. Across the synthetic sweep the delivered distribution tightened from min 0.082 / median 0.110 / max 0.151 to min 0.075 / median 0.103 / max 0.151, against an approved-ideal median of 0.102. **The general lesson is the one worth carrying: a preference expressed as an override is not a preference.** The strict/relaxed mechanism ranks before tier and cost, so anything folded into it is promoted above every constraint in the ladder, whether or not that was intended.
