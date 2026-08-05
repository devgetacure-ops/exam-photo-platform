"""Property sweep: do the crop planner's outputs satisfy the invariants?

These are deliberately not example tests. An example test tells you about the
photograph it names; a sweep over the input space tells you whether the next
photograph will be fine. The generated geometries cover the range real
candidate uploads produce -- faces from small-and-distant to close-and-large,
centred and off-centre, high and low in the frame, against portrait, square and
landscape sources, for portrait, square and tall output aspects.

No model is needed: the planner consumes geometry, so the sweep constructs
geometry directly.
"""

from __future__ import annotations

import itertools
from typing import Iterator

from exam_photo.models.geometry import BoundingBox, Landmarks, Point
from exam_photo.orchestration.output_invariants import check_composition_invariants
from exam_photo.providers.crop_planners.deterministic_crop_planner import (
    DeterministicCropPlanner,
)
from exam_photo.providers.crop_planning import CropConfig, CropProfile, EarsPolicy
from exam_photo.providers.face_detection import FaceDetection

# Source frames candidates actually upload: portrait phone, square, landscape.
SOURCE_SIZES = [(960, 1280), (1200, 1600), (1280, 960), (1080, 1080)]
# Face height as a fraction of frame height: distant full-body to close portrait.
FACE_FRACTIONS = [0.10, 0.14, 0.20, 0.30, 0.45]
# Horizontal and vertical placement of the face centre within the frame.
FACE_CENTRES = [(0.5, 0.30), (0.5, 0.42), (0.38, 0.35), (0.62, 0.35)]
# Output aspects: 413x531, 200x230, square, and the tall 1200x1800 class.
TARGETS = [(413, 531), (200, 230), (400, 400), (1200, 1800)]
# How far the estimated head box extends above the face box, in face heights.
#
# This axis matters more than it looks. The planner is fed a head box derived
# from the subject mask, and that box varies enormously with hairstyle: a
# close-cropped head barely exceeds the face box, voluminous hair reaches far
# above it, and an over-estimated box makes the planner reserve room for a
# subject that is not there. Sweeping only clean geometry tests the planner's
# arithmetic while missing the input that actually varies in production.
HEAD_ABOVE_FACE = [0.30, 0.55, 0.85]


def _face(
    frame_w: int, frame_h: int, frac: float, cx: float, cy: float
) -> FaceDetection:
    face_h = frac * frame_h
    face_w = face_h * 0.75
    left = cx * frame_w - face_w / 2.0
    top = cy * frame_h - face_h / 2.0
    box = BoundingBox(left=left, top=top, right=left + face_w, bottom=top + face_h)
    eye_y = top + 0.32 * face_h
    return FaceDetection(
        bounding_box=box,
        confidence=0.9,
        landmarks=Landmarks(
            left_eye=Point(x=left + 0.30 * face_w, y=eye_y),
            right_eye=Point(x=left + 0.70 * face_w, y=eye_y),
            chin=Point(x=left + 0.5 * face_w, y=top + 0.98 * face_h),
        ),
    )


def _head_box(
    face: FaceDetection, frame_w: int, frame_h: int, above: float = 0.55
) -> BoundingBox:
    """A plausible full-head box: hair above, a little beyond the jaw below."""
    b = face.bounding_box
    return BoundingBox(
        left=max(0.0, b.left - 0.18 * b.width),
        top=max(0.0, b.top - above * b.height),
        right=min(float(frame_w), b.right + 0.18 * b.width),
        bottom=min(float(frame_h), b.bottom + 0.12 * b.height),
    )


def _cases() -> Iterator[tuple]:
    for size, frac, centre, target, above in itertools.product(
        SOURCE_SIZES, FACE_FRACTIONS, FACE_CENTRES, TARGETS, HEAD_ABOVE_FACE
    ):
        yield size, frac, centre, target, above


CASES = list(_cases())


def _plan(size, frac, centre, target, above):
    frame_w, frame_h = size
    face = _face(frame_w, frame_h, frac, *centre)
    config = CropConfig(
        target_width=target[0],
        target_height=target[1],
        target_aspect_ratio=target[0] / target[1],
        crop_profile=CropProfile.TIGHT_EXAM_PORTRAIT,
        ears_policy=EarsPolicy.PREFERRED_VISIBLE,
        target_head_height_ratio=0.86,
        minimum_head_height_ratio=0.75,
        maximum_head_height_ratio=0.93,
        target_top_margin_ratio=0.05,
        minimum_top_margin_ratio=0.02,
        maximum_top_margin_ratio=0.10,
        target_eye_line_ratio=0.487,
        minimum_eye_line_ratio=0.43,
        maximum_eye_line_ratio=0.54,
        allow_padding=True,
        complete_hair_required=True,
        complete_chin_required=True,
    )
    planner = DeterministicCropPlanner()
    return planner.plan_crop(
        image_width=frame_w,
        image_height=frame_h,
        face=face,
        head_estimate=_head_box(face, frame_w, frame_h, above),
        config=config,
    )


def _delivered_ratios(result, face_chin_y: float, head_top_y: float):
    """Composition as delivered, measured off the chosen crop box."""
    box = result.crop_box
    height = max(1.0, box.bottom - box.top)
    return {
        "head_height": (face_chin_y - head_top_y) / height,
        "above_hair": max(0.0, head_top_y - box.top) / height,
        "below_chin": max(0.0, box.bottom - face_chin_y) / height,
    }


# Cases still violating an invariant, as a ratchet rather than a target.
#
# A hard zero would either sit red in CI or force the bound to be loosened until
# it stopped detecting anything. A ratchet keeps the gate honest: the count may
# fall, never rise. It is at zero; do not raise it to make a change pass.
#
# History, because the shape of the defect is the useful part. 960 generated
# geometries once produced 224 failures, all of them the same invariant --
# below-chin space -- and 212 of the 224 where the head box reached far above
# the face box, i.e. voluminous hair. The cause was that below-chin space was
# never a constraint anywhere, only a residual: the search satisfied the eye
# line by shrinking head height, and the space that freed up drained out under
# the chin where nothing looked at it. Bounding it in the crop planner's
# candidate search, and ranking it above the eye line in the relaxation ladder,
# took it to zero. Delivered below-chin space across the sweep now measures
# min 0.082, median 0.110, p90 0.137, max 0.151, against 0.054/0.102/0.179/0.247
# on the 60 approved ideal outputs.
_KNOWN_VIOLATIONS = 0


def test_invariant_violations_do_not_increase() -> None:
    """Sweep every generated geometry and ratchet the violation count."""
    failures = []
    for size, frac, centre, target, above in CASES:
        frame_w, frame_h = size
        face = _face(frame_w, frame_h, frac, *centre)
        head = _head_box(face, frame_w, frame_h, above)
        result = _plan(size, frac, centre, target, above)
        assert result.crop_box is not None
        chin_y = (
            face.landmarks.chin.y
            if face.landmarks and face.landmarks.chin
            else face.bounding_box.bottom
        )
        ratios = _delivered_ratios(result, chin_y, head.top)
        report = check_composition_invariants(
            head_height_ratio=ratios["head_height"],
            above_hair_ratio=ratios["above_hair"],
            below_chin_ratio=ratios["below_chin"],
        )
        if not report.holds:
            failures.append(
                f"{frame_w}x{frame_h} frac={frac} centre={centre} "
                f"target={target[0]}x{target[1]} above={above}: "
                + ", ".join(
                    f"{v.invariant}={v.measured:.3f}>{v.bound}"
                    for v in report.violations
                    if v.measured is not None
                )
            )
    detail = "\n".join(failures[:12])
    assert len(failures) <= _KNOWN_VIOLATIONS, (
        f"invariant violations rose to {len(failures)} "
        f"from {_KNOWN_VIOLATIONS}:\n{detail}"
    )


def test_the_sweep_is_actually_broad() -> None:
    """Guard against the sweep silently shrinking to a handful of cases."""
    assert len(CASES) >= 700


def test_crop_box_is_always_well_formed() -> None:
    """Whatever the input, the plan must return usable geometry."""
    for size, frac, centre, target, above in CASES:
        result = _plan(size, frac, centre, target, above)
        box = result.crop_box
        assert box is not None
        assert box.right > box.left and box.bottom > box.top
        aspect = (box.right - box.left) / (box.bottom - box.top)
        assert abs(aspect - target[0] / target[1]) < 0.02, (
            f"aspect drift on {size} {frac} {centre} {target} {above}: {aspect:.4f}"
        )
