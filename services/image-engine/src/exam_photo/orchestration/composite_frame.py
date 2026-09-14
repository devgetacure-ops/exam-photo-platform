"""The pixel size a crop is composited at, and the box that fills it exactly.

The composite resizes one box of the source into one output rectangle. If the
two do not share a shape, the resize distorts the face, and nothing after this
point can notice: the output preparer sees an image already at the target size
and passes it. That is how a 3:4 crop was delivered squeezed into 200 x 230
for thirteen examinations.

So the rule lives here, in one pure function the pipeline calls and the tests
sweep: the output size is resolved from the box that will actually be
composited, and if the rule's size still cannot hold that box's shape, the box
is trimmed to the target shape -- never the image stretched to fit.
"""

from __future__ import annotations

from typing import Optional

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.output_preparation import OutputPreparationConfig
from exam_photo.providers.output_preparers.deterministic_output_preparer import (
    DeterministicOutputPreparer,
)

#: Largest difference in width/height ratio resized without trimming. At a
#: 0.87 portrait this is about 0.6%, well under a pixel of distortion across a
#: face at any output size the catalogue asks for, and it absorbs the rounding
#: of a crop box to whole pixels.
ASPECT_TOLERANCE = 0.005


def fit_box_to_aspect(box: BoundingBox, aspect: float) -> BoundingBox:
    """The largest box of ``aspect`` (width / height) inside ``box``.

    A box too wide loses width equally from both sides, keeping the face
    centred. A box too tall loses height from the bottom, because the top of a
    portrait crop is the head and the bottom is torso.
    """
    if aspect <= 0 or box.width <= 0 or box.height <= 0:
        return box
    current = box.width / box.height
    if abs(current - aspect) <= 1e-9:
        return box
    if current > aspect:
        width = box.height * aspect
        inset = (box.width - width) / 2.0
        return BoundingBox(
            left=box.left + inset,
            top=box.top,
            right=box.right - inset,
            bottom=box.bottom,
        )
    height = box.width / aspect
    return BoundingBox(
        left=box.left,
        top=box.top,
        right=box.right,
        bottom=box.top + height,
    )


def resolve_composite_frame(
    prep: Optional[OutputPreparationConfig], crop_box: BoundingBox
) -> tuple[int, int, BoundingBox, bool]:
    """Output width, height, the box to composite, and whether it was trimmed."""
    target_w = prep.target_width if prep else None
    target_h = prep.target_height if prep else None
    if target_w is None or target_h is None:
        if prep is None:
            target_w, target_h = 300, 400
        else:
            assert prep.min_width is not None and prep.max_width is not None
            assert prep.min_height is not None and prep.max_height is not None
            resolved_w, resolved_h, _ = (
                DeterministicOutputPreparer()._resolve_range_dimensions(
                    source_width=max(1, int(round(crop_box.width))),
                    source_height=max(1, int(round(crop_box.height))),
                    min_w=prep.min_width,
                    max_w=prep.max_width,
                    min_h=prep.min_height,
                    max_h=prep.max_height,
                    pref_w=prep.preferred_width,
                    pref_h=prep.preferred_height,
                )
            )
            assert resolved_w is not None and resolved_h is not None
            target_w, target_h = resolved_w, resolved_h

    target_aspect = target_w / target_h
    box_aspect = crop_box.width / crop_box.height if crop_box.height else 0.0
    if abs(box_aspect - target_aspect) > ASPECT_TOLERANCE:
        return target_w, target_h, fit_box_to_aspect(crop_box, target_aspect), True
    return target_w, target_h, crop_box, False
