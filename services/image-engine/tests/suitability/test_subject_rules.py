"""What a photograph must be of (DEC-133)."""

from __future__ import annotations

import numpy as np
from PIL import Image

from exam_photo.models.geometry import BoundingBox, Landmarks, Point
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.subject_checks import VerifiedFace
from exam_photo.suitability.subject_rules import (
    chest_skin_fraction,
    real_face_confirmed,
    second_person_present,
)

SUBJECT = BoundingBox(left=100, top=100, right=200, bottom=200)


def _face(left: float, top: float, size: float, score: float) -> VerifiedFace:
    return VerifiedFace(
        box=BoundingBox(left=left, top=top, right=left + size, bottom=top + size),
        score=score,
    )


def test_a_real_face_where_the_subject_is_confirms_it() -> None:
    assert real_face_confirmed([_face(110, 110, 80, 0.93)], SUBJECT)


def test_an_object_blazeface_mistook_for_a_face_is_not_confirmed() -> None:
    # A bottle or a football: YuNet finds nothing, or nothing it believes.
    assert not real_face_confirmed([], SUBJECT)
    assert not real_face_confirmed([_face(110, 110, 80, 0.38)], SUBJECT)


def test_a_real_face_somewhere_else_does_not_confirm_the_subject() -> None:
    assert not real_face_confirmed([_face(400, 400, 80, 0.95)], SUBJECT)


def test_a_second_clear_face_of_similar_size_is_a_second_person() -> None:
    assert second_person_present([_face(0, 0, 100, 0.94), _face(200, 0, 43, 0.94)])


def test_a_small_or_doubtful_second_detection_is_not() -> None:
    # Labelled photograph 20: a 0.84 detection at a third of the face's height.
    assert not second_person_present([_face(0, 0, 100, 0.93), _face(200, 0, 32, 0.84)])
    assert not second_person_present([_face(0, 0, 100, 0.93), _face(200, 0, 90, 0.68)])
    assert not second_person_present([_face(0, 0, 100, 0.93)])


def _portrait(
    chest_rgb: tuple[int, int, int], skin=(196, 140, 110)
) -> tuple[Image.Image, FaceDetection]:
    canvas = np.full((400, 300, 3), 240, dtype=np.uint8)
    canvas[60:200, 100:200] = skin  # face
    canvas[230:400, 60:240] = chest_rgb  # chest
    face = FaceDetection(
        bounding_box=BoundingBox(left=100, top=60, right=200, bottom=200),
        confidence=0.9,
        landmarks=Landmarks(
            left_eye=Point(x=170, y=110),
            right_eye=Point(x=130, y=110),
            chin=Point(x=150, y=190),
        ),
    )
    return Image.fromarray(canvas), face


def test_a_bare_chest_matches_the_face_and_a_shirt_does_not() -> None:
    bare, face = _portrait((196, 140, 110))
    shirt, _ = _portrait((30, 60, 140))
    assert (chest_skin_fraction(bare, face, None) or 0) > 0.9
    assert (chest_skin_fraction(shirt, face, None) or 0) < 0.05


def test_black_and_white_is_not_judged() -> None:
    grey, face = _portrait((120, 120, 120), skin=(150, 150, 150))
    assert chest_skin_fraction(grey, face, None) is None
