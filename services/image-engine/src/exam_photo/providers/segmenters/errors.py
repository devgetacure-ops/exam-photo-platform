"""Typed exceptions for subject segmentation operations."""

from exam_photo.providers.model_errors import (
    ModelChecksumError as ModelChecksumError,
)
from exam_photo.providers.model_errors import (
    ModelNotFoundError as ModelNotFoundError,
)


class SegmentationError(RuntimeError):
    """Base exception class for all subject segmentation errors."""

    pass


class SegmentationOutputError(SegmentationError):
    """Raised when the output of the segmentation model is invalid or malformed."""

    pass


class SegmentationModelConfigurationError(SegmentationError):
    """Raised when there is an issue with model initialization or configuration parameters."""

    pass
