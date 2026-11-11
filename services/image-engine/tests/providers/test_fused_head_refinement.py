from __future__ import annotations

import numpy as np
from PIL import Image

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.fused_head_refinement import FusedHeadRefiner
from exam_photo.providers.landmark_geometric_head_estimator import (
    LandmarkGeometricHeadEstimator,
)


def test_fused_head_refinement_does_not_follow_torso_foreground() -> None:
    image = Image.new("RGB", (220, 260), (240, 240, 240))
    face = FaceDetection(
        bounding_box=BoundingBox(left=80, top=80, right=140, bottom=150),
        confidence=0.98,
    )
    geometric = LandmarkGeometricHeadEstimator().estimate_head(image, face, None)

    alpha = np.zeros((260, 220), dtype=np.float32)
    alpha[30:170, 65:155] = 1.0
    alpha[170:255, 90:130] = 1.0

    refined = FusedHeadRefiner().refine_head_estimation(
        image=image,
        face=face,
        head_result=geometric,
        alpha_mask=alpha,
    )

    assert refined.head_bounding_box.bottom <= geometric.head_bounding_box.bottom
    assert refined.head_bounding_box.bottom < 200
    assert refined.head_bounding_box.contains(face.bounding_box)


def test_collar_touching_the_beard_does_not_widen_or_lengthen_the_head() -> None:
    """A shirt collar that rises beside the jaw is not head (DEC-131).

    The owner's own photograph (JEE Main, 11 November 2026): the head measured
    about 219 px across to the mouth, but the dark collar met the beard above
    the landmark chin, the old width band ran to the bottom of the face box and
    took in the collar, and the head box came out 355 px wide and reaching into
    the shirt. The crop sized itself to that and the head filled 61% of the
    frame instead of about 85%.
    """
    from exam_photo.models.geometry import Landmarks, Point

    image = Image.new("RGB", (240, 280), (240, 240, 240))
    face = FaceDetection(
        bounding_box=BoundingBox(left=80, top=80, right=150, bottom=158),
        confidence=0.98,
        landmarks=Landmarks(
            left_eye=Point(x=130, y=105),
            right_eye=Point(x=100, y=105),
            nose_tip=Point(x=115, y=122),
            chin=Point(x=115, y=150),
            custom_landmarks={"mouth_center": Point(x=115, y=135)},
        ),
    )
    geometric = LandmarkGeometricHeadEstimator().estimate_head(image, face, None)

    alpha = np.zeros((280, 240), dtype=np.float32)
    alpha[40:152, 72:158] = 1.0  # hair, face and beard: 86 px wide
    alpha[142:280, 20:220] = 1.0  # collar and shirt, rising above the chin

    refined = FusedHeadRefiner().refine_head_estimation(
        image=image,
        face=face,
        head_result=geometric,
        alpha_mask=alpha,
    )
    box = refined.head_bounding_box

    assert box.left >= 72 - 1 and box.right <= 158 + 1
    # Kept to the chin and a beard's margin, not the shirt below it.
    assert box.bottom <= 170
    assert box.bottom >= 150
    assert box.contains(face.bounding_box)


def test_a_beard_on_a_narrow_neck_is_kept_whole() -> None:
    """Below the mouth, only a sudden widening ends the head; a beard does not."""
    from exam_photo.models.geometry import Landmarks, Point

    image = Image.new("RGB", (240, 300), (240, 240, 240))
    face = FaceDetection(
        bounding_box=BoundingBox(left=80, top=80, right=150, bottom=158),
        confidence=0.98,
        landmarks=Landmarks(
            left_eye=Point(x=130, y=105),
            right_eye=Point(x=100, y=105),
            nose_tip=Point(x=115, y=122),
            chin=Point(x=115, y=150),
            custom_landmarks={"mouth_center": Point(x=115, y=135)},
        ),
    )
    geometric = LandmarkGeometricHeadEstimator().estimate_head(image, face, None)

    alpha = np.zeros((300, 240), dtype=np.float32)
    alpha[40:150, 72:158] = 1.0  # head
    alpha[150:185, 85:145] = 1.0  # beard, narrower than the head
    alpha[185:300, 95:135] = 1.0  # neck

    before = FusedHeadRefiner().refine_head_estimation(
        image=image, face=face, head_result=geometric, alpha_mask=alpha
    )
    assert before.head_bounding_box.bottom >= 180


def test_a_shoulder_rising_on_one_side_above_the_mouth_is_not_head() -> None:
    """A leaning subject's shoulder can rise past the mouth on one side.

    Labelled photograph 25: the shoulder entered above the mouth line, so a
    width read down to the mouth still took it in, and the lopsided head box
    made tall frames looser. The head's span is read down to the nose only.
    """
    from exam_photo.models.geometry import Landmarks, Point

    image = Image.new("RGB", (240, 280), (240, 240, 240))
    face = FaceDetection(
        bounding_box=BoundingBox(left=80, top=80, right=150, bottom=158),
        confidence=0.98,
        landmarks=Landmarks(
            left_eye=Point(x=130, y=105),
            right_eye=Point(x=100, y=105),
            nose_tip=Point(x=115, y=122),
            chin=Point(x=115, y=150),
            custom_landmarks={"mouth_center": Point(x=115, y=135)},
        ),
    )
    geometric = LandmarkGeometricHeadEstimator().estimate_head(image, face, None)

    alpha = np.zeros((280, 240), dtype=np.float32)
    alpha[40:152, 72:158] = 1.0  # head
    alpha[128:280, 30:120] = 1.0  # left shoulder, rising above the mouth

    refined = FusedHeadRefiner().refine_head_estimation(
        image=image, face=face, head_result=geometric, alpha_mask=alpha
    )
    assert refined.head_bounding_box.left >= 71
    assert refined.head_bounding_box.contains(face.bounding_box)
