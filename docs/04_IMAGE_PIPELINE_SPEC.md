# Image Pipeline Specification (04_IMAGE_PIPELINE_SPEC.md)

> [!IMPORTANT]
> Pipeline stage 1 (file signature validation), stage 2 (secure image decoding), stage 3 (EXIF orientation normalization), and stage 4 (source metadata extraction) are implemented in Milestone 3. Stage 5 (face detection), stage 6 (complete-head estimation), and stage 7 (source suitability analysis) are implemented in Milestones 5 and 6. Stage 8a (coarse foreground mask generation) is implemented in Milestone 7. Stage 8b (coarse-mask edge refinement and foreground-boundary cleanup) is implemented in Milestone 8. Stage 8c (background composition) is implemented in Milestone 11. Stage 9 (crop-mode selection) and stage 10 (crop calculation) planning logic is implemented in Milestones 9 and 10. Stage 11 (restrained image correction), Stage 12 (resizing), and Stage 13 (format selection) are implemented in Milestone 12. Stage 14 (quality-aware compression) and Stage 16 (final decode test) are implemented in Milestone 13. Stage 15 (filename generation) and Stage 17 (final validation) are implemented in Milestone 14. Stage 18 (secure output write) and Stage 19 (deletion scheduling) are implemented in Milestones 15 and 16. All other stages detailed in this document are planned future implementations.

> [!NOTE]
> **Implementation sequencing note**: Crop planning (stages 9–10) was implemented before background composition (stage 8c) because crop window calculation depends only on face, head, and mask geometry — not on the final composited image. The full pipeline orchestration will reconcile execution order when background replacement, resizing, and compression stages are integrated in later milestones.

> [!NOTE]
> **Updated 2026-08-04.** Every stage in this document is now implemented and
> orchestrated by `RuleOrchestratedPipeline`; the "planned future
> implementations" caveat above no longer applies. Three stages were added
> after the original specification and are described below: **5b** dense
> landmark refinement and head pose, **5c** appearance disposition, and **10b**
> crop-region matte recomputation. Stage **8b** is now skipped on the default
> path, because the portrait matting backend already resolves the boundary.
> The only specified behaviour not yet built is noise reduction within stage 11.

---

## Pipeline Execution Order

```text
[Source File]
      │
      ├── 1. File-signature validation
      ├── 2. Magic-bytes check (JPEG/PNG only)
      ├── 3. EXIF orientation normalization
      ├── 4. Source metadata extraction
      ├── 5. Face detection  ─┐
      ├── 5b. Dense landmark refinement & head pose
      ├── 5c. Appearance disposition: accept / warn / block
      ├── 6. Complete-head estimation
      ├── 7. Source suitability analysis
      ├── 8. Background processing
      ├── 9. Crop-mode selection
      ├── 10. Crop calculation
      ├── 10b. Crop-region matte recomputation
      ├── 11. Restrained image correction (planned from measured deficits)
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
- **Failure Conditions**: No face detected. **Multiple detections are no longer an automatic failure** -- see stage 5c. When the subject is unambiguous the pipeline proceeds with the largest face.
- **Warning Conditions**: Low confidence score. The detector steps down through a confidence ladder (0.50, 0.35, 0.25, 0.15) when the primary pass finds nothing, and the tier it settled on is recorded, because a detection recovered at the lowest tier is not trustworthy enough to block on.
- **Privacy Considerations**: Bounding boxes are stored strictly in-memory during the session.
- **Status**: **Implemented (Milestone 5)**
- **Planned Tests**: Feed image with no face, feed image with multiple faces, feed an image whose only second "face" is a printed banner found at the lowest tier.
- **Dependencies**: MediaPipe face detection model (`blaze_face_short_range.tflite`).

### 5b. Dense Landmark Refinement & Head Pose
- **Purpose**: Sharpen the two points the crop planner is most sensitive to -- the chin and the eye line -- and supply head pose (DEC-032).
- **Inputs**: Normalized image, the primary face detection.
- **Outputs**: The same detection with a refined chin, eye line, head pose (yaw/pitch/roll), and a `dense_landmarks_found` flag.
- **Critical detail**: the landmarker runs on a **crop around the detector box**, not the full frame. Its internal detector is tuned for a face filling a reasonable fraction of the frame and finds nothing on a full-body photograph at any confidence; cropping first resolves that.
- **Failure Conditions**: None. Refinement is an improvement, never a precondition -- failure leaves the detector's own points in place.
- **Note**: `dense_landmarks_found` is reported separately from whether the reading was *accepted*, because "the landmarker could not read this face" is evidence of extreme pose or occlusion while "its chin reading was implausible" is not.
- **Status**: **Implemented (DEC-032)**
- **Dependencies**: MediaPipe face landmarker (`face_landmarker.task`).

### 5c. Appearance Disposition
- **Purpose**: Classify the upload **accept**, **warn**, or **block** (DEC-041).
- **Inputs**: Photometric and geometric measurements of the image and face region; the exam's appearance rules.
- **Outputs**: A disposition plus findings at two severities, `likely_rejection` and `possible_issue`.
- **Blocks only when a truthful output is impossible**: an undecodable file, no detectable face, or a genuinely ambiguous subject -- two or more faces of comparable size, found above the lowest confidence tier. A small bystander removed by the crop is not ambiguity.
- **Never blocks for appearance.** No stage anywhere in the pipeline may block for an appearance or composition reason; background-composition concerns are reported as findings and still produce a photograph.
- **Exposure is measured on the face, never the frame**: a correctly exposed portrait against a dark backdrop reads a low frame luminance and a perfectly lit face.
- **Status**: **Implemented (DEC-041)**
- **Not implemented**: sunglasses, head coverings and eye closure, all measured as not separable with the shipped models.

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

### 8b. Refined Foreground Mask, Trimap & Guided Filter Matting
- **Purpose**: Convert the validated coarse mask into a cleaner, smoothed foreground boundary, creating a high-resolution alpha mask and trimap (0/128/255) for downstream matting, and applying Guided Filter refinement to capture fine details (e.g. hair strands).
- **Inputs**: Original image (PIL Image), coarse mask (PIL L-mode), probability mask (np.ndarray), face detection coordinates.
- **Outputs**: Refined alpha mask (float32 array in [0.0, 1.0]), refined binary mask (PIL L-mode 0/255), trimap (PIL L-mode 0/128/255), validation metrics.
- **Guided Filter Strategy**:
  - Uses a two-resolution approach: downscales mask to compute trimap/uncertainty band at a reduced resolution (512px max), then projects the uncertain band ($0.05 < \alpha < 0.95$) back to high/native resolution for edge refinement using the RGB guidance image.
  - Supports three quality modes: `fast` (reduced-resolution refinement at 512px max), `balanced` (high-res boundary ROI refinement at 1024px max), and `high` (native-resolution boundary ROI refinement).
  - Memory-safe tiling and resolution safeguards ensure fallback mechanisms append `MATTE_QUALITY_DOWNGRADED` to issue codes without throwing OOM errors.
- **Failure Conditions**: Refinement input/output format validation errors, or execution failures.
- **Warning/Info Conditions**: Coverage diverged too much (warning), low coarse-to-refined IoU overlap (warning), or matting resolution downgraded (`MATTE_QUALITY_DOWNGRADED`).
- **Privacy Considerations**: Alpha masks, binary masks, and trimaps are kept strictly in-memory during the session.
- **Status**: **Morphological refinement and Guided Filter matting implemented (Milestone 18)**
- **Dependencies**: Morphological and Guided Filter pipeline (pure NumPy/PIL vectorized operations).

> [!IMPORTANT]
> **This entire stage is skipped when a portrait matting backend is in use
> (DEC-033), which is the default path.** BiRefNet already resolves the
> boundary, and re-refining it destroyed detail the model had produced while
> costing minutes of native-resolution work on a large photograph. The alpha is
> passed through and only the contract artifacts -- binary mask, trimap,
> validation report -- are constructed. The refinement described above still
> runs for the coarse MediaPipe segmenter, which is diagnostic-only.

### 8c. Solid Background Composition & Edge Decontamination
- **Purpose**: Decontaminate background color spill from candidate foreground edges and composite the subject accurately and cleanly over a compliant solid-colour background.
- **Inputs**: Original normalized image, refined alpha mask, configured target background colour.
- **Outputs**: Composed RGB/RGBA image, validation metrics.
- **Edge Color Decontamination**:
  - Restricts edge color adjustment strictly to the uncertain boundary region ($0.05 < \alpha < 0.95$), leaving opaque foreground ($\alpha \ge 0.95$) unchanged to preserve identity.
  - Uses nearby background and opaque foreground colors to recover uncontaminated boundary pixels while bounding the recovery distance.
- **Premultiplied Resizing & Compositing**:
  - Decouples decontamination, cropping, premultiplied resizing, and final compositing to avoid dark or bright edge fringes.
  - Resizes the premultiplied RGB foreground and the alpha mask together, then composites them onto the solid background.
- **Failure Conditions**: Invalid dimensions, mask mismatch, insufficient foreground coverage, target colour rejected.
- **Warning/Info Conditions**: Minimal clipping risk at boundaries.
- **Privacy Considerations**: Does not adjust skin tone or facial details; color correction is strictly limited to the boundary band to prevent identity modification.
- **Status**: **Edge decontamination and premultiplied compositing implemented (Milestone 18)**
- **Dependencies**: `SolidBackgroundComposer`, edge decontamination and premultiplied composite pipeline (pure NumPy/PIL).

### 9. Crop-mode Selection
- **Purpose**: Choose Crop Mode A (exact aspect/size) or B (natural head framing with margins) based on the rule configuration.
- **Inputs**: Stored exam rule.
- **Outputs**: Selected crop mode.
- **Failure Conditions**: Missing processing configuration.
- **Warning Conditions**: None.
- **Privacy Considerations**: None.
- **Planned Tests**: Assert correct mode routing.
- **Dependencies**: Rule validation logic.

### 9b. Exam Portrait Composition
- **Purpose**: Build semantic crop-framing geometry for exam portraits before crop calculation. This stage separates the full foreground mask used for background removal from the head-led composition box used for crop sizing.
- **Inputs**: Face detection, geometric/refined head estimate, refined alpha mask.
- **Outputs**: Portrait preservation box, portrait framing box, lower-body exclusion boundary, confidence, warnings.
- **Rules**:
  - Preserve top hair, ears/side-head boundaries, chin, and lower beard line.
  - Treat neck, collar, shoulders, and torso foreground as non-framing evidence so they cannot shrink the face in a tight exam crop.
  - Use upper alpha evidence only inside a face/head-led ROI; do not allow full-person segmentation bounds to expand crop geometry.
- **Failure Conditions**: Composition provider failure falls back to existing head geometry with a warning; it must not fall back to full foreground-driven crop sizing.
- **Warning Conditions**: Alpha unavailable or mismatched dimensions.
- **Privacy Considerations**: Uses in-memory geometry only; no photo or mask artifact is persisted unless explicit diagnostic artifact saving is enabled.
- **Planned Tests**: Synthetic torso-mask regressions for Crop Mode A and Crop Mode B.
- **Dependencies**: Face detection, head estimation, refined alpha mask.

### 10. Crop Calculation
- **Purpose**: Calculate the crop window coordinates.
  - **Crop Mode A**: Fit crop window to target aspect ratio, keeping face centered, preserving hair, ears, chin, and beard lines.
  - **Crop Mode B**: Build crop box directly around head with small natural margins on top, sides, and bottom. Use this for dimension ranges and documented unspecified-dimension fallback profiles.
- **Inputs**: Exam portrait composition geometry, head boundaries, crop mode.
- **Outputs**: Crop window coordinates `(x1, y1, x2, y2)`.
- **Failure Conditions**: Crop coordinates fall outside original image boundaries and preservation-first background padding is disallowed.
- **Warning Conditions**: Margin size is below default minimum.
- **Privacy Considerations**: In-memory only.
- **Planned Tests**: Verify aspect ratio matches target.
- **Dependencies**: Pillow crop tool parameters.

### 10b. Crop-Region Matte Recomputation
- **Purpose**: Spend the matting model's resolution on the part of the photograph that survives into the output (DEC-040).
- **Why it exists**: the model sees a fixed 512x512 square, so the alpha detail any region receives is set by how much of the *source frame* it occupies, not by how large it will be in the finished photo. Candidates submit half- and full-body photographs and the output is a tight head crop. Measured across 60 reference photographs, the head arrived with a median of 121 px of alpha detail (worst 42) and was then magnified by a median 2.1x, worst 17.4x. Every photograph with visible hair-edge streaking or halo sat in the high-magnification group.
- **Inputs**: Normalized image, the planned crop box, the full-frame alpha.
- **Outputs**: The full-frame alpha with the crop region replaced at native resolution.
- **Runs after crop planning**, which is already decided and is not revisited, so this cannot feed back into planning. Skipped when the crop region is within 1.15x of the full frame. A failure here degrades edge detail rather than failing the photograph.
- **Status**: **Implemented (DEC-040)**
- **Known limit**: this fixes matte resolution, not source resolution. A photograph whose head occupies few source pixels still needs heavy enlargement for a large output, which no matting can recover; that is reported as a finding instead.

### 11. Restrained Image Correction
- **Purpose**: Correct measured capture defects without altering candidate identity (DEC-043).
- **Inputs**: Source image, face-region photometric measurements.
- **Outputs**: Corrected source image, plus a disclosure list of what was applied.
- **What triggers each correction**: a compressed tonal range triggers a contrast lift; clipped shadows or highlights trigger a brightness correction *away from the clipped end*; a non-neutral illuminant triggers partial grey-world neutralisation; a low normalised sharpness triggers a bounded sharpen. A photograph with no measured deficit receives a no-op plan, which is the common case.
- **What must never trigger a correction**: how light or dark the subject is. Brightness is triggered by clipping and contrast by compressed range, neither of which is a property of complexion, so **a correctly exposed dark-skinned face is left completely untouched.** An absolute luminance target would be skin lightening and is prohibited.
- **Applied before compositing, never after**, so the replacement background is laid down at the rule's exact colour afterwards and cannot be tinted by an adjustment intended for the subject.
- **Failure Conditions**: Adjustments outside conservative limits (brightness/contrast: 0.88–1.12; sharpness: 0.80–1.20) trigger `OUTPUT_ENHANCEMENT_UNSAFE` blocking failure. Any adjustment in `NONE` mode other than `1.0` triggers failure.
- **Warning Conditions**: A colour cast too severe for correction alone is both corrected and reported, since a half-corrected stage-lit face is still not compliant.
- **Privacy Considerations**: Retains face structures exactly.
- **Planned Tests**: Limits and `OUTPUT_ENHANCEMENT_UNSAFE`; a correctly exposed dark face producing a no-op plan; monochrome never cast-corrected.
- **Dependencies**: Pillow ImageEnhance, NumPy.
- **Not yet implemented**: noise reduction. A chroma-noise guard on the sharpen was written, measured against the labelled set, found not to separate, and removed rather than shipped as a dead constant.

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
- **Inputs**: Resized image, maximum file size (`maximum_bytes`), minimum file size (`minimum_bytes`), target ceiling ratio, safety margin, optional target DPI.
- **Outputs**: Compressed byte array with configured JPEG DPI density when supplied by the rule.
- **Failure Conditions**: Cannot compress below maximum file size without going below the quality floor of 20 (fails with `COMPRESSION_QUALITY_TOO_LOW`), final size exceeds maximum bytes (`COMPRESSION_MAX_SIZE_EXCEEDED`), or final size is below minimum bytes (`COMPRESSION_MIN_SIZE_NOT_REACHED`).
- **Warning Conditions**: Low quality warning (final quality < min_quality).
- **Privacy Considerations**: Metadata is stripped from the byte stream, and raw compressed bytes are excluded from model serialization.
- **Status**: **Implemented (Milestone 13)**
- **Planned Tests**: Verify binary search convergence, quality floor enforcement, minimum size validation, metadata stripping, DPI writing, and serialization safety.
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
- **Purpose**: Audit the final output file against dimensions, aspect ratio, DPI when specified, size limit, and name rules.
- **Inputs**: Final file bytes, metadata, exam rule.
- **Outputs**: Compliance report.
- **Failure Conditions**: Output fails any single check.
- **Warning Conditions**: None.
- **Privacy Considerations**: None.
- **Planned Tests**: Assert failure if file size exceeds configured limits or if encoded DPI differs from the configured rule DPI.
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
