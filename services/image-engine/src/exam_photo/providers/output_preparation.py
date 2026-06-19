from enum import Enum
from typing import List, Protocol, runtime_checkable

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field


class ResizeMode(str, Enum):
    EXACT = "exact"
    RANGE_SELECT = "range_select"


class ResampleMethod(str, Enum):
    LANCZOS = "lanczos"
    BICUBIC = "bicubic"
    BILINEAR = "bilinear"


class EnhancementMode(str, Enum):
    NONE = "none"
    CONSERVATIVE = "conservative"


class OutputPreparationIssueCode(str, Enum):
    OUTPUT_INPUT_INVALID = "OUTPUT_INPUT_INVALID"
    OUTPUT_TARGET_DIMENSIONS_MISSING = "OUTPUT_TARGET_DIMENSIONS_MISSING"
    OUTPUT_TARGET_DIMENSIONS_INVALID = "OUTPUT_TARGET_DIMENSIONS_INVALID"
    OUTPUT_RANGE_INVALID = "OUTPUT_RANGE_INVALID"
    OUTPUT_ASPECT_MISMATCH = "OUTPUT_ASPECT_MISMATCH"
    OUTPUT_UPSCALE_LIMIT_EXCEEDED = "OUTPUT_UPSCALE_LIMIT_EXCEEDED"
    OUTPUT_UPSCALE_WARNING = "OUTPUT_UPSCALE_WARNING"
    OUTPUT_UPSCALE_STRONG_WARNING = "OUTPUT_UPSCALE_STRONG_WARNING"
    OUTPUT_DOWNSCALE_TOO_SEVERE = "OUTPUT_DOWNSCALE_TOO_SEVERE"
    OUTPUT_DOWNSCALE_WARNING = "OUTPUT_DOWNSCALE_WARNING"
    OUTPUT_DOWNSCALE_SEVERE_WARNING = "OUTPUT_DOWNSCALE_SEVERE_WARNING"
    OUTPUT_UNSUPPORTED_COLOUR_MODE = "OUTPUT_UNSUPPORTED_COLOUR_MODE"
    OUTPUT_ENHANCEMENT_UNSAFE = "OUTPUT_ENHANCEMENT_UNSAFE"
    OUTPUT_IDENTITY_RISK = "OUTPUT_IDENTITY_RISK"
    OUTPUT_RESIZE_FAILED = "OUTPUT_RESIZE_FAILED"
    OUTPUT_PROVIDER_FAILED = "OUTPUT_PROVIDER_FAILED"


class OutputPreparationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resize_mode: ResizeMode

    target_width: int | None = None
    target_height: int | None = None

    min_width: int | None = None
    max_width: int | None = None
    min_height: int | None = None
    max_height: int | None = None
    preferred_width: int | None = None
    preferred_height: int | None = None

    preserve_aspect_ratio: bool = True
    allow_padding: bool = False
    allow_upscale: bool = True
    max_upscale_factor: float = 3.0
    min_downscale_factor: float = 0.05

    resample_method: ResampleMethod = ResampleMethod.LANCZOS

    output_colour_mode: str = "RGB"
    strip_metadata: bool = True

    enhancement_mode: EnhancementMode = EnhancementMode.NONE
    brightness_adjustment: float = 1.0
    contrast_adjustment: float = 1.0
    sharpness_adjustment: float = 1.0

    max_brightness_adjustment_delta: float = 0.12
    max_contrast_adjustment_delta: float = 0.12
    max_sharpness_adjustment_delta: float = 0.20

    generate_preview: bool = True


class OutputPreparationValidationReport(BaseModel):
    is_valid: bool
    issue_codes: List[str]


class OutputPreparationResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    provider_name: str
    provider_version: str

    resize_mode: ResizeMode
    source_width: int
    source_height: int
    output_width: int
    output_height: int

    scale_x: float
    scale_y: float
    aspect_ratio_error: float

    output_colour_mode: str
    metadata_stripped: bool

    enhancement_mode: EnhancementMode
    brightness_adjustment: float
    contrast_adjustment: float
    sharpness_adjustment: float

    validation: OutputPreparationValidationReport
    processing_duration_ms: float

    output_image: Image.Image | None = Field(default=None, exclude=True)


@runtime_checkable
class OutputPreparer(Protocol):
    def prepare_output(
        self,
        image: Image.Image,
        config: OutputPreparationConfig,
    ) -> OutputPreparationResult: ...
