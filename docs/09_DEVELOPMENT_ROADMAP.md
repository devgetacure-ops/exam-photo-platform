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
- **Objective**: Implement algorithms to refine the coarse portrait segmentation masks, smoothing boundaries and handling complex areas like hair/ears/shoulders.
- **Dependencies**: Milestone 7.
- **Expected Deliverables**: Edge refinement filter/model integration, alpha matting, and boundary cleanup logic.
- **Exit Criteria**: Mask boundaries show improved transition smoothness and reduced artifacts compared to the coarse baseline.

#### Milestone 9: Exact-Dimension Crop (Crop Mode A)
- **Objective**: Implement Crop Mode A: exact aspect ratio crop centered around the face, preserving hair, ears, chin, and beard before resizing.
- **Dependencies**: Milestone 4, Milestone 6, Milestone 8.
- **Expected Deliverables**: Aspect ratio crop calculator, face centering and centering preservation math.
- **Exit Criteria**: Tests verify output crop dimensions match required aspect ratios without stretching or distortion.

#### Milestone 10: Face/Head-Led Crop (Crop Mode B)
- **Objective**: Implement Crop Mode B: tight crop with dimension range based on the estimated head region.
- **Dependencies**: Milestone 4, Milestone 6, Milestone 8.
- **Expected Deliverables**: Margined head crop calculator and padding builder.
- **Exit Criteria**: Output images satisfy the rule range constraints and head margins.

#### Milestone 11: Image Resizing & Enhancement
- **Objective**: Implement high-quality image resizing (LANCZOS/Bicubic) and exposure, contrast, and sharpness adjustments.
- **Dependencies**: Milestone 3, Milestone 9, Milestone 10.
- **Expected Deliverables**: Resize utility, luminance correction filter, and unsharp mask filter.
- **Exit Criteria**: Output resolution matches rule criteria exactly, and processed image sharpness metrics pass suitability tests.

#### Milestone 12: Quality-Aware Compression Loop
- **Objective**: Implement an iterative file compression loop to compress the normalized, cropped image to be close to but strictly under the maximum byte size limit.
- **Dependencies**: Milestone 3, Milestone 11.
- **Expected Deliverables**: Iterative encoder optimizer, target file size compliance validator.
- **Exit Criteria**: Test cases assert output files comply with rules' file size limits while maintaining visual quality.

#### Milestone 13: CLI Execution & Rule Matching
- **Objective**: Connect the CLI to run the full pipeline (normalization, suitability, crop, remove background, enhance, compress) against configured rules.
- **Dependencies**: Milestones 2, 7, 8, 9, 10, 11, 12.
- **Expected Deliverables**: Integrated end-to-end CLI command handlers.
- **Exit Criteria**: Running CLI with a rule file and input image outputs a processed compliant photo or structured compliance failures.

#### Milestone 14: Application API & Deletion Lifecycle
- **Objective**: Create a secure FastAPI backend to serve processing requests, retrieve cycle rules, and clean up uploaded files.
- **Dependencies**: Milestone 13, docs/05_PRIVACY_SECURITY.md.
- **Expected Deliverables**: REST endpoints, temporary upload handler, and background deletion worker tasks.
- **Exit Criteria**: Audit logs verify complete removal of files after session expiry or download.

#### Milestone 15: Web Frontend & Admin Dashboard
- **Objective**: Build the public Next.js single-page application and the rule configuration admin dashboard.
- **Dependencies**: Milestone 14, packages/exam-rules.
- **Expected Deliverables**: Interactive user interfaces, rule editor panels, and visual compliance check indicators.
- **Exit Criteria**: E2E tests verify successful photo uploading, crop adjustment, and download compliance loops.

*(Milestones 16 to 35: Advanced features, security reviews, and pre-launch hardening)*

### Phase 1: Post-MVP & Future Operations
- **Milestone 36**: Post-MVP crop adjustments editor tool.
- **Milestone 37**: Background manual mask touchup brush tools.
- **Milestone 38**: Billing gates and Stripe/Razorpay integrations.
- **Milestone 39**: Operational analytics, telemetry, and metrics dashboards.
