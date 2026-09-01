# Development Roadmap (09_DEVELOPMENT_ROADMAP.md)

This roadmap charts the milestones for building the Indian Exam-Photo Compliance Platform across multiple development cycles.

---

## Phases and Milestones

### Phase 0: Foundation and Prototype
This phase covers establishing directory, configuration, and interfaces foundations.

#### Milestone 1: Repository Foundation
- **Objective**: Establish repo layout, document product criteria, set up packaging, and verify linters and test CI scripts.
- **Dependencies**: None.
- **Expected Deliverables**: Structural directories, root documents (`AGENTS.md`, `CONTRIBUTING.md`), `image-engine` package configs, validation CI configs.
- **Exit Criteria**: Codebase runs static analysis tools and unit tests successfully under standard CI pipelines.
- **Status**: **Completed (Milestone 1)**
- **Explicitly Excluded Work**: No image loading, AI face boundaries, segmentation models, frontend frameworks, database setups, or public hosting deployments.

#### Milestone 2: Typed Examination-Rule Contracts
- **Objective**: Define JSON Schema configurations for exam rules.
- **Dependencies**: Milestone 1.
- **Expected Deliverables**: Schema files, JSON validations inside `packages/exam-rules`.
- **Exit Criteria**: Automated checks verify example rule files parse without errors.
- **Status**: **Completed (Milestone 2)**
- **Explicitly Excluded Work**: Direct database storage or rule editors.

#### Milestone 3: Secure Input Normalization
- **Objective**: Implement file signature and orientation fixes.
- **Dependencies**: Milestone 1.
- **Expected Deliverables**: Secure byte verification helpers, orientation normalization algorithms.
- **Exit Criteria**: Code successfully parses magic bytes and processes EXIF rotation updates.
- **Status**: **Completed (Milestone 3)**
- **Explicitly Excluded Work**: Face extraction, landmark checks.

#### Milestone 4: Source-Photo Suitability Framework
- **Objective**: Establish suitability reporting structure and replace-able CV provider contracts.
- **Dependencies**: Milestone 3.
- **Expected Deliverables**: BoundingBox, Point, Pose, Landmarks, face provider interfaces, head estimator interfaces, evaluator engine, fake testing providers.
- **Exit Criteria**: Checks execute, fakes verify orchestration, and unit test suites pass successfully.
- **Status**: **Completed (Milestone 4)**
- **Explicitly Excluded Work**: Real MediaPipe or machine learning library installations/inference.

#### Milestone 5: Real Face Detection Integration
- **Objective**: Integrate a real computer-vision face-detection model (e.g. MediaPipe Face Detector or lightweight ONNX model) to replace the fake face provider.
- **Dependencies**: Milestone 4.
- **Expected Deliverables**: FaceDetectionProvider implementation wrapper, model weight loading mechanism, and bounding box extractor.
- **Exit Criteria**: Unit tests verify correct face detection coordinates on public domain and synthetic face fixtures.
- **Status**: **Completed (Milestone 5)** (with `short_range` selected as the provisional baseline)


#### Milestone 6: Landmark-Assisted Geometric Head-Box Estimation
- **Objective**: Implement a provisional landmark-assisted geometric head-box estimator (`LandmarkGeometricHeadEstimator`) to calculate a conservative head-region estimate using the validated face bounding box and canonical facial landmarks, and integrate it with the suitability framework.
- **Dependencies**: Milestone 5.
- **Expected Deliverables**: `LandmarkGeometricHeadEstimator` provider implementing `HeadEstimationProvider`, refined suitability issue codes, dynamic normalized head box properties, and CLI `estimate-head` support.
- **Exit Criteria**: All unit tests pass; benchmark confirms deterministic execution; clamping to image edges produces `suspected` clipping state; compatibility properties preserve correct type/fallback mapping.
- **Status**: **Completed (Milestone 6: provisional landmark-assisted geometric head-box baseline)**


#### Milestone 7: Portrait-Segmentation and Coarse Foreground-Mask Generation
- **Objective**: Evaluate local CPU-capable portrait segmentation technologies, select a provisional baseline (MediaPipe Selfie Multiclass/Binary), integrate it behind a provider-neutral contract, and generate validated coarse foreground masks.
- **Dependencies**: Milestone 5, Milestone 6.
- **Expected Deliverables**: `SubjectSegmentationProvider` contract, `MediapipeSubjectSegmenter` implementation, `MaskValidationReport` (DSU connectivity component analysis, face containment, head coverage), `PublicSegmentationReport` and `InternalSegmentationDiagnostic` models, CLI `segment-subject` support, and benchmark tools.
- **Exit Criteria**: All unit and integration tests pass; benchmark compares multiclass vs binary segmenters on licensed fixtures; mask validation detects empty, full frame, fragmented, and non-contained face masks.
- **Status**: **Milestone 7 completed: repository-verified provisional coarse subject-segmentation baseline.**

#### Milestone 8: Coarse-Mask Edge Refinement and Foreground-Boundary Cleanup
- **Objective**: Convert the coarse portrait segmentation masks into a cleaner, smoothed foreground boundary, creating a high-resolution alpha mask and trimap (0/128/255) for downstream matting and background replacement.
- **Dependencies**: Milestone 7.
- **Expected Deliverables**: `ForegroundRefinementProvider` protocol, `RefinedMaskResult` and `RefinedMaskValidationReport` models, `MorphologicalForegroundRefiner` implementation, CLI `refine-mask` command, and `benchmark_mask_refinement.py` benchmark.
- **Exit Criteria**: Stability and Quality IoU metrics tracked over real fixtures; CLI verify returns refined alpha/binary/trimap outputs; CI tests confirm boundary morphological closing/opening, size-aware radius scaling, and face protection are fully operational.
- **Status**: **Completed (Milestone 8: morphological foreground-boundary refinement baseline)**

#### Milestone 9: Exact-Dimension Crop (Crop Mode A)
- **Objective**: Implement Crop Mode A: exact aspect ratio crop centered around the face, preserving hair, ears, chin, and beard before resizing.
- **Dependencies**: Milestone 4, Milestone 6, Milestone 8.
- **Expected Deliverables**: Aspect ratio crop calculator, face centering and centering preservation math.
- **Exit Criteria**: Tests verify output crop dimensions match required aspect ratios without stretching or distortion.
- **Status**: **Completed (Milestone 9: exact-aspect crop planning baseline)**

#### Milestone 10: Face/Head-Led Crop (Crop Mode B)
- **Objective**: Implement Crop Mode B: tight crop with dimension range based on the estimated head region.
- **Dependencies**: Milestone 4, Milestone 6, Milestone 8.
- **Expected Deliverables**: `DeterministicCropModeBPlanner`, `CropModeBConfig`, `CropModeBResult`, head-led crop window calculation, CLI `plan-crop-mode-b` command, and benchmark.
- **Exit Criteria**: Tests verify crop windows satisfy head-height ratio constraints and natural margins; benchmark confirms deterministic execution on all licensed fixtures.
- **Status**: **Completed (Milestone 10: head-led range crop planning baseline)**

#### Milestone 11: Background Composition
- **Objective**: Implement the first safe, deterministic background replacement / background composition baseline for exam-photo processing.
- **Dependencies**: Milestone 8, Milestone 9, Milestone 10.
- **Expected Deliverables**: `BackgroundComposer` protocol, `SolidBackgroundComposer`, CLI `compose-background`, and benchmarks.
- **Exit Criteria**: Output correctly composites the foreground onto the target colour, validation rules block invalid dimensions/coverage, and benchmark passes on fixtures.
- **Status**: **Completed (Milestone 11)**

#### Milestone 12: Resizing, output dimensioning, format preparation, restrained enhancement
- **Objective**: Implement high-quality image resizing (LANCZOS/Bicubic), prepare formatting, and handle exposure, contrast, and sharpness adjustments.
- **Dependencies**: Milestone 3, Milestone 9, Milestone 10, Milestone 11.
- **Expected Deliverables**: Resize utility, format conversion, luminance correction filter, and unsharp mask filter.
- **Exit Criteria**: Output resolution matches rule criteria exactly, and processed image sharpness metrics pass suitability tests.
- **Status**: **Completed (Milestone 12: Resizing, output dimensioning, format preparation, and restrained enhancement baseline)**

#### Milestone 13: Quality-Aware Compression Loop
- **Objective**: Implement an iterative file compression loop to compress the normalized, cropped, and resized image to be close to but strictly under the maximum byte size limit.
- **Dependencies**: Milestone 12.
- **Expected Deliverables**: Iterative encoder optimizer, target file size compliance validator.
- **Exit Criteria**: Test cases assert output files comply with rules' file size limits while maintaining visual quality.
- **Status**: **Completed (Milestone 13: Quality-Aware Compression Loop Baseline)**

#### Milestone 14: Full CLI orchestration and final validation
- **Objective**: Connect the CLI to run the full pipeline (normalization, suitability, crop, remove background, enhance, compress) against configured rules.
- **Dependencies**: Milestones 2, 7, 8, 9, 10, 11, 12, 13.
- **Expected Deliverables**: Integrated end-to-end CLI command handlers.
- **Exit Criteria**: Running CLI with a rule file and input image outputs a processed compliant photo or structured compliance failures.
- **Status**: **Completed (Milestone 14: Full CLI orchestration and final validation)**

#### Milestone 15: Local Processing API, Privacy Lifecycle, and Safe Job Orchestration
- **Objective**: Expose the rule-orchestrated processing pipeline through a safe, local-only API boundary with file management under a privacy-first temporary lifecycle.
- **Dependencies**: Milestone 14.
- **Expected Deliverables**: FastAPI application (`serve-api`), persistent job manifests (`job.json`), path traversal guards, size upload limits, relative API routes, manual deletion, and TTL cleanup.
- **Exit Criteria**: API integration tests and smoke tests execute successfully; CLI subcommand `serve-api` is verified.
- **Status**: **Completed (Milestone 15)**

#### Milestone 16: Public Web App MVP and Local API Integration
- **Objective**: Build the public Next.js single-page application MVP allowing users to select/upload exam rules, upload candidate photos, process via local API, view diagnostic reports, download compliant output, and delete job assets.
- **Dependencies**: Milestone 15, packages/exam-rules.
- **Expected Deliverables**: Interactive user page, file validation wrappers, api-client, step-based stepper components, result previewers, delete flows with URL revocation.
- **Exit Criteria**: Typescript typechecks, Vitest tests, and Next.js production builds pass successfully. Deletion and download flows are verified.
- **Status**: **Completed (Milestone 16)**

#### Milestone 17: Local Rule Configuration Console and Validation API
- **Objective**: Build a local developer/operator console (`/admin/rules`) to select, edit, reset, and export structured rules, coupled with a stateless backend validation endpoint (`POST /v1/rules/validate`) that returns standard 422 errors and does not write files.
- **Dependencies**: Milestone 16.
- **Expected Deliverables**: Gated admin console layout, rule editor state helpers, warning banner, reset/revert actions, backend stateless validation endpoint, and frontend-sync tests.
- **Exit Criteria**: Unit tests, typechecks, and builds pass; backend API tests verify 422 validation response and no file writes; frontend/backend sync tests pass.
- **Status**: **Completed (Milestone 17: Local Rule Configuration Console and Validation API)**


### Phase 0.5: Engine Quality Hardening Against a Reference Set

This phase was driven by measurement against user-supplied reference material
rather than by feature scope: a 60-photo set with matched approved outputs, and
later a 40-photo adversarial set with human defect labels. Decisions are
recorded as DEC-029 through DEC-043.

#### Milestone 18: Generalized Engine Visual Quality Hardening
- **Objective**: Raise matte and composition quality to a publishable standard, replacing the coarse selfie segmenter with a portrait matting backend and correcting the crop geometry against approved reference outputs.
- **Dependencies**: Milestone 17.
- **Expected Deliverables**: BiRefNet matting backend and vendored model assets; dense face-landmark refinement; adaptive portrait composition; crop margins calibrated to the approved ideal outputs; matting recomputed on the planned crop region; matched engine-vs-ideal benchmark.
- **Exit Criteria**: Measured across all 60 reference pairs -- 57/60 produce output, margin mean absolute error 0.0422 against the approved ideals, median delivered head height 0.833 against an ideal 0.855.
- **Status**: **Completed (Milestone 18)** -- see DEC-029 through DEC-040.
- **Explicitly Excluded Work**: Appearance classification, candidate-facing messaging, throughput work.

#### Milestone 18B: Candidate Disposition Policy and Natural Enhancement
- **Objective**: Decide and implement what the platform does with a non-compliant photograph, and apply restrained enhancement only where a capture defect is measured.
- **Dependencies**: Milestone 18; the 48-examination input-rule research.
- **Expected Deliverables**: Accept/warn/block policy (DEC-041); per-exam appearance rules with three-state policies in the canonical schema (DEC-042); enhancement planned from measured deficits (DEC-043); 11 real exam rule records; a 40-photo human-labelled ground-truth fixture.
- **Exit Criteria**: Measured against the reviewer's own labels at an ordinary output size -- 29 accept, 9 warn, 2 block, with zero false positives across the ten photographs labelled clean.
- **Status**: **Completed (Milestone 18B)**
- **Explicitly Excluded Work**: Sunglasses, headwear and eye-closure detection, all of which were measured as unreliable with the shipped models and deferred to Milestone 23.

---

### Phase 0.6: Path to Public Launch

Milestones 19 to 30 replace the former placeholder line covering 18-35. The
governing constraint is that the platform will publish which photographs are
rejected, so every rejection has to be defensible before launch.

#### Milestone 19: Exam Rule Completeness -- Output Specifications
- **Objective**: Give every encoded exam a verified output specification so the engine can produce a correctly sized, named and compressed file for a real examination.
- **Dependencies**: Milestone 18B.
- **Expected Deliverables**: A second official-source research pass covering pixel dimensions, file size, DPI, format and filename rules for the 11 encoded exams; updated rule records; provenance upgraded from `platform_default` to `official`.
- **Exit Criteria**: All 11 records leave `provisional` status and produce a correctly sized, correctly named output end to end.
- **Status**: Not started.
- **Why this is first**: Every record currently carries `dimensions.mode: unspecified`, because the appearance research deliberately excluded file specifications. Until this closes, the engine cannot size a photograph for any real examination.

#### Milestone 20: Candidate-Facing Disposition Interface
- **Objective**: Surface in the web application what the engine already computes.
- **Dependencies**: Milestone 18B.
- **Expected Deliverables**: An acknowledgement step for `likely_rejection` findings with retaking as the primary action and downloading as a quiet secondary; an inline notice for `possible_issue`; disclosure of any enhancement applied; download enabled in every non-blocked state.
- **Exit Criteria**: Every finding the engine can emit has a tested interface state; blocked photographs explain themselves in candidate language.
- **Status**: Not started.
- **Explicitly Excluded Work**: No appearance signal may be presented as a rejection before its reliability is measured (DEC-041).

#### Milestone 21: Published Upload Instruction Manual
- **Objective**: Publish the hero-banner guidance telling candidates how to photograph and upload, and what will be rejected.
- **Dependencies**: Milestone 19.
- **Expected Deliverables**: Manual content derived from the 48-examination research; per-exam variations surfaced where bodies conflict; citations retained for every claim.
- **Exit Criteria**: Published, and every stated rule traces to a cited official source.
- **Status**: Not started.
- **Explicitly Excluded Work**: Blanket claims the evidence contradicts -- that all examinations require a white background, prohibit smiling, or prohibit spectacles.

#### Milestone 22: Engine Edge-Quality Closeout
- **Objective**: Close the three known engine defects remaining after Milestone 18.
- **Dependencies**: Milestone 18.
- **Expected Deliverables**: Hair-edge colour fringe corrected; crop planning fixed for hard photographs where the subject occupies little of the frame; noise reduction implemented as specified but not built in DEC-043.
- **Exit Criteria**: Re-verified on the 40-photo adversarial set with no disposition regression.
- **Status**: Not started.

#### Milestone 23: Appearance Classifiers
- **Objective**: Detect sunglasses, head coverings and closed eyes to a measured standard.
- **Dependencies**: Milestone 20.
- **Expected Deliverables**: A face-attribute classifier scored against the 40-photo label fixture; per-exam interpretation driven by the DEC-042 three-state policies.
- **Exit Criteria**: Published precision and recall per class; no signal promoted to `likely_rejection` below an agreed bar.
- **Status**: Not started.
- **Principal risk**: Head coverings must distinguish a cap from a turban or hijab, because IBPS, GATE and the Indian Navy permit religious coverings that SSC prohibits. Misclassifying these is a discrimination problem rather than an accuracy problem, and the class may ship as advisory guidance instead.

#### Milestone 24: Throughput and Inference Cost
- **Objective**: Establish whether the engine can serve examination-season demand, and at what cost per photograph.
- **Dependencies**: Milestone 18.
- **Expected Deliverables**: Measured latency budget; GPU or reduced-model inference path; a real job queue with backpressure; autoscaling model; unit cost per processed photograph.
- **Exit Criteria**: A measured throughput and cost figure capacity can be planned against.
- **Status**: Partially addressed. DEC-054 exported BiRefNet to ONNX and made it the default matting backend, halving the figure below without touching the maths: mean per-photograph time over the ten `perfect` photographs at 413x531 fell from 21.38 s to **10.64 s**, warmed, with delivered JPEGs pixel-equivalent to the PyTorch backend. The queue, autoscaling and unit-cost deliverables are untouched.
- **Why this was the largest risk**: Originally measured at 16-24 seconds per photograph on CPU, roughly doubled by the crop-region rematte, giving 30-40 seconds each -- not viable at the concurrency implied by national examination cycles. The ONNX export removed the acute half of that without the model change that would have partly invalidated Milestone 22.
- **What remains**: Two items, in this order. (1) **Cold start**: onnxruntime pays a 100-150 s one-time spin-up on its first inference in a process and nothing warms the process at boot, so the first request to a fresh worker is catastrophic and `/health` cannot distinguish a warm process from a cold one. This is a readiness-protocol gap, not a throughput one, and it must be closed before the first deploy. (2) **The double matte**: DEC-040 runs BiRefNet twice per photograph, whole-frame then crop-region, and the first pass exists only to feed crop planning. Reducing its resolution is the obvious remaining lever, but it trades against the resolution argument DEC-040 was built on, so it needs measurement rather than assumption.

#### Milestone 25: Service Hardening for Public Exposure
- **Objective**: Make the processing API safe to expose publicly.
- **Dependencies**: Milestone 24.
- **Expected Deliverables**: Authentication, rate limiting, upload size and abuse controls, TLS termination, CORS policy, structured logging and alerting.
- **Exit Criteria**: Passes an adversarial security review.
- **Status**: Not started.
- **Current state**: The API is documented as local-only with no TLS, authentication or rate limiting, and cannot face the public as built.

#### Milestone 26: Privacy, Retention and Data Protection
- **Objective**: Handle candidate photographs lawfully and demonstrably.
- **Dependencies**: Milestone 25.
- **Expected Deliverables**: Retention and deletion policy with enforced guarantees; consent and privacy copy; a documented data-flow and processing record; access controls on stored artifacts.
- **Exit Criteria**: A documented data lifecycle reviewed by someone qualified to assess it.
- **Status**: Not started.
- **Note**: Candidate face photographs are sensitive personal data and India's Digital Personal Data Protection Act 2023 applies. This milestone requires legal input; engineering can implement controls but should not decide what compliance requires.

#### Milestone 27: Exam Catalogue Scale-Out
- **Objective**: Cover the examinations representing the large majority of candidate volume.
- **Dependencies**: Milestone 19.
- **Expected Deliverables**: 30 or more encoded examinations drawn from the 48 already researched; the unverified and partially verified bodies revisited.
- **Exit Criteria**: Coverage target met, with every record citing an official source and unverified categories recorded as absent rather than assumed.
- **Status**: Not started.

#### Milestone 28: Accuracy QA and Regression Gate
- **Objective**: Prevent silent regression in disposition accuracy and crop composition.
- **Dependencies**: Milestones 22 and 23.
- **Expected Deliverables**: The 40-photo label fixture wired into CI as an accuracy gate; refreshed paired ideal outputs for composition scoring.
- **Exit Criteria**: A build fails when disposition accuracy or crop composition regresses beyond an agreed tolerance.
- **Status**: Not started.
- **Blocked on input**: The adversarial 40 have no paired ideal outputs, so crop composition currently cannot be scored or gated at all.

#### Milestone 29: Accessibility, Mobile and Language
- **Objective**: Make the platform usable by the candidates who actually use it.
- **Dependencies**: Milestones 20 and 21.
- **Expected Deliverables**: Mobile-first upload and review flow; Hindi at minimum alongside English; WCAG basics on contrast, focus order and labelling.
- **Exit Criteria**: Usable one-handed on a mid-range Android device on a slow connection.
- **Status**: Not started.

#### Milestone 30: Pre-Launch Hardening and Load Test
- **Objective**: Establish launch readiness.
- **Dependencies**: All of Milestones 19 to 29.
- **Expected Deliverables**: Full marker-gated test matrix; load test at projected peak; security review; incident runbook; rollback plan.
- **Exit Criteria**: Documented go/no-go decision.
- **Status**: Not started.

---

### Phase 1: Post-MVP & Future Operations
- **Milestone 36**: Post-MVP crop adjustments editor tool.
- **Milestone 37**: Background manual mask touchup brush tools.
- **Milestone 38**: Billing gates and Stripe/Razorpay integrations.
- **Milestone 39**: Operational analytics, telemetry, and metrics dashboards.

---

## Critical path

`19 -> 21` is the shortest route to the published upload manual. `24 -> 25 -> 26`
is the longest chain and the one that decides whether the platform can go live
at all. Milestones 20, 22 and 24 touch different areas and can proceed in
parallel.

Milestone 24 should be probed early even while feature work continues: if the
inference budget does not hold, the matting backend changes and part of
Milestone 22 is rework.

## Related documents needing revision

These predate the current direction and should be rewritten rather than
consulted:

- `01_MVP_SCOPE.md` (2026-06-17) -- predates the published-rejection-criteria
  strategy, which changes what the minimum product includes.
- `05_PRIVACY_SECURITY.md` (2026-06-17) -- governs Milestone 26.
- `06_QA_STRATEGY.md` (2026-06-17) -- governs Milestone 28.
