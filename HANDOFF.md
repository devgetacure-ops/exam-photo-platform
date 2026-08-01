# Session Handoff — Crop & Matte Quality Work

**Date:** 2026-08-01
**Status:** Verified fixes in place, uncommitted. One known regression outstanding.
**Delete this file once the work is committed and the next session is oriented.**

---

## Read this first

The user's spec is **the ideal-output photos**, not any threshold derived from
first principles:

- Test images: `C:\Users\dmbar\Pictures\Test Images` (60 photos, 6 dimension folders)
- Ideal outputs: `C:\Users\dmbar\Pictures\Test Images- Ideal Outputs` (1:1 correspondence)

The previous session's main process failure was drifting off these: it started
optimising an abstract "75% head coverage" target it had derived itself, and
spent a long time doing feasibility algebra and single-photo debugging instead
of diffing engine output against the corresponding ideal output.

**Measure engine output against the matching ideal output, per photo, across all
60. Do not tune against a self-derived threshold.**

Per the user, the two things that matter right now are **crop** and **background
removal / edge quality**. Everything else waits. If a photo is geometrically
impossible, log it and move on — do not chase it.

The user's stated crop requirements (verbatim intent):
- Face coverage 75% is a floor that must not be crossed; 80–90% is better;
  "the tighter the better" — but never at the cost of clipping hair, ears, chin,
  or beard line.
- Edges must look like a studio photo on white, not AI-generated or cut-and-pasted.
- Compression should land just *below* the size limit, never at or over it.
- Crop is user-fixable later via UI; background removal is not.

---

## What was actually fixed this session (all verified, all uncommitted)

One root cause behind both user complaints ("crop too loose", "ears gone"):
**three separate places measured head width from a mask region that extended
past the neck into the shoulders**, so "head width" silently became "shoulder
width".

Measured on photo `6-3.jpeg`: silhouette width holds at 85–124px through the
head and neck (y=590–750), then jumps to 224–291px by y=780–810 once shoulders
enter frame. True head-core width is 124px; the pipeline was using 267px.

| # | File | Fix |
|---|---|---|
| 1 | `providers/crop_planners/deterministic_crop_planner.py` | `_estimate_head_core_x` plausibility check no longer requires the mask band to reach the detector face-box edges (it rejected the *correct* narrow reading on subjects whose hair covers their ears). Replaced with centred-on-face + `_MIN_HEAD_WIDTH_FACE_RATIO` (0.5) / `_MAX_HEAD_WIDTH_FACE_RATIO` (2.6). |
| 2 | `providers/portrait_composition.py` | `_observed_upper_alpha_box` now reads left/right from a band capped at `face_box.bottom`; bottom still uses the full range. |
| 3 | `providers/fused_head_refinement.py` | Same chin-cap for the width scan; **and** left/right no longer floor against `geometric_box` (that box widens ear-tragion keypoints assuming ears are visible, which discarded the corrected reading). |
| 4 | `providers/mediapipe_face_landmarker.py` | `refine()` now crops around the BlazeFace box (`_CROP_MARGIN_RATIO = 1.5`) before running the dense landmarker. Verified on 6-3: **0 faces found on the full frame at every confidence from 0.5 down to 0.01; 1 face immediately once cropped.** This was why the chin fell back to `face_box.bottom` (into the neck) on large photos. |
| 5 | `providers/crop_planners/deterministic_crop_planner.py` | `_SIDE_MARGIN_RATIO` 0.07 → 0.03, calibrated against the structural feasibility ceiling (see below). |

Verified progression on 6-3 as each fix landed: **0.36 → 0.37 → 0.50 → 0.53**.

### Aggregate, measured across all 60 photos

| | Met 75% floor | Produced no output |
|---|---|---|
| Before this session's fixes | 17 / 60 | 3 |
| After fixes 1–4 | 31 / 60 | 7 |

Coverage nearly doubled, **but 4 more photos now produce no output — that is an
unfixed regression introduced by these changes.**

Raw per-photo data is in the scratchpad of the previous session; regenerate with
the diagnostic pattern in "How to reproduce" below rather than trusting stale
numbers.

---

## Outstanding / known issues

1. **7 photos produce no output** (up from 3): `1-4`, `3-1`, `3-3`, `5-1`,
   `5-5`, `6-4`, `6-7`. `3-3` is multi-face, `5-1` is a face-detection failure,
   `6-7` is background clipping. The other 4 are new regressions from this
   session's changes. **Highest-priority fix.**

2. **10 of 58 measurable photos are geometrically impossible at 75%.** Their
   measured head width exceeds 0.89 × head span, so in a 2:3 frame no crop can
   hit 75% height coverage. Either the width reading is still too generous on
   those, or they genuinely need the crop-fix UI. **Per the user: do not burn
   time here — verify against the ideal outputs, log, move on.**

3. **A reverted experiment, for the record.** Re-anchoring the crop search's
   horizontal sweep on the measured head-core centre instead of `face_cx`
   (`l_ideal = head_core_cx - wc / 2.0`) *broke* 6-3 outright — it returned
   `is_valid=False` with no output. The reasoning (the ±8% dx sweep can miss
   mandatory containment when the head core is off-centre in the face box) may
   still be sound, but the naive change is wrong. **It has been reverted. Do not
   re-apply without understanding why it failed.**

4. **BiRefNet is not the pipeline default.** Only `api/service.py` auto-selects
   it. `RuleOrchestratedPipeline` and the CLI still default to
   `matting_backend="mediapipe"`. Anyone calling the engine directly gets the
   old, much worse matte.

5. **Decision log is behind.** `docs/08_DECISION_LOG.md` currently ends at
   DEC-031. DEC-032 (face landmarker) is referenced in code but the log entry
   should be confirmed; DEC-033/034/035 are referenced in code comments and are
   **not** written. The fixes above need DEC-036+ entries.
   `docs/07_REQUIREMENTS_TRACEABILITY.md` also needs updating.

---

## Verification state

Run from `services/image-engine`:

- `ruff format --check .` — clean
- `ruff check .` — clean
- `mypy src tests` — clean, 111 source files
- Core pytest subset — **143 passed, 15 skipped**

The `mandatory_*` marker suites were **not** run this session (they need model
assets + env vars). See `.github/workflows/image-engine-ci.yml` for the exact
per-marker invocation. **Run them before committing.**

---

## Nothing is committed

The entire session's work is in the working tree only — ~2000 insertions across
32 tracked files plus 17 untracked new files (BiRefNet segmenter, face
landmarker, manifests, download scripts, benchmark rule configs, new tests,
`CLAUDE.md`, `mypy.ini`).

This is the single biggest risk right now. Suggested split:

1. Model vendoring infra (manifests, download scripts, `.gitignore`, pyproject `matting` extra)
2. BiRefNet backend + landmarker provider + wiring (`rule_pipeline`, `api/service`, `settings`, `cli`)
3. Matte refinement changes (`morphological_refiner`, `foreground_refinement`, `foreground_decontamination`)
4. Crop geometry fixes (the 5 fixes above) + tests
5. Docs (decision log, traceability)

Never commit real candidate photos or model weights — see `AGENTS.md`.

---

## How to reproduce the measurement

Full pipeline on one photo, forcing BiRefNet:

```python
import sys, json
from pathlib import Path
REPO = Path('C:/Projects/exam-photo-platform')
sys.path.insert(0, str(REPO / 'services/image-engine/src'))
from exam_photo.orchestration.rule_pipeline import RuleOrchestratedPipeline, RulePipelineConfig
from exam_photo.providers.segmenters.birefnet_segmenter import load_manifest_defaults

md, wf, sha, sz = load_manifest_defaults(REPO)
pipe = RuleOrchestratedPipeline(
    face_model_path=REPO/'model-assets/blaze_face_short_range.tflite',
    segmenter_model_path=REPO/'model-assets/selfie_segmentation.tflite',
    face_expected_sha256='b4578f35940bf5a1a655214a1cce5cab13eba73c1297cd78e1a04c2380b0152f',
    segmenter_expected_sha256='9ee168ec7c8f2a16c56fe8e1cfbc514974cbbb7e434051b455635f1bd1462f5c',
    matting_backend='birefnet', birefnet_model_dir=md, birefnet_expected_sha256=sha)

p = Path('C:/Users/dmbar/Pictures/Test Images/6- 1200 × 1800 px ; 72 DPI/6-3.jpeg')
rule = json.loads((REPO/'examples/rules/benchmark_exact_1200x1800_72dpi_white_bg.json').read_text())
r = pipe.process_rule(p.read_bytes(), rule,
    RulePipelineConfig(allow_padding=True, allow_invalid_output=True, quality_mode='high'))
print(r.portrait_quality_report.get('head_height_ratio'), r.is_valid)
```

Interior geometry is easiest to inspect by monkey-patching
`DeterministicCropPlanner._estimate_crown_y` / `_estimate_chin_y` /
`_estimate_head_core_x` to print before delegating to the original.

Benchmark rule configs matching each test folder's dimensions are in
`examples/rules/benchmark_exact_*.json`.

Each folder in `Test Images` maps to one rule config by dimensions — e.g.
`6- 1200 × 1800 px ; 72 DPI` → `benchmark_exact_1200x1800_72dpi_white_bg.json`.

---

## Recommended next plan

1. Build the **per-photo engine-vs-ideal diff** across all 60, reporting exactly
   what the user asked for: crop W/H, negative space left, negative space right,
   headspace above hair, space below chin, and edge behaviour at hair / ears /
   beard-line / chin / neck. This is the missing feedback loop.
2. Read composition targets off the ideal outputs' measured distribution;
   replace any self-derived constants that disagree.
3. Fix the 7 no-output photos.
4. Re-run all 60, confirm both coverage and no-output counts improved.
5. Run the `mandatory_*` suites, then commit in the slices above and update
   the decision log + traceability matrix.
