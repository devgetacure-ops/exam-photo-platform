import io
from typing import List, Optional

from PIL import Image
from pydantic import BaseModel

from exam_photo.providers.output_compression import OutputCompressionConfig

#: A finished photograph under the examination's published minimum size.
#: Reported on the file, never a reason to withhold it.
BELOW_MINIMUM_CODE = "PIPELINE_FINAL_BYTE_SIZE_BELOW_MINIMUM"


class FinalValidationReport(BaseModel):
    is_valid: bool
    issue_codes: List[str]
    actual_width: Optional[int] = None
    actual_height: Optional[int] = None
    actual_bytes: Optional[int] = None
    actual_format: Optional[str] = None
    actual_dpi: Optional[int] = None
    metadata_stripped: bool = False


def validate_final_candidate(
    encoded_bytes: Optional[bytes],
    expected_width: int,
    expected_height: int,
    config: OutputCompressionConfig,
) -> FinalValidationReport:
    issue_codes = []

    if not encoded_bytes:
        issue_codes.append("PIPELINE_FINAL_DECODE_FAILED")
        return FinalValidationReport(is_valid=False, issue_codes=issue_codes)

    actual_size = len(encoded_bytes)

    # Decode check
    try:
        buf = io.BytesIO(encoded_bytes)
        img = Image.open(buf)
        img.load()
        actual_width = img.width
        actual_height = img.height
        actual_format = img.format.upper() if img.format else "UNKNOWN"
        actual_dpi = _extract_square_dpi(img)
        has_exif = "exif" in img.info
        metadata_stripped = not has_exif
    except Exception:
        issue_codes.append("PIPELINE_FINAL_DECODE_FAILED")
        return FinalValidationReport(is_valid=False, issue_codes=issue_codes)

    # Verify dimensions
    if actual_width != expected_width or actual_height != expected_height:
        issue_codes.append("PIPELINE_FINAL_DIMENSIONS_INVALID")

    # Verify format (must be JPEG)
    if actual_format != "JPEG":
        issue_codes.append("PIPELINE_FINAL_FORMAT_INVALID")

    # Verify DPI when the rule supplies an explicit target.
    if config.target_dpi is not None and actual_dpi != config.target_dpi:
        issue_codes.append("PIPELINE_FINAL_DPI_INVALID")

    # Verify file size limits. Over the ceiling is a file the portal refuses
    # outright, so it fails. Under a published minimum is reported, not failed
    # (DEC-041, DEC-051): the compressor has already taken the largest honest
    # encoding, and the alternative is handing the candidate nothing at all.
    if actual_size > config.maximum_bytes:
        issue_codes.append("PIPELINE_FINAL_BYTE_SIZE_INVALID")
    elif config.minimum_bytes is not None and actual_size < config.minimum_bytes:
        issue_codes.append(BELOW_MINIMUM_CODE)

    # Verify metadata stripped
    if not metadata_stripped:
        issue_codes.append("COMPRESSION_METADATA_STRIP_FAILED")

    is_valid = all(code == BELOW_MINIMUM_CODE for code in issue_codes)

    return FinalValidationReport(
        is_valid=is_valid,
        issue_codes=issue_codes,
        actual_width=actual_width,
        actual_height=actual_height,
        actual_bytes=actual_size,
        actual_format=actual_format,
        actual_dpi=actual_dpi,
        metadata_stripped=metadata_stripped,
    )


def _extract_square_dpi(image: Image.Image) -> Optional[int]:
    dpi_value = image.info.get("dpi")
    if not isinstance(dpi_value, tuple) or len(dpi_value) < 2:
        return None
    x_dpi, y_dpi = dpi_value[:2]
    try:
        x_int = int(round(float(x_dpi)))
        y_int = int(round(float(y_dpi)))
    except (TypeError, ValueError):
        return None
    if x_int != y_int:
        return None
    return x_int
