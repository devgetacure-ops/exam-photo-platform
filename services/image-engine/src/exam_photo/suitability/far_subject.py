"""A photograph taken too far away to frame tightly (DEC-132).

When a face is small in the photograph the detector cannot read it closely and
draws a box much wider than the head the subject mask actually shows. The crop
then has to keep that box, and the head ends up small in the finished photo.
The engine does not try to second-guess the detector here: it delivers the
photo and tells the candidate to stand closer.

Measured on the 40 labelled photographs: the two far-away photographs whose
crops came out loose had a face box 1.52x and 1.67x the width of the head's
outline; every other photograph was at 1.18x or less. 1.35 sits between. The
note also needs the head to fill under 75% of the finished frame, the
coverage floor, so a far-away photograph that still frames well is left alone,
and a turned or tilted head that frames loose is never told to stand closer.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np

from exam_photo.providers.face_detection import FaceDetection

FACE_BOX_OVER_HEAD_RATIO = 1.35
HEAD_FILL_FLOOR = 0.75


def head_outline_width(
    face: FaceDetection, alpha_mask: Optional[np.ndarray[Any, Any]]
) -> float:
    """Widest row of the subject mask between the face box top and the nose.

    Only hair, ears and face can be there. Returns 0 when the mask shows
    nothing in that band, which happens when the coarse matte misses the head.
    """
    if alpha_mask is None or alpha_mask.ndim != 2 or alpha_mask.size == 0:
        return 0.0
    mask = alpha_mask.astype(np.float32, copy=False)
    threshold = 0.5 if float(mask.max(initial=0.0)) <= 1.01 else 127.5
    height, width = mask.shape
    box = face.bounding_box
    landmarks = face.landmarks
    nose_y = (
        landmarks.nose_tip.y
        if landmarks is not None and landmarks.nose_tip is not None
        else box.top + box.height / 2.0
    )
    y0 = max(0, int(round(box.top)))
    y1 = min(height, max(y0 + 1, int(round(nose_y))))
    x0 = max(0, int(round(box.left - 0.40 * box.width)))
    x1 = min(width, int(round(box.right + 0.40 * box.width)))
    widest = 0
    for y in range(y0, y1):
        xs = np.flatnonzero(mask[y, x0:x1] > threshold)
        if len(xs) > 0:
            widest = max(widest, int(xs[-1] - xs[0]))
    return float(widest)


def too_far_for_a_tight_crop(
    face: FaceDetection,
    alpha_mask: Optional[np.ndarray[Any, Any]],
    head_height_ratio: Optional[float],
) -> bool:
    """True when the face is too small to read and the crop came out loose."""
    if head_height_ratio is None or head_height_ratio >= HEAD_FILL_FLOOR:
        return False
    outline = head_outline_width(face, alpha_mask)
    if outline <= 0.0:
        return False
    return face.bounding_box.width > FACE_BOX_OVER_HEAD_RATIO * outline
