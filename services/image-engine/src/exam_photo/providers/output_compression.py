from enum import Enum
from typing import List, Protocol, runtime_checkable

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, model_validator

from exam_photo.suitability.issue_codes import IssueSeverity


class CompressionFormat(str, Enum):
    JPEG = "jpeg"


class CompressionSearchMode(str, Enum):
    BINARY_SEARCH = "binary_search"
    LINEAR_FALLBACK = "linear_fallback"


class OutputCompressionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_format: CompressionFormat = CompressionFormat.JPEG

    maximum_bytes: int
    minimum_bytes: int | None = Field(default=None, ge=0)

    target_ceiling_ratio: float = 0.96
    safety_margin_bytes: int = 512

    min_quality: int = 35
    # Raised from 95 so spare size budget is spent on retained quality rather
    # than left unused: with a generous ceiling the search previously stopped at
    # 95 and emitted a file using only ~60% of the permitted bytes.  Held below
    # 100 because JPEG quality above ~98 inflates size sharply for no visible
    # gain, which would waste the same budget in the opposite direction.
    max_quality: int = 98
    initial_quality: int = 92

    max_iterations: int = 10
    search_mode: CompressionSearchMode = CompressionSearchMode.BINARY_SEARCH

    optimize: bool = True
    progressive: bool = False
    strip_metadata: bool = True
    target_dpi: int | None = Field(default=None, gt=0)

    allow_quality_below_minimum: bool = False
    allow_oversize_output: bool = False

    generate_preview: bool = True

    @model_validator(mode="after")
    def validate_config(self) -> "OutputCompressionConfig":
        if self.maximum_bytes <= 0:
            raise ValueError("maximum_bytes must be positive")
        if self.minimum_bytes is not None:
            if self.minimum_bytes < 0:
                raise ValueError("minimum_bytes must be non-negative")
            if self.minimum_bytes > self.maximum_bytes:
                raise ValueError("minimum_bytes cannot exceed maximum_bytes")
        if not (0.0 < self.target_ceiling_ratio <= 1.0):
            raise ValueError("target_ceiling_ratio must be in (0.0, 1.0]")
        if not (0 <= self.safety_margin_bytes < self.maximum_bytes):
            raise ValueError("safety_margin_bytes must be in [0, maximum_bytes)")
        if not (1 <= self.min_quality <= self.max_quality <= 100):
            raise ValueError(
                "quality range must satisfy 1 <= min_quality <= max_quality <= 100"
            )
        if not (self.min_quality <= self.initial_quality <= self.max_quality):
            raise ValueError(
                "initial_quality must be between min_quality and max_quality"
            )
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")
        return self


class OutputCompressionIssueCode(str, Enum):
    COMPRESSION_INPUT_INVALID = "COMPRESSION_INPUT_INVALID"
    COMPRESSION_FORMAT_UNSUPPORTED = "COMPRESSION_FORMAT_UNSUPPORTED"
    COMPRESSION_SIZE_LIMIT_INVALID = "COMPRESSION_SIZE_LIMIT_INVALID"
    COMPRESSION_QUALITY_RANGE_INVALID = "COMPRESSION_QUALITY_RANGE_INVALID"
    COMPRESSION_TARGET_TOO_SMALL = "COMPRESSION_TARGET_TOO_SMALL"
    COMPRESSION_MIN_SIZE_NOT_REACHED = "COMPRESSION_MIN_SIZE_NOT_REACHED"
    COMPRESSION_MAX_SIZE_EXCEEDED = "COMPRESSION_MAX_SIZE_EXCEEDED"
    COMPRESSION_QUALITY_TOO_LOW = "COMPRESSION_QUALITY_TOO_LOW"
    COMPRESSION_DECODE_FAILED = "COMPRESSION_DECODE_FAILED"
    COMPRESSION_METADATA_STRIP_FAILED = "COMPRESSION_METADATA_STRIP_FAILED"
    COMPRESSION_SEARCH_FAILED = "COMPRESSION_SEARCH_FAILED"
    COMPRESSION_PROVIDER_FAILED = "COMPRESSION_PROVIDER_FAILED"


class OutputCompressionValidationIssue(BaseModel):
    code: OutputCompressionIssueCode
    severity: IssueSeverity
    blocking_for_processing: bool
    confidence: float = 1.0


class OutputCompressionValidationReport(BaseModel):
    is_valid: bool
    issue_codes: List[OutputCompressionIssueCode]
    issues: List[OutputCompressionValidationIssue]

    format_supported: bool
    maximum_size_satisfied: bool
    minimum_size_satisfied: bool | None = None
    quality_within_bounds: bool
    decode_after_encode_valid: bool
    metadata_stripped: bool
    dpi_satisfied: bool | None = None

    target_bytes: int
    actual_bytes: int | None = None
    actual_dpi: int | None = None
    byte_size_ratio_to_max: float | None = None
    final_quality: int | None = None
    iterations_used: int = 0


class OutputCompressionResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    provider_name: str
    provider_version: str

    target_format: CompressionFormat | str
    source_width: int
    source_height: int

    maximum_bytes: int
    target_bytes: int
    actual_bytes: int

    final_quality: int | None = None
    min_quality: int
    max_quality: int
    iterations_used: int

    search_mode: CompressionSearchMode
    optimize: bool
    progressive: bool
    metadata_stripped: bool
    target_dpi: int | None = None
    actual_dpi: int | None = None

    validation: OutputCompressionValidationReport
    processing_duration_ms: float

    encoded_bytes: bytes | None = Field(default=None, exclude=True)


@runtime_checkable
class OutputCompressor(Protocol):
    def compress_output(
        self,
        image: Image.Image,
        config: OutputCompressionConfig,
    ) -> OutputCompressionResult: ...
