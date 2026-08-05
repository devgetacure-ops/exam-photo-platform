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

    definite_foreground_threshold: float = Field(default=0.95, ge=0.0, le=1.0)
    definite_background_threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    uncertainty_band_scale: float = Field(default=1.0, ge=0.1, le=5.0)
    edge_refinement_radius_ratio: float = Field(default=0.02, ge=0.0, le=0.2)
    # Contrast window applied to the matted alpha.  Everything at or below the
    # low threshold becomes fully transparent and everything at or above the
    # high threshold fully opaque, so a narrow window discards genuine partial
    # coverage -- exactly the values that describe hair.  The previous
    # 0.18/0.72 window clipped 46% of the alpha range and cut the soft edge band
    # measured on reference photos from 4.6% of the frame to 1.2%.  The grey
    # outline this was fighting comes from background colour retained in
    # semi-transparent pixels, which foreground_decontamination corrects at
    # source, so the window here can stay wide.
    alpha_snap_low_threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    alpha_snap_high_threshold: float = Field(default=0.92, ge=0.0, le=1.0)
    # Set when the incoming probability mask already resolves the subject
    # boundary accurately (a matting model rather than a coarse selfie
    # segmenter).  The morphological pipeline exists to clean up a noisy,
    # low-resolution mask; run against an accurate one it is purely
    # destructive.  Measured on BiRefNet masks, refinement roughly doubled
    # staircase artifacts along the silhouette (0.074 -> 0.133, 0.085 -> 0.137,
    # 0.099 -> 0.126 on three photos), removed 15-40% of the genuine soft-alpha
    # band, and did not improve edge alignment at all (4.72 -> 4.61,
    # 1.76 -> 1.77, 6.83 -> 6.79).  See DEC-033.
    trust_input_alpha: bool = False

    quality_mode: str = Field(default="balanced", pattern="^(fast|balanced|high)$")
    maximum_matting_pixels: int = Field(default=2000000, ge=100000)
    maximum_boundary_roi_pixels: int = Field(default=500000, ge=10000)
    maximum_native_dimension: int = Field(default=4000, ge=500)
    allow_tiled_boundary_processing: bool = Field(default=False)

    @model_validator(mode="after")
    def validate_alpha_snap_thresholds(self) -> RefinementConfig:
        if self.alpha_snap_low_threshold >= self.alpha_snap_high_threshold:
            raise ValueError(
                "alpha_snap_low_threshold must be less than alpha_snap_high_threshold."
            )
        return self

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
        image: Image.Image,
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
