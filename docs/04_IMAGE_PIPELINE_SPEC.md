# Image Pipeline Specification (04_IMAGE_PIPELINE_SPEC.md)

> [!IMPORTANT]
> Pipeline stage 1 (file signature validation), stage 2 (secure image decoding), stage 3 (EXIF orientation normalization), and stage 4 (source metadata extraction) are implemented in Milestone 3. Stage 5 (face detection), stage 6 (complete-head estimation), and stage 7 (source suitability analysis) are implemented in Milestones 5 and 6. Stage 8a (coarse foreground mask generation) is implemented in Milestone 7. Stage 8b (coarse-mask edge refinement and foreground-boundary cleanup) is implemented in Milestone 8. Stage 8c (background composition) is implemented in Milestone 11. Stage 9 (crop-mode selection) and stage 10 (crop calculation) planning logic is implemented in Milestones 9 and 10. Stage 11 (restrained image correction), Stage 12 (resizing), and Stage 13 (format selection) are implemented in Milestone 12. Stage 14 (quality-aware compression) and Stage 16 (final decode test) are implemented in Milestone 13. All other stages detailed in this document are planned future implementations.

> [!NOTE]
> **Implementation sequencing note**: Crop planning (stages 9–10) was implemented before background composition (stage 8c) because crop window calculation depends only on face, head, and mask geometry — not on the final composited image. The full pipeline orchestration will reconcile execution order when background replacement, resizing, and compression stages are integrated in later milestones.

---

## Pipeline Execution Order

```text
[Source File]
      │
      ├── 1. File-signature validation
      ├── 2. Magic-bytes check (JPEG/PNG only)
      ├── 3. EXIF orientation normalization
      ├── 4. Source metadata extraction
      ├── 5. Face detection
      ├── 6. Complete-head estimation
      ├── 7. Source suitability analysis
      ├── 8. Background processing
      ├── 9. Crop-mode selection
      ├── 10. Crop calculation
      ├── 11. Restrained image correction
      ├── 12. Resizing
      ├── 13. Format selection
      ├── 14. Quality-aware compression
      ├── 15. Filename generation
      ├── 16. Final decode test
      ├── 17. Final validation
      ├── 18. Secure output write
      └── 19. Deletion scheduling
```

---

## Detailed Pipeline Stages

### 1. File-signature Validation
- **Purpose**: Verify that the input file starts with valid magic numbers corresponding to JPEG/PNG, rejecting spoofed uploads.

- **Inputs**: Raw byte stream.
- **Outputs**: Verified byte stream.
- **Failure Conditions**: Invalid magic bytes, unknown extensions.
- **Warning Conditions**: Mismatch between declared Content-Type header and physical magic bytes.
- **Privacy Considerations**: File inspected in memory. No metadata read yet.
- **Status**: **Implemented (Milestone 3)**
- **Planned Tests**: Test validation with invalid files, dummy txt files renamed to `.jpg`.
- **Dependencies**: Standard library.

### 2. Secure Image Decoding
- **Purpose**: Safely decode image pixels into memory using sandboxed libraries.
- **Inputs**: Verified bytes.
- **Outputs**: Pixel array/Pillow Image object.
- **Failure Conditions**: Decompress-bomb (too large dimension), memory exhaustion, corrupted image stream.
- **Warning Conditions**: None.
- **Privacy Considerations**: Read only.
- **Status**: **Implemented (Milestone 3)**
- **Planned Tests**: Test load constraints with large pixel dimensions.
- **Dependencies**: Decoupled Pillow library configurations.

### 3. EXIF Orientation Normalization
- **Purpose**: Read the image's orientation flag and physically rotate the pixels so the subject is upright.
- **Inputs**: Pillow Image.
- **Outputs**: Rotated Pillow Image with normalized EXIF tags.
- **Failure Conditions**: None (if orientation missing, skip).
- **Warning Conditions**: Corrupted EXIF table.
- **Privacy Considerations**: Strips orientation details after transformation.
- **Status**: **Implemented (Milestone 3)**
- **Planned Tests**: Test images taken at 90, 180, 270 degree rotations.
- **Dependencies**: Pillow ImageOps.

### 4. Source Metadata Extraction
- **Purpose**: Extract physical attributes like resolution, color depth, and format.
- **Inputs**: Normalised image.
- **Outputs**: Metadata JSON.
- **Failure Conditions**: Reading failure.
- **Warning Conditions**: Resolution below recommended minimums.
- **Privacy Considerations**: Excludes geolocation coordinates.
- **Status**: **Implemented (Milestone 3)**
- **Planned Tests**: Assert correct size/resolution properties are extracted.
- **Dependencies**: None.

### 5. Face Detection
- **Purpose**: Detect bounding boxes and primary facial landmarks (eyes, nose, mouth).
- **Inputs**: Pre-processed image.
- **Outputs**: Coordinates of face bounding box and landmarks.
- **Failure Conditions**: No face detected, multiple faces detected.
- **Warning Conditions**: Low confidence score.
- **Privacy Considerations**: Bounding boxes are stored strictly in-memory during the session.
- **Status**: **Implemented (Milestone 5)**
- **Planned Tests**: Feed image with no face, feed image with multiple faces.
- **Dependencies**: MediaPipe face detection model (`blaze_face_short_range.tflite`).

### 6. Complete-head Estimation
- **Purpose**: Calculate total head volume including hair boundaries, ears, and chin.
- **Inputs**: Face bounding boxes, image.
- **Outputs**: Complete head bounding box.
- **Failure Conditions**: Unable to resolve head contours.
- **Warning Conditions**: Side-profile posing, tilted neck.
- **Privacy Considerations**: In-memory only.
- **Status**: **Implemented (Milestone 6) as a landmark-assisted geometric baseline**
- **Dependencies**: `FaceDetection` output.

### 7. Source Suitability Analysis
- **Purpose**: Decide if the photograph is suitable for processing.
- **Inputs**: Head boundaries, metadata.
- **Outputs**: Suitability score and classification (`processable`, `processable_with_caution`, `unsuitable`).
- **Failure Conditions**: High tilt angle, severe blur, or key feature occlusion.
- **Warning Conditions**: Uneven shadow, low light.
- **Privacy Considerations**: No embeddings retained.
- **Status**: **Implemented (Milestone 6) suitability evaluation framework**
- **Dependencies**: Normalized image metadata, face detection reference, and head estimation result.


### 8a. Coarse Foreground Mask Generation
- **Purpose**: Generate a coarse foreground mask to separate the candidate subject from the original background, and validate mask properties (e.g. connectivity, face containment) to ensure suitability.
- **Inputs**: Normalised image, face detection coordinates, head estimation bounding box.
- **Outputs**: Probability mask (0-1 confidence), binary mask (0/255 foreground/background), validation metrics.
- **Failure Conditions**: Segmentation failure (e.g., invalid dimensions, inference crash), low foreground coverage, excessive disjoint components, or failure to contain the detected face bounding box.
- **Warning/Info Conditions**: Moderate mask imperfections or disjoint regions when background replacement is not requested.
- **Privacy Considerations**: The raw probability/binary masks, model paths, and internal error traces are kept strictly in-memory/private and excluded from the public suitability report to prevent biometrics and model metadata leaks.
- **Status**: **Coarse mask generation and validation implemented (Milestone 7)**
- **Dependencies**: MediaPipe Selfie Multiclass (`selfie_multiclass_256x256.tflite`) or Selfie Binary (`selfie_segmentation.tflite`) model.

### 8b. Refined Foreground Mask & Trimap Generation
- **Purpose**: Convert the validated coarse mask into a cleaner, smoothed foreground boundary, creating a high-resolution alpha mask and trimap (0/128/255) for downstream matting and background replacement.
- **Inputs**: Coarse mask (PIL L-mode), probability mask (np.ndarray), face detection coordinates.
- **Outputs**: Refined alpha mask (float32 array in [0.0, 1.0]), refined binary mask (PIL L-mode 0/255), trimap (PIL L-mode 0/128/255), validation metrics.
- **Failure Conditions**: Refinement input/output format validation errors.
- **Warning/Info Conditions**: Coverage diverged too much (warning), low coarseleftrightarrowrefined IoU overlap (warning).
- **Privacy Considerations**: Alpha masks, binary masks, and trimaps are kept strictly in-memory during the session.
- **Status**: **Refined mask and trimap generation implemented (Milestone 8)**
- **Dependencies**: None (pure NumPy/PIL deterministic morphological operations).

### 8c. Solid Background Composition
- **Purpose**: Place the candidate foreground accurately and cleanly over a compliant solid-colour background without altering their original identity.
- **Inputs**: Original normalized image, refined alpha mask, configured target background colour.
- **Outputs**: Composed RGB/RGBA image, validation metrics.
- **Failure Conditions**: Invalid dimensions, mask mismatch, insufficient foreground coverage, target colour rejected.
- **Warning/Info Conditions**: Minimal clipping risk at boundaries.
- **Privacy Considerations**: Does not hallucinate or alter candidate pixels; uses mathematical alpha composite of the original image source.
- **Status**: **Implemented (Milestone 11)**
- **Dependencies**: `SolidBackgroundComposer` (pure NumPy/PIL).

### 9. Crop-mode Selection
- **Purpose**: Choose Crop Mode A (exact aspect/size) or B (natural head framing with margins) based on the rule configuration.
- **Inputs**: Stored exam rule.
- **Outputs**: Selected crop mode.
- **Failure Conditions**: Missing processing configuration.
- **Warning Conditions**: None.
- **Privacy Considerations**: None.
- **Planned Tests**: Assert correct mode routing.
- **Dependencies**: Rule validation logic.

### 10. Crop Calculation
- **Purpose**: Calculate the crop window coordinates.
  - **Crop Mode A**: Fit crop window to target aspect ratio, keeping face centered, preserving hair, ears, chin, and beard lines.
  - **Crop Mode B**: Build crop box directly around head with small natural margins on top, sides, and bottom.
- **Inputs**: Head boundaries, crop mode.
- **Outputs**: Crop window coordinates `(x1, y1, x2, y2)`.
- **Failure Conditions**: Crop coordinates fall outside original image boundaries.
- **Warning Conditions**: Margin size is below default minimum.
- **Privacy Considerations**: In-memory only.
- **Planned Tests**: Verify aspect ratio matches target.
- **Dependencies**: Pillow crop tool parameters.

### 11. Restrained Image Correction
- **Purpose**: Improve image legibility without altering candidate identity.
- **Inputs**: Cropped image segment, enhancement configuration.
- **Outputs**: Corrected image segment.
- **Failure Conditions**: Adjustments outside conservative limits (brightness/contrast: 0.88–1.12; sharpness: 0.80–1.20) trigger `OUTPUT_ENHANCEMENT_UNSAFE` blocking failure. Any adjustment in `NONE` mode other than `1.0` triggers failure.
- **Warning Conditions**: None.
- **Privacy Considerations**: Retains face structures exactly.
- **Planned Tests**: Test contrast/brightness/sharpness limits and check for `OUTPUT_ENHANCEMENT_UNSAFE`.
- **Dependencies**: Pillow ImageEnhance.

### 12. Resizing
- **Purpose**: Resize cropped segment to exact target dimensions or selected range dimensions.
- **Inputs**: Image segment, dimensions config.
- **Outputs**: Resized image in-memory.
- **Failure Conditions**:
  - **Exact Mode**: Aspect ratio mismatch (over 1% tolerance) triggers `OUTPUT_ASPECT_MISMATCH` blocking failure (fail early, do not stretch).
  - **Range Mode**: No aspect-preserving or closest valid size inside range, or aspect ratio cannot be preserved (triggers `OUTPUT_ASPECT_MISMATCH` blocking failure).
  - Upscale factor `scale > 3.0` triggers `OUTPUT_UPSCALE_LIMIT_EXCEEDED` blocking failure.
  - Downscale factor `scale < 0.05` triggers `OUTPUT_DOWNSCALE_TOO_SEVERE` blocking failure.
- **Warning Conditions**:
  - `1.5 < scale <= 2.0` -> `OUTPUT_UPSCALE_WARNING`
  - `2.0 < scale <= 3.0` -> `OUTPUT_UPSCALE_STRONG_WARNING`
  - `0.10 <= scale < 0.20` -> `OUTPUT_DOWNSCALE_WARNING`
  - `0.05 <= scale < 0.10` -> `OUTPUT_DOWNSCALE_SEVERE_WARNING`
- **Privacy Considerations**: In-memory only.
- **Planned Tests**: Verify output size matches exact or range select priority; verify upscale/downscale warning boundaries and errors.
- **Dependencies**: Pillow image resize.

### 13. Format Selection
- **Purpose**: Convert to candidate colour mode and strip EXIF metadata.
- **Inputs**: Resized image, target colour mode, strip metadata flag.
- **Outputs**: Candidate image in-memory with stripped metadata.
- **Failure Conditions**: Target colour mode conversion fails or is unsupported.
- **Warning Conditions**: None.
- **Privacy Considerations**: EXIF and other image metadata are stripped.
- **Planned Tests**: Verify metadata stripped from output image info; verify colour mode conversions (RGBA -> RGB, etc.).
- **Dependencies**: Pillow.

### 14. Quality-aware Compression
- **Purpose**: Iteratively optimize quality compression factor (JPEG only in Milestone 13) using a binary search to approach but remain strictly below the maximum file size limit, preserving biometric details at a minimum quality floor of 20.
- **Inputs**: Resized image, maximum file size (`maximum_bytes`), minimum file size (`minimum_bytes`), target ceiling ratio, safety margin.
- **Outputs**: Compressed byte array.
- **Failure Conditions**: Cannot compress below maximum file size without going below the quality floor of 20 (fails with `COMPRESSION_QUALITY_TOO_LOW`), final size exceeds maximum bytes (`COMPRESSION_MAX_SIZE_EXCEEDED`), or final size is below minimum bytes (`COMPRESSION_MIN_SIZE_NOT_REACHED`).
- **Warning Conditions**: Low quality warning (final quality < min_quality).
- **Privacy Considerations**: Metadata is stripped from the byte stream, and raw compressed bytes are excluded from model serialization.
- **Status**: **Implemented (Milestone 13)**
- **Planned Tests**: Verify binary search convergence, quality floor enforcement, minimum size validation, metadata stripping, and serialization safety.
- **Dependencies**: Pillow JPEG encoder.

### 15. Filename Generation
- **Purpose**: Format filename according to exam specifications.
- **Inputs**: Exam rule, default fallback name.
- **Outputs**: String filename.
- **Failure Conditions**: Invalid characters in rule pattern.
- **Warning Conditions**: None.
- **Privacy Considerations**: Excludes user IDs in filenames.
- **Planned Tests**: Verify naming outputs (e.g., `photograph.jpg`).
- **Dependencies**: Standard string utils.

### 16. Final Decode Test
- **Purpose**: Decode the newly compressed output file to verify it is readable and not corrupted.
- **Inputs**: Compressed bytes.
- **Outputs**: Successful decode flag.
- **Failure Conditions**: Decompression failure or decoded dimensions do not match the input dimensions.
- **Warning Conditions**: None.
- **Privacy Considerations**: Temporary validation.
- **Status**: **Implemented (Milestone 13)**
- **Planned Tests**: Assert failure on corrupted byte streams or mismatched dimensions.
- **Dependencies**: Pillow.

### 17. Final Validation
- **Purpose**: Audit the final output file against dimensions, aspect ratio, size limit, and name rules.
- **Inputs**: Final file bytes, metadata, exam rule.
- **Outputs**: Compliance report.
- **Failure Conditions**: Output fails any single check.
- **Warning Conditions**: None.
- **Privacy Considerations**: None.
- **Planned Tests**: Assert failure if file size exceeds configured limits.
- **Dependencies**: Validation modules.

### 18. Secure Output Write
- **Purpose**: Write final output bytes to temporary private storage.
- **Inputs**: Final bytes.
- **Outputs**: Reference storage URI.
- **Failure Conditions**: Storage write error.
- **Warning Conditions**: None.
- **Privacy Considerations**: Written to private container.
- **Planned Tests**: Check file existences.
- **Dependencies**: Temporary storage driver.

### 19. Deletion Scheduling
- **Purpose**: Schedule automated deletion of all temporary session files (original, intermediate, and final).
- **Inputs**: Session ID, retention policy.
- **Outputs**: Deletion job scheduled.
- **Failure Conditions**: Scheduling failure.
- **Warning Conditions**: None.
- **Privacy Considerations**: Core privacy mechanism.
- **Planned Tests**: Verify deletion runs after expiration.
- **Dependencies**: Task orchestration scheduler.
