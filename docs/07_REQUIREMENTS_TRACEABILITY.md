# Requirements Traceability Matrix (07_REQUIREMENTS_TRACEABILITY.md)

This matrix maps stable requirement identifiers to design documents, status indicators, and planned testing structures.

---

## Traceability Matrix

| Requirement ID | Summary | Source | Decision Status | Implementation Status | Planned Module | Planned Tests | Milestone | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PROD-001** | Selection of exam triggers rules | PDF Sec 1.1 | CONFIRMED | Documentation Complete | `apps/web`, `packages/exam-rules` | Search route assertions | Milestone 2 | First step in workflow |
| **CROP-001** | Crop Mode A (Exact Size) | PDF Sec 5.3 | CONFIRMED | **Implemented (Milestone 9)** | `services/image-engine` | `test_crop_mode_a.py` | Milestone 9 | Aspect ratio preserved |
| **CROP-002** | Crop Mode B (Ranges) | PDF Sec 5.3 | CONFIRMED | Not Implemented | `services/image-engine` | Tight cropping margins | Milestone 10 | Fallbacks applied |
| **BG-001** | Background cleaning | PDF Sec 5.2 | CONFIRMED | Not Implemented | `services/image-engine` | Edge visual checks | Future | White background standard |
| **SEG-001** | Portrait coarse segmentation | PDF Sec 5.2 | CONFIRMED | **Implemented (Milestone 7)** | `services/image-engine` | `test_subject_segmentation.py` | Milestone 7 | MediaPipe multiclass & binary segmenters |
| **SEG-002** | Coarse-mask edge refinement and trimap | PDF Sec 5.2 | CONFIRMED | **Implemented (Milestone 8)** | `services/image-engine` | `test_foreground_refinement.py` | Milestone 8 | NumPy & PIL morphological operations |
| **ID-001** | Identity preservation | PDF Sec 5.5 | CONFIRMED | Not Implemented | `services/image-engine` | Geometric similarity checks | Milestone 11 | Enhancements limited |
| **RULE-001** | Versioned structured rules | PDF Sec 6 | CONFIRMED | **Implemented (Milestone 2)** | `packages/exam-rules`, `services/image-engine` | `test_rule_validation.py` | Milestone 2 | JSON schema & Python models |
| **FILE-001** | Target output naming | PDF Sec 5.7 | CONFIRMED | Not Implemented | `services/image-engine` | Pattern check tests | Milestone 13 | Sanitize string output |
| **COMP-001** | Quality-aware compression | PDF Sec 5.6 | CONFIRMED | Not Implemented | `services/image-engine` | Compression limits check | Milestone 12 | Below maximum ceiling |
| **PRIV-001** | Deletion lifecycle | PDF Sec 10.2 | CONFIRMED | Not Implemented | `Application API` | Retention timer tests | Milestone 14 | automatic cleanup |
| **SEC-001** | Magic byte validation | PDF Sec 10.4 | CONFIRMED | **Implemented (Milestone 3)** | `services/image-engine` | `test_signatures.py` | Milestone 3 | Input signature sanitization |
| **QA-001** | Visual regression testing | PDF Sec 12.3 | CONFIRMED | Not Implemented | `QA Strategy` | Visual checks runs | Milestone 5 | Golden images setup |
| **UX-001** | Mobile responsiveness | PDF Sec 11.5 | CONFIRMED | Not Implemented | `apps/web` | Screen size checks | Milestone 15 | Mobile-first layouts |
| **SUIT-001** | Suitability framework & provider interfaces | PDF Sec 5.2 | CONFIRMED | **Implemented (Milestone 4)** | `services/image-engine/suitability` | Evaluator, Quality metrics, and Provider contracts tests | Milestone 4 | Framework structure & contracts |
| **FACE-001** | Face detection integration | PDF Sec 5.2 | CONFIRMED | **Implemented (Milestone 5)** | `services/image-engine/providers` | `test_mediapipe_face_detector.py` | Milestone 5 | MediaPipe face detection integration |
| **HEAD-001** | Provisional geometric head-box estimator | PDF Sec 5.2 | CONFIRMED | **Implemented (Milestone 6)** | `services/image-engine/providers` | `test_landmark_geometric_head_estimator.py` | Milestone 6 | Heuristic-driven head estimator |

