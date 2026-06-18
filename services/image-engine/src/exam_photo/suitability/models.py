from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from exam_photo.suitability.issue_codes import SuitabilityIssueCode


class SuitabilityStatus(str, Enum):
    SUITABLE = "suitable"
    SUITABLE_WITH_WARNINGS = "suitable_with_warnings"
    UNSUITABLE = "unsuitable"
    INDETERMINATE = "indeterminate"


class SuitabilityCheck(str, Enum):
    DIMENSIONS = "dimensions"
    PIXEL_COUNT = "pixel_count"
    LUMINANCE = "luminance"
    CONTRAST = "contrast"
    TRANSPARENCY = "transparency"
    SHARPNESS = "sharpness"
    FACE_PRESENCE = "face_presence"
    POSE = "pose"
    EYES_VISIBILITY = "eyes_visibility"
    OCCLUSION = "occlusion"
    HEAD_COMPLETENESS = "head_completeness"
    TOP_HAIR_BOUNDARY = "top_hair_boundary"
    SIDE_HEAD_BOUNDARY = "side_head_boundary"
    CHIN_BOUNDARY = "chin_boundary"
    BEARD_BOUNDARY = "beard_boundary"
    BACKGROUND = "background"


class IssueSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"


class IssueStatus(str, Enum):
    CONFIRMED = "confirmed"
    SUSPECTED = "suspected"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


class PublicSuitabilityIssue(BaseModel):
    code: SuitabilityIssueCode
    severity: IssueSeverity
    category: str
    message: str
    safe_user_guidance: str
    blocking: bool
    confidence: float
    measurement_reference: Optional[str] = None
    provider_reference: Optional[str] = None
    status: IssueStatus


class SuitabilityIssue(BaseModel):
    code: SuitabilityIssueCode
    severity: IssueSeverity
    category: str
    message: str
    safe_user_guidance: str
    blocking: bool
    confidence: float
    measurement_reference: Optional[str] = None
    provider_reference: Optional[str] = None
    internal_details: Optional[str] = None
    status: IssueStatus

    def to_public(self) -> PublicSuitabilityIssue:
        return PublicSuitabilityIssue(
            code=self.code,
            severity=self.severity,
            category=self.category,
            message=self.message,
            safe_user_guidance=self.safe_user_guidance,
            blocking=self.blocking,
            confidence=self.confidence,
            measurement_reference=self.measurement_reference,
            provider_reference=self.provider_reference,
            status=self.status,
        )


class PublicSegmentationReport(BaseModel):
    is_valid: bool
    segmentation_status: str  # "success", "failed", "unavailable"
    issue_codes: List[str]
    safe_user_guidance: List[str]
    can_proceed: bool
    foreground_coverage_ratio: float


class InternalSegmentationDiagnostic(BaseModel):
    is_valid: bool
    segmentation_status: str
    issue_codes: List[str]
    safe_user_guidance: List[str]
    can_proceed: bool
    provider_name: str
    provider_version: str
    model_name: str
    model_version: str
    threshold_used: float
    processing_duration_ms: float
    foreground_coverage_ratio: float
    uncertain_edge_ratio: float
    connected_components_count: int
    largest_component_ratio: float
    face_contained: Optional[bool]
    head_region_coverage_ratio: Optional[float]
    mask_width: int
    mask_height: int
    warnings: List[str]

    def to_public(self) -> PublicSegmentationReport:
        return PublicSegmentationReport(
            is_valid=self.is_valid,
            segmentation_status=self.segmentation_status,
            issue_codes=self.issue_codes,
            safe_user_guidance=self.safe_user_guidance,
            can_proceed=self.can_proceed,
            foreground_coverage_ratio=self.foreground_coverage_ratio,
        )


class PublicSuitabilityReport(BaseModel):
    overall_status: SuitabilityStatus
    issues: List[PublicSuitabilityIssue]
    warnings: List[str]
    measurements: Dict[str, Any]
    provider_status: Dict[str, str]
    checks_completed: List[SuitabilityCheck]
    checks_unavailable: List[SuitabilityCheck]
    safe_user_guidance: List[str]
    evaluator_version: str
    segmentation_report: Optional[PublicSegmentationReport] = None


class SuitabilityReport(BaseModel):
    overall_status: SuitabilityStatus
    issues: List[SuitabilityIssue]
    warnings: List[str]
    measurements: Dict[str, Any]
    provider_status: Dict[str, str]
    checks_completed: List[SuitabilityCheck]
    checks_unavailable: List[SuitabilityCheck]
    safe_user_guidance: List[str]
    internal_summary: str
    evaluator_version: str
    segmentation_diagnostic: Optional[InternalSegmentationDiagnostic] = None

    def to_public(self) -> PublicSuitabilityReport:
        seg_report = (
            self.segmentation_diagnostic.to_public()
            if self.segmentation_diagnostic is not None
            else None
        )
        return PublicSuitabilityReport(
            overall_status=self.overall_status,
            issues=[issue.to_public() for issue in self.issues],
            warnings=self.warnings,
            measurements=self.measurements,
            provider_status=self.provider_status,
            checks_completed=self.checks_completed,
            checks_unavailable=self.checks_unavailable,
            safe_user_guidance=self.safe_user_guidance,
            evaluator_version=self.evaluator_version,
            segmentation_report=seg_report,
        )
