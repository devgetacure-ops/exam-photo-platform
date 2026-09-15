"""Whether the lighting correction changed a photograph visibly (DEC-095).

DEC-076 offers the candidate a switch between the corrected photograph and
the one without the correction. The owner's testing (note K1) found the
switch offered where flipping it changes nothing anyone can see: a
sharpening-only correction moves the face by 0.2-0.3 levels of 255, while a
colour-cast or contrast correction moves it by 4.6-23 levels on the same
40-photograph set. A switch that visibly does nothing reads as broken, so the
alternate is kept only when the difference is one a person could see.

The comparison is made on the central region of the finished frame, where the
face sits in every crop, because the background is composited identically in
both variants and would only dilute the measurement.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

#: Mean absolute difference, in levels of 255, below which the two variants
#: look the same. est.: set between the measured invisible case (0.2-0.3) and
#: the smallest visible one (4.6), well clear of both.
VISIBLE_CHANGE_LEVELS = 1.0

#: The part of the frame the face occupies in every crop, as fractions of the
#: height and width: (top, bottom, left, right).
FACE_REGION = (0.15, 0.75, 0.2, 0.8)


def mean_face_difference(corrected: Image.Image, original: Image.Image) -> float:
    """Mean absolute difference over the face region, in levels of 255."""
    a = np.asarray(corrected.convert("RGB"), dtype=np.int16)
    b = np.asarray(original.convert("RGB"), dtype=np.int16)
    if a.shape != b.shape:
        return float("inf")
    height, width = a.shape[:2]
    top, bottom, left, right = FACE_REGION
    rows = slice(int(height * top), max(int(height * bottom), int(height * top) + 1))
    cols = slice(int(width * left), max(int(width * right), int(width * left) + 1))
    return float(np.abs(a[rows, cols] - b[rows, cols]).mean())


def lighting_change_is_visible(corrected: Image.Image, original: Image.Image) -> bool:
    """True when switching between the two variants would show a difference."""
    return mean_face_difference(corrected, original) >= VISIBLE_CHANGE_LEVELS
