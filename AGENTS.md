# Repository Operating Contract (AGENTS.md)

This document is the permanent repository operating contract. It applies neutrally to developers, contributors, automated agents, review environments, and continuous integration (CI) systems.

---

## 1. Product Summary & Objective

The **Indian Exam-Photo Compliance Platform** allows candidates to select an examination, upload a source photo, and automatically receive a compliant, correctly formatted, cropped, and named photo that matches the stored requirements of the selected exam cycle.

---

## 2. Binding Product Principles

1. **Exam First, Tool Second**: The chosen examination record configures the entire processing pipeline.
2. **Two Cropping Modes**:
   - **Crop Mode A (Exact Dimensions)**: Build required aspect ratio frame, position head naturally, keep face visually centered, and preserve hair/ears/chin/beard before resizing. Never stretch or distort the subject.
   - **Crop Mode B (Dimension Range/Unspecified)**: Crop tightly around head, leave natural margins, choose suitable output size. **No record selects this since DEC-105**: a range or an unpublished size now resolves to a concrete size and Crop Mode A, which is the framing the owner's reviewed outputs show. The mode stays implemented and tested.
3. **Face Coverage**: Approximately 75–80% face coverage is an expected result of correct natural cropping and a diagnostic indicator, not a rigid mathematical rejection threshold.
4. **Identity Preservation**: Image correction is strictly limited to exposure, contrast, color balance, sharpening, and mild noise reduction. Reshaping, skin whitening, cosmetic retouching, or AI-generated identity modification are strictly prohibited.
5. **No Silent Assumptions**: Material ambiguities, architectural updates, or design questions must be documented in the Decision Log with explicit recommendations before implementation. Never invent silent defaults.
6. **Background Quality**: Masking must keep realistic margins for hair, ears, collar, clothing, and jawlines. Painted-looking hair, halos, and hard cutouts are unacceptable.
7. **Revalidation**: Every edit or retry must trigger output regeneration and a final pass of all validation rules.

---

## 3. Module Boundaries & Repository Structure

- `docs/`: Product decisions, scope, specs, traceability, decisions, and roadmap.
- `apps/web/`: Public-facing React/Next.js single-page application (unimplemented boilerplate).
- `apps/admin/`: Configuration manager console for rules research and verified data entry.
- `services/image-engine/`: Python-based package carrying out the image processing operations.
- `packages/exam-rules/`: JSON rules and schema parsing validator helper.
- `packages/shared-contracts/`: Shared JSON/TypeScript/Python types and JSON schema files.
- `examples/rules/`: Three fictional JSON schema compliance configuration examples.
- `tests/fixtures/`: Synthetic, public domain, or consented test files.
- `tests/golden-images/`: Visual regression source-truth pairs.

---

## 4. Privacy & Security Rules

- **Sensitive Personal Data**: Uploaded photographs contain biometric credentials. Never commit real user photos, intermediate outputs, facial embeddings, or storage URLs to version control.
- **Model Training**: Uploads must never be used for AI training without explicit, documented user permission.
- **Sandboxing & Boundaries**: Perform secure content-type verification, magic signature checks, and safe decoding logic to prevent directory traversal and exploitation.

---

## 5. Scope-Control & Coding Rules

- **Strict Milestone Control**: Do not exceed the defined milestone scope or build forward features ahead of schedule.
- **Code Quality**: Keep strict type annotations (Mypy/Pyright), formatting (Ruff), and formatting validation.
- **Documentation**: Read all specifications in `docs/` before changing a module. Keep `docs/07_REQUIREMENTS_TRACEABILITY.md` and `docs/08_DECISION_LOG.md` completely updated.
- **No Fictional Successes**: Do not construct code placeholders that mock successful compliance results. If not implemented, raise `NotImplementedError`.

---

## 6. Verification and Reporting Requirements

Before presenting a milestone completed to the user, you must:
1. Run all code checks: formatting, linting, type-checking, and tests.
2. Inspect Git status to ensure no sensitive files or environment directories are tracked.
3. Report all results honestly. Provide the status of all failed, skipped, or unavailable checks. Do not hide limitations.
4. Verify that `docs/07_REQUIREMENTS_TRACEABILITY.md` matches the current implementation state.
