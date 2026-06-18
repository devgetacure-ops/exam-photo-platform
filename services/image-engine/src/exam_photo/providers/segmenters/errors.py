"""Typed exceptions for subject segmentation operations."""


class SegmentationError(RuntimeError):
    """Base exception class for all subject segmentation errors."""

    pass


class ModelNotFoundError(SegmentationError):
    """Raised when the segmentation model asset file does not exist."""

    pass


class ModelChecksumError(SegmentationError):
    """Raised when the SHA-256 digest of the model file does not match expected."""

    pass


class SegmentationOutputError(SegmentationError):
    """Raised when the output of the segmentation model is invalid or malformed."""

    pass


class SegmentationModelConfigurationError(SegmentationError):
    """Raised when there is an issue with model initialization or configuration parameters."""

    pass
