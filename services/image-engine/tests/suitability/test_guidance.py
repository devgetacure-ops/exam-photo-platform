from exam_photo.suitability.guidance import get_safe_user_guidance
from exam_photo.suitability.issue_codes import SuitabilityIssueCode


def test_guidance_mapping() -> None:
    guidance = get_safe_user_guidance(SuitabilityIssueCode.SUITABILITY_NO_FACE)
    assert "one person" in guidance

    guidance_blur = get_safe_user_guidance(SuitabilityIssueCode.SUITABILITY_BLUR_SEVERE)
    assert "too blurred" in guidance_blur

    # Fallback default
    guidance_unknown = get_safe_user_guidance("SOME_UNKNOWN_CODE")  # type: ignore[arg-type]
    assert "could not be fully assessed" in guidance_unknown
