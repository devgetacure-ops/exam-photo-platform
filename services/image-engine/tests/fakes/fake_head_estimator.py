from typing import Any, Dict, Optional

from PIL import Image

from exam_photo.models.geometry import BoundingBox, Landmarks
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.head_estimation import (
    ClippingFindingValue,
    HeadBoundaryVisibility,
    HeadClippingAssessment,
    HeadClippingFinding,
    HeadEstimationProvider,
    HeadEstimationResult,
)


class FakeHeadEstimator(HeadEstimationProvider):
    def __init__(
        self,
        bounding_box: Optional[BoundingBox] = None,
        confidence: float = 0.9,
        boundary_visibility: Optional[Dict[str, Any]] = None,
        warnings: Optional[list[str]] = None,
        raise_error: Optional[str] = None,
    ) -> None:
        self.bounding_box = bounding_box or BoundingBox(
            left=0.1, top=0.05, right=0.9, bottom=0.95
        )
        self.confidence = confidence

        vis_dict = {
            "top_hair_boundary": {"state": "visible", "basis": "observed"},
            "left_head_boundary": {"state": "visible", "basis": "observed"},
            "right_head_boundary": {"state": "visible", "basis": "observed"},
            "chin_boundary": {"state": "visible", "basis": "observed"},
            "lower_beard_boundary": {"state": "visible", "basis": "observed"},
            "left_ear": {"state": "unknown", "basis": "unsupported"},
            "right_ear": {"state": "unknown", "basis": "unsupported"},
        }
        if boundary_visibility is not None:
            # Handle booleans/strings from old tests mapping to BoundaryAssessment dicts
            for k, val in boundary_visibility.items():
                target_key = k
                if k.endswith("_visible") and not k.startswith("lower_"):
                    target_key = k[:-8]  # strip _visible
                elif k == "beard_boundary_visible":
                    target_key = "lower_beard_boundary"

                state_str = "unknown"
                if val is True or val == "true" or val == "visible":
                    state_str = "visible"
                elif val is False or val == "false" or val == "not_visible":
                    state_str = "not_visible"
                elif val == "not_applicable":
                    state_str = "not_applicable"

                vis_dict[target_key] = {"state": state_str, "basis": "observed"}

        self.boundary_visibility = HeadBoundaryVisibility(**vis_dict)  # type: ignore[arg-type]
        self.warnings = warnings or []
        self.raise_error = raise_error

    def estimate_head(
        self,
        image: Image.Image,
        face: FaceDetection,
        landmarks: Optional[Landmarks] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> HeadEstimationResult:
        if self.raise_error:
            raise RuntimeError(self.raise_error)

        img_w, img_h = image.size

        # In fake mode, if bounding_box is in normalized coords [0, 1],
        # convert to absolute pixels based on input image.
        pixel_box = self.bounding_box
        if self.bounding_box.right <= 1.01:
            pixel_box = BoundingBox(
                left=self.bounding_box.left * img_w,
                top=self.bounding_box.top * img_h,
                right=self.bounding_box.right * img_w,
                bottom=self.bounding_box.bottom * img_h,
            )

        not_clip = HeadClippingFinding(
            status=ClippingFindingValue.NOT_DETECTED,
            confidence=1.0,
            basis="fake",
            related_boundary="none",
        )
        clipping = HeadClippingAssessment(
            top_hair=not_clip,
            left_side=not_clip,
            right_side=not_clip,
            chin=not_clip,
            lower_beard=not_clip,
        )

        return HeadEstimationResult(
            provider_name="FakeHeadEstimator",
            provider_version="0.0.1-fake",
            method="fake_heuristic",
            face_detection_reference=face,
            head_bounding_box=pixel_box,
            confidence=self.confidence,
            confidence_basis="fake",
            boundary_visibility=self.boundary_visibility,
            clipping_assessment=clipping,
            warnings=self.warnings,
            provider_status="success",
            processing_duration=0.0,
            safe_internal_metadata={
                "image_width": img_w,
                "image_height": img_h,
            },
        )
