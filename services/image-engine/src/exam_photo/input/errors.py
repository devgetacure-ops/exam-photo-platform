from enum import Enum
from typing import Any, Dict, Optional


class InputErrorCode(str, Enum):
    INPUT_EMPTY = "INPUT_EMPTY"
    INPUT_TOO_LARGE = "INPUT_TOO_LARGE"
    INPUT_SIGNATURE_UNSUPPORTED = "INPUT_SIGNATURE_UNSUPPORTED"
    INPUT_SIGNATURE_CONFLICT = "INPUT_SIGNATURE_CONFLICT"
    INPUT_DECODE_FAILED = "INPUT_DECODE_FAILED"
    INPUT_CORRUPTED = "INPUT_CORRUPTED"
    INPUT_TRUNCATED = "INPUT_TRUNCATED"
    INPUT_DIMENSIONS_EXCEEDED = "INPUT_DIMENSIONS_EXCEEDED"
    INPUT_PIXEL_COUNT_EXCEEDED = "INPUT_PIXEL_COUNT_EXCEEDED"
    INPUT_MULTIFRAME_UNSUPPORTED = "INPUT_MULTIFRAME_UNSUPPORTED"
    INPUT_FORMAT_NOT_ALLOWED = "INPUT_FORMAT_NOT_ALLOWED"
    INPUT_CONFIGURATION_INVALID = "INPUT_CONFIGURATION_INVALID"


class InputWarningCode(str, Enum):
    INPUT_EXTENSION_MISMATCH = "INPUT_EXTENSION_MISMATCH"
    INPUT_ORIENTATION_METADATA_INVALID = "INPUT_ORIENTATION_METADATA_INVALID"
    INPUT_COLOUR_MODE_CONVERTED = "INPUT_COLOUR_MODE_CONVERTED"
    INPUT_ICC_PROFILE_INVALID = "INPUT_ICC_PROFILE_INVALID"
    INPUT_METADATA_REMOVED = "INPUT_METADATA_REMOVED"


class ImageInspectionError(Exception):
    """Base exception for input image inspection failures."""

    def __init__(
        self,
        code: InputErrorCode,
        message: str,
        suggested_resolution: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.suggested_resolution = suggested_resolution
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        safe_context = {
            k: v
            for k, v in self.context.items()
            if not k.startswith("internal_") and "error" not in k.lower()
        }
        return {
            "error_code": self.code.value,
            "message": self.message,
            "suggested_resolution": self.suggested_resolution,
            "context": safe_context,
        }
