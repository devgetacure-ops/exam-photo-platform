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
from exam_photo.providers.model_errors import ModelChecksumError, ModelNotFoundError
from exam_photo.providers.segmenters.errors import SegmentationOutputError
from exam_photo.providers.subject_segmentation import (
    SegmentationConfig,
    SubjectSegmentationProvider,
)
from exam_photo.suitability.configuration import SuitabilityThresholds
from exam_photo.suitability.guidance import get_safe_user_guidance
from exam_photo.suitability.issue_codes import SuitabilityIssueCode
from exam_photo.suitability.models import (
    InternalSegmentationDiagnostic,
    IssueSeverity,
    IssueStatus,
    ProcessingReadinessStatus,
    SuitabilityCheck,
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
        segmentation_provider: Optional[SubjectSegmentationProvider] = None,
        segmentation_config: Optional[SegmentationConfig] = None,
    ) -> None:
        self.thresholds = thresholds
        self.face_provider = face_provider
        self.head_provider = head_provider
        self.segmentation_provider = segmentation_provider
        self.segmentation_config = segmentation_config
        self.version = "1.0.0"

    def evaluate(
        self,
        norm_result: NormalizationResult,
        background_replacement_required: bool = False,
    ) -> SuitabilityReport:
        start_time = time.perf_counter()
        image = norm_result.image

        # 1. Quality Calculations
        metrics = calculate_image_quality_metrics(image)

        issues: List[SuitabilityIssue] = []
        warnings: List[str] = []
        checks_completed: List[SuitabilityCheck] = [
            SuitabilityCheck.DIMENSIONS,
            SuitabilityCheck.PIXEL_COUNT,
            SuitabilityCheck.LUMINANCE,
            SuitabilityCheck.CONTRAST,
            SuitabilityCheck.TRANSPARENCY,
            SuitabilityCheck.SHARPNESS,
        ]
        checks_unavailable: List[SuitabilityCheck] = []
        provider_status: Dict[str, str] = {
            "face_detector": "not_configured",
            "head_estimator": "not_configured",
            "subject_segmenter": "not_configured",
        }

        # 2. Apply preliminary image-wide checks
        self._apply_global_checks(metrics, issues, warnings)

        # 3. Call Face Detection Provider
        face_result: Optional[FaceDetectionResult] = None
        if self.face_provider is None:
            provider_status["face_detector"] = "unavailable"
            checks_unavailable.extend(
                [
                    SuitabilityCheck.FACE_PRESENCE,
                    SuitabilityCheck.POSE,
                    SuitabilityCheck.EYES_VISIBILITY,
                    SuitabilityCheck.OCCLUSION,
                ]
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
                checks_completed.append(SuitabilityCheck.FACE_PRESENCE)
                if face_result.warnings:
                    warnings.extend(face_result.warnings)

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
                    policy = self.thresholds.multiple_face_handling_policy
                    is_reject = policy == "reject"
                    issues.append(
                        self._create_issue(
                            code=SuitabilityIssueCode.SUITABILITY_MULTIPLE_FACES,
                            severity=IssueSeverity.ERROR
                            if is_reject
                            else IssueSeverity.WARNING,
                            category="face",
                            message=f"Multiple faces ({len(faces)}) detected in the image.",
                            blocking=is_reject,
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
        head_result: Optional[HeadEstimationResult] = None
        if self.head_provider is None:
            provider_status["head_estimator"] = "unavailable"
            checks_unavailable.append(SuitabilityCheck.HEAD_COMPLETENESS)
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
                checks_completed.append(SuitabilityCheck.HEAD_COMPLETENESS)
                if head_result.warnings:
                    warnings.extend(head_result.warnings)
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
            checks_unavailable.append(SuitabilityCheck.HEAD_COMPLETENESS)

        # 5. Call Subject Segmentation Provider
        segmentation_diagnostic = None
        single_face = None
        if face_result is not None and len(face_result.detections) == 1:
            single_face = face_result.detections[0]

        head_box = None
        if head_result is not None:
            head_box = head_result.head_bounding_box

        if self.segmentation_provider is None:
            if background_replacement_required:
                provider_status["subject_segmenter"] = "unavailable"
                code = SuitabilityIssueCode.SEGMENTATION_PROVIDER_UNAVAILABLE
                issues.append(
                    self._create_issue(
                        code=code,
                        severity=IssueSeverity.ERROR,
                        category="background",
                        message="Portrait segmentation provider is not configured but background replacement is required.",
                        blocking=False,  # Not photographic blocking
                        status=IssueStatus.CONFIRMED,
                    )
                )
                segmentation_diagnostic = InternalSegmentationDiagnostic(
                    is_valid=False,
                    segmentation_status="unavailable",
                    issue_codes=[code.value],
                    safe_user_guidance=[get_safe_user_guidance(code)],
                    can_proceed=False,
                    provider_name="unknown",
                    provider_version="unknown",
                    model_name="unknown",
                    model_version="unknown",
                    threshold_used=0.0,
                    processing_duration_ms=0.0,
                    foreground_coverage_ratio=0.0,
                    uncertain_pixel_ratio=0.0,
                    connected_components_count=0,
                    largest_component_ratio=0.0,
                    face_contained=None,
                    head_region_coverage_ratio=None,
                    mask_width=0,
                    mask_height=0,
                    warnings=["Segmentation provider not configured"],
                )
            else:
                provider_status["subject_segmenter"] = "not_configured"
                code = SuitabilityIssueCode.SEGMENTATION_PROVIDER_UNAVAILABLE
                issues.append(
                    self._create_issue(
                        code=code,
                        severity=IssueSeverity.INFORMATION,
                        category="background",
                        message="Portrait segmentation provider is not configured.",
                        blocking=False,
                        status=IssueStatus.UNAVAILABLE,
                    )
                )
                segmentation_diagnostic = InternalSegmentationDiagnostic(
                    is_valid=False,
                    segmentation_status="unavailable",
                    issue_codes=[code.value],
                    safe_user_guidance=[get_safe_user_guidance(code)],
                    can_proceed=True,
                    provider_name="unknown",
                    provider_version="unknown",
                    model_name="unknown",
                    model_version="unknown",
                    threshold_used=0.0,
                    processing_duration_ms=0.0,
                    foreground_coverage_ratio=0.0,
                    uncertain_pixel_ratio=0.0,
                    connected_components_count=0,
                    largest_component_ratio=0.0,
                    face_contained=None,
                    head_region_coverage_ratio=None,
                    mask_width=0,
                    mask_height=0,
                    warnings=["Segmentation provider not configured"],
                )
            checks_unavailable.append(SuitabilityCheck.SUBJECT_SEGMENTATION)
        else:
            provider_status["subject_segmenter"] = "active"
            try:
                seg_result = self.segmentation_provider.segment_subject(
                    image,
                    face=single_face,
                    head_estimate=head_box,
                    config=self.segmentation_config,
                )
                val_report = seg_result.mask_validation
                checks_completed.append(SuitabilityCheck.SUBJECT_SEGMENTATION)

                if seg_result.warnings:
                    warnings.extend(seg_result.warnings)

                for issue_code_str in val_report.issue_codes:
                    issue_code = SuitabilityIssueCode(issue_code_str)
                    severity = (
                        IssueSeverity.WARNING
                        if background_replacement_required
                        else IssueSeverity.INFORMATION
                    )

                    if background_replacement_required:
                        if issue_code_str in [
                            "SEGMENTATION_MASK_EMPTY",
                            "SEGMENTATION_MASK_FULL_FRAME",
                            "SEGMENTATION_FACE_NOT_CONTAINED",
                            "SEGMENTATION_FOREGROUND_COVERAGE_LOW",
                            "SEGMENTATION_FOREGROUND_COVERAGE_HIGH",
                        ]:
                            severity = IssueSeverity.ERROR

                    issues.append(
                        self._create_issue(
                            code=issue_code,
                            severity=severity,
                            category="background",
                            message=f"Segmentation validation: {issue_code_str.replace('SEGMENTATION_', '').replace('_', ' ').lower()}",
                            blocking=False,  # Not photographic blocking
                            status=IssueStatus.CONFIRMED,
                        )
                    )

                can_proceed = True
                if background_replacement_required and not val_report.is_valid:
                    can_proceed = False

                segmentation_diagnostic = InternalSegmentationDiagnostic(
                    is_valid=val_report.is_valid,
                    segmentation_status="success",
                    issue_codes=val_report.issue_codes,
                    safe_user_guidance=[
                        get_safe_user_guidance(SuitabilityIssueCode(c))
                        for c in val_report.issue_codes
                    ],
                    can_proceed=can_proceed,
                    provider_name=seg_result.provider_name,
                    provider_version=seg_result.provider_version,
                    model_name=seg_result.model_name,
                    model_version=seg_result.model_version,
                    threshold_used=seg_result.threshold_used,
                    processing_duration_ms=seg_result.processing_duration,
                    foreground_coverage_ratio=seg_result.foreground_coverage_ratio,
                    uncertain_pixel_ratio=val_report.uncertain_pixel_ratio,
                    connected_components_count=val_report.connected_components_count,
                    largest_component_ratio=val_report.largest_component_ratio,
                    face_contained=val_report.face_contained,
                    head_region_coverage_ratio=val_report.head_region_coverage_ratio,
                    mask_width=seg_result.mask_width,
                    mask_height=seg_result.mask_height,
                    warnings=seg_result.warnings,
                )
            except ModelNotFoundError as mne:
                provider_status["subject_segmenter"] = "failed"
                code = SuitabilityIssueCode.SEGMENTATION_MODEL_MISSING
                issues.append(
                    self._create_issue(
                        code=code,
                        severity=IssueSeverity.ERROR
                        if background_replacement_required
                        else IssueSeverity.INFORMATION,
                        category="background",
                        message="Segmentation model file is missing.",
                        blocking=False,  # Not photographic blocking
                        status=IssueStatus.CONFIRMED,
                        internal_details=str(mne),
                    )
                )
                segmentation_diagnostic = InternalSegmentationDiagnostic(
                    is_valid=False,
                    segmentation_status="failed",
                    issue_codes=[code.value],
                    safe_user_guidance=[get_safe_user_guidance(code)],
                    can_proceed=not background_replacement_required,
                    provider_name=getattr(
                        self.segmentation_provider, "provider_name", "unknown"
                    ),
                    provider_version=getattr(
                        self.segmentation_provider, "provider_version", "unknown"
                    ),
                    model_name="unknown",
                    model_version="unknown",
                    threshold_used=0.0,
                    processing_duration_ms=0.0,
                    foreground_coverage_ratio=0.0,
                    uncertain_pixel_ratio=0.0,
                    connected_components_count=0,
                    largest_component_ratio=0.0,
                    face_contained=None,
                    head_region_coverage_ratio=None,
                    mask_width=0,
                    mask_height=0,
                    warnings=[str(mne)],
                )
                checks_unavailable.append(SuitabilityCheck.SUBJECT_SEGMENTATION)
            except ModelChecksumError as mce:
                provider_status["subject_segmenter"] = "failed"
                code = SuitabilityIssueCode.SEGMENTATION_MODEL_CHECKSUM_FAILED
                issues.append(
                    self._create_issue(
                        code=code,
                        severity=IssueSeverity.ERROR
                        if background_replacement_required
                        else IssueSeverity.INFORMATION,
                        category="background",
                        message="Segmentation model checksum verification failed.",
                        blocking=False,  # Not photographic blocking
                        status=IssueStatus.CONFIRMED,
                        internal_details=str(mce),
                    )
                )
                segmentation_diagnostic = InternalSegmentationDiagnostic(
                    is_valid=False,
                    segmentation_status="failed",
                    issue_codes=[code.value],
                    safe_user_guidance=[get_safe_user_guidance(code)],
                    can_proceed=not background_replacement_required,
                    provider_name=getattr(
                        self.segmentation_provider, "provider_name", "unknown"
                    ),
                    provider_version=getattr(
                        self.segmentation_provider, "provider_version", "unknown"
                    ),
                    model_name="unknown",
                    model_version="unknown",
                    threshold_used=0.0,
                    processing_duration_ms=0.0,
                    foreground_coverage_ratio=0.0,
                    uncertain_pixel_ratio=0.0,
                    connected_components_count=0,
                    largest_component_ratio=0.0,
                    face_contained=None,
                    head_region_coverage_ratio=None,
                    mask_width=0,
                    mask_height=0,
                    warnings=[str(mce)],
                )
                checks_unavailable.append(SuitabilityCheck.SUBJECT_SEGMENTATION)
            except SegmentationOutputError as soe:
                provider_status["subject_segmenter"] = "failed"
                code = SuitabilityIssueCode.SEGMENTATION_OUTPUT_INVALID
                issues.append(
                    self._create_issue(
                        code=code,
                        severity=IssueSeverity.ERROR
                        if background_replacement_required
                        else IssueSeverity.INFORMATION,
                        category="background",
                        message="Subject segmentation output is invalid or malformed.",
                        blocking=False,  # Not photographic blocking
                        status=IssueStatus.CONFIRMED,
                        internal_details=str(soe),
                    )
                )
                segmentation_diagnostic = InternalSegmentationDiagnostic(
                    is_valid=False,
                    segmentation_status="failed",
                    issue_codes=[code.value],
                    safe_user_guidance=[get_safe_user_guidance(code)],
                    can_proceed=False,
                    provider_name=getattr(
                        self.segmentation_provider, "provider_name", "unknown"
                    ),
                    provider_version=getattr(
                        self.segmentation_provider, "provider_version", "unknown"
                    ),
                    model_name="unknown",
                    model_version="unknown",
                    threshold_used=0.0,
                    processing_duration_ms=0.0,
                    foreground_coverage_ratio=0.0,
                    uncertain_pixel_ratio=0.0,
                    connected_components_count=0,
                    largest_component_ratio=0.0,
                    face_contained=None,
                    head_region_coverage_ratio=None,
                    mask_width=0,
                    mask_height=0,
                    warnings=[str(soe)],
                )
                checks_unavailable.append(SuitabilityCheck.SUBJECT_SEGMENTATION)
            except Exception as e:
                provider_status["subject_segmenter"] = "failed"
                code = SuitabilityIssueCode.SEGMENTATION_PROVIDER_FAILED
                issues.append(
                    self._create_issue(
                        code=code,
                        severity=IssueSeverity.ERROR
                        if background_replacement_required
                        else IssueSeverity.INFORMATION,
                        category="background",
                        message="Subject segmentation failed.",
                        blocking=False,  # Not photographic blocking
                        status=IssueStatus.CONFIRMED,
                        internal_details=str(e),
                    )
                )
                segmentation_diagnostic = InternalSegmentationDiagnostic(
                    is_valid=False,
                    segmentation_status="failed",
                    issue_codes=[code.value],
                    safe_user_guidance=[get_safe_user_guidance(code)],
                    can_proceed=not background_replacement_required,
                    provider_name=getattr(
                        self.segmentation_provider, "provider_name", "unknown"
                    ),
                    provider_version=getattr(
                        self.segmentation_provider, "provider_version", "unknown"
                    ),
                    model_name="unknown",
                    model_version="unknown",
                    threshold_used=0.0,
                    processing_duration_ms=0.0,
                    foreground_coverage_ratio=0.0,
                    uncertain_pixel_ratio=0.0,
                    connected_components_count=0,
                    largest_component_ratio=0.0,
                    face_contained=None,
                    head_region_coverage_ratio=None,
                    mask_width=0,
                    mask_height=0,
                    warnings=[str(e)],
                )
                checks_unavailable.append(SuitabilityCheck.SUBJECT_SEGMENTATION)

        # 5. Determine Overall Statuses
        # Source suitability checks
        photographic_blocking = any(
            iss.blocking
            for iss in issues
            if iss.status == IssueStatus.CONFIRMED
            and not iss.code.value.startswith("SEGMENTATION")
        )
        photographic_indeterminate = (
            self.face_provider is None
            or self.head_provider is None
            or provider_status["face_detector"] == "failed"
            or provider_status["head_estimator"] == "failed"
            or SuitabilityCheck.TOP_HAIR_BOUNDARY in checks_unavailable
            or SuitabilityCheck.SIDE_HEAD_BOUNDARY in checks_unavailable
            or SuitabilityCheck.CHIN_BOUNDARY in checks_unavailable
        )
        photographic_warnings = (
            any(
                iss.severity == IssueSeverity.WARNING
                for iss in issues
                if not iss.code.value.startswith("SEGMENTATION")
            )
            or len(warnings) > 0
        )

        if photographic_blocking:
            source_suitability = SuitabilityStatus.UNSUITABLE
        elif photographic_indeterminate:
            source_suitability = SuitabilityStatus.INDETERMINATE
        elif photographic_warnings:
            source_suitability = SuitabilityStatus.SUITABLE_WITH_WARNINGS
        else:
            source_suitability = SuitabilityStatus.SUITABLE

        # Processing readiness checks
        segmentation_failed = False
        if background_replacement_required:
            if self.segmentation_provider is None:
                segmentation_failed = True
            elif provider_status["subject_segmenter"] in ("failed", "unavailable"):
                segmentation_failed = True
            elif (
                segmentation_diagnostic is not None
                and not segmentation_diagnostic.can_proceed
            ):
                segmentation_failed = True

        any_blocking_issue = any(
            iss.blocking for iss in issues if iss.status == IssueStatus.CONFIRMED
        )
        any_warning_issue = any(iss.severity == IssueSeverity.WARNING for iss in issues)
        readiness_indeterminate = (
            provider_status["face_detector"] == "failed"
            or provider_status["head_estimator"] == "failed"
            or (
                self.segmentation_provider is not None
                and provider_status["subject_segmenter"] == "failed"
                and not background_replacement_required
            )
        )

        if any_blocking_issue or segmentation_failed:
            processing_readiness = ProcessingReadinessStatus.BLOCKED
        elif readiness_indeterminate:
            processing_readiness = ProcessingReadinessStatus.INDETERMINATE
        elif any_warning_issue or len(warnings) > 0:
            processing_readiness = ProcessingReadinessStatus.READY_WITH_WARNINGS
        else:
            processing_readiness = ProcessingReadinessStatus.READY

        overall_status = source_suitability

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

        if not guidance_messages:
            guidance_messages.append(
                "The photograph complies with general suitability standards."
            )

        duration = (time.perf_counter() - start_time) * 1000.0
        internal_summary = f"Evaluator run completed in {duration:.2f}ms. Status: {overall_status.value}."

        return SuitabilityReport(
            overall_status=overall_status,
            source_suitability=source_suitability,
            processing_readiness=processing_readiness,
            issues=issues,
            warnings=warnings,
            measurements=metrics,
            provider_status=provider_status,
            checks_completed=checks_completed,
            checks_unavailable=checks_unavailable,
            safe_user_guidance=guidance_messages,
            internal_summary=internal_summary,
            evaluator_version=self.version,
            segmentation_diagnostic=segmentation_diagnostic,
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

        # Shadow / Highlight Clipping
        clipped_shadow = metrics["clipped_shadow_ratio"]
        if clipped_shadow > self.thresholds.shadow_clipping_threshold:
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_UNDEREXPOSED_WARNING,
                    severity=IssueSeverity.WARNING,
                    category="exposure",
                    message=f"High ratio of shadow clipping ({clipped_shadow * 100:.1f}%) exceeds threshold ({self.thresholds.shadow_clipping_threshold * 100:.1f}%).",
                    blocking=False,
                    status=IssueStatus.CONFIRMED,
                )
            )

        clipped_highlight = metrics["clipped_highlight_ratio"]
        if clipped_highlight > self.thresholds.highlight_clipping_threshold:
            issues.append(
                self._create_issue(
                    code=SuitabilityIssueCode.SUITABILITY_OVEREXPOSED_WARNING,
                    severity=IssueSeverity.WARNING,
                    category="exposure",
                    message=f"High ratio of highlight clipping ({clipped_highlight * 100:.1f}%) exceeds threshold ({self.thresholds.highlight_clipping_threshold * 100:.1f}%).",
                    blocking=False,
                    status=IssueStatus.CONFIRMED,
                )
            )

    def _apply_face_checks(
        self,
        face: Any,
        issues: List[SuitabilityIssue],
        warnings: List[str],
        checks_completed: List[SuitabilityCheck],
        checks_unavailable: List[SuitabilityCheck],
    ) -> None:
        # Confidence
        if face.confidence < self.thresholds.face_confidence_threshold:
            # Record warning about face confidence, not necessarily blocking unless below hard min
            warnings.append(
                f"Face confidence ({face.confidence:.2f}) is below standard threshold."
            )

        # Pose Checks
        if face.pose is not None:
            checks_completed.append(SuitabilityCheck.POSE)
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
            checks_unavailable.append(SuitabilityCheck.POSE)
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
            checks_completed.append(SuitabilityCheck.OCCLUSION)
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
            checks_unavailable.append(SuitabilityCheck.OCCLUSION)
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
        checks_completed: List[SuitabilityCheck],
        checks_unavailable: List[SuitabilityCheck],
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
            checks_completed.append(SuitabilityCheck.TOP_HAIR_BOUNDARY)
        elif visibility.top_hair_boundary.state == BoundaryVisibilityValue.UNKNOWN:
            checks_unavailable.append(SuitabilityCheck.TOP_HAIR_BOUNDARY)
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
            checks_completed.append(SuitabilityCheck.TOP_HAIR_BOUNDARY)

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
            checks_completed.append(SuitabilityCheck.SIDE_HEAD_BOUNDARY)
        elif (
            visibility.left_head_boundary.state == BoundaryVisibilityValue.UNKNOWN
            or visibility.right_head_boundary.state == BoundaryVisibilityValue.UNKNOWN
        ):
            checks_unavailable.append(SuitabilityCheck.SIDE_HEAD_BOUNDARY)
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
            checks_completed.append(SuitabilityCheck.SIDE_HEAD_BOUNDARY)

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
            checks_completed.append(SuitabilityCheck.CHIN_BOUNDARY)
        elif visibility.chin_boundary.state == BoundaryVisibilityValue.UNKNOWN:
            checks_unavailable.append(SuitabilityCheck.CHIN_BOUNDARY)
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
            checks_completed.append(SuitabilityCheck.CHIN_BOUNDARY)

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
            checks_completed.append(SuitabilityCheck.BEARD_BOUNDARY)
        elif visibility.lower_beard_boundary.state == BoundaryVisibilityValue.UNKNOWN:
            checks_unavailable.append(SuitabilityCheck.BEARD_BOUNDARY)
        else:
            checks_completed.append(SuitabilityCheck.BEARD_BOUNDARY)

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
