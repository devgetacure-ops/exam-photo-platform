from __future__ import annotations

import time
from typing import Any, Optional, Protocol, cast, runtime_checkable

import numpy as np
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.head_estimation import HeadEstimationResult


class PortraitCompositionResult(BaseModel):
    """Semantic crop-framing geometry for exam portraits.

    This is intentionally separate from the full foreground mask. Background
    removal may preserve hair, clothing and shoulders, but crop sizing should be
    driven by the head/hair/ear/chin/beard area only.
    """

    model_config = ConfigDict(extra="forbid")

    provider_name: str
    provider_version: str
    method: str
    preservation_box: BoundingBox
    framing_box: BoundingBox
    source_head_box: BoundingBox
    lower_body_exclusion_y: float
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)
    signal_summary: dict[str, Any] = Field(default_factory=dict)
    processing_duration_ms: float


@runtime_checkable
class PortraitCompositionProvider(Protocol):
    def estimate_composition(
        self,
        image: Image.Image,
        face: FaceDetection,
        head_result: HeadEstimationResult,
        alpha_mask: Optional[np.ndarray[Any, Any]] = None,
    ) -> PortraitCompositionResult: ...


class DeterministicPortraitCompositionEstimator:
    """Builds reusable exam-portrait crop geometry from face, head and alpha signals."""

    def __init__(self) -> None:
        self.provider_name = "DeterministicPortraitCompositionEstimator"
        self.provider_version = "1.0.0"

    def estimate_composition(
        self,
        image: Image.Image,
        face: FaceDetection,
        head_result: HeadEstimationResult,
        alpha_mask: Optional[np.ndarray[Any, Any]] = None,
    ) -> PortraitCompositionResult:
        start_time = time.perf_counter()
        image_width, image_height = image.size
        face_box = face.bounding_box
        head_box = (
            head_result.refined_head_bounding_box
            or head_result.head_bounding_box
            or head_result.geometric_head_bounding_box
        )
        if head_box is None:
            head_box = self._face_fallback_head_box(face_box, image_width, image_height)

        lower_body_exclusion_y = self._lower_body_exclusion_y(
            face_box=face_box,
            head_box=head_box,
            image_height=image_height,
        )

        observed_head_box = self._observed_upper_alpha_box(
            alpha_mask=alpha_mask,
            face_box=face_box,
            head_box=head_box,
            image_width=image_width,
            image_height=image_height,
            lower_body_exclusion_y=lower_body_exclusion_y,
        )

        if observed_head_box is None:
            preservation_box = head_box
            method = "head_geometry"
            confidence = head_result.confidence
            warnings = ["PORTRAIT_COMPOSITION_ALPHA_UNAVAILABLE"]
        else:
            preservation_box = self._union_boxes(head_box, observed_head_box)
            method = "head_geometry_upper_alpha"
            confidence = min(1.0, max(0.0, head_result.confidence + 0.05))
            warnings = []

        preservation_box = self._contain_box(preservation_box, face_box)
        preservation_box = BoundingBox(
            left=max(0.0, preservation_box.left),
            top=max(0.0, preservation_box.top),
            right=min(float(image_width), preservation_box.right),
            bottom=min(float(image_height), preservation_box.bottom),
        )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return PortraitCompositionResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            method=method,
            preservation_box=preservation_box,
            framing_box=preservation_box,
            source_head_box=head_box,
            lower_body_exclusion_y=lower_body_exclusion_y,
            confidence=confidence,
            warnings=warnings,
            signal_summary={
                "alpha_observed": observed_head_box is not None,
                "face_box": face_box.model_dump(),
                "source_head_box": head_box.model_dump(),
                "observed_head_box": observed_head_box.model_dump()
                if observed_head_box is not None
                else None,
            },
            processing_duration_ms=duration_ms,
        )

    def _face_fallback_head_box(
        self,
        face_box: BoundingBox,
        image_width: int,
        image_height: int,
    ) -> BoundingBox:
        face_width = face_box.width
        face_height = face_box.height
        return BoundingBox(
            left=max(0.0, face_box.left - face_width * 0.25),
            top=max(0.0, face_box.top - face_height * 0.60),
            right=min(float(image_width), face_box.right + face_width * 0.25),
            bottom=min(float(image_height), face_box.bottom + face_height * 0.30),
        )

    def _lower_body_exclusion_y(
        self,
        *,
        face_box: BoundingBox,
        head_box: BoundingBox,
        image_height: int,
    ) -> float:
        face_based_lower_bound = face_box.bottom + face_box.height * 0.22
        return min(float(image_height), max(head_box.bottom, face_based_lower_bound))

    def _observed_upper_alpha_box(
        self,
        *,
        alpha_mask: Optional[np.ndarray[Any, Any]],
        face_box: BoundingBox,
        head_box: BoundingBox,
        image_width: int,
        image_height: int,
        lower_body_exclusion_y: float,
    ) -> BoundingBox | None:
        if alpha_mask is None:
            return None

        alpha = self._normalise_alpha(alpha_mask)
        if alpha.shape[0] != image_height or alpha.shape[1] != image_width:
            return None

        face_width = face_box.width
        head_width = head_box.width
        left = max(0, int(round(min(head_box.left, face_box.left - face_width * 0.35))))
        right = min(
            image_width,
            int(round(max(head_box.right, face_box.right + face_width * 0.35))),
        )
        top = max(0, int(round(min(head_box.top, face_box.top - face_box.height))))
        bottom = min(image_height, int(round(lower_body_exclusion_y)))

        # The left/right extent must be read from a band that ends at the
        # chin, not from the full top..lower_body_exclusion_y range used for
        # the box's bottom.  lower_body_exclusion_y reaches the collar, and
        # the neck-to-shoulder transition is a sharp, large jump -- measured
        # on reference photo 6-3, silhouette width holds at 85-124px through
        # the head and neck (y=590..750) then jumps to 224-291px by y=780-810
        # once shoulders enter the band.  Taking the bounding box over the
        # full range silently swaps "head width" for "shoulder width"
        # whenever shoulders are visible, which they almost always are:
        # measured preservation width 267px against a true head-core width of
        # 124px on that photo. Capping the width scan at the face box's own
        # bottom keeps the reading on the head (it still finds the true
        # widest point -- cheekbone/ear level -- since the scan covers the
        # whole head band, not just its lowest row).
        width_scan_bottom = min(bottom, int(round(face_box.bottom)))
        if right <= left or width_scan_bottom <= top:
            return None

        width_roi = alpha[top:width_scan_bottom, left:right] > 0.5
        width_ys, width_xs = np.where(width_roi)
        if len(width_ys) == 0:
            return None
        abs_width_xs = width_xs + left

        full_roi = alpha[top:bottom, left:right] > 0.5
        ys, xs = np.where(full_roi)
        if len(ys) == 0:
            return None
        abs_ys = ys + top

        observed = BoundingBox(
            left=float(np.min(abs_width_xs)),
            top=float(np.min(abs_ys)),
            right=float(np.max(abs_width_xs) + 1),
            bottom=float(np.max(abs_ys) + 1),
        )

        side_expansion = max(1.0, head_width * 0.01)
        return BoundingBox(
            left=max(0.0, observed.left - side_expansion),
            top=max(0.0, observed.top),
            right=min(float(image_width), observed.right + side_expansion),
            bottom=min(float(image_height), observed.bottom),
        )

    def _normalise_alpha(
        self, alpha_mask: np.ndarray[Any, Any]
    ) -> np.ndarray[Any, Any]:
        alpha = alpha_mask.astype(np.float32, copy=False)
        if alpha.size == 0:
            return alpha
        if float(np.nanmax(alpha)) > 1.01:
            alpha = alpha / 255.0
        return cast(np.ndarray[Any, Any], np.clip(alpha, 0.0, 1.0))

    def _union_boxes(self, first: BoundingBox, second: BoundingBox) -> BoundingBox:
        return BoundingBox(
            left=min(first.left, second.left),
            top=min(first.top, second.top),
            right=max(first.right, second.right),
            bottom=max(first.bottom, second.bottom),
        )

    def _contain_box(self, outer: BoundingBox, inner: BoundingBox) -> BoundingBox:
        return BoundingBox(
            left=min(outer.left, inner.left),
            top=min(outer.top, inner.top),
            right=max(outer.right, inner.right),
            bottom=max(outer.bottom, inner.bottom),
        )
