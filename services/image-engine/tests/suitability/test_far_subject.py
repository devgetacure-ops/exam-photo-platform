"""A face too far away to read closely is told to come closer (DEC-132)."""

from __future__ import annotations

import numpy as np

from exam_photo.models.geometry import BoundingBox, Landmarks, Point
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.suitability.far_subject import (
    head_outline_width,
    too_far_for_a_tight_crop,
)


def _face(width: float) -> FaceDetection:
    left = 100.0 - width / 2.0
    return FaceDetection(
        bounding_box=BoundingBox(
            left=left, top=80, right=left + width, bottom=80 + width
        ),
        confidence=0.9,
        landmarks=Landmarks(nose_tip=Point(x=100, y=80 + width * 0.55)),
    )


def _head_mask(head_width: int) -> np.ndarray:
    alpha = np.zeros((400, 200), dtype=np.float32)
    left = 100 - head_width // 2
    alpha[40:260, left : left + head_width] = 1.0
    return alpha


def test_outline_width_reads_the_head_between_box_top_and_nose() -> None:
    assert head_outline_width(_face(100), _head_mask(90)) == 89.0


def test_an_oversized_face_box_and_a_loose_crop_say_stand_closer() -> None:
    # The labelled far-away photograph: box 164 px over a 98 px head.
    assert too_far_for_a_tight_crop(_face(164), _head_mask(98), 0.57)


def test_a_far_photo_that_still_frames_well_is_left_alone() -> None:
    assert not too_far_for_a_tight_crop(_face(164), _head_mask(98), 0.82)


def test_a_loose_crop_with_an_honest_face_box_is_not_called_far() -> None:
    # A turned or tilted head frames loose for other reasons.
    assert not too_far_for_a_tight_crop(_face(100), _head_mask(110), 0.60)


def test_no_outline_in_the_band_says_nothing() -> None:
    empty = np.zeros((400, 200), dtype=np.float32)
    assert not too_far_for_a_tight_crop(_face(164), empty, 0.50)
    assert not too_far_for_a_tight_crop(_face(164), None, 0.50)
