"""Tests for the accept / warn / block disposition policy (DEC-041).

These run without any model: the policy consumes measurements, not pixels.
Thresholds referenced here are the ones calibrated against the 40-photo
adversarial set, and the cases named after specific photographs are the ones
that motivated each rule.
"""

from __future__ import annotations

import pytest

from exam_photo.suitability.disposition import (
    AppearanceSignals,
    Disposition,
    FindingLevel,
    evaluate_disposition,
)
from exam_photo.suitability.issue_codes import SuitabilityIssueCode


def signals(**overrides: object) -> AppearanceSignals:
    base: dict[str, object] = {
        "image_width": 960,
        "image_height": 1280,
        "face_count": 1,
        "detection_confidence": 0.5,
        "primary_face_height_px": 260.0,
        "second_face_height_ratio": 0.0,
        "landmarks_available": True,
        "yaw_degrees": 0.0,
        "pitch_degrees": 0.0,
        "roll_degrees": 0.0,
        "mean_luminance": 130.0,
        "dark_pixel_fraction": 0.05,
        "mean_saturation": 35.0,
    }
    base.update(overrides)
    return AppearanceSignals(**base)  # type: ignore[arg-type]


def test_clean_photograph_is_accepted_silently() -> None:
    report = evaluate_disposition(signals())
    assert report.disposition is Disposition.ACCEPT
    assert report.findings == []


def test_no_face_blocks() -> None:
    report = evaluate_disposition(signals(face_count=0))
    assert report.disposition is Disposition.BLOCK
    assert report.findings[0].code is SuitabilityIssueCode.SUITABILITY_NO_FACE


def test_two_comparable_faces_block() -> None:
    """Photograph 3 and 21: two people, genuinely ambiguous subject."""
    report = evaluate_disposition(
        signals(face_count=2, second_face_height_ratio=0.98, detection_confidence=0.5)
    )
    assert report.disposition is Disposition.BLOCK
    assert report.findings[0].code is SuitabilityIssueCode.SUITABILITY_MULTIPLE_FACES


def test_low_confidence_second_face_does_not_block() -> None:
    """Photograph 36: a printed banner yields a spurious second face at 0.15.

    Blocking on it would reject a perfectly usable single-person photograph,
    which is the false-block cost the policy exists to avoid.
    """
    report = evaluate_disposition(
        signals(face_count=2, second_face_height_ratio=0.95, detection_confidence=0.15)
    )
    assert report.disposition is not Disposition.BLOCK


def test_small_bystander_does_not_block() -> None:
    """A distant person in the background is not ambiguity about the subject."""
    report = evaluate_disposition(
        signals(face_count=2, second_face_height_ratio=0.20, detection_confidence=0.5)
    )
    assert report.disposition is not Disposition.BLOCK


def test_severe_underexposure_warns_but_still_produces() -> None:
    """A genuinely dark FACE, not merely a dark frame."""
    report = evaluate_disposition(
        signals(mean_luminance=38.0, dark_pixel_fraction=0.55)
    )
    assert report.disposition is Disposition.WARN
    assert report.likely_rejections
    assert (
        report.likely_rejections[0].code
        is SuitabilityIssueCode.SUITABILITY_UNDEREXPOSED_SEVERE
    )


def test_ordinary_dim_photograph_is_not_flagged() -> None:
    """Photographs 18 and 19: frame luminance 29 but face luminance 93."""
    report = evaluate_disposition(
        signals(mean_luminance=93.0, dark_pixel_fraction=0.23)
    )
    assert report.disposition is Disposition.ACCEPT


def test_missing_landmarks_on_a_confident_face_is_extreme_pose() -> None:
    """Photograph 7: a true side profile the dense landmarker cannot read."""
    report = evaluate_disposition(
        signals(landmarks_available=False, detection_confidence=0.5)
    )
    assert report.disposition is Disposition.WARN
    assert any(
        f.code is SuitabilityIssueCode.SUITABILITY_POSE_EXTREME
        for f in report.likely_rejections
    )


def test_missing_landmarks_on_a_weak_detection_is_not_reported() -> None:
    """Below the blocking-confidence tier the detection itself is unreliable,
    so the absence of landmarks says nothing about the subject's pose."""
    report = evaluate_disposition(
        signals(landmarks_available=False, detection_confidence=0.15)
    )
    assert all(
        f.code is not SuitabilityIssueCode.SUITABILITY_POSE_EXTREME
        for f in report.findings
    )


@pytest.mark.parametrize("yaw", [21.0, -21.0])
def test_moderate_yaw_is_only_a_possible_issue(yaw: float) -> None:
    report = evaluate_disposition(signals(yaw_degrees=yaw))
    assert report.disposition is Disposition.WARN
    assert report.findings[0].level is FindingLevel.POSSIBLE_ISSUE
    assert report.likely_rejections == []


def test_extreme_yaw_is_a_likely_rejection() -> None:
    report = evaluate_disposition(signals(yaw_degrees=40.0))
    assert report.likely_rejections
    assert (
        report.likely_rejections[0].code
        is SuitabilityIssueCode.SUITABILITY_POSE_EXTREME
    )


def test_monochrome_flagged_only_when_the_exam_requires_colour() -> None:
    """Photograph 39 reads saturation 0.0; the least saturated colour
    photograph in the set reads 13.5."""
    mono = signals(mean_saturation=0.0)
    assert evaluate_disposition(mono, monochrome_accepted=False).likely_rejections
    assert evaluate_disposition(mono, monochrome_accepted=True).findings == []
    # Unspecified is not permission and not prohibition: it produces nothing.
    assert evaluate_disposition(mono, monochrome_accepted=None).findings == []


def test_small_face_warns_about_enlargement() -> None:
    report = evaluate_disposition(
        signals(
            primary_face_height_px=180.0,
            target_height_px=1800,
            target_head_height_ratio=0.85,
        )
    )
    assert report.disposition is Disposition.WARN
    finding = report.findings[0]
    assert finding.code is SuitabilityIssueCode.SUITABILITY_RESOLUTION_WARNING
    assert finding.level is FindingLevel.POSSIBLE_ISSUE
    assert finding.measured_value is not None and finding.measured_value > 2.0


def test_a_large_source_face_needs_no_enlargement_warning() -> None:
    report = evaluate_disposition(
        signals(
            primary_face_height_px=900.0,
            target_height_px=1800,
            target_head_height_ratio=0.85,
        )
    )
    assert report.disposition is Disposition.ACCEPT


def test_appearance_never_blocks() -> None:
    """The engine's public contract: only an unusable or ambiguous photograph
    is refused. Every appearance defect stacked together still produces."""
    report = evaluate_disposition(
        signals(
            mean_luminance=20.0,
            dark_pixel_fraction=0.9,
            yaw_degrees=50.0,
            mean_saturation=0.0,
            primary_face_height_px=100.0,
            target_height_px=1800,
            target_head_height_ratio=0.85,
        ),
        monochrome_accepted=False,
    )
    assert report.disposition is Disposition.WARN
    assert len(report.likely_rejections) >= 3
