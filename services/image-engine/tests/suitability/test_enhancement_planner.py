"""Tests for natural enhancement planning (DEC-043).

The load-bearing test here is ``test_a_correctly_exposed_dark_face_is_untouched``:
enhancement must correct capture defects and never move a subject toward a
target appearance, because the latter is skin lightening.
"""

from __future__ import annotations

from exam_photo.suitability.enhancement_planner import (
    FaceToneMeasurements,
    plan_enhancement,
    severe_cast_detected,
)


def face(**overrides: object) -> FaceToneMeasurements:
    base: dict[str, object] = {
        "mean_luminance": 118.0,
        "tonal_range_p5_p95": 140.0,
        "shadow_clipped_fraction": 0.02,
        "highlight_clipped_fraction": 0.01,
        "blue_minus_red": -50.0,
        "sharpness": 200.0,
        "is_monochrome": False,
    }
    base.update(overrides)
    return FaceToneMeasurements(**base)  # type: ignore[arg-type]


def test_a_good_capture_gets_no_enhancement() -> None:
    plan = plan_enhancement(face())
    assert plan.is_noop
    assert plan.brightness_adjustment == 1.0
    assert plan.contrast_adjustment == 1.0
    assert plan.sharpness_adjustment == 1.0


def test_a_correctly_exposed_dark_face_is_untouched() -> None:
    """The contract boundary: dark skin is not a defect.

    A low mean luminance with a healthy tonal range is a correctly exposed
    dark-skinned subject. Brightening it would be skin lightening, which the
    identity-preservation principle prohibits outright.
    """
    plan = plan_enhancement(
        face(
            mean_luminance=62.0, tonal_range_p5_p95=145.0, shadow_clipped_fraction=0.05
        )
    )
    assert plan.is_noop
    assert plan.brightness_adjustment == 1.0


def test_a_flat_capture_is_stretched() -> None:
    plan = plan_enhancement(face(tonal_range_p5_p95=40.0))
    assert plan.contrast_adjustment > 1.0
    assert "lifted flat contrast" in plan.applied


def test_no_adjustment_exceeds_its_cap() -> None:
    plan = plan_enhancement(
        face(
            tonal_range_p5_p95=5.0,
            shadow_clipped_fraction=0.95,
            sharpness=1.0,
        )
    )
    assert plan.contrast_adjustment <= 1.12
    assert plan.brightness_adjustment <= 1.12
    assert plan.sharpness_adjustment <= 1.20


def test_crushed_shadows_are_lifted_and_blown_highlights_pulled_down() -> None:
    lifted = plan_enhancement(face(shadow_clipped_fraction=0.40))
    assert lifted.brightness_adjustment > 1.0
    pulled = plan_enhancement(face(highlight_clipped_fraction=0.30))
    assert pulled.brightness_adjustment < 1.0


def test_blue_cast_is_partly_corrected() -> None:
    """Photograph 24: blue stage lighting, measured +58.8 against a normal
    range of -38 to -88."""
    plan = plan_enhancement(face(blue_minus_red=58.8))
    assert 0.0 < plan.cast_correction_strength <= 0.5
    assert "reduced colour cast from the lighting" in plan.applied
    assert severe_cast_detected(face(blue_minus_red=58.8))


def test_ordinary_warm_skin_is_not_treated_as_a_cast() -> None:
    """Red-dominant is what skin looks like; it is never a defect."""
    assert plan_enhancement(face(blue_minus_red=-87.8)).is_noop
    assert not severe_cast_detected(face(blue_minus_red=-87.8))


def test_monochrome_is_never_cast_corrected() -> None:
    """A greyscale photograph has zero channel difference by construction,
    which says nothing about its lighting."""
    plan = plan_enhancement(face(blue_minus_red=0.0, is_monochrome=True))
    assert plan.cast_correction_strength == 0.0
    assert not severe_cast_detected(face(blue_minus_red=0.0, is_monochrome=True))


def test_soft_capture_is_sharpened() -> None:
    plan = plan_enhancement(face(sharpness=48.0))
    assert 1.0 < plan.sharpness_adjustment <= 1.20
    assert "sharpened a soft image" in plan.applied


def test_every_adjustment_is_disclosed() -> None:
    plan = plan_enhancement(
        face(tonal_range_p5_p95=40.0, shadow_clipped_fraction=0.4, sharpness=48.0)
    )
    assert len(plan.applied) == 3
