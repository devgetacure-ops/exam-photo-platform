"""Decide what natural enhancement a photograph actually needs (DEC-043).

The governing principle is **correct the capture defect, never the subject.**
Every adjustment here is relative to the photograph's own rendering: a flat
image is stretched back toward the range it should have had, a colour-cast
image has its *illuminant* neutralised, a soft image is sharpened. None of them
move the subject toward a target appearance.

That distinction is not stylistic, it is a hard contract boundary.  An
"enhancement" that drove every face toward some absolute target luminance would
lighten dark skin, which the identity-preservation principle prohibits
outright.  A correctly exposed dark-skinned subject must come out of this
module completely untouched, and the tests assert exactly that.

Deliberately NOT derived from the photographs a reviewer labelled "perfect":
those labels record pose, quality and compliance, not lighting.  Treating their
measured luminance as a target would import whatever lighting they happened to
have as a specification.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

# Caps on any single adjustment.  These mirror the output preparer's own
# conservative limits: enough to make a visible difference, not enough to look
# processed.
_MAX_BRIGHTNESS_DELTA = 0.12
_MAX_CONTRAST_DELTA = 0.12
_MAX_SHARPNESS_DELTA = 0.20

# A face using less than this much of the tonal range is flat enough that a
# gentle stretch is a correction rather than a stylistic choice.  Measured
# across the 40-photo set, the two softest/flattest faces use 37 and 42 levels
# of range while ordinary captures use 115-190.
_FLAT_RANGE_P5_P95 = 90.0
_HEALTHY_RANGE_P5_P95 = 140.0

# Clipping is a defect in either direction and is corrected away from the
# clipped end only.
_SHADOW_CLIP_FRACTION = 0.20
_HIGHLIGHT_CLIP_FRACTION = 0.10

# Human skin under a neutral illuminant is red-dominant: across all 40
# photographs the red channel leads blue by 38 to 88 levels.  A face where blue
# approaches or exceeds red is lit by a coloured source, not merely
# dark-skinned -- the sign of the difference is a property of the illuminant,
# not of the subject, which is what makes this safe to correct.
_CAST_NEUTRAL_MARGIN = -10.0
_SEVERE_CAST_MARGIN = 35.0

# Normalised face sharpness below which a bounded sharpen helps.  Same measure
# and calibration as the blur warning.
_SOFT_SHARPNESS = 97.0


class EnhancementPlan(BaseModel):
    """What to apply, and what to tell the candidate was applied."""

    model_config = ConfigDict(extra="forbid")

    brightness_adjustment: float = 1.0
    contrast_adjustment: float = 1.0
    sharpness_adjustment: float = 1.0
    # Fraction of the measured colour cast to remove, 0.0-1.0.
    cast_correction_strength: float = 0.0
    # Human-readable disclosure, one entry per adjustment actually made.
    applied: List[str] = Field(default_factory=list)

    @property
    def is_noop(self) -> bool:
        return not self.applied


class FaceToneMeasurements(BaseModel):
    """Photometric measurements of the face region only."""

    model_config = ConfigDict(extra="forbid")

    mean_luminance: float
    tonal_range_p5_p95: float
    shadow_clipped_fraction: float = 0.0
    highlight_clipped_fraction: float = 0.0
    blue_minus_red: Optional[float] = None
    sharpness: Optional[float] = None
    is_monochrome: bool = False


def _clamp(value: float, limit: float) -> float:
    return max(1.0 - limit, min(1.0 + limit, value))


def plan_enhancement(face: FaceToneMeasurements) -> EnhancementPlan:
    """Return the smallest set of corrections this photograph actually needs.

    Returns a no-op plan for a photograph with no measurable deficit, which is
    the common case and the intended one.
    """
    plan = EnhancementPlan()

    # --- Tonal range: stretch a flat capture, do not brighten a dark subject ---
    #
    # The trigger is compressed *range*, not low luminance. A correctly exposed
    # dark-skinned face has a normal range and is left alone; a hazy or
    # low-contrast capture of any subject has a compressed one and is stretched.
    if face.tonal_range_p5_p95 < _FLAT_RANGE_P5_P95:
        shortfall = (
            _HEALTHY_RANGE_P5_P95 - face.tonal_range_p5_p95
        ) / _HEALTHY_RANGE_P5_P95
        plan.contrast_adjustment = _clamp(1.0 + shortfall, _MAX_CONTRAST_DELTA)
        plan.applied.append("lifted flat contrast")

    # --- Clipping: correct only away from the clipped end ---
    if face.shadow_clipped_fraction > _SHADOW_CLIP_FRACTION:
        plan.brightness_adjustment = _clamp(
            1.0 + face.shadow_clipped_fraction, _MAX_BRIGHTNESS_DELTA
        )
        plan.applied.append("recovered crushed shadows")
    elif face.highlight_clipped_fraction > _HIGHLIGHT_CLIP_FRACTION:
        plan.brightness_adjustment = _clamp(
            1.0 - face.highlight_clipped_fraction, _MAX_BRIGHTNESS_DELTA
        )
        plan.applied.append("recovered blown highlights")

    # --- Colour cast: neutralise the light source ---
    #
    # Skipped entirely for a monochrome photograph, where the channel
    # difference is zero by construction and means nothing about the lighting.
    if (
        not face.is_monochrome
        and face.blue_minus_red is not None
        and face.blue_minus_red > _CAST_NEUTRAL_MARGIN
    ):
        excess = face.blue_minus_red - _CAST_NEUTRAL_MARGIN
        # Partial by design. Fully neutralising a severe stage-lit cast invents
        # colour the sensor never recorded; halving it looks natural and honest.
        plan.cast_correction_strength = min(0.5, excess / 100.0)
        plan.applied.append("reduced colour cast from the lighting")

    # --- Focus: bounded sharpen for a soft capture ---
    if face.sharpness is not None and face.sharpness < _SOFT_SHARPNESS:
        shortfall = (_SOFT_SHARPNESS - face.sharpness) / _SOFT_SHARPNESS
        plan.sharpness_adjustment = _clamp(1.0 + shortfall, _MAX_SHARPNESS_DELTA)
        plan.applied.append("sharpened a soft image")

    return plan


def severe_cast_detected(face: FaceToneMeasurements) -> bool:
    """Whether the cast is too strong for correction alone to rescue.

    Measured: one photograph lit by blue stage lighting reads +58.8, while the
    next most cast reads +20.1 and ordinary captures run -38 to -88. At that
    magnitude the correction is disclosed *and* the candidate is warned, because
    a half-corrected stage-lit face is still not a compliant portrait.
    """
    return (
        not face.is_monochrome
        and face.blue_minus_red is not None
        and face.blue_minus_red > _SEVERE_CAST_MARGIN
    )
