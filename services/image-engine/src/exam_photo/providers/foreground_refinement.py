from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable

import numpy as np
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, model_validator

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.suitability.issue_codes import IssueSeverity, SuitabilityIssueCode


class RefinementConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Size-aware radius: if morphology_radius_ratio is set, it computes
    # radius from min(width, height), clamped to [min_radius_px, max_radius_px].
    # If None, morphology_radius_px is used directly.
    morphology_radius_px: int = Field(default=3, ge=1, le=30)
    morphology_radius_ratio: Optional[float] = Field(default=0.005, ge=0.0, le=0.05)
    min_radius_px: int = Field(default=2, ge=1, le=10)
    max_radius_px: int = Field(default=15, ge=3, le=30)
    gaussian_sigma: float = Field(default=1.0, ge=0.0, le=10.0)
    probability_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    trimap_band_width_px: int = Field(default=10, ge=1, le=50)
    preserve_face_core: bool = True

    def effective_radius(self, image_width: int, image_height: int) -> int:
        if self.morphology_radius_ratio is not None:
            short_edge = min(image_width, image_height)
            computed = int(round(short_edge * self.morphology_radius_ratio))
            return max(self.min_radius_px, min(computed, self.max_radius_px))
        return self.morphology_radius_px


class RefinementValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: SuitabilityIssueCode
    severity: IssueSeverity
    blocking_for_processing: bool
    confidence: Optional[float] = None


class RefinedMaskValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    is_valid: bool
    foreground_coverage_before: float
    foreground_coverage_after: float
    foreground_coverage_delta: float
    coarse_iou: float
    edge_transition_ratio: float
    unknown_trimap_ratio: float
    definite_foreground_ratio: float
    definite_background_ratio: float
    connected_components_before: int
    connected_components_after: int
    connectivity_improvement: bool
    face_coverage_before: Optional[float] = None
    face_coverage_after: Optional[float] = None
    face_coverage_delta: Optional[float] = None
    head_region_coverage_before: Optional[float] = None
    head_region_coverage_after: Optional[float] = None
    head_region_coverage_delta: Optional[float] = None
    bounding_box_before: Optional[BoundingBox] = None
    bounding_box_after: Optional[BoundingBox] = None
    large_hole_count: int
    largest_hole_ratio: float
    issue_codes: list[str]
    issues: list[RefinementValidationIssue]


class RefinedMaskResult(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    provider_name: str
    provider_version: str
    refined_alpha_mask: Any = Field(exclude=True)  # np.ndarray, float32, [0.0, 1.0]
    refined_binary_mask: Any = Field(exclude=True)  # PIL Image, mode "L", 0/255
    trimap: Any = Field(exclude=True)  # PIL Image, mode "L", 0/128/255
    input_width: int
    input_height: int
    effective_radius_px: int
    refinement_duration_ms: float
    config_used: RefinementConfig
    validation: RefinedMaskValidationReport

    @model_validator(mode="after")
    def validate_refined_masks(self) -> RefinedMaskResult:
        if not isinstance(self.refined_alpha_mask, np.ndarray):
            raise ValueError("refined_alpha_mask must be a numpy ndarray")
        if self.refined_alpha_mask.dtype != np.float32:
            raise ValueError("refined_alpha_mask dtype must be float32")
        if len(self.refined_alpha_mask.shape) != 2:
            raise ValueError("refined_alpha_mask must be a 2D array")
        if self.refined_alpha_mask.shape != (self.input_height, self.input_width):
            raise ValueError("refined_alpha_mask dimensions mismatch")
        if not np.all(np.isfinite(self.refined_alpha_mask)):
            raise ValueError(
                "refined_alpha_mask must only contain finite values (no NaN or inf)"
            )
        if np.any(
            (self.refined_alpha_mask < -1e-5) | (self.refined_alpha_mask > 1.00001)
        ):
            raise ValueError("refined_alpha_mask values must be in range [0.0, 1.0]")

        if not isinstance(self.refined_binary_mask, Image.Image):
            raise ValueError("refined_binary_mask must be a PIL Image")
        if self.refined_binary_mask.mode != "L":
            raise ValueError("refined_binary_mask mode must be 'L'")
        if self.refined_binary_mask.size != (self.input_width, self.input_height):
            raise ValueError("refined_binary_mask size mismatch")

        binary_arr = np.array(self.refined_binary_mask)
        if np.any((binary_arr != 0) & (binary_arr != 255)):
            raise ValueError("refined_binary_mask values must strictly be 0 or 255")

        if not isinstance(self.trimap, Image.Image):
            raise ValueError("trimap must be a PIL Image")
        if self.trimap.mode != "L":
            raise ValueError("trimap mode must be 'L'")
        if self.trimap.size != (self.input_width, self.input_height):
            raise ValueError("trimap size mismatch")

        trimap_arr = np.array(self.trimap)
        if np.any((trimap_arr != 0) & (trimap_arr != 128) & (trimap_arr != 255)):
            raise ValueError("trimap values must strictly be 0, 128, or 255")

        return self


@runtime_checkable
class ForegroundRefinementProvider(Protocol):
    def refine_mask(
        self,
        coarse_mask: Image.Image,
        probability_mask: np.ndarray[Any, Any],
        face: Optional[FaceDetection | list[FaceDetection]] = None,
        config: Optional[RefinementConfig] = None,
        head_estimate: Optional[BoundingBox] = None,
    ) -> RefinedMaskResult:
        """Refines a coarse foreground subject mask using boundary morphological cleanup.

        Returns a RefinedMaskResult containing the refined masks, trimap, and quality report.
        """
        ...
