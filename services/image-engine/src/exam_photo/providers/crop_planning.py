from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional, Protocol, runtime_checkable

import numpy as np
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, model_validator

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.suitability.issue_codes import IssueSeverity


class CropMode(str, Enum):
    EXACT_ASPECT = "exact_aspect"
    HEAD_LED_RANGE = "head_led_range"


class CropIssueCode(str, Enum):
    CROP_TARGET_ASPECT_MISSING = "CROP_TARGET_ASPECT_MISSING"
    CROP_TARGET_ASPECT_INVALID = "CROP_TARGET_ASPECT_INVALID"
    CROP_BOX_OUT_OF_BOUNDS = "CROP_BOX_OUT_OF_BOUNDS"
    CROP_ASPECT_RATIO_MISMATCH = "CROP_ASPECT_RATIO_MISMATCH"
    CROP_FACE_NOT_CENTERED = "CROP_FACE_NOT_CENTERED"
    CROP_HEAD_CLIPPED = "CROP_HEAD_CLIPPED"
    CROP_TOP_HAIR_RISK = "CROP_TOP_HAIR_RISK"
    CROP_SIDE_HEAD_RISK = "CROP_SIDE_HEAD_RISK"
    CROP_CHIN_RISK = "CROP_CHIN_RISK"
    CROP_BEARD_RISK = "CROP_BEARD_RISK"
    CROP_HEAD_COVERING_RISK = "CROP_HEAD_COVERING_RISK"
    CROP_MASK_PRESERVATION_LOW = "CROP_MASK_PRESERVATION_LOW"
    CROP_PADDING_REQUIRED = "CROP_PADDING_REQUIRED"
    CROP_SOURCE_TOO_TIGHT = "CROP_SOURCE_TOO_TIGHT"
    CROP_INPUT_INVALID = "CROP_INPUT_INVALID"
    CROP_PROVIDER_FAILED = "CROP_PROVIDER_FAILED"

    # Crop Mode B specific issue codes
    CROP_B_RANGE_MISSING = "CROP_B_RANGE_MISSING"
    CROP_B_RANGE_INVALID = "CROP_B_RANGE_INVALID"
    CROP_B_HEAD_RATIO_LOW = "CROP_B_HEAD_RATIO_LOW"
    CROP_B_HEAD_RATIO_HIGH = "CROP_B_HEAD_RATIO_HIGH"
    CROP_B_WIDTH_OUT_OF_RANGE = "CROP_B_WIDTH_OUT_OF_RANGE"
    CROP_B_HEIGHT_OUT_OF_RANGE = "CROP_B_HEIGHT_OUT_OF_RANGE"
    CROP_B_ASPECT_OUT_OF_RANGE = "CROP_B_ASPECT_OUT_OF_RANGE"
    CROP_B_FACE_NOT_CENTERED = "CROP_B_FACE_NOT_CENTERED"
    CROP_B_HEAD_CLIPPED = "CROP_B_HEAD_CLIPPED"
    CROP_B_MASK_PRESERVATION_LOW = "CROP_B_MASK_PRESERVATION_LOW"
    CROP_B_PADDING_REQUIRED = "CROP_B_PADDING_REQUIRED"
    CROP_B_SOURCE_TOO_TIGHT = "CROP_B_SOURCE_TOO_TIGHT"
    CROP_B_INPUT_INVALID = "CROP_B_INPUT_INVALID"
    CROP_B_PROVIDER_FAILED = "CROP_B_PROVIDER_FAILED"
    CROP_B_TOP_HAIR_RISK = "CROP_B_TOP_HAIR_RISK"
    CROP_B_SIDE_HEAD_RISK = "CROP_B_SIDE_HEAD_RISK"
    CROP_B_CHIN_RISK = "CROP_B_CHIN_RISK"
    CROP_B_BEARD_RISK = "CROP_B_BEARD_RISK"
    CROP_B_HEAD_COVERING_RISK = "CROP_B_HEAD_COVERING_RISK"


class CropValidationIssue(BaseModel):
    code: CropIssueCode
    severity: IssueSeverity
    blocking_for_processing: bool
    confidence: float = 1.0


class CropConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_width: Optional[int] = None
    target_height: Optional[int] = None
    target_aspect_ratio: Optional[float] = None
    minimum_top_margin_ratio: float = 0.06
    minimum_side_margin_ratio: float = 0.06
    minimum_bottom_margin_ratio: float = 0.08
    preferred_face_center_y_ratio: float = 0.44
    maximum_face_center_y_deviation: float = 0.12
    allow_padding: bool = False
    allow_subject_clipping: bool = False
    edge_safety_margin_px: int = 2
    mask_preservation_threshold: float = 0.995

    @model_validator(mode="after")
    def validate_config(self) -> CropConfig:
        # Enforce margin validity
        if (
            self.minimum_top_margin_ratio < 0.0
            or self.minimum_bottom_margin_ratio < 0.0
            or self.minimum_side_margin_ratio < 0.0
        ):
            raise ValueError("Margins must be non-negative.")
        if self.minimum_top_margin_ratio + self.minimum_bottom_margin_ratio >= 1.0:
            raise ValueError("Sum of top and bottom margins must be less than 1.0.")
        if 2 * self.minimum_side_margin_ratio >= 1.0:
            raise ValueError("Double side margin must be less than 1.0.")

        has_dims = self.target_width is not None and self.target_height is not None
        has_aspect = self.target_aspect_ratio is not None

        if (self.target_width is None) != (self.target_height is None):
            if not has_aspect:
                raise ValueError(
                    "Both target_width and target_height must be provided unless target_aspect_ratio is specified."
                )

        if not has_dims and not has_aspect:
            raise ValueError(
                "Either target dimensions or aspect ratio must be provided."
            )

        if self.target_width is not None and self.target_width <= 0:
            raise ValueError("target_width must be greater than zero.")
        if self.target_height is not None and self.target_height <= 0:
            raise ValueError("target_height must be greater than zero.")
        if self.target_aspect_ratio is not None and (
            self.target_aspect_ratio <= 0.0 or not np.isfinite(self.target_aspect_ratio)
        ):
            raise ValueError("target_aspect_ratio must be positive and finite.")

        # Enforce target aspect ratio consistency if both are provided
        if has_dims and has_aspect:
            assert self.target_width is not None
            assert self.target_height is not None
            assert self.target_aspect_ratio is not None
            resolved = self.target_width / self.target_height
            if abs(resolved - self.target_aspect_ratio) > 1e-4:
                raise ValueError(
                    f"Conflicting target aspect ratio. Resolved from dimensions: "
                    f"{resolved:.4f}, but target_aspect_ratio was: {self.target_aspect_ratio:.4f}"
                )

        return self


class CropValidationReport(BaseModel):
    is_valid: bool
    issue_codes: List[CropIssueCode]
    issues: List[CropValidationIssue]
    crop_inside_source: bool
    ideal_crop_inside_source: bool
    aspect_ratio_valid: bool
    face_contained: bool
    head_preservation_valid: Optional[bool] = None
    mask_preservation_valid: Optional[bool] = None
    padding_required: bool
    valid_without_padding: bool
    subject_clipping_detected: bool
    top_margin_px: Optional[int] = None
    bottom_margin_px: Optional[int] = None
    left_margin_px: Optional[int] = None
    right_margin_px: Optional[int] = None
    head_estimate_unavailable: bool = False
    segmentation_refinement_failed_or_skipped: bool = False
    mask_aware_validation_unavailable: bool = False
    fallback_source: Optional[str] = None
    face_centering_valid: bool = True


class CropPlanResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    provider_name: str
    provider_version: str
    crop_mode: CropMode
    crop_box: BoundingBox
    crop_box_width: int
    crop_box_height: int
    crop_box_aspect_ratio: float

    ideal_crop_box: Optional[BoundingBox] = None
    ideal_crop_width: Optional[int] = None
    ideal_crop_height: Optional[int] = None
    ideal_crop_aspect_ratio: Optional[float] = None

    target_aspect_ratio: float
    aspect_ratio_error: float
    padding_required: bool
    can_crop_without_padding: bool

    # Deprecated / compatibility fields
    crop_width: int
    crop_height: int
    crop_aspect_ratio: float
    face_center_x_ratio: float
    face_center_y_ratio: float
    head_coverage_ratio: Optional[float] = None
    mask_preservation_ratio: Optional[float] = None
    validation: CropValidationReport
    processing_duration_ms: float
    preview_image: Optional[Image.Image] = Field(default=None, exclude=True)


@runtime_checkable
class CropPlanner(Protocol):
    def plan_crop(
        self,
        image_width: int,
        image_height: int,
        face: FaceDetection,
        head_estimate: Optional[BoundingBox],
        refined_mask: Optional[Image.Image] = None,
        alpha_mask: Optional[np.ndarray[Any, Any]] = None,
        config: Optional[CropConfig] = None,
    ) -> CropPlanResult: ...


class CropModeBConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_width: Optional[int] = None
    max_width: Optional[int] = None
    min_height: Optional[int] = None
    max_height: Optional[int] = None

    preferred_aspect_ratio: float = 0.75
    min_aspect_ratio: Optional[float] = 0.65
    max_aspect_ratio: Optional[float] = 0.90

    target_head_height_ratio: float = 0.76
    min_head_height_ratio: float = 0.68
    max_head_height_ratio: float = 0.84

    minimum_top_margin_ratio: float = 0.04
    minimum_side_margin_ratio: float = 0.05
    minimum_bottom_margin_ratio: float = 0.08

    preferred_face_center_x_ratio: float = 0.50
    preferred_face_center_y_ratio: float = 0.44
    maximum_face_center_x_deviation: float = 0.08
    maximum_face_center_y_deviation: float = 0.12

    mask_preservation_threshold: float = 0.995
    allow_padding: bool = False
    allow_subject_clipping: bool = False
    edge_safety_margin_px: int = 2

    @model_validator(mode="after")
    def validate_config(self) -> CropModeBConfig:
        # Reject negative dimensions
        if self.min_width is not None and self.min_width < 0:
            raise ValueError("min_width cannot be negative.")
        if self.max_width is not None and self.max_width < 0:
            raise ValueError("max_width cannot be negative.")
        if self.min_height is not None and self.min_height < 0:
            raise ValueError("min_height cannot be negative.")
        if self.max_height is not None and self.max_height < 0:
            raise ValueError("max_height cannot be negative.")

        # Reject min > max
        if (
            self.min_width is not None
            and self.max_width is not None
            and self.min_width > self.max_width
        ):
            raise ValueError("min_width cannot be greater than max_width.")
        if (
            self.min_height is not None
            and self.max_height is not None
            and self.min_height > self.max_height
        ):
            raise ValueError("min_height cannot be greater than max_height.")

        # Reject invalid/impossible aspect ranges
        if self.preferred_aspect_ratio <= 0.0 or not np.isfinite(
            self.preferred_aspect_ratio
        ):
            raise ValueError("preferred_aspect_ratio must be positive and finite.")
        if self.min_aspect_ratio is not None and (
            self.min_aspect_ratio <= 0.0 or not np.isfinite(self.min_aspect_ratio)
        ):
            raise ValueError("min_aspect_ratio must be positive and finite.")
        if self.max_aspect_ratio is not None and (
            self.max_aspect_ratio <= 0.0 or not np.isfinite(self.max_aspect_ratio)
        ):
            raise ValueError("max_aspect_ratio must be positive and finite.")
        if (
            self.min_aspect_ratio is not None
            and self.max_aspect_ratio is not None
            and self.min_aspect_ratio > self.max_aspect_ratio
        ):
            raise ValueError(
                "min_aspect_ratio cannot be greater than max_aspect_ratio."
            )

        # Reject invalid head ratio ranges
        if not (0.0 < self.target_head_height_ratio <= 1.0):
            raise ValueError("target_head_height_ratio must be in (0, 1].")
        if not (0.0 < self.min_head_height_ratio <= 1.0):
            raise ValueError("min_head_height_ratio must be in (0, 1].")
        if not (0.0 < self.max_head_height_ratio <= 1.0):
            raise ValueError("max_head_height_ratio must be in (0, 1].")
        if self.min_head_height_ratio > self.max_head_height_ratio:
            raise ValueError(
                "min_head_height_ratio cannot be greater than max_head_height_ratio."
            )
        if not (
            self.min_head_height_ratio
            <= self.target_head_height_ratio
            <= self.max_head_height_ratio
        ):
            raise ValueError(
                "target_head_height_ratio must be between min_head_height_ratio and max_head_height_ratio."
            )

        # Reject invalid margin sums
        if (
            self.minimum_top_margin_ratio < 0.0
            or self.minimum_side_margin_ratio < 0.0
            or self.minimum_bottom_margin_ratio < 0.0
        ):
            raise ValueError("Margins must be non-negative.")
        if self.minimum_top_margin_ratio + self.minimum_bottom_margin_ratio >= 1.0:
            raise ValueError("Sum of top and bottom margins must be less than 1.0.")
        if 2 * self.minimum_side_margin_ratio >= 1.0:
            raise ValueError("Double side margin must be less than 1.0.")

        # Deviations
        if not (0.0 <= self.preferred_face_center_x_ratio <= 1.0):
            raise ValueError("preferred_face_center_x_ratio must be in [0, 1].")
        if not (0.0 <= self.preferred_face_center_y_ratio <= 1.0):
            raise ValueError("preferred_face_center_y_ratio must be in [0, 1].")
        if self.maximum_face_center_x_deviation < 0.0:
            raise ValueError("maximum_face_center_x_deviation must be non-negative.")
        if self.maximum_face_center_y_deviation < 0.0:
            raise ValueError("maximum_face_center_y_deviation must be non-negative.")

        return self


class CropModeBResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    provider_name: str
    provider_version: str
    crop_mode: CropMode

    crop_box: BoundingBox
    crop_box_width: int
    crop_box_height: int
    crop_box_aspect_ratio: float

    ideal_crop_box: Optional[BoundingBox] = None
    ideal_crop_width: Optional[int] = None
    ideal_crop_height: Optional[int] = None
    ideal_crop_aspect_ratio: Optional[float] = None

    head_height_ratio: Optional[float] = None
    face_center_x_ratio: float
    face_center_y_ratio: float

    head_coverage_ratio: Optional[float] = None
    mask_preservation_ratio: Optional[float] = None

    width_within_range: Optional[bool] = None
    height_within_range: Optional[bool] = None
    aspect_within_range: Optional[bool] = None

    can_crop_without_padding: bool
    padding_required: bool

    validation: CropValidationReport
    processing_duration_ms: float

    preview_image: Optional[Image.Image] = Field(default=None, exclude=True)
