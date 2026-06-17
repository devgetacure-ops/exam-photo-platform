from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class SourceImageMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_basename: str
    encoded_byte_size: int
    signature_detected_format: Optional[str]
    decoder_detected_format: Optional[str]
    original_width: int
    original_height: int
    normalized_width: int
    normalized_height: int
    total_pixels: int
    original_mode: str
    normalized_mode: str
    frame_count: int
    orientation_tag_present: bool
    orientation_operation: Optional[str] = None
    orientation_applied: bool
    alpha_present: bool
    metadata_present: bool
    icc_profile_present: bool
    icc_conversion_status: str
    extension_mismatch: bool
    warnings: List[str]
    warning_codes: List[str]
