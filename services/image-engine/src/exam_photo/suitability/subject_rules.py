"""What a photograph must be of to be prepared (DEC-133).

Each threshold below is stated with the separation measured on the 40
labelled photographs, the owner's own photograph, an Instagram collage and 31
public-domain images of objects, animals, paintings and groups.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

import numpy as np
from PIL import Image

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.subject_checks import VerifiedFace

# A real face scores 0.85-0.95 on every real photograph in the set; objects
# BlazeFace mistook for a face (a bottle, a charger, a football, a laptop, a
# cartoon, a clothes hanger) score under 0.4 or are not found at all.
REAL_FACE_MIN_SCORE = 0.5

# When BlazeFace's subject is not confirmed but YuNet is this sure of a face
# elsewhere, the engine moves to that face instead of refusing. The three
# labelled photographs where BlazeFace chose the wrong spot score 0.91-0.93.
REAL_FACE_SWITCH_MIN_SCORE = 0.8

# A second person is a second face scoring at least this...
SECOND_PERSON_MIN_SCORE = 0.8
# ...and at least this fraction of the first face's height. All four group
# photographs and the collage clear both (the smallest, 34, at 0.43); the
# nearest real single-person photograph, 20, has a 0.84 detection at 0.32.
SECOND_PERSON_MIN_HEIGHT_RATIO = 0.38

# Probability of "nsfw" at which an upload is refused. Every ordinary test
# image, the shirtless one included, scores 0.005 or less.
EXPLICIT_MIN_SCORE = 0.7

# Share of the upper chest whose colour matches the face's own skin. The two
# shirtless photographs score 0.50 and 0.59; every clothed single-person
# photograph scores 0.13 or less.
SHIRTLESS_MIN_SKIN_FRACTION = 0.3


def _centre_inside(inner: BoundingBox, outer: BoundingBox, grow: float) -> bool:
    cx = (inner.left + inner.right) / 2.0
    cy = (inner.top + inner.bottom) / 2.0
    dx, dy = outer.width * grow, outer.height * grow
    return (
        outer.left - dx <= cx <= outer.right + dx
        and outer.top - dy <= cy <= outer.bottom + dy
    )


def real_face_confirmed(faces: Sequence[VerifiedFace], subject: BoundingBox) -> bool:
    """A face YuNet believes in sits where BlazeFace put the subject."""
    return any(
        f.score >= REAL_FACE_MIN_SCORE and _centre_inside(f.box, subject, 0.25)
        for f in faces
    )


def second_person_present(faces: Sequence[VerifiedFace]) -> bool:
    """Another clear face, not much smaller than the main one."""
    if len(faces) < 2:
        return False
    first = max(faces, key=lambda f: f.box.height)
    for other in faces:
        if other is first or other.score < SECOND_PERSON_MIN_SCORE:
            continue
        if other.box.height >= SECOND_PERSON_MIN_HEIGHT_RATIO * first.box.height:
            return True
    return False


def chest_skin_fraction(
    image: Image.Image,
    face: FaceDetection,
    alpha_mask: Optional[np.ndarray[Any, Any]],
) -> Optional[float]:
    """Share of the subject's upper chest the colour of their face's skin.

    ``None`` when it cannot be judged: no chest in the photograph, no
    landmarks, or a black-and-white photograph, where every grey matches.
    """
    import cv2

    landmarks = face.landmarks
    if landmarks is None or landmarks.left_eye is None or landmarks.right_eye is None:
        return None
    rgb = np.asarray(image.convert("RGB"))
    ycc = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb).astype(np.float32)
    height, width = ycc.shape[:2]
    box = face.bounding_box
    eye_y = (landmarks.left_eye.y + landmarks.right_eye.y) / 2.0
    chin = landmarks.chin.y if landmarks.chin is not None else box.bottom
    cx = (box.left + box.right) / 2.0
    fw = box.width

    def clamp(v: float, hi: int) -> int:
        return max(0, min(hi, int(v)))

    # The face's skin: cheeks and nose, between the eyes and the mouth.
    sample = ycc[
        clamp(eye_y + 0.1 * (chin - eye_y), height) : clamp(
            eye_y + 0.6 * (chin - eye_y), height
        ),
        clamp(cx - 0.25 * fw, width) : clamp(cx + 0.25 * fw, width),
    ].reshape(-1, 3)
    if sample.size == 0:
        return None
    ref = np.median(sample, axis=0)
    if abs(ref[1] - 128.0) < 4.0 and abs(ref[2] - 128.0) < 4.0:
        return None  # black and white

    face_height = chin - box.top
    y0, y1 = (
        clamp(chin + 0.35 * face_height, height),
        clamp(chin + 1.0 * face_height, height),
    )
    x0, x1 = clamp(cx - 0.6 * fw, width), clamp(cx + 0.6 * fw, width)
    if y1 - y0 < 5 or x1 - x0 < 5:
        return None
    band = ycc[y0:y1, x0:x1]
    if alpha_mask is not None and alpha_mask.shape[:2] == (height, width):
        mask = alpha_mask.astype(np.float32, copy=False)
        threshold = 0.5 if float(mask.max(initial=0.0)) <= 1.01 else 127.5
        subject = mask[y0:y1, x0:x1] > threshold
    else:
        subject = np.ones(band.shape[:2], dtype=bool)
    if subject.sum() < 25:
        return None
    distance = np.sqrt((band[..., 1] - ref[1]) ** 2 + (band[..., 2] - ref[2]) ** 2)
    skin = (distance < 8.0) & (np.abs(band[..., 0] - ref[0]) < 60.0) & subject
    return float(skin.sum()) / float(subject.sum())
