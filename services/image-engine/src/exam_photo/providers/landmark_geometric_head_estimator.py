import time
from typing import Any, Dict, List, Optional

from PIL import Image

from exam_photo.models.geometry import BoundingBox, Landmarks
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.head_estimation import (
    BoundaryAssessment,
    BoundaryBasis,
    BoundaryVisibilityValue,
    ClippingFindingValue,
    HeadBoundaryVisibility,
    HeadClippingAssessment,
    HeadClippingFinding,
    HeadEstimationConfig,
    HeadEstimationResult,
    ProviderStatusValue,
)



class LandmarkGeometricHeadEstimator:
    """Provisional geometric complete-head estimator.

    Estimates the head bounding box using facial geometry and expansion ratios,
    assisted by key landmarks when available. Runs locally and deterministically.
    """

    def __init__(self) -> None:
        self.provider_name = "LandmarkGeometricHeadEstimator"
        self.provider_version = "1.0.0"

    def estimate_head(
        self,
        image: Image.Image,
        face: FaceDetection,
        landmarks: Optional[Landmarks] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> HeadEstimationResult:
        """Estimates complete head bounding box and boundary clipping states."""
        start_time = time.perf_counter()

        img_w, img_h = image.size

        # 1. Parse and validate configuration
        cfg = HeadEstimationConfig(**(config or {}))

        # 2. Validate face detection input
        face_box = face.bounding_box
        if (
            face_box.left < 0
            or face_box.top < 0
            or face_box.right > img_w
            or face_box.bottom > img_h
            or face_box.left >= face_box.right
            or face_box.top >= face_box.bottom
        ):
            raise ValueError("Invalid face bounding box coordinates.")

        if face.confidence < cfg.minimum_face_confidence:
            raise ValueError(
                f"Face detection confidence {face.confidence:.3f} below minimum "
                f"{cfg.minimum_face_confidence:.3f}."
            )

        face_w = face_box.right - face_box.left
        face_h = face_box.bottom - face_box.top

        # 3. Calculate initial expansions
        # Vertical expansion (upward for hair, downward for chin)
        top_exp = face_h * cfg.top_expansion_ratio
        lower_exp = face_h * cfg.lower_expansion_ratio
        side_exp = face_w * cfg.side_expansion_ratio

        # Determine boundaries and bases
        top_basis = BoundaryBasis.GEOMETRY_INFERRED
        left_basis = BoundaryBasis.GEOMETRY_INFERRED
        right_basis = BoundaryBasis.GEOMETRY_INFERRED
        chin_basis = BoundaryBasis.GEOMETRY_INFERRED
        beard_basis = BoundaryBasis.UNSUPPORTED
        ear_basis = BoundaryBasis.UNSUPPORTED

        # Side boundaries (Left / Right)
        left_val = face_box.left - side_exp
        right_val = face_box.right + side_exp

        # Use ear landmarks if present and valid
        if (
            landmarks
            and landmarks.custom_landmarks
            and "left_ear_tragion" in landmarks.custom_landmarks
            and "right_ear_tragion" in landmarks.custom_landmarks
        ):
            left_tragion = landmarks.custom_landmarks["left_ear_tragion"]
            right_tragion = landmarks.custom_landmarks["right_ear_tragion"]
            if (
                left_tragion.x > 0
                and right_tragion.x > left_tragion.x
                and right_tragion.x < img_w
            ):
                left_val = left_tragion.x - (face_w * 0.15)
                right_val = right_tragion.x + (face_w * 0.15)
                left_basis = BoundaryBasis.LANDMARK_INFERRED
                right_basis = BoundaryBasis.LANDMARK_INFERRED

        # Top boundary (Crown of Head)
        top_val = face_box.top - top_exp

        # Bottom boundary (Chin / Beard)
        bottom_val = face_box.bottom + lower_exp

        # Use mouth center if present to refine vertical chin boundary
        if (
            landmarks
            and landmarks.custom_landmarks
            and "mouth_center" in landmarks.custom_landmarks
        ):
            mouth = landmarks.custom_landmarks["mouth_center"]
            if mouth.y > face_box.top and mouth.y < img_h:
                bottom_val = mouth.y + face_h * cfg.lower_expansion_ratio
                chin_basis = BoundaryBasis.LANDMARK_INFERRED


        # Apply generic lower chin margin if configured
        if cfg.lower_margin_ratio > 0:
            bottom_val += face_h * cfg.lower_margin_ratio

        # 4. Containment Constraints (Head box must contain face box)
        head_left = min(left_val, face_box.left)
        head_top = min(top_val, face_box.top)
        head_right = max(right_val, face_box.right)
        head_bottom = max(bottom_val, face_box.bottom)

        # Guard against unreasonable aspect ratios
        head_w = head_right - head_left
        head_h = head_bottom - head_top
        if head_h > 0:
            aspect = head_w / head_h
            if aspect < cfg.min_aspect_ratio:
                # Too narrow, expand sides
                target_w = head_h * cfg.min_aspect_ratio
                diff = target_w - head_w
                head_left -= diff / 2
                head_right += diff / 2
            elif aspect > cfg.max_aspect_ratio:
                # Too wide, expand vertical height
                target_h = head_w / cfg.max_aspect_ratio
                diff = target_h - head_h
                head_top -= diff / 2
                head_bottom += diff / 2

        # 5. Clamping and Edge clipping assessment
        warnings_list: List[str] = []
        clamped = False

        clamped_left = max(0.0, head_left)
        clamped_top = max(0.0, head_top)
        clamped_right = min(float(img_w), head_right)
        clamped_bottom = min(float(img_h), head_bottom)

        if (
            clamped_left != head_left
            or clamped_top != head_top
            or clamped_right != head_right
            or clamped_bottom != head_bottom
        ):
            clamped = True
            warnings_list.append(
                "Head bounding box coordinates clamped to image edges."
            )

        # Re-verify containment after clamping
        clamped_left = min(clamped_left, face_box.left)
        clamped_top = min(clamped_top, face_box.top)
        clamped_right = max(clamped_right, face_box.right)
        clamped_bottom = max(clamped_bottom, face_box.bottom)

        head_box = BoundingBox(
            left=clamped_left,
            top=clamped_top,
            right=clamped_right,
            bottom=clamped_bottom,
        )

        # Clipping findings: heuristic can only report "suspected" when reaching image edge
        def make_clipping_finding(dist: float, related: str) -> HeadClippingFinding:
            if dist <= 0.001:  # reached edge
                return HeadClippingFinding(
                    status=ClippingFindingValue.SUSPECTED,
                    confidence=0.7,
                    basis="geometric_clamping",
                    image_edge_distance=max(0.0, dist),
                    related_boundary=related,
                )
            else:
                return HeadClippingFinding(
                    status=ClippingFindingValue.NOT_DETECTED,
                    confidence=0.9,
                    basis="geometric_expansion",
                    image_edge_distance=dist,
                    related_boundary=related,
                )

        clip_top = make_clipping_finding(head_top, "top_hair_boundary")
        clip_left = make_clipping_finding(left_val, "left_head_boundary")
        clip_right = make_clipping_finding(img_w - right_val, "right_head_boundary")
        clip_chin = make_clipping_finding(img_h - bottom_val, "chin_boundary")
        clip_beard = make_clipping_finding(img_h - bottom_val, "lower_beard_boundary")

        clipping = HeadClippingAssessment(
            top_hair=clip_top,
            left_side=clip_left,
            right_side=clip_right,
            chin=clip_chin,
            lower_beard=clip_beard,
        )

        # Boundary visibility states: a geometric heuristic cannot observe the actual boundaries,
        # so they remain UNKNOWN even if clipping is suspected.
        top_hair_state = BoundaryVisibilityValue.UNKNOWN
        left_head_state = BoundaryVisibilityValue.UNKNOWN
        right_head_state = BoundaryVisibilityValue.UNKNOWN
        chin_state = BoundaryVisibilityValue.UNKNOWN
        lower_beard_state = BoundaryVisibilityValue.UNKNOWN

        visibility = HeadBoundaryVisibility(
            top_hair_boundary=BoundaryAssessment(state=top_hair_state, basis=top_basis),
            left_head_boundary=BoundaryAssessment(
                state=left_head_state, basis=left_basis
            ),
            right_head_boundary=BoundaryAssessment(
                state=right_head_state, basis=right_basis
            ),
            chin_boundary=BoundaryAssessment(state=chin_state, basis=chin_basis),
            lower_beard_boundary=BoundaryAssessment(
                state=lower_beard_state, basis=beard_basis
            ),
            left_ear=BoundaryAssessment(
                state=BoundaryVisibilityValue.UNKNOWN, basis=ear_basis
            ),
            right_ear=BoundaryAssessment(
                state=BoundaryVisibilityValue.UNKNOWN, basis=ear_basis
            ),
        )

        # Calculate final confidence
        confidence = face.confidence
        if clamped:
            # Penalize confidence slightly when box is clamped
            confidence = max(0.1, confidence * 0.8)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return HeadEstimationResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            method="landmark_assisted_geometric_expansion",
            face_detection_reference=face,
            head_bounding_box=head_box,
            confidence=confidence,
            confidence_basis="face_box_landmark_heuristic_expansion",
            boundary_visibility=visibility,
            clipping_assessment=clipping,
            warnings=warnings_list,
            provider_status=ProviderStatusValue.SUCCESS,
            processing_duration=duration_ms,

            safe_internal_metadata={
                "image_width": img_w,
                "image_height": img_h,
                "clamped": clamped,
                "original_head_box": [left_val, top_val, right_val, bottom_val],
            },
        )
