# Requirements Traceability Matrix (07_REQUIREMENTS_TRACEABILITY.md)

This matrix maps stable requirement identifiers to design documents, status indicators, and planned testing structures.

---

## Traceability Matrix

| Requirement ID | Summary | Source | Decision Status | Implementation Status | Planned Module | Planned Tests | Milestone | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PROD-001** | Selection of exam triggers rules | PDF Sec 1.1 | CONFIRMED | Documentation Complete | `apps/web`, `packages/exam-rules` | Search route assertions | Milestone 2 | First step in workflow |
| **CROP-001** | Crop Mode A (Exact Size) | PDF Sec 5.3 | CONFIRMED | **Implemented (Milestone 9)** | `services/image-engine` | `test_crop_mode_a.py` | Milestone 9 | Aspect ratio preserved |
| **CROP-002** | Crop Mode B (Ranges) | PDF Sec 5.3 | CONFIRMED | **Implemented (Milestone 10)** | `services/image-engine` | `test_crop_mode_b.py` | Milestone 10 | Fallbacks applied |
| **BG-001** | Background cleaning | PDF Sec 5.2 | CONFIRMED | **Implemented (Milestone 11)** | `services/image-engine/providers` | `test_background_composition.py` | Milestone 11 | Solid background composition |
| **SEG-001** | Portrait coarse segmentation | PDF Sec 5.2 | CONFIRMED | **Implemented (Milestone 7)** | `services/image-engine` | `test_subject_segmentation.py` | Milestone 7 | MediaPipe multiclass & binary segmenters |
| **SEG-002** | Coarse-mask edge refinement and trimap | PDF Sec 5.2 | CONFIRMED | **Implemented (Milestone 8)** | `services/image-engine` | `test_foreground_refinement.py` | Milestone 8 | NumPy & PIL morphological operations |
| **ID-001** | Identity preservation | PDF Sec 5.5 | CONFIRMED | **Partially Implemented (Milestone 12)** | `services/image-engine` | `test_deterministic_output_preparer.py` | Milestone 12 | Restrained global enhancement baseline implemented; full identity-preservation validation remains ongoing through final validation and QA. |
| **RULE-001** | Versioned structured rules | PDF Sec 6 | CONFIRMED | **Implemented (Milestone 2)** | `packages/exam-rules`, `services/image-engine` | `test_rule_validation.py` | Milestone 2 | JSON schema & Python models |
| **FILE-001** | Target output naming | PDF Sec 5.7 | CONFIRMED | **Implemented (Milestone 14)** | `services/image-engine` | Pattern check tests | Milestone 14 | Sanitize string output |
| **COMP-001** | Quality-aware compression | PDF Sec 5.6 | CONFIRMED | **Implemented (Milestone 13)** | `services/image-engine` | `test_image_compression.py` | Milestone 13 | Below maximum ceiling |
| **PRIV-001** | Deletion lifecycle | PDF Sec 10.2 | CONFIRMED | **Partially Implemented (Milestone 15)** | `services/image-engine/src/exam_photo/api` | `test_api.py` | Milestone 15 | Local deletion lifecycle and TTL cleanup |
| **SEC-001** | Magic byte validation | PDF Sec 10.4 | CONFIRMED | **Implemented (Milestone 3)** | `services/image-engine` | `test_signatures.py` | Milestone 3 | Input signature sanitization |
| **QA-001** | Visual regression testing | PDF Sec 12.3 | CONFIRMED | **Implemented (Milestone 5)** | `QA Strategy` | Visual checks runs | Milestone 5 | Golden images setup |
| **UX-001** | Mobile responsiveness | PDF Sec 11.5 | CONFIRMED | **Partially Implemented (Milestone 16)** | `apps/web` | CSS media queries / responsive grid assertions | Milestone 16 | Mobile-first grid layouts |
| **SUIT-001** | Suitability framework & provider interfaces | PDF Sec 5.2 | CONFIRMED | **Implemented (Milestone 4)** | `services/image-engine/suitability` | Evaluator, Quality metrics, and Provider contracts tests | Milestone 4 | Framework structure & contracts |
| **FACE-001** | Face detection integration | PDF Sec 5.2 | CONFIRMED | **Implemented (Milestone 5)** | `services/image-engine/providers` | `test_mediapipe_face_detector.py` | Milestone 5 | MediaPipe face detection integration |
| **HEAD-001** | Provisional geometric head-box estimator | PDF Sec 5.2 | CONFIRMED | **Implemented (Milestone 6)** | `services/image-engine/providers` | `test_landmark_geometric_head_estimator.py` | Milestone 6 | Heuristic-driven head estimator |
| **API-001** | Local API processing boundaries | PDF Sec 8 | CONFIRMED | **Implemented (Milestone 15)** | `services/image-engine/src/exam_photo/api` | `test_api.py` | Milestone 15 | Synchronous endpoint execution |
| **STORAGE-001** | Local temporary artifact storage | PDF Sec 8.2 | CONFIRMED | **Implemented (Milestone 15)** | `services/image-engine/src/exam_photo/api` | Traversal check tests | Milestone 15 | Strict boundary guards |
| **WEB-001** | Public Web App MVP | PDF Sec 11.1 | CONFIRMED | **Implemented (Milestone 16)** | `apps/web` | `api-client.test.ts`, `file-validation.test.ts` | Milestone 16 | React Next.js single-page application MVP |
| **PRIV-UX-001** | Privacy-First User Flow | PDF Sec 10.2 | CONFIRMED | **Implemented (Milestone 16)** | `apps/web` | `delete-flow.test.tsx`, `validation-report.test.tsx` | Milestone 16 | No localStorage caching, URL revocation, manual deletion |
| **ADMIN-001** | Local admin configuration console | PDF Sec 11.2 | CONFIRMED | **Implemented (Milestone 17)** | `apps/web` | `rule-admin.test.tsx` | Milestone 17 | Local-only accidental-exposure warning gated admin page |
| **RULE-UI-001** | Rule editor with form/json and reset views | PDF Sec 11.2 | CONFIRMED | **Implemented (Milestone 17)** | `apps/web` | `rule-admin.test.tsx` | Milestone 17 | Advanced field preservation and reset behavior |
| **RULE-VALIDATION-API-001** | Stateless backend rule validation API | PDF Sec 8.3 | CONFIRMED | **Implemented (Milestone 17)** | `services/image-engine` | `test_rule_validation_api.py` | Milestone 17 | Returns 422 for bad bodies, does not write files |
| **MAT-001** | Guided Filter soft-alpha matting | PDF Sec 5.2 | CONFIRMED | **Implemented (Milestone 18)** | `services/image-engine/providers/refiners` | `test_matting_and_decontamination.py` | Milestone 18 | Two-resolution Guided Filter edge refinement |
| **DECON-001** | Edge color decontamination | PDF Sec 5.5 | CONFIRMED | **Implemented (Milestone 18)** | `services/image-engine/providers` | `test_matting_and_decontamination.py` | Milestone 18 | Restricted to boundary region ($0.05 < \alpha < 0.95$) |
| **COMPOS-002** | Premultiplied-alpha composite | PDF Sec 5.2 | CONFIRMED | **Implemented (Milestone 18)** | `services/image-engine/providers` | `test_matting_and_decontamination.py` | Milestone 18 | Prevents dark/bright edge fringes during resize |
| **BENCH-001** | Visual quality & composition benchmark | PDF Sec 12.3 | CONFIRMED | **Implemented (Milestone 18)** | `scripts`, `tests/fixtures/engine_quality` | `benchmark_engine_quality.py` | Milestone 18 | 30 base subjects, 192 variants, visual metrics |
