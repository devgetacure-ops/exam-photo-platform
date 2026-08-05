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
