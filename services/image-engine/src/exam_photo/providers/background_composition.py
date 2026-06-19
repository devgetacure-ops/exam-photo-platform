from __future__ import annotations

import re
from enum import Enum
from typing import Any, Protocol, runtime_checkable

import numpy as np
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, model_validator

from exam_photo.models.geometry import BoundingBox
from exam_photo.suitability.issue_codes import IssueSeverity


class BackgroundMode(str, Enum):
    SOLID_COLOUR = "solid_colour"
    PLAIN_WHITE = "plain_white"
    PLAIN_LIGHT = "plain_light"


class BackgroundCompositionIssueCode(str, Enum):
    BACKGROUND_INPUT_INVALID = "BACKGROUND_INPUT_INVALID"
    BACKGROUND_ALPHA_INVALID = "BACKGROUND_ALPHA_INVALID"
    BACKGROUND_MASK_SIZE_MISMATCH = "BACKGROUND_MASK_SIZE_MISMATCH"
    BACKGROUND_COLOUR_INVALID = "BACKGROUND_COLOUR_INVALID"
    BACKGROUND_FOREGROUND_TOO_SMALL = "BACKGROUND_FOREGROUND_TOO_SMALL"
    BACKGROUND_FOREGROUND_TOO_LARGE = "BACKGROUND_FOREGROUND_TOO_LARGE"
    BACKGROUND_SUBJECT_CLIPPING_RISK = "BACKGROUND_SUBJECT_CLIPPING_RISK"
    BACKGROUND_EDGE_HALO_RISK = "BACKGROUND_EDGE_HALO_RISK"
    BACKGROUND_EDGE_FRINGE_RISK = "BACKGROUND_EDGE_FRINGE_RISK"
    BACKGROUND_LOW_ALPHA_CONFIDENCE = "BACKGROUND_LOW_ALPHA_CONFIDENCE"
    BACKGROUND_COMPOSITION_FAILED = "BACKGROUND_COMPOSITION_FAILED"
    BACKGROUND_PROVIDER_FAILED = "BACKGROUND_PROVIDER_FAILED"


class BackgroundCompositionValidationIssue(BaseModel):
    code: BackgroundCompositionIssueCode
    severity: IssueSeverity
    blocking_for_processing: bool
    confidence: float = 1.0


class BackgroundCompositionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: BackgroundMode = BackgroundMode.PLAIN_WHITE
    target_colour_hex: str = "#FFFFFF"

    edge_blend_enabled: bool = True
    edge_blend_radius_px: int = 2
    edge_blend_max_radius_px: int = 5

    alpha_threshold: float = 0.5
    minimum_foreground_coverage: float = 0.02
    maximum_foreground_coverage: float = 0.95

    allow_transparent_output: bool = False
    allow_subject_clipping: bool = False
    allow_low_confidence_edges: bool = False

    generate_preview: bool = True

    @model_validator(mode="after")
    def validate_config(self) -> BackgroundCompositionConfig:
        if not re.match(r"^#[0-9A-Fa-f]{6}$", self.target_colour_hex):
            raise ValueError(f"Invalid target_colour_hex: {self.target_colour_hex}")

        if self.edge_blend_radius_px < 0:
            raise ValueError("edge_blend_radius_px cannot be negative")
        if self.edge_blend_max_radius_px < 0:
            raise ValueError("edge_blend_max_radius_px cannot be negative")
        if self.edge_blend_radius_px > self.edge_blend_max_radius_px:
            raise ValueError("edge_blend_radius_px cannot exceed max radius")

        if not (0.0 <= self.alpha_threshold <= 1.0):
            raise ValueError("alpha_threshold must be between 0.0 and 1.0")

        if not (0.0 < self.minimum_foreground_coverage < 1.0):
            raise ValueError(
                "minimum_foreground_coverage must be strictly between 0 and 1"
            )
        if not (0.0 < self.maximum_foreground_coverage < 1.0):
            raise ValueError(
                "maximum_foreground_coverage must be strictly between 0 and 1"
            )
        if self.minimum_foreground_coverage >= self.maximum_foreground_coverage:
            raise ValueError("minimum_foreground_coverage must be less than maximum")

        if self.allow_transparent_output and self.mode in (
            BackgroundMode.SOLID_COLOUR,
            BackgroundMode.PLAIN_WHITE,
            BackgroundMode.PLAIN_LIGHT,
        ):
            # Actually, the spec says "reject transparent output for solid-background modes."
            # But let's just make it a strict validation rule:
            raise ValueError(
                "Transparent output is not allowed for solid background modes."
            )

        return self


class BackgroundCompositionValidationReport(BaseModel):
    is_valid: bool
    issue_codes: list[BackgroundCompositionIssueCode]
    issues: list[BackgroundCompositionValidationIssue]

    input_dimensions_valid: bool
    alpha_dimensions_valid: bool
    alpha_values_valid: bool
    target_colour_valid: bool

    foreground_coverage_ratio: float | None = None
    edge_transition_ratio: float | None = None
    low_confidence_edge_ratio: float | None = None
    estimated_halo_risk_ratio: float | None = None
    estimated_fringe_risk_ratio: float | None = None

    subject_clipping_detected: bool | None = None
    mask_aware_validation_available: bool = True


class BackgroundCompositionResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    provider_name: str
    provider_version: str

    mode: BackgroundMode
    target_colour_hex: str

    source_width: int
    source_height: int
    composed_width: int
    composed_height: int

    foreground_coverage_ratio: float | None = None
    validation: BackgroundCompositionValidationReport
    processing_duration_ms: float

    composed_image: Image.Image | None = Field(default=None, exclude=True)
    alpha_mask: np.ndarray[Any, Any] | None = Field(default=None, exclude=True)


@runtime_checkable
class BackgroundComposer(Protocol):
    def compose_background(
        self,
        image: Image.Image,
        refined_alpha_mask: np.ndarray[Any, Any],
        config: BackgroundCompositionConfig | None = None,
        crop_box: BoundingBox | None = None,
    ) -> BackgroundCompositionResult: ...
