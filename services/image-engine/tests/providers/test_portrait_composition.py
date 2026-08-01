from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.crop_planners.deterministic_crop_mode_b_planner import (
    DeterministicCropModeBPlanner,
)
from exam_photo.providers.crop_planners.deterministic_crop_planner import (
    DeterministicCropPlanner,
)
from exam_photo.providers.crop_planning import CropConfig, CropModeBConfig, CropProfile
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.portrait_composition import (
    DeterministicPortraitCompositionEstimator,
)
from tests.fakes.fake_head_estimator import FakeHeadEstimator


def test_portrait_composition_ignores_lower_torso_foreground() -> None:
    image = Image.new("RGB", (600, 800), "white")
    face = FaceDetection(
        bounding_box=BoundingBox(left=240, top=250, right=360, bottom=370),
        confidence=0.99,
    )
    head_result = FakeHeadEstimator(
        bounding_box=BoundingBox(left=205, top=145, right=395, bottom=430)
    ).estimate_head(image, face)

    alpha = np.zeros((800, 600), dtype=np.float32)
    alpha[145:430, 205:395] = 1.0
    alpha[430:760, 110:500] = 1.0

    result = DeterministicPortraitCompositionEstimator().estimate_composition(
        image=image,
        face=face,
        head_result=head_result,
        alpha_mask=alpha,
    )

    assert result.preservation_box.top == pytest.approx(145)
    assert result.preservation_box.left <= 205
    assert result.preservation_box.right >= 395
    assert result.preservation_box.bottom <= result.lower_body_exclusion_y
    assert result.preservation_box.bottom < 500
    assert result.signal_summary["alpha_observed"] is True


def test_crop_mode_a_uses_portrait_composition_not_torso_mask_for_framing() -> None:
    image = Image.new("RGB", (600, 800), "white")
    face = FaceDetection(
        bounding_box=BoundingBox(left=240, top=250, right=360, bottom=370),
        confidence=0.99,
    )
    head_result = FakeHeadEstimator(
        bounding_box=BoundingBox(left=205, top=145, right=395, bottom=430)
    ).estimate_head(image, face)

    alpha = np.zeros((800, 600), dtype=np.float32)
    alpha[145:430, 205:395] = 1.0
    alpha[430:760, 110:500] = 1.0
    portrait_composition = (
        DeterministicPortraitCompositionEstimator().estimate_composition(
            image=image,
            face=face,
            head_result=head_result,
            alpha_mask=alpha,
        )
    )

    mask = Image.fromarray((alpha * 255).astype(np.uint8), mode="L")
    cfg = CropConfig(
        target_width=300,
        target_height=400,
        crop_profile=CropProfile.TIGHT_EXAM_PORTRAIT,
        target_head_height_ratio=0.76,
        minimum_head_height_ratio=0.70,
        maximum_head_height_ratio=0.82,
        maximum_torso_inclusion_ratio=0.20,
        allow_padding=True,
    )
    result = DeterministicCropPlanner().plan_crop(
        image_width=image.width,
        image_height=image.height,
        face=face,
        head_estimate=head_result.head_bounding_box,
        refined_mask=mask,
        portrait_composition=portrait_composition,
        config=cfg,
    )

    assert result.portrait_composition_box == portrait_composition.preservation_box
    assert result.head_height_ratio == pytest.approx(0.76, abs=0.03)
    assert result.torso_inclusion_ratio is not None
    assert result.torso_inclusion_ratio <= 0.20
    assert result.crop_box.bottom < 580


def test_crop_mode_b_uses_portrait_composition_not_torso_mask_for_framing() -> None:
    image = Image.new("RGB", (600, 800), "white")
    face = FaceDetection(
        bounding_box=BoundingBox(left=240, top=250, right=360, bottom=370),
        confidence=0.99,
    )
    head_result = FakeHeadEstimator(
        bounding_box=BoundingBox(left=205, top=145, right=395, bottom=430)
    ).estimate_head(image, face)

    alpha = np.zeros((800, 600), dtype=np.float32)
    alpha[145:430, 205:395] = 1.0
    alpha[430:760, 110:500] = 1.0
    portrait_composition = (
        DeterministicPortraitCompositionEstimator().estimate_composition(
            image=image,
            face=face,
            head_result=head_result,
            alpha_mask=alpha,
        )
    )

    mask = Image.fromarray((alpha * 255).astype(np.uint8), mode="L")
    result = DeterministicCropModeBPlanner().plan_crop(
        image_width=image.width,
        image_height=image.height,
        face=face,
        head_estimate=head_result.head_bounding_box,
        refined_mask=mask,
        portrait_composition=portrait_composition,
        config=CropModeBConfig(
            target_head_height_ratio=0.76,
            min_head_height_ratio=0.70,
            max_head_height_ratio=0.82,
            allow_padding=True,
        ),
    )

    assert result.portrait_composition_box == portrait_composition.preservation_box
    assert result.head_height_ratio == pytest.approx(0.76, abs=0.03)
    assert result.torso_inclusion_ratio is not None
    assert result.torso_inclusion_ratio < 0.25
