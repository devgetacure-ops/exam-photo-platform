# Landmark-Assisted Geometric Head-Box Estimation Technology Spike (Milestone 6)

This technology spike evaluates practical local CPU-compatible approaches for estimating the candidate's complete head region to support down-stream natural cropping.

> [!IMPORTANT]
> **Partly superseded (2026-08-04). Retained as a historical record.** The
> geometric expansion recommended here is still computed, but the crop planner
> no longer trusts it for the measurements that matter. Expansion ratios
> derived from the detector box proved unreliable in both directions -- the box
> bottom lands in the neck, and on low-confidence detections the box top sits
> above the hairline -- so crown, chin and head-core width are now measured
> from the subject mask and dense landmarks instead (DEC-037, DEC-038).
>
> The specific failure worth remembering: the geometric estimate widens
> ear-tragion keypoints on the assumption that ears are visible. On a subject
> whose hair covers their ears it produced a head 60% wider than the true one,
> which no crop could satisfy alongside the coverage target.

---

## 1. Candidate Approaches Evaluated

The following approaches were evaluated for locating the complete head bounding box:

### Approach A: Landmark-Assisted Geometric Heuristic Expansion
* **Description**: Consumes the canonical `FaceDetection` and `Landmarks` model outputs to compute a crop-oriented head bounding box using config-defined vertical and lateral scaling expansion factors.
* **Licence**: MIT/Apache-2.0 (No third-party packages needed beyond current core).
* **Model size**: 0 MB (Code-only logic).
* **Local Offline**: Yes.
* **CPU Latency**: < 0.1 ms (Measured locally).
* **Deterministic**: 100% deterministic given identical inputs and configurations.
* **Ears / Beard / Hair / Coverings**:
  * Visible hair: Inferred using top expansion ratio (cannot measure actual biological hair height).
  * Left/Right bounds: Inferred using side expansion ratio, adjusted slightly when ear tragions are present.
  * Chin/Beard: Inferred using lower expansion and beard allowance ratios from config (cannot detect actual beard presence or thickness).
  * Coverings: Expands geometrically over coverings (cannot classify or detect coverings).
* **Clipping Detection**: Edge-proximity check. Clamping to image boundaries results in `suspected` clipping finding rather than `confirmed`.
* **Platform Support**: Fully compatible with any platform supporting Python 3.11+.
* **Bias / Privacy**: No biometric templates, zero demographic bias since it uses only geometry. High privacy (no image data retained or analyzed beyond bounding box coordinates).
* **Observations**:
  * *Measured*: Latency is negligible; logic is fully offline.
  * *Assumption*: Face bounding box is pre-validated and reasonably accurate.
  * *Unresolved*: Optimal default expansion ratios for diverse hairstyles and beards.

### Approach B: Dense Face Mesh / 3D Landmark Estimation (e.g. MediaPipe FaceMesh)
* **Description**: MediaPipe FaceMesh provides 468 (or 478) dense 3D landmarks representing facial surface geometry.
* **Licence**: Apache-2.0.
* **Model size**: ~10 MB.
* **Local Offline**: Yes.
* **CPU Latency**: ~30–50 ms.
* **Deterministic**: Yes.
* **Ears / Beard / Hair / Coverings**:
  * Visible hair: Fails to detect hair; does not place landmarks on hair regions or coverings.
  * Left/Right bounds: Provides good cheek/jaw contours, but does not cover outer ears or ear outlines.
  * Chin/Beard: Locates the physical chin surface, but landmarks do not extend to beards.
  * Coverings: Blocked or corrupted by hijabs/turbans.
* **Platform Support**: Windows/Linux prebuilt wheels.
* **Bias / Privacy**: Biometric mesh structure. Might leak spatial/structural identity characteristics.
* **Observations**:
  * *Documentation-based*: FaceMesh coordinates do not cover hair or outer ears.
  * *Assumption*: High compute overhead on CPU for low marginal value in head-box cropping.

### Approach C: Dedicated Head Detection Models (e.g., custom YOLO or SSD head detector)
* **Description**: A dedicated object detection model trained to output bounding boxes for "head" instead of "face".
* **Licence**: Varies (many public models are AGPL/GPL).
* **Model size**: 15–50 MB.
* **Local Offline**: Yes.
* **CPU Latency**: ~50–150 ms.
* **Deterministic**: Yes.
* **Ears / Beard / Hair / Coverings**:
  * Visible hair: Trained to enclose the head including hair.
  * Left/Right bounds: Covers ears and cheeks.
  * Chin/Beard: Covers chin and beard.
  * Coverings: Usually encloses head coverings.
* **Platform Support**: Requires ONNX runtime or PyTorch. High dependency complexity.
* **Bias / Privacy**: Non-biometric (object detection only).
* **Observations**:
  * *Documentation-based*: Requires substantial model download and introduces large CPU runtime (e.g., ONNX Runtime), violating the principle of avoiding a second large CV runtime without strong evidence.
  * *Unresolved*: Model availability with Apache-2.0 or commercial-friendly licensing.

### Approach D: Portrait Segmentation Models (e.g., MediaPipe Selfie Segmenter)
* **Description**: Portrait segmentation extracts a binary mask separating the foreground person from the background. Head bounds can be derived from the mask bounding box.
* **Licence**: Apache-2.0.
* **Model size**: ~5 MB.
* **Local Offline**: Yes.
* **CPU Latency**: ~20–40 ms.
* **Deterministic**: Yes.
* **Ears / Beard / Hair / Coverings**:
  * Visible hair: Extracts hair boundaries very accurately (curly/voluminous hair is segmented).
  * Left/Right bounds: Includes ears.
  * Chin/Beard: Includes chin and beards.
  * Coverings: Includes hijabs, turbans, and hats.
* **Platform Support**: Windows/Linux prebuilt wheels.
* **Bias / Privacy**: High privacy, no identity recognition.
* **Observations**:
  * *Documentation-based*: Ideal for background replacement (Milestone 7), but overkill for pure crop head-box estimation in Milestone 6 if a lightweight geometric fallback performs sufficiently.

---

## 2. Technology Comparison Matrix

| Criteria | Approach A (Geometric) | Approach B (FaceMesh) | Approach C (YOLO Head) | Approach D (Selfie Segmenter) |
|---|---|---|---|---|
| **Visible Hair Bounds** | ⚠️ Inferred | ❌ No | ✅ Yes | ✅ Yes |
| **Ear Bounds** | ⚠️ Inferred | ❌ No | ✅ Yes | ✅ Yes |
| **Lower Beard Bounds** | ⚠️ Inferred | ❌ No | ✅ Yes | ✅ Yes |
| **CPU Latency** | **< 0.1 ms** | ~40 ms | ~100 ms | ~30 ms |
| **Model Size** | **0 MB** | ~10 MB | ~20 MB | ~5 MB |
| **Dependencies** | None (Core only) | Mediapipe | ONNX Runtime | Mediapipe |
| **Licence** | **Commercial** | Apache-2.0 | GPL/AGPL (typical) | Apache-2.0 |
| **Demographic Bias** | **None** | Moderate | Low | Low |

---

## 3. Selected Provisional Baseline: Approach A (Geometric)

### Selection Rationale
* **Zero Overhead**: Does not add any extra packages or model files to download.
* **Speed & Efficiency**: Runs virtually instantaneously (< 0.1 ms on CPU).
* **Determinism**: Completely deterministic for identical input parameters.
* **Robust Fallback**: Provides a clean geometric baseline and logical boundary-checking framework that remains fully compatible with future segmentation stages (Milestone 7) or dedicated ML estimators.

### Scope & Limitations of the Provisional Baseline
* **No biological boundary detection**: The estimator cannot "see" where the hair, ears, or beard actually end. All boundaries are marked as `geometry_inferred` or `landmark_inferred` rather than `observed`.
* **Unknown boundaries**: Beard and ear visibility remain `unknown` or `not_applicable` unless the configuration is adjusted.
* **Clipping**: When coordinates touch the image edge, clipping is reported as `suspected` rather than `confirmed`, since the actual subject boundary cannot be observed.
