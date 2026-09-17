"""A photograph is never stretched to fit its output size.

Written after thirteen examinations publishing a preferred 200 x 230 received
3:4 crops squeezed into that frame. Negative first: the sweep resolves every
photograph record in the catalogue and composites crops of every plausible
shape, including ones that do not match the rule, and fails if any box would
be resized into a rectangle of a different shape.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from exam_photo.models.exam_rule import ExamRule
from exam_photo.models.geometry import BoundingBox
from exam_photo.orchestration.composite_frame import (
    ASPECT_TOLERANCE,
    fit_box_to_aspect,
    resolve_composite_frame,
)
from exam_photo.orchestration.rule_resolver import RuleResolutionError, resolve_rule
from exam_photo.providers.crop_planning import CropModeBConfig

REPO_ROOT = Path(__file__).resolve().parents[4]
CATALOGUE = REPO_ROOT / "examples" / "rules"


def _photograph_rules() -> list[ExamRule]:
    rules = []
    for path in sorted(CATALOGUE.glob("exam_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("fictional_example") or not data.get("image_requirements"):
            continue
        rules.append(ExamRule.model_validate(data))
    return rules


PHOTOGRAPH_RULES = _photograph_rules()


def test_the_catalogue_has_photograph_rules_to_sweep() -> None:
    assert len(PHOTOGRAPH_RULES) >= 50


def test_fit_trims_a_wide_box_about_its_centre() -> None:
    box = BoundingBox(left=100, top=50, right=400, bottom=450)  # 300 x 400
    fitted = fit_box_to_aspect(box, 0.5)
    assert fitted.height == pytest.approx(400)
    assert fitted.width == pytest.approx(200)
    assert (fitted.left + fitted.right) / 2 == pytest.approx(250)


def test_fit_trims_a_tall_box_from_the_bottom() -> None:
    box = BoundingBox(left=0, top=10, right=300, bottom=410)  # 300 x 400
    fitted = fit_box_to_aspect(box, 200 / 230)
    assert fitted.top == pytest.approx(10)
    assert fitted.width == pytest.approx(300)
    assert fitted.width / fitted.height == pytest.approx(200 / 230)


def test_a_preferred_size_is_planned_and_delivered_as_an_exact_size() -> None:
    """DEC-103. A preferred-only size goes through Crop Mode A at exactly its
    shape and is delivered at exactly its pixels. Pinning Mode B's aspect range
    to one value (DEC-090) failed every real photograph for these examinations,
    because a whole-pixel crop cannot hit it within the planner's tolerance."""
    planned = 0
    for rule in PHOTOGRAPH_RULES:
        assert rule.image_requirements is not None
        dim = rule.image_requirements.dimensions
        if dim.mode.value != "unspecified" or not (
            dim.preferred_width_px and dim.preferred_height_px
        ):
            continue
        plan = resolve_rule(rule)
        assert plan.crop_mode == "a"
        assert not isinstance(plan.crop_config, CropModeBConfig)
        assert plan.crop_config.target_width == dim.preferred_width_px
        assert plan.crop_config.target_height == dim.preferred_height_px
        assert plan.output_preparation_config.target_width == dim.preferred_width_px
        assert plan.output_preparation_config.target_height == dim.preferred_height_px
        planned += 1
    # Twelve since DEC-093 removed the RBI Assistant duplicate record.
    assert planned >= 12


@pytest.mark.parametrize("box_aspect", [0.55, 0.65, 0.70, 0.75, 0.80, 0.87, 0.95, 1.1])
def test_no_rule_composites_a_box_into_a_different_shape(box_aspect: float) -> None:
    swept = 0
    for rule in PHOTOGRAPH_RULES:
        try:
            plan = resolve_rule(rule)
        except RuleResolutionError:
            continue
        for height in (180.0, 530.0, 1600.0):
            crop = BoundingBox(
                left=37, top=21, right=37 + height * box_aspect, bottom=21 + height
            )
            width, out_height, box, _ = resolve_composite_frame(
                plan.output_preparation_config, crop
            )
            shape_error = abs(box.width / box.height - width / out_height)
            assert shape_error <= ASPECT_TOLERANCE, (
                f"{rule.exam.exam_id}: a {box.width:.0f}x{box.height:.0f} box "
                f"would be resized into {width}x{out_height}"
            )
            # Trimming only ever removes; it never reaches outside the crop.
            assert box.left >= crop.left - 1e-6 and box.right <= crop.right + 1e-6
            assert box.top >= crop.top - 1e-6 and box.bottom <= crop.bottom + 1e-6
            swept += 1
    assert swept > 0
