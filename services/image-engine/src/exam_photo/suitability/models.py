from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from exam_photo.suitability.issue_codes import SuitabilityIssueCode


class SuitabilityStatus(str, Enum):
    SUITABLE = "suitable"
    SUITABLE_WITH_WARNINGS = "suitable_with_warnings"
    UNSUITABLE = "unsuitable"
    INDETERMINATE = "indeterminate"


class IssueSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"


class IssueStatus(str, Enum):
    CONFIRMED = "confirmed"
    SUSPECTED = "suspected"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


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


class SuitabilityReport(BaseModel):
    overall_status: SuitabilityStatus
    issues: List[SuitabilityIssue]
    warnings: List[str]
    measurements: Dict[str, Any]
    provider_status: Dict[str, str]
    checks_completed: List[str]
    checks_unavailable: List[str]
    safe_user_guidance: List[str]
    internal_summary: str
    evaluator_version: str
