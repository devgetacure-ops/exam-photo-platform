# Image Pipeline Specification (04_IMAGE_PIPELINE_SPEC.md)

> [!IMPORTANT]
> Pipeline stage 1 (file signature validation), stage 2 (secure image decoding), stage 3 (EXIF orientation normalization), and stage 4 (source metadata extraction) are implemented in Milestone 3. Stage 5 (face detection), stage 6 (complete-head estimation), and stage 7 (source suitability analysis) are implemented in Milestones 5 and 6. All other stages detailed in this document are planned future implementations.

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


### 8. Background Processing
- **Purpose**: Clean up background clutter and replace it with clean white or light color.
- **Inputs**: Image, head segmentation map, target color.
- **Outputs**: Segmented image with clean background.
- **Failure Conditions**: Failed segmentation segmentation map.
- **Warning Conditions**: Blending artifacts at edges.
- **Privacy Considerations**: Keep ear/hair boundaries intact.
- **Planned Tests**: Test masking edge preservation on frizzy/curly hair.
- **Dependencies**: Future segmentation model.

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
- **Inputs**: Cropped image segment.
- **Outputs**: Corrected image segment.
- **Failure Conditions**: None.
- **Warning Conditions**: High noise level detected.
- **Privacy Considerations**: Retains face structures exactly.
- **Planned Tests**: Test contrast/brightness improvements under dark lighting conditions.
- **Dependencies**: Pillow ImageEnhance.

### 12. Resizing
- **Purpose**: Resize cropped segment to exact target dimensions or maximum size within range.
- **Inputs**: Image segment, dimensions.
- **Outputs**: Resized image.
- **Failure Conditions**: Scaling down results in severe pixelation.
- **Warning Conditions**: None.
- **Privacy Considerations**: In-memory only.
- **Planned Tests**: Verify output size matches configured rules.
- **Dependencies**: Pillow image resize.

### 13. Format Selection
- **Purpose**: Export image to target preferred format (e.g., JPEG).
- **Inputs**: Resized image, allowed formats.
- **Outputs**: Formatted file data.
- **Failure Conditions**: Target format unsupported.
- **Warning Conditions**: None.
- **Privacy Considerations**: None.
- **Planned Tests**: Assert exported format is JPEG.
- **Dependencies**: Pillow.

### 14. Quality-aware Compression
- **Purpose**: Iteratively optimize quality compression factor to approach but remain below the maximum file size.
- **Inputs**: Resized image, maximum file size, safety margin.
- **Outputs**: Compressed byte array.
- **Failure Conditions**: Cannot compress below maximum file size without sacrificing minimum permitted resolution.
- **Warning Conditions**: Image quality falls below acceptable visual metrics.
- **Privacy Considerations**: Strip metadata.
- **Planned Tests**: Verify output byte sizes remain close to but under the maximum limit.
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
- **Failure Conditions**: Decompression failure.
- **Warning Conditions**: None.
- **Privacy Considerations**: Temporary validation.
- **Planned Tests**: Assert failure on corrupted byte streams.
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
