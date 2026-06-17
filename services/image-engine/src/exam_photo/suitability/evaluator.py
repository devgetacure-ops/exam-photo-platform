import time
from typing import Any, Dict, List, Optional

from exam_photo.input.normalization import NormalizationResult
from exam_photo.providers.face_detection import (
    FaceDetectionProvider,
    FaceDetectionResult,
)
from exam_photo.providers.head_estimation import (
    BoundaryVisibilityValue,
    HeadEstimationProvider,
    HeadEstimationResult,
)
from exam_photo.suitability.configuration import SuitabilityThresholds
from exam_photo.suitability.guidance import get_safe_user_guidance
from exam_photo.suitability.issue_codes import SuitabilityIssueCode
from exam_photo.suitability.models import (
    IssueSeverity,
    IssueStatus,
    SuitabilityIssue,
    SuitabilityReport,
    SuitabilityStatus,
)
from exam_photo.suitability.quality_metrics import calculate_image_quality_metrics


class SuitabilityEvaluator:
    def __init__(
        self,
        thresholds: SuitabilityThresholds,
        face_provider: Optional[FaceDetectionProvider] = None,
        head_provider: Optional[HeadEstimationProvider] = None,
    ) -> None:
        self.thresholds = thresholds
        self.face_provider = face_provider
        self.head_provider = head_provider
        self.version = "1.0.0"

    def evaluate(self, norm_result: NormalizationResult) -> SuitabilityReport:
        start_time = time.perf_counter()
        image = norm_result.image

        # 1. Quality Calculations
        metrics = calculate_image_quality_metrics(image)

        issues: List[SuitabilityIssue] = []
        warnings: List[str] = []
        checks_completed: List[str] = [
            "dimensions",
            "pixel_count",
            "luminance",
            "contrast",
            "transparency",
            "sharpness",
        ]
        checks_unavailable: List[str] = []
        provider_status: Dict[str, str] = {
            "face_detector": "not_configured",
            "head_estimator": "not_configured",
        }

        # 2. Apply preliminary image-wide checks
        self._apply_global_checks(metrics, issues, warnings)

        # 3. Call Face Detection Provider
        face_result: Optional[FaceDetectionResult] = None
        if self.face_provider is None:
            provider_status["face_detector"] = "unavailable"
            checks_unavailable.extend(
                ["face_presence", "pose", "eyes_visibility", "occlusion"]
            )
            # Record face check unavailable issue
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_FACE_CHECK_UNAVAILABLE,
                    severity=IssueSeverity.WARNING,
                    category="face",
                    message="Face detection provider is not configured.",
                    blocking=False,
                    status=IssueStatus.UNAVAILABLE,
                )
            )
        else:
            provider_status["face_detector"] = "active"
            try:
                # Run provider
                face_result = self.face_provider.detect_faces(image)
                checks_completed.append("face_presence")

                # Check face count
                faces = face_result.detections
                if len(faces) == 0:
                    issues.append(
                        self._create_issue(
                            code=SuitabilityIssueCode.SUITABILITY_NO_FACE,
                            severity=IssueSeverity.ERROR,
                            category="face",
                            message="No faces detected in the image.",
                            blocking=True,
                            status=IssueStatus.CONFIRMED,
                        )
                    )
                elif len(faces) > 1:
                    issues.append(
                        self._create_issue(
                            code=SuitabilityIssueCode.SUITABILITY_MULTIPLE_FACES,
                            severity=IssueSeverity.ERROR,
                            category="face",
                            message=f"Multiple faces ({len(faces)}) detected in the image.",
                            blocking=True,
                            status=IssueStatus.CONFIRMED,
                        )
                    )
                else:
                    # Exactly one face
                    face = faces[0]
                    self._apply_face_checks(
                        face, issues, warnings, checks_completed, checks_unavailable
                    )
            except Exception as e:
                provider_status["face_detector"] = "failed"
                issues.append(
                    self._create_issue(
                        code=SuitabilityIssueCode.SUITABILITY_FACE_PROVIDER_FAILED,
                        severity=IssueSeverity.ERROR,
                        category="face",
                        message="Face detection provider failed. Please try again later.",
                        blocking=False,
                        status=IssueStatus.CONFIRMED,
                        internal_details=str(e),
                    )
                )

        # 4. Call Complete Head Estimation Provider
        if self.head_provider is None:
            provider_status["head_estimator"] = "unavailable"
            checks_unavailable.append("head_completeness")
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_HEAD_COMPLETENESS_UNAVAILABLE,
                    severity=IssueSeverity.WARNING,
                    category="head",
                    message="Head estimation provider is not configured.",
                    blocking=False,
                    status=IssueStatus.UNAVAILABLE,
                )
            )
        elif face_result is not None and len(face_result.detections) == 1:
            provider_status["head_estimator"] = "active"
            try:
                face = face_result.detections[0]
                head_result = self.head_provider.estimate_head(
                    image, face, face.landmarks
                )
                checks_completed.append("head_completeness")
                self._apply_head_checks(
                    head_result, issues, warnings, checks_completed, checks_unavailable
                )
            except Exception as e:
                provider_status["head_estimator"] = "failed"
                issues.append(
                    self._create_issue(
                        code=SuitabilityIssueCode.SUITABILITY_PROVIDER_ERROR,
                        severity=IssueSeverity.ERROR,
                        category="head",
                        message="Head estimation provider failed. Please try again later.",
                        blocking=False,
                        status=IssueStatus.CONFIRMED,
                        internal_details=str(e),
                    )
                )
        else:
            # Head estimation check is skipped because face is missing, multiple, or face provider failed
            provider_status["head_estimator"] = "skipped"
            checks_unavailable.append("head_completeness")

        # 5. Determine Overall Status
        has_blocking = any(
            iss.blocking for iss in issues if iss.status == IssueStatus.CONFIRMED
        )
        has_warning = (
            any(iss.severity == IssueSeverity.WARNING for iss in issues)
            or len(warnings) > 0
        )

        # Check if required checks could not run
        has_indeterminate = (
            self.face_provider is None
            or self.head_provider is None
            or provider_status["face_detector"] == "failed"
            or provider_status["head_estimator"] == "failed"
            or "top_hair_boundary" in checks_unavailable
            or "side_head_boundary" in checks_unavailable
            or "chin_boundary" in checks_unavailable
        )

        if has_blocking:
            overall_status = SuitabilityStatus.UNSUITABLE
        elif has_indeterminate:
            overall_status = SuitabilityStatus.INDETERMINATE
        elif has_warning:
            overall_status = SuitabilityStatus.SUITABLE_WITH_WARNINGS
        else:
            overall_status = SuitabilityStatus.SUITABLE

        # Create safe user guidance list (ordered by blocking issues first)
        guidance_messages: List[str] = []
        blocking_issues = [
            iss
            for iss in issues
            if iss.blocking and iss.status == IssueStatus.CONFIRMED
        ]
        non_blocking_issues = [iss for iss in issues if not iss.blocking]

        for iss in blocking_issues:
            if iss.safe_user_guidance not in guidance_messages:
                guidance_messages.append(iss.safe_user_guidance)
        for iss in non_blocking_issues:
            if iss.safe_user_guidance not in guidance_messages:
                guidance_messages.append(iss.safe_user_guidance)

        # Fallback if no issues
        if not guidance_messages:
            guidance_messages.append(
                "The photograph complies with general suitability standards."
            )

        duration = (time.perf_counter() - start_time) * 1000.0
        internal_summary = f"Evaluator run completed in {duration:.2f}ms. Status: {overall_status.value}."

        return SuitabilityReport(
            overall_status=overall_status,
            issues=issues,
            warnings=warnings,
            measurements=metrics,
            provider_status=provider_status,
            checks_completed=checks_completed,
            checks_unavailable=checks_unavailable,
            safe_user_guidance=guidance_messages,
            internal_summary=internal_summary,
            evaluator_version=self.version,
        )

    def _create_issue(
        self,
        code: SuitabilityIssueCode,
        severity: IssueSeverity,
        category: str,
        message: str,
        blocking: bool,
        status: IssueStatus,
        internal_details: Optional[str] = None,
    ) -> SuitabilityIssue:
        return SuitabilityIssue(
            code=code,
            severity=severity,
            category=category,
            message=message,
            safe_user_guidance=get_safe_user_guidance(code),
            blocking=blocking,
            confidence=1.0,
            status=status,
            internal_details=internal_details,
        )

    def _apply_global_checks(
        self,
        metrics: Dict[str, Any],
        issues: List[SuitabilityIssue],
        warnings: List[str],
    ) -> None:
        # Width / Height
        w = metrics["normalized_width"]
        h = metrics["normalized_height"]
        pixels = metrics["total_pixels"]

        if (
            w < self.thresholds.minimum_source_width
            or h < self.thresholds.minimum_source_height
        ):
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_RESOLUTION_TOO_LOW,
                    severity=IssueSeverity.ERROR,
                    category="dimensions",
                    message=f"Image dimensions ({w}x{h}) are below minimum limits ({self.thresholds.minimum_source_width}x{self.thresholds.minimum_source_height}).",
                    blocking=True,
                    status=IssueStatus.CONFIRMED,
                )
            )
        elif pixels < self.thresholds.minimum_source_pixels:
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_RESOLUTION_TOO_LOW,
                    severity=IssueSeverity.ERROR,
                    category="dimensions",
                    message=f"Total pixel count ({pixels}) is below minimum allowed ({self.thresholds.minimum_source_pixels}).",
                    blocking=True,
                    status=IssueStatus.CONFIRMED,
                )
            )

        # Exposure / luminance checks
        mean_lum = metrics["mean_luminance"]
        if mean_lum < self.thresholds.mean_luminance_blocking_low:
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_UNDEREXPOSED_SEVERE,
                    severity=IssueSeverity.ERROR,
                    category="exposure",
                    message=f"Severe underexposure detected (mean luminance: {mean_lum:.2f}).",
                    blocking=True,
                    status=IssueStatus.CONFIRMED,
                )
            )
        elif mean_lum < self.thresholds.mean_luminance_warning_low:
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_UNDEREXPOSED_WARNING,
                    severity=IssueSeverity.WARNING,
                    category="exposure",
                    message=f"Image may be underexposed (mean luminance: {mean_lum:.2f}).",
                    blocking=False,
                    status=IssueStatus.CONFIRMED,
                )
            )

        if mean_lum > self.thresholds.mean_luminance_blocking_high:
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_OVEREXPOSED_SEVERE,
                    severity=IssueSeverity.ERROR,
                    category="exposure",
                    message=f"Severe overexposure detected (mean luminance: {mean_lum:.2f}).",
                    blocking=True,
                    status=IssueStatus.CONFIRMED,
                )
            )
        elif mean_lum > self.thresholds.mean_luminance_warning_high:
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_OVEREXPOSED_WARNING,
                    severity=IssueSeverity.WARNING,
                    category="exposure",
                    message=f"Image may be overexposed (mean luminance: {mean_lum:.2f}).",
                    blocking=False,
                    status=IssueStatus.CONFIRMED,
                )
            )

        # Contrast
        contrast = metrics["luminance_std"]
        if contrast < self.thresholds.low_contrast_threshold:
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_LOW_CONTRAST_WARNING,
                    severity=IssueSeverity.WARNING,
                    category="exposure",
                    message=f"Low contrast detected (contrast/std: {contrast:.2f}).",
                    blocking=False,
                    status=IssueStatus.CONFIRMED,
                )
            )

        # Sharpness / Blur
        sharpness = metrics["global_sharpness_heuristic"]
        if sharpness < self.thresholds.blur_blocking_threshold:
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_BLUR_SEVERE,
                    severity=IssueSeverity.ERROR,
                    category="blur",
                    message=f"Severe image blur detected (sharpness: {sharpness:.2f}).",
                    blocking=True,
                    status=IssueStatus.CONFIRMED,
                )
            )
        elif sharpness < self.thresholds.blur_warning_threshold:
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_BLUR_WARNING,
                    severity=IssueSeverity.WARNING,
                    category="blur",
                    message=f"Image may be slightly blurred (sharpness: {sharpness:.2f}).",
                    blocking=False,
                    status=IssueStatus.CONFIRMED,
                )
            )

        # Transparency
        trans_ratio = metrics["transparent_pixel_ratio"]
        if trans_ratio >= self.thresholds.transparent_pixel_blocking_threshold:
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_EXCESSIVE_TRANSPARENCY,
                    severity=IssueSeverity.ERROR,
                    category="transparency",
                    message=f"Excessive transparent pixels ({trans_ratio * 100:.1f}%).",
                    blocking=True,
                    status=IssueStatus.CONFIRMED,
                )
            )
        elif trans_ratio >= self.thresholds.transparent_pixel_warning_threshold:
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_ALPHA_WARNING,
                    severity=IssueSeverity.WARNING,
                    category="transparency",
                    message=f"Transparency detected in image ({trans_ratio * 100:.1f}%).",
                    blocking=False,
                    status=IssueStatus.CONFIRMED,
                )
            )

    def _apply_face_checks(
        self,
        face: Any,
        issues: List[SuitabilityIssue],
        warnings: List[str],
        checks_completed: List[str],
        checks_unavailable: List[str],
    ) -> None:
        # Confidence
        if face.confidence < self.thresholds.face_confidence_threshold:
            # Record warning about face confidence, not necessarily blocking unless below hard min
            warnings.append(
                f"Face confidence ({face.confidence:.2f}) is below standard threshold."
            )

        # Pose Checks
        if face.pose is not None:
            checks_completed.append("pose")
            yaw_abs = abs(face.pose.yaw)
            pitch_abs = abs(face.pose.pitch)
            roll_abs = abs(face.pose.roll)

            if (
                yaw_abs >= self.thresholds.pose_blocking_yaw
                or pitch_abs >= self.thresholds.pose_blocking_pitch
                or roll_abs >= self.thresholds.pose_blocking_roll
            ):
                issues.append(
                    self._create_issue(
                        code=SuitabilityIssueCode.SUITABILITY_POSE_EXTREME,
                        severity=IssueSeverity.ERROR,
                        category="pose",
                        message=f"Extreme head tilt/rotation detected: yaw={face.pose.yaw}, pitch={face.pose.pitch}, roll={face.pose.roll}",
                        blocking=True,
                        status=IssueStatus.CONFIRMED,
                    )
                )
            elif (
                yaw_abs >= self.thresholds.pose_warning_yaw
                or pitch_abs >= self.thresholds.pose_warning_pitch
                or roll_abs >= self.thresholds.pose_warning_roll
            ):
                issues.append(
                    self._create_issue(
                        code=SuitabilityIssueCode.SUITABILITY_POSE_WARNING,
                        severity=IssueSeverity.WARNING,
                        category="pose",
                        message=f"Head slightly rotated/tilted: yaw={face.pose.yaw}, pitch={face.pose.pitch}, roll={face.pose.roll}",
                        blocking=False,
                        status=IssueStatus.CONFIRMED,
                    )
                )
        else:
            checks_unavailable.append("pose")
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_POSE_CHECK_UNAVAILABLE,
                    severity=IssueSeverity.WARNING,
                    category="pose",
                    message="Head pose estimation not returned by provider.",
                    blocking=False,
                    status=IssueStatus.UNAVAILABLE,
                )
            )

        # Occlusion Indicators
        if face.occlusion_indicators is not None:
            checks_completed.append("occlusion")
            occluded = face.occlusion_indicators.get("face_occluded", False)
            eyes_covered = face.occlusion_indicators.get("eyes_occluded", False)
            if occluded:
                issues.append(
                    self._create_issue(
                        code=SuitabilityIssueCode.SUITABILITY_FACE_OCCLUDED,
                        severity=IssueSeverity.ERROR,
                        category="occlusion",
                        message="Facial features are partially or fully occluded.",
                        blocking=True,
                        status=IssueStatus.CONFIRMED,
                    )
                )
            if eyes_covered:
                issues.append(
                    self._create_issue(
                        code=SuitabilityIssueCode.SUITABILITY_EYES_NOT_VISIBLE,
                        severity=IssueSeverity.ERROR,
                        category="occlusion",
                        message="Eyes are not visible or covered by sunglasses/clothing.",
                        blocking=True,
                        status=IssueStatus.CONFIRMED,
                    )
                )
        else:
            checks_unavailable.append("occlusion")
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_OCCLUSION_CHECK_UNAVAILABLE,
                    severity=IssueSeverity.WARNING,
                    category="occlusion",
                    message="Occlusion estimation not returned by provider.",
                    blocking=False,
                    status=IssueStatus.UNAVAILABLE,
                )
            )

    def _apply_head_checks(
        self,
        head: HeadEstimationResult,
        issues: List[SuitabilityIssue],
        warnings: List[str],
        checks_completed: List[str],
        checks_unavailable: List[str],
    ) -> None:
        visibility = head.boundary_visibility

        # Check boundary visibility variables
        if visibility.top_hair_boundary.state == BoundaryVisibilityValue.NOT_VISIBLE:
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_HEAD_TOP_CLIPPED,
                    severity=IssueSeverity.ERROR,
                    category="head",
                    message="Top of head or hair boundary appears clipped.",
                    blocking=True,
                    status=IssueStatus.CONFIRMED,
                )
            )
            checks_completed.append("top_hair_boundary")
        elif visibility.top_hair_boundary.state == BoundaryVisibilityValue.UNKNOWN:
            checks_unavailable.append("top_hair_boundary")
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_HEAD_COMPLETENESS_UNAVAILABLE,
                    severity=IssueSeverity.WARNING,
                    category="head",
                    message="Top hair boundary check unavailable.",
                    blocking=False,
                    status=IssueStatus.UNAVAILABLE,
                )
            )
        else:
            checks_completed.append("top_hair_boundary")

        if (
            visibility.left_head_boundary.state == BoundaryVisibilityValue.NOT_VISIBLE
            or visibility.right_head_boundary.state
            == BoundaryVisibilityValue.NOT_VISIBLE
        ):
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_HEAD_SIDE_CLIPPED,
                    severity=IssueSeverity.ERROR,
                    category="head",
                    message="Sides of head or ears appear clipped.",
                    blocking=True,
                    status=IssueStatus.CONFIRMED,
                )
            )
            checks_completed.append("side_head_boundary")
        elif (
            visibility.left_head_boundary.state == BoundaryVisibilityValue.UNKNOWN
            or visibility.right_head_boundary.state == BoundaryVisibilityValue.UNKNOWN
        ):
            checks_unavailable.append("side_head_boundary")
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_HEAD_COMPLETENESS_UNAVAILABLE,
                    severity=IssueSeverity.WARNING,
                    category="head",
                    message="Side head boundary check unavailable.",
                    blocking=False,
                    status=IssueStatus.UNAVAILABLE,
                )
            )
        else:
            checks_completed.append("side_head_boundary")

        if visibility.chin_boundary.state == BoundaryVisibilityValue.NOT_VISIBLE:
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_CHIN_CLIPPED,
                    severity=IssueSeverity.ERROR,
                    category="head",
                    message="Chin is clipped or out of frame.",
                    blocking=True,
                    status=IssueStatus.CONFIRMED,
                )
            )
            checks_completed.append("chin_boundary")
        elif visibility.chin_boundary.state == BoundaryVisibilityValue.UNKNOWN:
            checks_unavailable.append("chin_boundary")
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_HEAD_COMPLETENESS_UNAVAILABLE,
                    severity=IssueSeverity.WARNING,
                    category="head",
                    message="Chin boundary check unavailable.",
                    blocking=False,
                    status=IssueStatus.UNAVAILABLE,
                )
            )
        else:
            checks_completed.append("chin_boundary")

        if visibility.lower_beard_boundary.state == BoundaryVisibilityValue.NOT_VISIBLE:
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_BEARD_BOUNDARY_CLIPPED,
                    severity=IssueSeverity.WARNING,
                    category="head",
                    message="Beard boundary is partially clipped.",
                    blocking=False,
                    status=IssueStatus.CONFIRMED,
                )
            )
            checks_completed.append("beard_boundary")
        elif visibility.lower_beard_boundary.state == BoundaryVisibilityValue.UNKNOWN:
            checks_unavailable.append("beard_boundary")
        else:
            checks_completed.append("beard_boundary")

        # Check overall head estimation confidence
        if head.confidence < 0.5:
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_HEAD_ESTIMATION_LOW_CONFIDENCE,
                    severity=IssueSeverity.WARNING,
                    category="head",
                    message="Head estimation has low confidence.",
                    blocking=False,
                    status=IssueStatus.CONFIRMED,
                )
            )

        # Check if clamping occurred
        meta = head.safe_internal_metadata or {}
        if meta.get("clamped", False):
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_HEAD_BOX_CLAMPED,
                    severity=IssueSeverity.WARNING,
                    category="head",
                    message="Head bounding box was clamped to the image edge.",
                    blocking=False,
                    status=IssueStatus.CONFIRMED,
                )
            )
