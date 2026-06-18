from __future__ import annotations

from enum import Enum
from typing import Any, Optional, Protocol, runtime_checkable

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, model_validator

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.suitability.issue_codes import IssueSeverity, SuitabilityIssueCode


class SegmentationStatusValue(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


class SegmentationCapabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")
    probability_masks: bool
    category_mask: bool
    multiclass: bool
    hair_class: bool
    face_skin_class: bool
    clothes_class: bool
    accessories_class: bool
    multiple_people_supported: bool
    instance_separation: bool
    cpu_execution: bool
    local_execution: bool


class SegmentationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    foreground_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    uncertain_low_threshold: float = Field(default=0.2, ge=0.0, le=1.0)
    uncertain_high_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    minimum_foreground_coverage: float = Field(default=0.05, ge=0.0, le=1.0)
    maximum_foreground_coverage: float = Field(default=0.95, ge=0.0, le=1.0)
    minimum_face_mask_coverage: float = Field(default=0.5, ge=0.0, le=1.0)
    minimum_head_mask_coverage: float = Field(default=0.5, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_thresholds(self) -> SegmentationConfig:
        if not (
            self.uncertain_low_threshold
            <= self.foreground_threshold
            <= self.uncertain_high_threshold
        ):
            raise ValueError(
                "Thresholds must satisfy: uncertain_low_threshold <= foreground_threshold <= uncertain_high_threshold"
            )
        if not (self.minimum_foreground_coverage < self.maximum_foreground_coverage):
            raise ValueError(
                "Coverage limits must satisfy: minimum_foreground_coverage < maximum_foreground_coverage"
            )
        return self


class SegmentationClassCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    background: float = Field(ge=0.0, le=1.0)
    hair: float = Field(ge=0.0, le=1.0)
    body_skin: float = Field(ge=0.0, le=1.0)
    face_skin: float = Field(ge=0.0, le=1.0)
    clothing: float = Field(ge=0.0, le=1.0)
    accessories: float = Field(ge=0.0, le=1.0)


class SegmentationValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: SuitabilityIssueCode
    severity: IssueSeverity
    blocking_for_processing: bool
    confidence: Optional[float] = None


class MaskValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_valid: bool
    foreground_coverage_ratio: float = Field(ge=0.0, le=1.0)
    uncertain_pixel_ratio: float = Field(ge=0.0, le=1.0)
    connected_components_count: int
    largest_component_ratio: float = Field(ge=0.0, le=1.0)
    mask_bounding_box: Optional[BoundingBox] = None
    image_edge_contact: bool
    face_contained: Optional[bool] = None
    head_region_coverage_ratio: Optional[float] = None
    issue_codes: list[str]
    issues: list[SegmentationValidationIssue]


class SubjectSegmentationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    provider_name: str
    provider_version: str
    model_name: str
    model_version: str
    capabilities: SegmentationCapabilities
    provider_status: SegmentationStatusValue
    probability_mask: Any = Field(exclude=True)  # np.ndarray, float32, [0, 1]
    coarse_mask: Any = Field(exclude=True)  # Image.Image, uint8, L mode
    input_width: int
    input_height: int
    mask_width: int
    mask_height: int
    threshold_used: float
    foreground_coverage_ratio: float = Field(ge=0.0, le=1.0)
    warnings: list[str]
    processing_duration: float
    inference_duration_ms: Optional[float] = None
    mask_extraction_duration_ms: Optional[float] = None
    resize_threshold_duration_ms: Optional[float] = None
    validation_duration_ms: Optional[float] = None
    safe_internal_metadata: Optional[dict[str, Any]] = None
    class_coverage: Optional[SegmentationClassCoverage] = None
    mask_validation: MaskValidationReport

    @model_validator(mode="after")
    def validate_masks(self) -> SubjectSegmentationResult:
        import numpy as np
        from PIL import Image

        # Probability mask checks
        if not isinstance(self.probability_mask, np.ndarray):
            raise ValueError("probability_mask must be a numpy ndarray")
        if self.probability_mask.dtype != np.float32:
            raise ValueError("probability_mask dtype must be float32")
        if len(self.probability_mask.shape) != 2:
            raise ValueError("probability_mask must be a 2D array")
        if self.probability_mask.shape != (self.mask_height, self.mask_width):
            raise ValueError("probability_mask dimensions mismatch")
        if not np.all(np.isfinite(self.probability_mask)):
            raise ValueError("probability_mask contains non-finite values")
        if np.any((self.probability_mask < 0.0) | (self.probability_mask > 1.0)):
            # Support small floating-point errors tolerance
            if np.any(
                (self.probability_mask < -1e-5) | (self.probability_mask > 1.00001)
            ):
                raise ValueError("probability_mask values must be in range [0.0, 1.0]")

        # Coarse mask checks
        if not isinstance(self.coarse_mask, Image.Image):
            raise ValueError("coarse_mask must be a PIL Image")
        if self.coarse_mask.mode != "L":
            raise ValueError("coarse_mask mode must be 'L'")
        if self.coarse_mask.size != (self.mask_width, self.mask_height):
            raise ValueError("coarse_mask size mismatch")

        # Size limits checks to protect against maliciously large masks
        if self.mask_width > 10000 or self.mask_height > 10000:
            raise ValueError("mask dimensions exceed safety limits (10000px)")

        return self


@runtime_checkable
class SubjectSegmentationProvider(Protocol):
    def segment_subject(
        self,
        image: Image.Image,
        face: Optional[FaceDetection | list[FaceDetection]] = None,
        head_estimate: Optional[BoundingBox] = None,
        config: Optional[SegmentationConfig] = None,
    ) -> SubjectSegmentationResult:
        """Segments the foreground subject from the background.

        Returns a SubjectSegmentationResult containing probability and coarse masks.
        """
        ...
