import time
from typing import Any

import numpy as np
from PIL import Image

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.head_estimation import (
    HeadEstimationResult,
)

# The crop planner's margin below the landmark chin for a beard, as a fraction
# of the crown-to-chin span (``deterministic_crop_planner._CHIN_BEARD_MARGIN_RATIO``).
# The head box is never cut shorter than the planner will protect anyway.
_CHIN_BEARD_MARGIN_RATIO = 0.09

# How much wider than the head a row below the mouth must be to count as a
# collar or shoulders rather than a beard or neck.
_COLLAR_WIDENING_RATIO = 1.2


def mouth_line_y(face: FaceDetection) -> float | None:
    landmarks = face.landmarks
    if landmarks is None:
        return None
    centre = landmarks.custom_landmarks.get("mouth_center")
    if centre is not None:
        return float(centre.y)
    if landmarks.mouth_left is not None and landmarks.mouth_right is not None:
        return (landmarks.mouth_left.y + landmarks.mouth_right.y) / 2.0
    return None


def landmark_chin_y(face: FaceDetection) -> float | None:
    landmarks = face.landmarks
    if landmarks is None:
        return None
    refined = landmarks.custom_landmarks.get("refined_chin")
    if refined is not None:
        return float(refined.y)
    return float(landmarks.chin.y) if landmarks.chin is not None else None


def first_widening_row(
    binary: np.ndarray[Any, Any],
    y_start: int,
    y_end: int,
    x_min: int,
    x_max: int,
    core_width: float,
) -> int | None:
    """First row from ``y_start`` whose silhouette is clearly wider than the head."""
    limit = core_width * _COLLAR_WIDENING_RATIO
    for y in range(max(0, y_start), y_end):
        xs = np.flatnonzero(binary[y, x_min:x_max])
        if len(xs) > 0 and float(xs[-1] - xs[0]) > limit:
            return y
    return None


class FusedHeadRefiner:
    """Refines coarse head estimation bounding box using segmenter alpha mask and face landmarks."""

    def __init__(self) -> None:
        self.provider_name = "FusedHeadRefiner"
        self.provider_version = "1.0.0"

    def refine_head_estimation(
        self,
        image: Image.Image,
        face: FaceDetection,
        head_result: HeadEstimationResult,
        alpha_mask: np.ndarray[Any, Any],
    ) -> HeadEstimationResult:
        """Refines the head bounding box based on the alpha mask and face box.

        Restricts search to a horizontal band around the face to ignore shoulders,
        limits the upper search based on face height, and finds the true hairline
        and side/ear boundaries using alpha mask connectivity.
        """
        start_time = time.perf_counter()
        w, h = image.size

        # 1. Coarse bounds from face
        fb = face.bounding_box
        geometric_box = head_result.head_bounding_box
        fw = fb.width
        fh = fb.height
        fb.left + fw / 2.0
        fb.top + fh / 2.0

        # Define limits to ignore shoulders and background noise
        # Horizontal band: face width + 40% margin on each side
        left_limit = max(0.0, fb.left - fw * 0.40)
        right_limit = min(float(w), fb.right + fw * 0.40)

        # Upper limit: face height * 1.5 above face top
        top_limit = max(0.0, fb.top - fh * 1.50)

        # Bottom limit for head: keep beard/chin, but do not let neck, collar or
        # shirt foreground drive the portrait frame.
        geometric_bottom = geometric_box.bottom
        bottom_limit = min(float(h), max(geometric_bottom, fb.bottom + fh * 0.18))

        # Convert alpha mask to binary (0 or 255)
        # alpha_mask is a 2D numpy array with shape (h, w) and values in [0.0, 1.0] or [0, 255]
        # Normalize to [0, 255]
        if alpha_mask.dtype in (np.float32, np.float64):
            if np.max(alpha_mask) <= 1.01:
                binary = (alpha_mask * 255.0).astype(np.uint8) > 127
            else:
                binary = alpha_mask.astype(np.uint8) > 127
        else:
            binary = alpha_mask > 127

        # 2. Extract active head mask region within ROI
        roi_mask = np.zeros_like(binary)
        y_min, y_max = int(round(top_limit)), int(round(bottom_limit))
        x_min, x_max = int(round(left_limit)), int(round(right_limit))

        # Safe clamp ROI coordinates
        y_min = max(0, min(y_min, h))
        y_max = max(0, min(y_max, h))
        x_min = max(0, min(x_min, w))
        x_max = max(0, min(x_max, w))

        if y_max > y_min and x_max > x_min:
            roi_mask[y_min:y_max, x_min:x_max] = binary[y_min:y_max, x_min:x_max]

        # 3. Find connected component of the face/head to filter noise
        # Since we don't have scipy installed by default, we can do a simple BFS/DFS
        # starting from the face center, or just take the bounding box of the active pixels in the ROI.
        # Since selfie_segmentation is generally clean in the ROI, taking active pixels is very robust.
        ys, xs = np.where(roi_mask)

        # Left/right must come from a row band that ends at the chin, not
        # from the full ROI down to bottom_limit.  bottom_limit is meant to
        # stop short of the shoulders (see the comment above), but it is
        # computed as max(geometric_bottom, ...) and geometric_bottom (from
        # the upstream expansion-ratio estimate) already reaches close to the
        # neck-to-shoulder transition, so the "avoid shoulders" intent does
        # not hold in practice: measured on reference photo 6-3, silhouette
        # width holds at 85-124px through the head/neck (y=590-750) then
        # jumps to 224-291px by y=780-810 once shoulders enter frame, and
        # bottom_limit there was 792 -- past the jump.  A row band capped at
        # the face box's own bottom still finds the true widest point
        # (cheekbone/ear level) since it scans the whole head band, not just
        # its lowest row.
        width_y_max = min(y_max, max(y_min, int(round(fb.bottom))))
        # And it ends at the mouth line where there is one (DEC-131). The
        # face box reaches below the chin, and a shirt collar can rise beside
        # the jaw above it: on the owner's own photograph the head measured
        # 219 px across to the mouth and 266 px by the chin, all of it collar.
        # The widest part of a head (hair, ears, cheekbones) is above the
        # mouth, so nothing that belongs to the head is lost.
        mouth_y = mouth_line_y(face)
        if mouth_y is not None:
            width_y_max = min(width_y_max, max(y_min + 1, int(round(mouth_y))))
        width_roi_mask = np.zeros_like(binary)
        if width_y_max > y_min and x_max > x_min:
            width_roi_mask[y_min:width_y_max, x_min:x_max] = binary[
                y_min:width_y_max, x_min:x_max
            ]
        width_ys, width_xs = np.where(width_roi_mask)

        if len(ys) > 0 and len(width_xs) > 0:
            # Mathematical refinement
            refined_top = float(np.min(ys))
            refined_left = float(np.min(width_xs))
            refined_right = float(np.max(width_xs))
            # Bottom of head is neck level
            refined_bottom = float(np.max(ys))

            # Add safety bounds: must at least contain the face box.
            #
            # Left/right deliberately do NOT also floor against
            # geometric_box: that estimate widens the detector's ear-tragion
            # keypoints by a fixed face-width fraction, which assumes ears
            # are visible. When hair covers them (reference photo 6-3: mask
            # measures a true 124px head-core width against a 198px
            # ear-tragion-derived geometric estimate), that assumption is
            # wrong, and flooring the mask reading against it silently
            # discards the corrected measurement this refiner exists to
            # produce. The face box is a real per-photo detection, not a
            # heuristic, so it remains a valid floor.
            refined_top = min(refined_top, fb.top, geometric_box.top)
            refined_left = min(refined_left, fb.left)
            refined_right = max(refined_right, fb.right)
            refined_bottom = max(refined_bottom, fb.bottom)

            refined_bottom = min(refined_bottom, bottom_limit)

            # Below the mouth, the head ends where the silhouette suddenly
            # widens past the head itself: that is a collar or shoulders. A
            # beard or neck is narrower than the head and is kept. The bottom
            # never rises above the chin plus the planner's beard margin, nor
            # above the face box.
            core_width = refined_right - refined_left
            collar_y = first_widening_row(
                binary, width_y_max, y_max, x_min, x_max, core_width
            )
            if collar_y is not None:
                chin = landmark_chin_y(face)
                chin_floor = (
                    chin + _CHIN_BEARD_MARGIN_RATIO * max(1.0, chin - refined_top)
                    if chin is not None
                    else fb.bottom
                )
                refined_bottom = min(
                    refined_bottom, max(float(collar_y), chin_floor, fb.bottom)
                )
        else:
            # Fallback to coarse head bounding box
            refined_top = head_result.head_bounding_box.top
            refined_left = head_result.head_bounding_box.left
            refined_right = head_result.head_bounding_box.right
            refined_bottom = head_result.head_bounding_box.bottom

        refined_box = BoundingBox(
            left=refined_left,
            top=refined_top,
            right=refined_right,
            bottom=refined_bottom,
        )

        duration = (time.perf_counter() - start_time) * 1000.0

        # Update metadata/signals
        sig_summary = {
            "roi_top_limit": top_limit,
            "roi_bottom_limit": bottom_limit,
            "roi_left_limit": left_limit,
            "roi_right_limit": right_limit,
            "alpha_pixels_found": int(np.sum(roi_mask)),
        }

        # Build refined estimation result inheriting other fields from head_result
        return HeadEstimationResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            method="fused_alpha_refinement",
            face_detection_reference=face,
            head_bounding_box=refined_box,  # Canonical refined box
            geometric_head_bounding_box=head_result.head_bounding_box,  # Keep old as geometric reference
            refined_head_bounding_box=refined_box,
            confidence=head_result.confidence,
            confidence_basis=head_result.confidence_basis,
            boundary_visibility=head_result.boundary_visibility,
            clipping_assessment=head_result.clipping_assessment,
            warnings=head_result.warnings,
            provider_status=head_result.provider_status,
            processing_duration=head_result.processing_duration + duration,
            safe_internal_metadata={
                **(head_result.safe_internal_metadata or {}),
                "image_width": w,
                "image_height": h,
            },
            uncertainty_reasons=getattr(head_result, "uncertainty_reasons", []),
            signal_summary=sig_summary,
        )
