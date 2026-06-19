# Decision Log (08_DECISION_LOG.md)

This log tracks architectural and product decisions, open questions, and recommended paths.

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
- **Affected Modules**: `services/image-engine/providers/crop_planners/deterministic_crop_mode_b_planner.py`, `services/image-engine/providers/crop_planning.py`.
- **Approval Owner**: Lead Architect



