# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Product summary

Indian Exam-Photo Compliance Platform: candidates select an exam, upload a source photo, and the system automatically produces a compliant, correctly cropped/sized/named photo matching that exam's stored rules. See [AGENTS.md](AGENTS.md) for the full binding operating contract — read it before making non-trivial changes; it takes precedence over generic conventions.

Binding product principles (from AGENTS.md, do not violate):
- **Exam First, Tool Second** — the exam rule record drives the whole pipeline.
- **Two crop modes**: Mode A (exact dimensions — build the aspect frame, position head naturally, never stretch/distort) and Mode B (dimension range/unspecified — crop tightly around the head with natural margins). **Selection superseded by DEC-105**: every record now resolves to a concrete size and so to Mode A, which is the framing the owner's reviewed outputs show; Mode B stays implemented and tested but nothing selects it.
- **Identity preservation** — only exposure/contrast/color/sharpening/mild noise reduction is allowed. No reshaping, skin whitening, cosmetic retouching, or AI identity modification.
- **No silent assumptions** — material ambiguities go in `docs/08_DECISION_LOG.md` with an explicit recommendation before implementation.
- **No fictional successes** — unimplemented behavior raises `NotImplementedError`, never a mocked "success".
- Never commit real candidate photos, processed outputs, facial embeddings, or model weight files. Test fixtures must be synthetic/public-domain only (see `tests/fixtures/`).

## Repository layout

- `apps/web/` — public Next.js (App Router) SPA: exam selection, upload, validation diagnostics, download, and a local-only rule admin console (`/admin/rules`, gated by `NEXT_PUBLIC_ENABLE_RULE_ADMIN=true`).
- `apps/admin/` — placeholder for a future standalone rule administration app (currently just a README).
- `services/image-engine/` — the Python image-processing engine; this is where almost all backend logic lives (see below).
- `packages/exam-rules/` — canonical language-neutral JSON Schema for exam rules (`schema/exam-rule.schema.json`); all typed models (e.g. Python Pydantic) must conform to it.
- `packages/shared-contracts/` — shared cross-language type/schema definitions.
- `examples/rules/` — example exam-rule JSON configs (fictional data only).
- `tests/fixtures/`, `tests/golden-images/` — shared synthetic/public-domain test images and golden-image regression pairs.
- `model-assets/`, `model-manifests/` — downloaded MediaPipe model weights (gitignored; fetched via `scripts/download_model.py` / `scripts/download_segmenter.py`) and their manifests.
- `docs/` — numbered product/spec documents; read the ones relevant to your task before changing behavior (`03_EXAM_RULE_SCHEMA.md`, `04_IMAGE_PIPELINE_SPEC.md` are the most code-relevant). `07_REQUIREMENTS_TRACEABILITY.md` and `08_DECISION_LOG.md` must be kept in sync with implementation changes.

## Commands

### Python image-engine (`services/image-engine/`)

Set up once:
```bash
cd services/image-engine
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install --upgrade pip
pip install -e .[dev,face]    # add `face` extra for mediapipe-backed tests
```

Run from inside `services/image-engine` (or prefix paths as shown):
```bash
ruff format --check .                     # formatting check
ruff check .                              # lint
mypy src tests                            # strict type check
pytest                                    # full test suite
pytest -m "not mandatory_segmentation and not mandatory_refinement and not mandatory_crop and not mandatory_crop_b and not mandatory_background and not mandatory_output_preparation and not mandatory_output_compression and not mandatory_rule_pipeline and not mandatory_api and not mandatory_rule_admin and not mandatory_engine_quality"  # fast/core subset (no model downloads needed)
pytest tests/providers/test_crop_mode_a.py::test_name   # single test
```

Model-gated test markers (`mandatory_segmentation`, `mandatory_refinement`, `mandatory_crop`, `mandatory_crop_b`, `mandatory_background`, `mandatory_output_preparation`, `mandatory_output_compression`, `mandatory_rule_pipeline`, `mandatory_api`, `mandatory_rule_admin`, `mandatory_engine_quality`) require real model assets and `EXAM_PHOTO_FACE_MODEL_PATH` / `EXAM_PHOTO_SEGMENTER_MODEL_PATH` (+ matching `*_SHA256`) env vars — see `.github/workflows/image-engine-ci.yml` for the exact invocation per marker and the download commands (`python scripts/download_model.py --variant short_range --yes`, `python scripts/download_segmenter.py --variant <variant> --yes`). Skipping a `mandatory_*` test without the model present fails the session via `tests/conftest.py`'s `pytest_sessionfinish` hook (currently wired for `mandatory_segmentation`).

The CLI is invoked as `python -m exam_photo <subcommand>` (defined in `src/exam_photo/cli.py`), e.g. `validate-rule`, `inspect-input`, `plan-crop-mode-a`, `plan-crop-mode-b`, `compose-background`, `prepare-output`, `compress-output`, `process-rule`, `serve-api`. Run `python -m exam_photo <subcommand> --help` to see options; each subcommand mirrors one pipeline stage plus its own benchmark script under `scripts/`.

Benchmarks (accuracy/quality regression, not part of default pytest run) live in `scripts/benchmark_*.py` and generally accept `--require-real` to force real models instead of fakes.

### Web app (`apps/web/`)

```bash
cd apps/web
npm ci
npm run dev         # Next.js dev server
npm run build        # production build
npm run lint          # eslint
npm run typecheck     # tsc --noEmit
npm test               # vitest run
```
`apps/web/AGENTS.md` warns this Next.js version has breaking changes vs. training data — check `node_modules/next/dist/docs/` before relying on remembered Next.js APIs.

### CI

`.github/workflows/image-engine-ci.yml` is the source of truth for the full verification sequence (format → lint → mypy → staged marker-gated pytest runs with model downloads between them → CLI smoke checks → package build → web lint/typecheck/test/build). Reproduce the relevant subset locally before calling work done; don't assume `pytest` alone covers the mandatory-marked suites.

## Architecture: image-engine pipeline

The engine (`services/image-engine/src/exam_photo/`) is a straight-line, provider-based pipeline orchestrated by `orchestration/rule_pipeline.py`, driven end-to-end by `process-rule` / the API. Stages, in order:

1. **Input normalization** (`input/`) — decode, verify magic-signature/content-type, strip EXIF/orientation-correct, map to sRGB (`normalization.py`, `signatures.py`, `metadata.py`, `limits.py` for size/dimension caps, `errors.py`).
2. **Suitability evaluation** (`suitability/`) — face-count/quality checks and guidance codes (`evaluator.py`, `quality_metrics.py`, `issue_codes.py`, `guidance.py`) before any geometry work proceeds.
3. **Face detection & head estimation** (`providers/face_detection.py`, `mediapipe_face_detector.py`, `head_estimation.py`, `landmark_geometric_head_estimator.py`) — locate face and estimate the full head box.
4. **Subject segmentation & refinement** (`providers/subject_segmentation.py`, `segmenters/`, `foreground_refinement.py`, `fused_head_refinement.py`, `refiners/`, `foreground_decontamination.py`) — coarse mask → DSU/connected-component cleanup → face/head-containment validation → edge decontamination.
5. **Crop planning** — `providers/crop_planning.py` dispatches to `crop_planners/deterministic_crop_planner.py` (Mode A, exact dimensions) or `deterministic_crop_mode_b_planner.py` (Mode B, range/unspecified), both driven by the estimated head geometry.
6. **Background composition** (`providers/background_composition.py`, `background_composers/`, `premultiplied_compositing.py`) — solid-background compositing with coverage/clipping-risk checks.
7. **Portrait composition** (`providers/portrait_composition.py`) — adaptive framing/matting hardening pass.
8. **Output preparation** (`providers/output_preparation.py`, `output_preparers/`) — resize to target dimensions, format conversion (e.g. RGBA→RGB), restrained brightness/contrast/sharpness.
9. **Output compression** (`providers/output_compression.py`, `compression/deterministic_image_compressor.py`) — binary-search quality loop to hit a byte-size budget, with EXIF stripping and decode-after-encode verification.
10. **Final validation & filename generation** (`orchestration/final_validation.py`, `orchestration/filename_generation.py`) — revalidate the finished image against every rule constraint and generate a PII-free filename. Every edit/retry re-triggers this full revalidation pass, per the "Revalidation" product principle.

Cross-cutting pieces:
- `models/exam_rule.py` (Pydantic) is the typed mirror of `packages/exam-rules/schema/exam-rule.schema.json` — the JSON Schema is canonical; keep the Pydantic model in sync with it.
- `orchestration/rule_resolver.py` resolves/loads a rule prior to pipeline execution; `rule_validation.py` + the `validate-rule` CLI validate a rule file standalone.
- `providers/__init__.py` and `providers/capabilities.py` define the provider interface contracts — most provider modules have a real ("deterministic"/"mediapipe") implementation and a fake counterpart under `tests/fakes/` for fast, model-free unit tests.
- `api/` (`app.py`, `service.py`, `jobs.py`, `storage.py`, `settings.py`, `contracts.py`) is a local-only FastAPI service (`serve-api` CLI) exposing pipeline execution as opaque jobs with manifest persistence, manual deletion, and TTL cleanup — explicitly not hardened for public exposure (no TLS/auth/rate-limiting).
- `models/geometry.py` provides shared `BoundingBox`/`Point` primitives with safety-clamping math used throughout crop/head-estimation code.

## Web app structure

- `src/app/` — Next.js App Router pages: `page.tsx` (main upload/validate/download flow), `admin/` (local rule console, dev-flag gated).
- `src/components/` — UI components; `components/admin/` holds the rule editor/preview/validation-panel pieces for the admin console.
- `src/lib/` — `api-client.ts` (talks to the image-engine's local FastAPI service), `rule-admin-api.ts` (talks to `POST /v1/rules/validate`), `file-validation.ts`, `rule-editor-state.ts`, `rule-export.ts`, `types.ts`.
- `src/tests/` — Vitest + Testing Library tests colocated by feature.

## Contribution workflow

`CONTRIBUTING.md` defines the expected sequence for any change: read relevant `docs/`, trace to a requirement ID in `docs/07_REQUIREMENTS_TRACEABILITY.md`, check `docs/08_DECISION_LOG.md` for open ambiguities (log new ones before implementing), implement, add/update tests, run format/lint/type-check/tests, then update the traceability matrix and decision log to match. Commit messages follow conventional-commit style (e.g. `feat(engine): ...`, `fix(image-engine): ...`).
