# Output Invariants — Working Contract

**Read this before changing composition, crop geometry, or anything the
invariant sweep gates.** It is a standing document, not a session note: it
describes how invariant work is done here and why, and it should be amended
when the practice changes rather than deleted when a task finishes.

---

## What the invariants are

`services/image-engine/src/exam_photo/orchestration/output_invariants.py` states
properties every **delivered** photograph must satisfy, whatever the input.

They exist because composition was previously constrained only *during* crop
planning, and every one of those constraints is waivable — the last relaxation
tier waives them, and the geometric-projection fallback applies none. Final
validation checked byte size, pixel dimensions, format and DPI: properties of
the file, not of the photograph. So nothing guaranteed anything about what the
candidate actually received, and a defect only surfaced when a human looked at
an output and said it was wrong. That does not scale.

Two properties of the invariants matter and are easy to erode:

- **They are stated over the result, not over the search.** They are
  deliberately far looser than the composition targets. Their job is to catch
  the grossly wrong, not to enforce the ideal. A photograph that satisfies every
  invariant may still be mediocre; one that violates an invariant is broken.
- **A violation reports, it never refuses** (DEC-041). The candidate still gets
  their photograph. The value is that the violation is *recorded*, so it can be
  counted across a population, alerted on, and regression-tested.

## The gate

```bash
cd services/image-engine && .venv/Scripts/python.exe -m pytest tests/orchestration/test_output_invariants.py -q
```

`tests/orchestration/test_output_invariants.py` sweeps 960 synthetic geometries
— source frame, face size, face placement, output aspect, and how far the head
box reaches above the face box — and ratchets the violation count in
`_KNOWN_VIOLATIONS`.

**The ratchet may fall. It may never rise.** Raising it to make a change pass
defeats the only mechanism that keeps the gate honest. If a change genuinely
requires more violations, that is a finding to argue in the decision log, not a
number to edit.

The sweep needs no model: the planner consumes geometry, so the sweep
constructs geometry directly. It runs in about 20 seconds.

`HEAD_ABOVE_FACE` is the axis that earns its place. The planner is fed a head
box derived from the subject mask, and that box varies enormously with
hairstyle. Sweeping only clean geometry tests the planner's arithmetic while
missing the input that actually varies in production.

## Rules of engagement

These are the working rules for this area. They were each learned the
expensive way.

1. **No per-photo fixes.** Fix the class of defect and prove it with the sweep.
   A change justified by one photograph will be undone by the next one.
2. **Every threshold comment must state the measurement on both sides of it.**
   A bound with only one side recorded cannot be checked by the next reader, and
   at least one bound in this codebase was originally placed *past* both of the
   values it was derived to separate — a bound outside the range it came from is
   not a bound.
3. **Do not ship a signal whose reliability you have not measured.** Two were
   written, measured, found not to separate, and removed: eye-blink scoring and
   the chroma-noise guard. Removing beats shipping a dead constant. The same
   applies to checks: a check that cannot fail is worse than no check, because
   it reads as evidence.
4. **Measure against the ideal outputs, not against a self-derived threshold.**
   The 60 approved reference outputs are the composition specification
   (DEC-037). Deriving a target from first principles and then optimising toward
   it is the documented failure mode of an earlier session.
5. **Move the planner and its validator together.** See below — this is the
   recurring defect class here.
6. **Never commit real candidate photos, processed outputs, mattes or model
   weights.** Numeric measurements and issue codes only. The public-domain
   golden fixture under `tests/golden-images/` is the sole exception and is
   already committed.

## The recurring defect class

**The planner promises one region and the validator judges another.**

DEC-029, DEC-038 and DEC-044 are all instances of it. The crop planner works
with several nested regions and it is easy to enforce one in the candidate
search while validating against a different one afterwards. The symptom is
always the same shape: the search selects a crop that its own validation then
rejects as a blocking error, or — worse — a correctly framed crop is reported as
clipping a subject that was never there.

The regions, from generous to strict:

| Region | What it is | Status |
|---|---|---|
| `preserve_box` | head estimate / portrait composition box, trimmed at the crown. Extends below the jaw and absorbs hair spread — roughly 1.14× the real head height, 1.31× its width | A *preference*. Keeping all of it is never guaranteed |
| `mandatory_box` | crown − top margin → chin + beard margin, spanning the head core ± side margin, plus every landmark the detector actually located | The **guarantee**. The candidate search enforces containment as a hard constraint |
| `face_box` | the raw BlazeFace rectangle | A coarse proxy that misses real anatomy in both directions. Not used for containment in adaptive mode (DEC-038) |

Rules that follow:

- Box containment (`head_coverage_ratio`, `face_contained`) and margin
  reporting are judged against `mandatory_box`, under the search's own
  condition: adaptive planning with subject clipping disallowed. Not against
  `outer_hair_relaxation_used`, which is the weaker and different statement
  that no candidate happened to keep the whole preservation box.
- Pixel retention (`mask_preservation_ratio`) is deliberately measured against
  the *generous* box. Keyed to `mandatory_box` it would return 1.0 by
  construction on every crop the search can select. It earns its place by
  covering what the box test cannot: foreground the crop drops from the outer
  region.
- If you change one of these, change the others in the same commit and say so.

## Verifying before claiming

`.github/workflows/image-engine-ci.yml` is the source of truth. Reproduce the
relevant subset locally; `pytest` alone does not cover the eleven
`mandatory_*` marker suites.

```bash
cd services/image-engine && ruff format --check . && ruff check . && .venv/Scripts/python.exe -m mypy src tests
```

The marker suites need real model assets and the matching env vars. All models
are present under `model-assets/`; run from the repo root with
`EXAM_PHOTO_FACE_MODEL_PATH` / `EXAM_PHOTO_SEGMENTER_MODEL_PATH` and their
`*_SHA256` set as the workflow sets them, once per marker:

```bash
services/image-engine/.venv/Scripts/python.exe -m pytest services/image-engine -m "mandatory_rule_pipeline" -q
```

The eleven markers are `mandatory_segmentation`, `mandatory_refinement`,
`mandatory_crop`, `mandatory_crop_b`, `mandatory_background`,
`mandatory_output_preparation`, `mandatory_output_compression`,
`mandatory_rule_pipeline`, `mandatory_api`, `mandatory_rule_admin`,
`mandatory_engine_quality`.

## Reference material — local only, never commit

| What | Where | Notes |
|---|---|---|
| 60 source photos | `C:\Users\dmbar\Pictures\Test Images` | 6 folders, one per output dimension class |
| 60 approved ideal outputs | `C:\Users\dmbar\Pictures\Test Images- Ideal Outputs` | 1:1 with the sources. **This set is the composition specification** |
| 40 adversarial photos | `C:\Users\dmbar\Pictures\new-test-images` | Filenames carry human labels across 11 defect classes |
| Label map | `services/image-engine/tests/fixtures/adversarial_label_map.json` | Committed. Records where the engine deliberately disagrees with a label |

The matched benchmark writes numbers only — no source photos, output photos,
alpha mattes or weights:

```bash
services/image-engine/.venv/Scripts/python.exe scripts/benchmark_reference_pairs.py --inputs "C:/Users/dmbar/Pictures/Test Images" --ideals "C:/Users/dmbar/Pictures/Test Images- Ideal Outputs" --output-json out.json --ideal-cache ideal_cache.json
```

It takes roughly 30–45 minutes on CPU (M24: 16–24 s per photo, roughly doubled
by the crop-region rematte). Pass `--ideal-cache` so the ideal measurements are
computed once.

### Measured on the approved ideal outputs

Composition as delivered, as a fraction of each photograph's own frame height:

| | min | p10 | p25 | median | p75 | p90 | max |
|---|---|---|---|---|---|---|---|
| below chin | 0.054 | 0.068 | 0.081 | 0.102 | 0.142 | 0.179 | 0.247 |
| head height | 0.665 | 0.769 | 0.819 | 0.855 | 0.884 | 0.904 | 0.918 |
| above hair | 0.005 | 0.026 | 0.033 | 0.042 | 0.062 | 0.078 | 0.132 |

Note the tension worth knowing about before you touch the bound: 6 of the 60
approved outputs exceed the 0.175 below-chin invariant, four of them in the
1200×1800 class where head height is bound by the target's width rather than by
composition. The invariant is calibrated on a reviewer's accept/reject verdicts
over engine outputs (accepted ≤ 0.155; rejected at 0.188 and 0.190), not on the
ideal distribution, and it is a report rather than a refusal.

## State

Sweep at **0 violations** of 960 (2026-08-04). Delivered below-chin space across
the sweep measures min 0.082, median 0.110, p90 0.137, max 0.151.

**Known gap: `check_composition_invariants` has no pipeline consumer.** Its only
caller is the sweep. The module's own docstring describes the invariants as
checks over the delivered photograph producing a finding per DEC-041, and that
half is not built: `orchestration/final_validation.py` does not call it, so a
real candidate upload is never measured against these bounds. The sweep gates
the *planner* against synthetic geometry, which is genuinely useful and is what
caught the below-chin defect, but it is not the population-level detector the
module was written to be. Wiring it into final validation — measuring crown,
chin and crop box on the finished image and attaching violations as findings —
is the obvious next step and is not done.

Open composition work is tracked in `docs/09_DEVELOPMENT_ROADMAP.md`,
Milestones 19–30. The product blocker is M19: all 11 encoded exams are
provisional with `dimensions.mode` `"unspecified"`, so the engine cannot yet
size a photograph for any real examination.
