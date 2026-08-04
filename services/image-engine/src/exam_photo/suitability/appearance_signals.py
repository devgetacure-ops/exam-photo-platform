"""Measure the signals the disposition policy consumes (DEC-041).

Kept apart from ``disposition`` so the policy stays testable without a model
and so measurement can change without touching the rule.  Everything here is
cheap: face detections and landmarks are supplied by the caller, and the image
statistics are single passes over the pixels.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

import numpy as np
from PIL import Image

from exam_photo.providers.face_detection import FaceDetection
from exam_photo.suitability.disposition import AppearanceSignals


def _luminance_stats(rgb: np.ndarray[Any, Any]) -> tuple[float, float, float]:
    """Return (mean luminance, near-black fraction, mean saturation), 0-255.

    Saturation is the max-minus-min channel spread rather than an HSV
    conversion: it costs one pass, and for the only question asked of it --
    "is this photograph monochrome?" -- it is exact, since a greyscale image
    has zero spread on every pixel by construction.
    """
    grey = rgb.mean(axis=2)
    spread = rgb.max(axis=2) - rgb.min(axis=2)
    return (
        float(grey.mean()),
        float((grey < 40.0).mean()),
        float(spread.mean()),
    )


# Side of the fixed box a face is resampled into before its focus is measured.
_SHARPNESS_NORMALISATION_PX = 192


def _normalised_sharpness(face: Image.Image) -> float:
    """Laplacian variance of the face resampled to a fixed box.

    The size normalisation is the whole point.  Raw Laplacian variance scales
    with how many pixels the face occupies, so on the adversarial set it ranked
    a photograph a reviewer called perfect (33) as blurrier than the one they
    called blurred (43).  Resampling to a fixed box first removes that term and
    separates them cleanly: 48 for the blurred photograph against a minimum of
    97 across all ten labelled perfect.

    A contrast-normalised variant was also measured and rejected -- dividing by
    the region's own variance put the blurred photograph (0.125) squarely
    inside the perfect range (0.050-0.280), because an evenly lit face has low
    contrast without being soft.
    """
    grey = np.asarray(
        face.convert("L").resize(
            (_SHARPNESS_NORMALISATION_PX, _SHARPNESS_NORMALISATION_PX),
            Image.Resampling.BICUBIC,
        ),
        dtype=np.float32,
    )
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    windows = np.lib.stride_tricks.sliding_window_view(grey, (3, 3))
    return float((windows * kernel).sum(axis=(2, 3)).var())


def measure_appearance_signals(
    image: Image.Image,
    detections: Sequence[FaceDetection],
    *,
    detection_confidence: Optional[float] = None,
    landmarks_available: bool = False,
    target_height_px: Optional[int] = None,
    target_head_height_ratio: Optional[float] = None,
) -> AppearanceSignals:
    """Collect the measurements for one photograph.

    ``detection_confidence`` is the tier the detector had to fall back to
    before it found anything, not the score of any individual detection: a
    face found only at the lowest tier is not trustworthy enough to block on
    (see ``disposition``).
    """
    width, height = image.size
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    _, _, mean_saturation = _luminance_stats(rgb)

    primary_height: Optional[float] = None
    second_ratio = 0.0
    if detections:
        heights = sorted(
            (float(d.bounding_box.height) for d in detections), reverse=True
        )
        primary_height = heights[0]
        if len(heights) > 1 and primary_height > 0:
            second_ratio = heights[1] / primary_height

    # Exposure is measured on the face, never on the whole frame.
    #
    # A correctly exposed portrait shot at night, or against a dark backdrop,
    # has a low frame luminance and a perfectly lit face. Measured on two such
    # photographs in the adversarial set: frame luminance 29 with 78% of pixels
    # near black, while the face itself reads 98 and 93. A frame-based rule
    # calls those severely underexposed, which is a false likely-rejection on
    # two photographs a reviewer classed as ideal.
    mean_luma: Optional[float] = None
    dark_fraction: Optional[float] = None
    sharpness: Optional[float] = None
    if detections:
        box = max(detections, key=lambda d: d.bounding_box.height).bounding_box
        y0, y1 = max(0, int(box.top)), min(height, int(box.bottom))
        x0, x1 = max(0, int(box.left)), min(width, int(box.right))
        if y1 > y0 and x1 > x0:
            face_grey = rgb[y0:y1, x0:x1].mean(axis=2)
            mean_luma = float(face_grey.mean())
            dark_fraction = float((face_grey < 40.0).mean())
        if y1 - y0 >= 8 and x1 - x0 >= 8:
            sharpness = _normalised_sharpness(image.crop((x0, y0, x1, y1)))

    yaw = pitch = roll = None
    if detections:
        primary = max(detections, key=lambda d: d.bounding_box.height)
        if primary.pose is not None:
            yaw, pitch, roll = primary.pose.yaw, primary.pose.pitch, primary.pose.roll

    return AppearanceSignals(
        image_width=width,
        image_height=height,
        face_count=len(detections),
        detection_confidence=detection_confidence,
        primary_face_height_px=primary_height,
        second_face_height_ratio=second_ratio,
        landmarks_available=landmarks_available,
        yaw_degrees=yaw,
        pitch_degrees=pitch,
        roll_degrees=roll,
        mean_luminance=mean_luma,
        dark_pixel_fraction=dark_fraction,
        mean_saturation=mean_saturation,
        face_sharpness=sharpness,
        target_height_px=target_height_px,
        target_head_height_ratio=target_head_height_ratio,
    )
