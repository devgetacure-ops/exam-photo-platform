import os
import threading
from typing import List

from PIL import Image, ImageFile, ImageOps

from exam_photo.input.errors import (
    ImageInspectionError,
    InputErrorCode,
    InputWarningCode,
)
from exam_photo.input.limits import InputLimits
from exam_photo.input.metadata import SourceImageMetadata
from exam_photo.input.signatures import detect_signature_format

try:
    from PIL import ImageCms

    HAS_IMAGE_CMS = True
except ImportError:
    ImageCms = None  # type: ignore[assignment,unused-ignore]
    HAS_IMAGE_CMS = False

_pillow_load_lock = threading.Lock()


class NormalizationResult:
    def __init__(
        self,
        image: Image.Image,
        metadata: SourceImageMetadata,
        warnings: List[InputWarningCode],
    ) -> None:
        self.image = image
        self.metadata = metadata
        self.warnings = warnings


def normalize_image_input(
    data: bytes,
    filename: str,
    limits: InputLimits,
) -> NormalizationResult:
    """Safely normalizes raw image bytes into a canonical RGBA in-memory representation.

    Enforces limits, signatures, safe decoding, transposes orientations, conversions,
    and returns a NormalizationResult containing the in-memory Image and metadata records.
    """
    warnings: List[str] = []
    warning_codes: List[InputWarningCode] = []

    # 1. File-size Preflight
    byte_size = len(data)
    if byte_size == 0:
        raise ImageInspectionError(
            InputErrorCode.INPUT_EMPTY,
            "Uploaded image file is empty.",
            "Please select a valid non-empty photograph file.",
        )
    if byte_size > limits.maximum_encoded_byte_size:
        raise ImageInspectionError(
            InputErrorCode.INPUT_TOO_LARGE,
            f"Uploaded file size ({byte_size} bytes) exceeds maximum limit ({limits.maximum_encoded_byte_size} bytes).",
            "Please compress the photograph or choose a smaller file.",
        )

    # 2. Signature verification
    sig_format = detect_signature_format(data)
    if not sig_format:
        raise ImageInspectionError(
            InputErrorCode.INPUT_SIGNATURE_UNSUPPORTED,
            "Unsupported image file signature. Only JPEG and PNG formats are supported.",
            "Please convert the photograph to JPEG or PNG format.",
        )

    # Check allowed formats
    if sig_format not in limits.allowed_actual_formats:
        raise ImageInspectionError(
            InputErrorCode.INPUT_FORMAT_NOT_ALLOWED,
            f"The format detected by file signature ({sig_format}) is not allowed by limits.",
            "Please use a permitted format.",
        )

    # Extension mismatch check
    basename = os.path.basename(filename)
    _, ext = os.path.splitext(basename.lower())
    ext_cleaned = ext.lstrip(".")
    if ext_cleaned == "jpg":
        ext_cleaned = "jpeg"

    extension_mismatch = False
    if ext_cleaned != sig_format:
        extension_mismatch = True
        if limits.extension_mismatch_policy == "reject":
            raise ImageInspectionError(
                InputErrorCode.INPUT_SIGNATURE_CONFLICT,
                f"File signature format ({sig_format}) does not match extension ({ext}).",
                "Please rename the file extension to match the actual format.",
            )
        else:
            warnings.append(
                f"Extension mismatch: file claims '{ext}' but signature contains '{sig_format}' data."
            )
            warning_codes.append(InputWarningCode.INPUT_EXTENSION_MISMATCH)

    # 3. Safe Decode using PIL (wrapped stream load)
    import io

    stream = io.BytesIO(data)
    try:
        # Lazy open
        image = Image.open(stream)
    except Exception as e:
        raise ImageInspectionError(
            InputErrorCode.INPUT_DECODE_FAILED,
            "Decoder failed to initialize image structure.",
            "Please ensure the file is not corrupted.",
            context={"internal_error": str(e)},
        ) from e

    # Verify format matches signature
    decoder_format = image.format.lower() if image.format else ""
    if decoder_format == "jpg":
        decoder_format = "jpeg"

    if decoder_format != sig_format:
        raise ImageInspectionError(
            InputErrorCode.INPUT_SIGNATURE_CONFLICT,
            f"Signature format ({sig_format}) contradicts decoder format ({decoder_format}).",
            "Please check if the file structure is corrupted.",
        )

    # Validate dimensions before loading pixels (prevent decomp bombs)
    original_width, original_height = image.size
    total_pixels = original_width * original_height

    if original_width > limits.maximum_width or original_height > limits.maximum_height:
        raise ImageInspectionError(
            InputErrorCode.INPUT_DIMENSIONS_EXCEEDED,
            f"Image dimensions ({original_width}x{original_height}) exceed maximum allowed limits.",
            "Please resize the image before uploading.",
        )

    if total_pixels > limits.maximum_total_pixel_count:
        raise ImageInspectionError(
            InputErrorCode.INPUT_PIXEL_COUNT_EXCEEDED,
            f"Image total pixels ({total_pixels}) exceeds safety limit.",
            "Please reduce resolution before uploading.",
        )

    # Truncation and corruption preflight checks by forcing pixel loading
    with _pillow_load_lock:
        old_load_truncated = ImageFile.LOAD_TRUNCATED_IMAGES
        try:
            if limits.truncated_image_policy == "allow":
                ImageFile.LOAD_TRUNCATED_IMAGES = True
            else:
                ImageFile.LOAD_TRUNCATED_IMAGES = False
            image.load()
        except Exception as e:
            # If it's a truncation error or load fail
            raise ImageInspectionError(
                InputErrorCode.INPUT_CORRUPTED,
                "File data is corrupted or truncated.",
                "Please re-upload a clean, complete image file.",
                context={"internal_error": str(e)},
            ) from e
        finally:
            ImageFile.LOAD_TRUNCATED_IMAGES = old_load_truncated

    # 4. Multi-frame check
    frame_count = getattr(image, "n_frames", 1)
    is_animated = getattr(image, "is_animated", False)
    if (frame_count > 1 or is_animated) and limits.multi_frame_policy == "reject":
        raise ImageInspectionError(
            InputErrorCode.INPUT_MULTIFRAME_UNSUPPORTED,
            "Animated or multi-frame images are not supported.",
            "Please upload a single-frame still candidate photograph.",
        )

    # 5. EXIF orientation normalization
    orientation_tag_present = False
    orientation_operation = None
    orientation_applied = False

    exif = image.getexif()
    if exif and 274 in exif:
        orientation_tag_present = True
        val = exif[274]
        if val in [2, 3, 4, 5, 6, 7, 8]:
            orientation_operation = f"transpose_{val}"
            try:
                # Perform rotation transpose safely
                rotated_image = ImageOps.exif_transpose(image)
                if rotated_image:
                    image = rotated_image
                    orientation_applied = True
            except Exception:
                warnings.append("Invalid orientation metadata found.")
                warning_codes.append(
                    InputWarningCode.INPUT_ORIENTATION_METADATA_INVALID
                )

    # Width and height of current displayed working mode
    normalized_width, normalized_height = image.size

    # 6. Mode Normalization
    original_mode = image.mode
    alpha_present = (
        "A" in original_mode
        or "a" in original_mode
        or (original_mode == "P" and "transparency" in image.info)
    )

    # Perform RGBA convert safely
    if original_mode != "RGBA":
        image = image.convert("RGBA")
        warnings.append(f"Colour mode converted from '{original_mode}' to 'RGBA'.")
        warning_codes.append(InputWarningCode.INPUT_COLOUR_MODE_CONVERTED)
    normalized_mode = image.mode

    # 7. ICC color profile check
    icc_profile_present = "icc_profile" in image.info
    icc_conversion_status = "none"

    if icc_profile_present and HAS_IMAGE_CMS:
        assert ImageCms is not None
        try:
            # Basic validation check and sRGB mapping boundary
            icc_bytes = image.info.get("icc_profile")
            if icc_bytes:
                src_profile = ImageCms.getProfileFromBytes(icc_bytes)  # type: ignore[attr-defined]
                # Attempt to map to standard sRGB
                srgb_profile = ImageCms.createProfile("sRGB")
                transform = ImageCms.buildTransform(
                    src_profile, srgb_profile, "RGBA", "RGBA"
                )
                transformed_image = ImageCms.applyTransform(image, transform)
                if transformed_image:
                    image = transformed_image
                    icc_conversion_status = "converted"
        except Exception:
            warnings.append("Ignoring invalid embedded ICC profile.")
            warning_codes.append(InputWarningCode.INPUT_ICC_PROFILE_INVALID)
            icc_conversion_status = "ignored"
    elif icc_profile_present:
        # ImageCms not available, keep profile as ignored/kept
        icc_conversion_status = "ignored"

    # 8. Metadata minimization (stripping original info maps)
    metadata_present = len(image.info) > 0
    if metadata_present:
        image.info = {}
        warnings.append("Unnecessary source metadata blocks stripped.")
        warning_codes.append(InputWarningCode.INPUT_METADATA_REMOVED)

    # Build response model
    metadata = SourceImageMetadata(
        source_basename=basename,
        encoded_byte_size=byte_size,
        signature_detected_format=sig_format,
        decoder_detected_format=decoder_format,
        original_width=original_width,
        original_height=original_height,
        normalized_width=normalized_width,
        normalized_height=normalized_height,
        total_pixels=total_pixels,
        original_mode=original_mode,
        normalized_mode=normalized_mode,
        frame_count=frame_count,
        orientation_tag_present=orientation_tag_present,
        orientation_operation=orientation_operation,
        orientation_applied=orientation_applied,
        alpha_present=alpha_present,
        metadata_present=metadata_present,
        icc_profile_present=icc_profile_present,
        icc_conversion_status=icc_conversion_status,
        extension_mismatch=extension_mismatch,
        warnings=warnings,
        warning_codes=[wc.value for wc in warning_codes],
    )

    return NormalizationResult(image, metadata, warning_codes)
