from enum import Enum
from typing import Any, Dict, Optional, Protocol, runtime_checkable

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, model_validator

from exam_photo.models.geometry import BoundingBox, Landmarks
from exam_photo.providers.face_detection import FaceDetection


class BoundaryVisibilityValue(str, Enum):
    VISIBLE = "visible"
    NOT_VISIBLE = "not_visible"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class BoundaryBasis(str, Enum):
    OBSERVED = "observed"
    LANDMARK_INFERRED = "landmark_inferred"
    GEOMETRY_INFERRED = "geometry_inferred"
    UNSUPPORTED = "unsupported"


class ProviderStatusValue(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


class BoundaryAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state: BoundaryVisibilityValue
    basis: BoundaryBasis


class HeadBoundaryVisibility(BaseModel):
    model_config = ConfigDict(extra="forbid")
    top_hair_boundary: BoundaryAssessment
    left_head_boundary: BoundaryAssessment
    right_head_boundary: BoundaryAssessment
    chin_boundary: BoundaryAssessment
    lower_beard_boundary: BoundaryAssessment
    left_ear: BoundaryAssessment
    right_ear: BoundaryAssessment

    def _to_bool_or_none(self, state: BoundaryVisibilityValue) -> Optional[bool]:
        if state == BoundaryVisibilityValue.VISIBLE:
            return True
        if state == BoundaryVisibilityValue.NOT_VISIBLE:
            return False
        return None

    @property
    def beard_boundary_visible(self) -> Optional[bool]:
        """Deprecated read-only compatibility property mapping to lower_beard_boundary.state."""
        return self._to_bool_or_none(self.lower_beard_boundary.state)

    @property
    def left_head_boundary_visible(self) -> Optional[bool]:
        return self._to_bool_or_none(self.left_head_boundary.state)

    @property
    def right_head_boundary_visible(self) -> Optional[bool]:
        return self._to_bool_or_none(self.right_head_boundary.state)

    @property
    def top_hair_boundary_visible(self) -> Optional[bool]:
        return self._to_bool_or_none(self.top_hair_boundary.state)

    @property
    def chin_boundary_visible(self) -> Optional[bool]:
        return self._to_bool_or_none(self.chin_boundary.state)

    @model_validator(mode="before")
    @classmethod
    def convert_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            new_data: dict[str, Any] = {}
            field_mappings = {
                "top_hair_boundary": ["top_hair_boundary", "top_hair_boundary_visible"],
                "left_head_boundary": [
                    "left_head_boundary",
                    "left_head_boundary_visible",
                ],
                "right_head_boundary": [
                    "right_head_boundary",
                    "right_head_boundary_visible",
                ],
                "chin_boundary": ["chin_boundary", "chin_boundary_visible"],
                "lower_beard_boundary": [
                    "lower_beard_boundary",
                    "lower_beard_boundary_visible",
                    "beard_boundary_visible",
                ],
                "left_ear": ["left_ear", "left_ear_visible"],
                "right_ear": ["right_ear", "right_ear_visible"],
            }
            for target_field, candidates in field_mappings.items():
                val = None
                for c in candidates:
                    if c in data:
                        val = data[c]
                        break

                if val is None:
                    default_basis = (
                        "unsupported"
                        if target_field
                        in ["left_ear", "right_ear", "lower_beard_boundary"]
                        else "geometry_inferred"
                    )
                    new_data[target_field] = {
                        "state": BoundaryVisibilityValue.UNKNOWN,
                        "basis": default_basis,
                    }
                elif isinstance(val, dict):
                    new_data[target_field] = val
                elif isinstance(val, BoundaryAssessment):
                    new_data[target_field] = val
                else:
                    state_str = BoundaryVisibilityValue.UNKNOWN
                    if val is True or val == "true" or val == "visible":
                        state_str = BoundaryVisibilityValue.VISIBLE
                    elif val is False or val == "false" or val == "not_visible":
                        state_str = BoundaryVisibilityValue.NOT_VISIBLE
                    elif val == "not_applicable":
                        state_str = BoundaryVisibilityValue.NOT_APPLICABLE

                    default_basis = (
                        "unsupported"
                        if target_field
                        in ["left_ear", "right_ear", "lower_beard_boundary"]
                        else "geometry_inferred"
                    )
                    new_data[target_field] = {
                        "state": state_str,
                        "basis": default_basis,
                    }
            return new_data
        return data


class ClippingFindingValue(str, Enum):
    CONFIRMED = "confirmed"
    SUSPECTED = "suspected"
    NOT_DETECTED = "not_detected"
    UNKNOWN = "unknown"


class HeadClippingFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: ClippingFindingValue
    confidence: float = Field(ge=0.0, le=1.0)
    basis: str
    image_edge_distance: Optional[float] = None
    related_boundary: str
    warning_code: Optional[str] = None


class HeadClippingAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    top_hair: HeadClippingFinding
    left_side: HeadClippingFinding
    right_side: HeadClippingFinding
    chin: HeadClippingFinding
    lower_beard: HeadClippingFinding


class HeadEstimationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_name: str
    provider_version: str
    method: str
    face_detection_reference: Optional[FaceDetection] = None
    head_bounding_box: BoundingBox  # Canonical pixel-space BoundingBox
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_basis: str
    boundary_visibility: HeadBoundaryVisibility
    clipping_assessment: HeadClippingAssessment
    warnings: list[str]
    provider_status: ProviderStatusValue
    processing_duration: float
    safe_internal_metadata: Optional[Dict[str, Any]] = None

    geometric_head_bounding_box: Optional[BoundingBox] = None
    refined_head_bounding_box: Optional[BoundingBox] = None
    uncertainty_reasons: list[str] = Field(default_factory=list)
    signal_summary: Dict[str, Any] = Field(default_factory=dict)

    @property
    def normalized_head_bounding_box(self) -> BoundingBox:
        metadata = self.safe_internal_metadata or {}
        img_w = float(metadata.get("image_width", 1.0))
        img_h = float(metadata.get("image_height", 1.0))
        return BoundingBox(
            left=self.head_bounding_box.left / img_w,
            top=self.head_bounding_box.top / img_h,
            right=self.head_bounding_box.right / img_w,
            bottom=self.head_bounding_box.bottom / img_h,
        )

    @property
    def estimated_bounding_box(self) -> BoundingBox:
        """Deprecated compatibility property returning normalized box."""
        return self.normalized_head_bounding_box

    @model_validator(mode="before")
    @classmethod
    def convert_result_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Setup metadata first
            metadata = data.get("safe_internal_metadata") or {}
            img_w = float(metadata.get("image_width", 1.0))
            img_h = float(metadata.get("image_height", 1.0))

            if "estimated_bounding_box" in data and "head_bounding_box" not in data:
                norm_box = data["estimated_bounding_box"]
                # Convert normalized box to pixel space
                data["head_bounding_box"] = BoundingBox(
                    left=norm_box.left * img_w,
                    top=norm_box.top * img_h,
                    right=norm_box.right * img_w,
                    bottom=norm_box.bottom * img_h,
                )
            if "estimation_method" in data and "method" not in data:
                data["method"] = data["estimation_method"]
            return data
        return data


class HeadEstimationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    top_expansion_ratio: float = Field(default=0.6, ge=0.0)
    side_expansion_ratio: float = Field(default=0.25, ge=0.0)
    lower_expansion_ratio: float = Field(default=0.35, ge=0.0)
    lower_margin_ratio: float = Field(default=0.15, ge=0.0)
    minimum_face_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    min_aspect_ratio: float = Field(default=0.5, gt=0.0)
    max_aspect_ratio: float = Field(default=2.0, gt=0.0)


@runtime_checkable
class HeadEstimationProvider(Protocol):
    def estimate_head(
        self,
        image: Image.Image,
        face: FaceDetection,
        landmarks: Optional[Landmarks] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> HeadEstimationResult:
        """Estimates complete head boundaries."""
        ...
