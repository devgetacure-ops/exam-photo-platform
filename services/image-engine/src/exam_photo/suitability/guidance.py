from typing import Dict

from exam_photo.suitability.issue_codes import SuitabilityIssueCode

_GUIDANCE_MAP: Dict[SuitabilityIssueCode, str] = {
    # Face presence
    SuitabilityIssueCode.SUITABILITY_NO_FACE: (
        "Upload a clear, front-facing photograph containing one person."
    ),
    SuitabilityIssueCode.SUITABILITY_MULTIPLE_FACES: (
        "Upload a photograph containing only the candidate."
    ),
    SuitabilityIssueCode.SUITABILITY_FACE_CHECK_UNAVAILABLE: (
        "Face presence validation could not be completed. Please try again."
    ),
    SuitabilityIssueCode.SUITABILITY_FACE_PROVIDER_FAILED: (
        "The face analyzer failed. Please check the image file format."
    ),
    # Resolution & dimensions
    SuitabilityIssueCode.SUITABILITY_RESOLUTION_TOO_LOW: (
        "The uploaded photo resolution is too low. Please upload a higher resolution image."
    ),
    SuitabilityIssueCode.SUITABILITY_FACE_REGION_TOO_SMALL: (
        "The face occupies too small a region. Please stand closer to the camera."
    ),
    SuitabilityIssueCode.SUITABILITY_RESOLUTION_WARNING: (
        "The photo resolution is near minimum limits. A clearer photo is recommended."
    ),
    # Blur & focus
    SuitabilityIssueCode.SUITABILITY_BLUR_SEVERE: (
        "Upload a sharper photograph. The current image appears too blurred for reliable processing."
    ),
    SuitabilityIssueCode.SUITABILITY_BLUR_WARNING: (
        "The photograph is slightly blurred. Please ensure the camera is in focus."
    ),
    SuitabilityIssueCode.SUITABILITY_FOCUS_CHECK_UNCERTAIN: (
        "Focus checks are uncertain. Please inspect quality manually."
    ),
    # Exposure & lighting
    SuitabilityIssueCode.SUITABILITY_UNDEREXPOSED_SEVERE: (
        "Upload a better-lit photograph where the face is clearly visible."
    ),
    SuitabilityIssueCode.SUITABILITY_UNDEREXPOSED_WARNING: (
        "The photo is slightly dark. Please ensure even lighting."
    ),
    SuitabilityIssueCode.SUITABILITY_OVEREXPOSED_SEVERE: (
        "Upload a photograph with less glare or bright light."
    ),
    SuitabilityIssueCode.SUITABILITY_OVEREXPOSED_WARNING: (
        "The photo contains bright regions. Shadows or glare should be avoided."
    ),
    SuitabilityIssueCode.SUITABILITY_LOW_CONTRAST_WARNING: (
        "The image has low contrast. Try capturing with a clean contrast backdrop."
    ),
    # Pose
    SuitabilityIssueCode.SUITABILITY_POSE_EXTREME: (
        "Ensure your head is looking straight at the camera without tilting."
    ),
    SuitabilityIssueCode.SUITABILITY_POSE_WARNING: (
        "Your face is slightly turned. A straight-ahead pose is recommended."
    ),
    SuitabilityIssueCode.SUITABILITY_POSE_CHECK_UNAVAILABLE: (
        "Face pose could not be validated. Please try again."
    ),
    # Head completeness
    SuitabilityIssueCode.SUITABILITY_HEAD_TOP_CLIPPED: (
        "Upload a photograph showing the complete hair boundary."
    ),
    SuitabilityIssueCode.SUITABILITY_HEAD_SIDE_CLIPPED: (
        "Upload a photograph showing both ears and complete cheeks."
    ),
    SuitabilityIssueCode.SUITABILITY_CHIN_CLIPPED: (
        "Upload a photograph showing the complete chin boundary."
    ),
    SuitabilityIssueCode.SUITABILITY_BEARD_BOUNDARY_CLIPPED: (
        "Upload a photograph showing the complete beard boundary."
    ),
    SuitabilityIssueCode.SUITABILITY_HEAD_COMPLETENESS_UNAVAILABLE: (
        "Head completeness checks could not be computed."
    ),
    # Eyes & occlusion
    SuitabilityIssueCode.SUITABILITY_EYES_NOT_VISIBLE: (
        "Ensure your eyes are open and clearly visible without sunglasses or hats."
    ),
    SuitabilityIssueCode.SUITABILITY_FACE_OCCLUDED: (
        "Please remove face coverings, masks, or objects blocking your face."
    ),
    SuitabilityIssueCode.SUITABILITY_OCCLUSION_CHECK_UNAVAILABLE: (
        "Face occlusion check was unavailable."
    ),
    # Transparency
    SuitabilityIssueCode.SUITABILITY_EXCESSIVE_TRANSPARENCY: (
        "The photograph is transparent or blank. Please upload an opaque image."
    ),
    SuitabilityIssueCode.SUITABILITY_ALPHA_WARNING: (
        "The photograph contains transparent borders. Keep borders solid."
    ),
    # Provider errors
    SuitabilityIssueCode.SUITABILITY_PROVIDER_UNAVAILABLE: (
        "The photograph could not be fully assessed. Please try again later or upload another clear photo."
    ),
    SuitabilityIssueCode.SUITABILITY_PROVIDER_ERROR: (
        "An internal error occurred during verification. Please try again later."
    ),
    SuitabilityIssueCode.SUITABILITY_CHECK_INDETERMINATE: (
        "Verification was inconclusive. Please ensure the image is a standard JPG or PNG."
    ),
    # Segmentation errors and warnings
    SuitabilityIssueCode.SEGMENTATION_PROVIDER_UNAVAILABLE: (
        "Portrait segmentation check is temporarily unavailable."
    ),
    SuitabilityIssueCode.SEGMENTATION_PROVIDER_FAILED: (
        "Portrait segmentation failed. Please try again."
    ),
    SuitabilityIssueCode.SEGMENTATION_MODEL_MISSING: (
        "Segmentation model file is missing."
    ),
    SuitabilityIssueCode.SEGMENTATION_MODEL_CHECKSUM_FAILED: (
        "Segmentation model file checksum verification failed."
    ),
    SuitabilityIssueCode.SEGMENTATION_OUTPUT_INVALID: (
        "Invalid output from portrait segmentation."
    ),
    SuitabilityIssueCode.SEGMENTATION_MASK_EMPTY: (
        "No clear subject boundary could be detected in the photograph."
    ),
    SuitabilityIssueCode.SEGMENTATION_MASK_FULL_FRAME: (
        "Could not separate the subject from the background."
    ),
    SuitabilityIssueCode.SEGMENTATION_MASK_DIMENSION_MISMATCH: (
        "Internal dimension mismatch during segmentation."
    ),
    SuitabilityIssueCode.SEGMENTATION_MASK_NONFINITE: (
        "Invalid values detected in subject segmentation."
    ),
    SuitabilityIssueCode.SEGMENTATION_FACE_NOT_CONTAINED: (
        "The candidate's face is not correctly positioned within the detected subject region."
    ),
    SuitabilityIssueCode.SEGMENTATION_HEAD_REGION_LOW_COVERAGE: (
        "The detected subject does not fully cover the estimated head region."
    ),
    SuitabilityIssueCode.SEGMENTATION_FOREGROUND_FRAGMENTED: (
        "The detected subject region is fragmented or disconnected."
    ),
    SuitabilityIssueCode.SEGMENTATION_MULTIPLE_MAJOR_COMPONENTS: (
        "Multiple disconnected subject regions detected."
    ),
    SuitabilityIssueCode.SEGMENTATION_FOREGROUND_COVERAGE_LOW: (
        "The candidate covers too small a portion of the photograph."
    ),
    SuitabilityIssueCode.SEGMENTATION_FOREGROUND_COVERAGE_HIGH: (
        "The candidate covers too large a portion of the photograph."
    ),
    SuitabilityIssueCode.SEGMENTATION_EDGE_CONTACT_WARNING: (
        "The candidate is touching or cut off by the frame boundary."
    ),
    SuitabilityIssueCode.SEGMENTATION_UNCERTAIN_EDGE_HIGH: (
        "The boundary between candidate and background is excessively blurry or uncertain."
    ),
}


def get_safe_user_guidance(code: SuitabilityIssueCode) -> str:
    """Returns deterministic clear user guidance for a given issue code."""
    return _GUIDANCE_MAP.get(
        code,
        "The photograph could not be fully assessed. Please try again later or upload another clear photo.",
    )
