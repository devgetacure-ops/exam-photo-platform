"""Properties every delivered photograph must satisfy, whatever the input.

Why this module exists
----------------------
Composition was previously constrained only *during* crop planning, and every
one of those constraints is waivable: the last relaxation tier waives all of
them, and the geometric-projection fallback applies none. Final validation
checked byte size, pixel dimensions, format and DPI -- properties of the file,
not of the photograph. So nothing in the pipeline guaranteed anything about
what the candidate actually received.

The practical consequence is that a defect only surfaced when a human looked at
an output and said it was wrong. That does not scale: at a few hundred
photographs a day nobody is looking, and a regression is invisible until a
candidate is rejected by an examination board.

These are therefore stated as **invariants over the delivered result**, not as
targets for the search. They are deliberately loose -- far looser than the
composition targets -- because their job is to catch the grossly wrong rather
than to enforce the ideal. A photograph that satisfies every invariant may
still be mediocre; a photograph that violates one is broken.

Bounds are measured, and the measurement is recorded beside each one.

Reporting, not blocking
-----------------------
A violation produces a finding, never a refusal (DEC-041). The candidate still
receives their photograph. The value is that the violation is *recorded*, so it
can be counted across a population, alerted on, and regression-tested --
none of which is possible when the only detector is a human eye.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

# --- Bounds -----------------------------------------------------------------
#
# Measured across ten photographs a reviewer assessed individually. Their
# verdicts split cleanly on below-chin space: everything they accepted sat at
# or below 0.155 of frame height, and both photographs they rejected as too
# loose sat at 0.188 and 0.190. The bound sits between those two clusters.
#
# It was first written at 0.20, which is past *both* rejected values and would
# therefore have flagged neither -- a bound placed outside the range it was
# derived from is not a bound. Recording the error because it is an easy one to
# repeat: a "deliberately loose" threshold still has to fall on the correct
# side of the evidence.
_MAX_BELOW_CHIN_RATIO = 0.175

# Same reviewer set: accepted photographs ran 0.019 to 0.081 above the hair,
# and the one rejected as badly cropped sat at 0.090 with the loosest head in
# the set. Bounded generously above the accepted range.
_MAX_ABOVE_HAIR_RATIO = 0.16

# Head height has an exam-level minimum that is deliberately waivable, because
# some subjects genuinely cannot reach it. This is the separate question of
# whether the crop is *grossly* wrong: the lowest head height in the approved
# reference set is 0.665, so anything under 0.55 is not a tight-but-imperfect
# crop, it is a failure.
_MIN_HEAD_HEIGHT_RATIO = 0.55
_MAX_HEAD_HEIGHT_RATIO = 0.97

# A detached fragment larger than this fraction of the subject is a matting
# failure rather than a stray hair: the subject of a portrait is one connected
# region.
_MAX_DETACHED_FRAGMENT_RATIO = 0.02


class InvariantViolation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invariant: str
    detail: str
    measured: Optional[float] = None
    bound: Optional[float] = None


class InvariantReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    violations: List[InvariantViolation] = Field(default_factory=list)

    @property
    def holds(self) -> bool:
        return not self.violations


def check_composition_invariants(
    *,
    head_height_ratio: Optional[float],
    above_hair_ratio: Optional[float],
    below_chin_ratio: Optional[float],
    face_fully_inside: Optional[bool] = None,
    largest_detached_fragment_ratio: Optional[float] = None,
) -> InvariantReport:
    """Check a delivered photograph against the stated invariants.

    Every argument is optional because a measurement may be unavailable, and an
    unavailable measurement is not a violation -- it is simply not checked. That
    distinction matters: silently treating "not measured" as "passed" is how a
    gate stops gating.
    """
    violations: List[InvariantViolation] = []

    if below_chin_ratio is not None and below_chin_ratio > _MAX_BELOW_CHIN_RATIO:
        violations.append(
            InvariantViolation(
                invariant="below_chin_bounded",
                detail=(
                    "Space below the chin exceeds the bound, which reads as a "
                    "loose crop with the subject sitting high in the frame."
                ),
                measured=below_chin_ratio,
                bound=_MAX_BELOW_CHIN_RATIO,
            )
        )

    if above_hair_ratio is not None and above_hair_ratio > _MAX_ABOVE_HAIR_RATIO:
        violations.append(
            InvariantViolation(
                invariant="above_hair_bounded",
                detail="Headroom above the hair exceeds the bound.",
                measured=above_hair_ratio,
                bound=_MAX_ABOVE_HAIR_RATIO,
            )
        )

    if head_height_ratio is not None:
        if head_height_ratio < _MIN_HEAD_HEIGHT_RATIO:
            violations.append(
                InvariantViolation(
                    invariant="head_height_not_grossly_small",
                    detail=(
                        "The head occupies far less of the frame than any "
                        "approved reference composition."
                    ),
                    measured=head_height_ratio,
                    bound=_MIN_HEAD_HEIGHT_RATIO,
                )
            )
        elif head_height_ratio > _MAX_HEAD_HEIGHT_RATIO:
            violations.append(
                InvariantViolation(
                    invariant="head_height_not_grossly_large",
                    detail="The head fills the frame so completely that it is likely clipped.",
                    measured=head_height_ratio,
                    bound=_MAX_HEAD_HEIGHT_RATIO,
                )
            )

    if face_fully_inside is False:
        violations.append(
            InvariantViolation(
                invariant="face_inside_frame",
                detail="Part of the detected face falls outside the delivered frame.",
            )
        )

    if (
        largest_detached_fragment_ratio is not None
        and largest_detached_fragment_ratio > _MAX_DETACHED_FRAGMENT_RATIO
    ):
        violations.append(
            InvariantViolation(
                invariant="subject_is_connected",
                detail=(
                    "The matte retains a fragment detached from the subject, "
                    "which appears as material floating in the background."
                ),
                measured=largest_detached_fragment_ratio,
                bound=_MAX_DETACHED_FRAGMENT_RATIO,
            )
        )

    return InvariantReport(violations=violations)
