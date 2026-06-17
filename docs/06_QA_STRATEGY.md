# Quality Assurance Strategy (06_QA_STRATEGY.md)

This document specifies the QA methodology, test categories, visual-regression workflows, and test fixture rules.

---

## 1. Test Categories & Execution

- **Unit Tests**: Test single functions (e.g., coordinate scaling, rotation calculations).
- **Contract Tests**: Validate API data boundaries and models using JSON schema.
- **Schema-Validation Tests**: Verify JSON rule files parse correctly.
- **Pipeline-Stage Tests**: Individually test each processing block (orientation, crop, resize).
- **Integration Tests**: Execute processing on sample rules and mock files from beginning to end.
- **End-to-End Tests**: Run user simulation flows from landing page search to output file download.
- **Golden-Image Visual Regression**: Compare output images pixel-by-pixel against reference outputs.
- **Manual Quality Review**: Human inspections to evaluate background segmentation edges and clothing blends.
- **Compression Boundary Tests**: Assert output sizes are close to but under maximum limits.
- **Crop-Geometry Validation**: Verify head height, side margins, and centering ratios.
- **Filename/Format Validation**: Verify naming strings match regulations.
- **Privacy Lifecycle Tests**: Audit deletion timelines and verify files are completely removed.
- **Windows 64-bit Development Checks**: Ensure library compatibility under Windows environments.
- **Cross-Platform Checks**: Validate APIs and pipelines under Linux containers and MacOS.
- **Mobile Usability & Accessibility**: Enforce WCAG 2.1 compliance and responsive web interfaces.

---

## 2. Privacy-Safe Fixture Policy

> [!CAUTION]
> **No real candidate photographs or outputs containing personal details may be committed to Git.**

The repository test suite must exclusively use:
1. **Synthetic Images**: Programmatically generated solid colors, grids, or geometric shapes.
2. **Public-Domain Images**: High-resolution portraits from public sources (e.g., CC0).
3. **Properly Licensed Images**: Stock photography with explicit licensing documentation.
4. **Explicitly Consented Test Images**: Team portraits with signed consent records.
