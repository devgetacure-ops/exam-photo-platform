# MVP Scope Specification (01_MVP_SCOPE.md)

This document defines the functional scope of the Minimum Viable Product (MVP) and distinguishes it from deferred post-MVP capabilities.

---

## 1. Included in the MVP

The MVP delivers a complete, automated, one-click compliance pipeline:

- **Curated Exam Selection**: A searchable, version-controlled library of top Indian exam rules.
- **Structured Examination Rules**: Schema-compliant rule records capturing dimensions, file sizes, format, and filenames.
- **Secure Photo Upload**: Secure endpoints handling standard image formats (JPEG, PNG, WebP) with EXIF orientation normalizations.
- **File Validation**: Input sanitization verifying magic bytes and preventing exploits.
- **Source-Photo Suitability Analysis**: Automated pre-checks (face presence, count, pose angle, blur, and severe occlusion).
- **Background Cleaning**: Clean segmentation and output replacement with pure white or light backgrounds.
- **Intelligent Cropping**: Automatically handles Crop Mode A (exact aspect/dimensions) and Crop Mode B (head-centered with natural margins).
- **Restrained Correction**: Limited adjustments (brightness, exposure, white balance, sharpening).
- **Dimensions Handling**: Exact target sizing and aspect ratio enforcement.
- **Format Handling**: Outputs formatted strictly as required (typically JPEG).
- **Quality-Aware Compression**: Smart iteratively-optimized compression landing just below the maximum size limit.
- **Filename Handling**: Applies target naming schemas (e.g., `photograph.jpg` or `candidate_photo.jpg`).
- **Final Validation**: Independent verification of the final output file format, dimensions, size, integrity, and crop ratios before delivery.
- **Preview & Download**: Clear side-by-side presentation and instant download link.
- **Re-upload & Reprocess**: Clear user guidance on failure with retry flows.
- **Temporary Storage & Deletion Lifecycle**: Files stored in private storage and purged automatically on window expiration.

---

## 2. Excluded from the MVP

These capabilities are explicitly excluded from the MVP baseline. They must not be implemented during initial development:

- **Commercial Payments**: Payment gateways, credits, subscriptions, or paid downloads.
- **Manual Composition Editors**: Interactive crop sliders, rotation dials, or manual adjustment panels.
- **Background Brush Tools**: Fine-grained pixel-level background erasure, restore brushes, or manual masking.
- **Cosmetic Retouching**: Skin smoothing, blemish removal, tooth whitening, or eye size scaling.
- **User Accounts & History**: Saved candidate profiles, photo history, or past download records.
- **Native Mobile Apps**: Android/iOS wrapper apps (mobile-responsiveness is required, but native wrappers are excluded).
- **Bulk Processing Tools**: Operational interfaces for batch processing uploads for multiple candidates.
- **Universal Exam Coverage**: Not supporting every Indian exam cycle on day one; only a vetted curated inventory.
- **Guaranteed Acceptance Claims**: The platform will never make claims guaranteeing acceptance by government portals.
