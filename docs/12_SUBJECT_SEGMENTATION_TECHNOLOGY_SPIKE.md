# Subject Segmentation Technology Spike (12_SUBJECT_SEGMENTATION_TECHNOLOGY_SPIKE.md)

This technology spike evaluates practical options for local, offline portrait-segmentation and coarse-mask generation on CPU platforms (Windows 64-bit and Linux) for the Indian Exam-Photo Compliance Platform.

---

## 1. Options Evaluated

We evaluated five realistic local portrait-segmentation technologies against the platform's requirements.

### Category A: MediaPipe Selfie Segmenter (General & Landscape)
*   **General Model (256x256)**: `selfie_segmentation.tflite`
*   **Landscape Model (256x144)**: `selfie_segmentation_landscape.tflite`
*   **Description**: MediaPipe's lightweight binary portrait-segmentation models.
*   **Licence**: Apache 2.0 (Google MediaPipe model assets).
*   **Runtime Dependency**: `mediapipe` package (already installed in `[face]` extra).
*   **Evaluation**:
    *   *Subject Coverage*: Segments the full visible person (hair, ears, beard, neck, shoulders, and upper clothing).
    *   *Performance*: Highly optimized for CPU inference on both Windows and Linux. Cold initialization is `< 50ms`; warm inference is `< 15ms` on average CPU.
    *   *Hair Preservation*: Preserves general volume; ignores fine frizzy strands but captures a clean coarse outline.
    *   *Confidence Outputs*: Returns confidence/probability values (float32 values in `[0.0, 1.0]` representing background vs. foreground).
    *   *Windows/Linux Support*: Native.

### Category B: MediaPipe Selfie Segmenter (Multiclass 256x256)
*   **Model**: `selfie_multiclass_256x256.tflite`
*   **Description**: A 6-class semantic segmenter identifying background, hair, body skin, face skin, clothing, and other/accessories.
*   **Licence**: Apache 2.0.
*   **Evaluation**:
		*   *Subject Coverage*: Segments background (0), hair (1), body skin (2), face skin (3), clothes (4), and other/accessories (5). This is ideal for detailed face and head containment validation.
    *   *Hair Preservation*: Excellent coarse detection.
		*   *Ear, Neck, Shoulders, Beard*: Categorized under body skin (2), face skin (3) and clothes (4) respectively.
    *   *Confidence Outputs*: Returns separate confidence masks for each of the 6 classes.
    *   *Performance*: Slightly heavier than binary models due to multiple output channels but extremely fast (warm inference `< 20ms` on CPU). Model size is ~16.4 MB.
    *   *Windows/Linux Support*: Native.

### Category C: ONNX Portrait Matting (MODNet / MobileNetV2)
*   **Description**: Photographic portrait matting networks exported to ONNX format.
*   **Licence**: Often custom/academic or Apache 2.0.
*   **Runtime Dependency**: Requires `onnxruntime` (adds ~80MB to dependencies) and complex preprocessing.
*   **Evaluation**:
    *   *Performance*: High quality hair edges, but CPU inference latency is high (150ms to 400ms depending on CPU thread count).
    *   *Demographics/Bias*: Less tested compared to MediaPipe's global models.
    *   *Replaceability*: Replaceable but requires shipping a heavy native binary dependency.

### Category D: U²-Net / rembg-compatible architectures
*   **Description**: Deep salient object detection networks.
*   **Licence**: Apache 2.0 (rembg wrapper), but model architectures are often GPL/custom.
*   **Runtime Dependency**: `onnxruntime`, `pymatting`, `scikit-image`, `scipy`.
*   **Evaluation**:
    *   *Resource Footprint*: Models are huge (176MB+), cold initialization takes several seconds, and warm CPU latency exceeds 800ms.
    *   *Transitive Dependency Risk*: Extremely high. Installing `scikit-image`, `scipy`, and `pymatting` drags in dozens of compiled packages.
    *   *Licensing*: Many U²-Net checkpoints are restricted or not cleared for commercial use.

### Category E: Semantic Segmentation (DeepLabV3)
*   **Description**: Large general semantic segmentation models.
*   **Evaluation**: Too heavy, not optimized for portraits (will segment tables, chairs, etc.), and coarse boundary performance on hair and ears is poor compared to selfie-specific models.

---

## 2. Comparison Table

| Metric / Feature | MediaPipe Binary (General) | MediaPipe Multiclass | MODNet (ONNX) | U²-Net / rembg | DeepLabV3 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Local Offline** | Yes | Yes | Yes | Yes | Yes |
| **CPU Latency** | **~12ms** | **~18ms** | ~250ms | ~900ms | ~180ms |
| **Model Size** | **~0.25 MB** | **~16.4 MB** | ~25 MB | ~176 MB | ~40 MB |
| **Package Licence**| Apache 2.0 | Apache 2.0 | Apache 2.0 / MIT | GPL / Custom | Apache 2.0 |
| **Model Licence** | Apache 2.0 | Apache 2.0 | Apache 2.0 / Custom | Custom / Academic| Apache 2.0 |
| **Fine Hair strands**| Coarse | Coarse | Fine | Medium | Coarse |
| **Face Containment**| Yes (Person) | Yes (Skin class) | Yes | Yes | No |
| **Ear Preservation**| Yes | Yes (Skin class) | Yes | Yes | Yes |
| **Neck/Shoulders** | Yes | Yes (Skin+Clothes) | Yes | Yes | Yes |
| **Head Coverings** | Yes | Yes (Skin/Clothes) | Yes | Yes | Yes |
| **Confidence Masks**| Yes | Yes (6 channels) | Yes | Yes | Yes |

---

## 3. Baseline Selection

We select **MediaPipe Selfie Multiclass** (`selfie_multiclass_256x256.tflite`) as the **provisional Milestone 7 baseline**.

### Rationale
1.  **Granular Validation**: The 6-class output enables robust, explicit validation rules:
    *   **Hair class (1)**, **Body/Skin class (2)** and **Face/Skin class (3)** must contain the face region and align with the provisional head box.
    *   **Clothes class (4)** and **Other/accessories class (5)** ensure shoulders and upper clothing/accessories are visible.
2.  **No Extra Dependencies**: It uses the same `mediapipe` package already integrated for face detection. No additional runtime wheel installations are needed.
3.  **Low Latency & Size**: It is extremely fast (~18ms on standard CPU) and has a small footprint (~16.4 MB) compared to heavy U²-Net or ONNX matting models.
4.  **Licensing**: The code, model, and weights are governed under **Apache 2.0**, making them safe for redistribution and commercial use.
5.  **Offline CPU Capability**: Fully local, offline, deterministic execution.

---

## 4. Known Limitations

*   **Coarse Hair Boundary**: The model outputs a coarse segment. Fine flyaway hairs or frizzy outlines may be blurred or grouped with background.
*   **Shadow Leakage**: Strong shadows cast on the background immediately adjacent to the hair or neck can occasionally be classified as clothes or hair.
*   **Color Confusion**: Subject hair or clothing of identical color to the background may result in boundary bleeding or minor holes.

---

## 5. Unresolved Questions

*   **Threshold values**: The optimal foreground confidence threshold (`default=0.5`) and uncertain-edge thresholds (`uncertain_low=0.2`, `uncertain_high=0.8`) remain provisional and will be tuned in subsequent edge-refinement and cropping milestones.
