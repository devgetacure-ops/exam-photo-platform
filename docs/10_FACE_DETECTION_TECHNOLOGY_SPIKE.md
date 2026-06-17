# Face Detection Technology Spike (Milestone 5)

This document summarizes the research, candidate evaluations, variant selection, model license verification, and benchmark results for the local CPU-capable face detection model integration.

---

## 1. Candidate Evaluation Table

The following table summarizes the candidate face detection libraries evaluated for the Indian Exam-Photo Compliance Platform:

| Candidate | License (pkg) | CPU-only | Install Method | Python 3.11+ | Deterministic | Notes |
|---|---|---|---|---|---|---|
| **MediaPipe** (BlazeFace) | Apache-2.0 | ✅ | Prebuilt platform wheels | ✅ | ✅ | 6 landmarks + confidence. Separate model asset required. |
| OpenCV DNN (Caffe/TF .pb) | Apache-2.0 | ✅ | `pip` + external model file | ✅ | ✅ | External model download at runtime — violates no-silent-download rule. |
| ONNX Runtime + YOLOv8n-face | AGPL-3.0 (model)| ✅ | `pip` + external model file | ✅ | ✅ | AGPL model license incompatible with proprietary product. |
| dlib HOG detector | BSL-1.0 | ✅ | Source build (requires cmake) | ⚠️ | ✅ | Brittle Windows build; no prebuilt wheel for Python 3.11+. |
| face_recognition (dlib) | MIT | ✅ | Same dlib compile issues | ⚠️ | ✅ | Inherits dlib build brittleness. |

### Selection Rationale: MediaPipe (`mediapipe~=0.10.35`)
MediaPipe Face Detector was selected because:
- The package is licensed under Apache-2.0, which is commercial-friendly.
- Prebuilt wheels are available on PyPI for Windows and Linux, avoiding compiler setup.
- The `vision.FaceDetector` API exposes a bounding box and 6 key landmarks matching our requirements.
- It is optimized for CPU-only execution with deterministic bounding-box coordinates for the same inputs.

---

## 2. BlazeFace Model Variant Selection & Benchmarking

Google publishes two primary BlazeFace model weights for the Tasks API:
1. `blaze_face_short_range.tflite`: Optimized for close-range selfies (face fills a significant portion of the frame).
2. `blaze_face_full_range.tflite`: Optimized for longer range or smaller faces (occupying <= 25% of the frame).

### Benchmarking Results
Benchmarks were executed on a machine running Windows with Python 3.10 and an AMD64 processor:

#### Test 1: `blaze_face_short_range.tflite`
- **Input Image**: `tests/fixtures/single_face_frontal.jpg` (3250×4333)
- **Face Count Detected**: 1 face
- **Detection Confidence**: 0.8160 (warm run)
- **Cold Initialization**: 213.5 ms
- **Warm Inference Latency (10 runs)**:
  - Minimum: 93.8 ms
  - Median: 115.0 ms
  - Mean: 111.6 ms
  - Maximum: 138.6 ms
- **Status**: PASSED. Works reliably and detects the face correctly.

#### Test 2: `blaze_face_full_range.tflite`
- **Input Image**: `tests/fixtures/single_face_frontal.jpg` (3250×4333)
- **Status**: FAILED.
- **Error**:
  ```
  CalculatorGraph::Run() failed: 
  Calculator::Process() for node "mediapipe_tasks_vision_face_detector_facedetectorgraph__TensorsToDetectionsCalculator" failed: ; RET_CHECK failure (mediapipe/calculators/tensor/tensors_to_detections_calculator.cc:365) (raw_box_tensor->shape().dims[1])==(num_boxes_)
  ```
- **Finding**: The MediaPipe Python Tasks API `vision.FaceDetector` expects a specific flatbuffer structure. The raw `blaze_face_full_range.tflite` model has a tensor shape mismatch and cannot be used directly without a `.task` bundle wrapper which was not available from Google's official TF Lite model downloads at this time.

### Baseline Selection
Short-range was successfully integrated and benchmarked. The tested regular full-range asset failed to initialize with the current Tasks configuration. Sparse full-range has not yet been successfully benchmarked. Short-range is selected as the provisional Milestone-5 baseline.

---

## 3. Model License Verification (DEC-012)

The model cards and licenses were independently verified:
- **Source**: Google's official MediaPipe Face Detector models catalog.
- **Model Card URL**: [https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector#models](https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector#models)
- **License**: Apache License, Version 2.0 (confirmed in the Google AI Edge developer portal).
- **Redistribution Conditions**: Allowed under Apache-2.0 terms, provided that appropriate copyright notices and license text are preserved.
- **Redistribution Notes**: Model files can be packaged and distributed along with client code under the Apache 2.0 license terms.

---

## 4. Coordinate Handling

- **Bounding Box**: MediaPipe returns pixel coordinates: `origin_x, origin_y, width, height`. The wrapper validates these values, clamps them to the image boundaries to prevent coordinates out of bounds, and converts them to `BoundingBox(left, top, right, bottom)`.
- **Keypoints**: MediaPipe returns 6 keypoints in normalized coordinate space `[0.0, 1.0]`. The wrapper converts these into absolute pixel values using the image width/height:
  - Keypoint 0: Left Eye -> mapped to `landmarks.left_eye`
  - Keypoint 1: Right Eye -> mapped to `landmarks.right_eye`
  - Keypoint 2: Nose Tip -> mapped to `landmarks.nose_tip`
  - Keypoint 3: Mouth Center -> mapped to custom landmarks
  - Keypoint 4: Left Ear Tragion -> mapped to custom landmarks
  - Keypoint 5: Right Ear Tragion -> mapped to custom landmarks
- Detections with zero or negative areas are automatically skipped.

---

## 5. Model Asset Management Specifications

- **Location**: Model assets must be placed in a directory outside git control (configured via `model-assets/`).
- **Git Exclusion**: `*.tflite` and `*.task` are explicitly ignored in `.gitignore`.
- **Acquisition**: A command line utility `scripts/download_model.py` is provided to allow explicit, manual model download.
- **Verification**: SHA-256 digests are computed and matched against expected values from `model-manifests/face-detector.json` at every initialization step. Mismatch triggers a `ModelChecksumError`.
