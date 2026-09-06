"""API response and request contract models."""

from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ApiJobStatus(str, Enum):
    """Execution status of a processing job."""

    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    DELETED = "DELETED"


class JobEntitlement(str, Enum):
    """Whether a job's clean output may be served (DEC-063).

    A job prepared through the candidate path starts ``PREVIEW_ONLY`` and only
    a payment confirmation inside the process may move it: there is
    deliberately no HTTP route that releases one, because an unauthenticated
    release endpoint is not a weaker gate than none but a worse one -- it looks
    like protection to everyone reading the route list.
    """

    PREVIEW_ONLY = "preview_only"
    RELEASED = "released"


class ProcessImageResponse(BaseModel):
    """Response returned upon initiating a processing request."""

    job_id: str
    status: ApiJobStatus
    report_url: Optional[str] = None
    output_url: Optional[str] = None
    expires_at: Optional[str] = None
    is_valid: Optional[bool] = None
    output_filename: Optional[str] = None
    issue_codes: List[str] = Field(default_factory=list)
    rule_compliant: Optional[bool] = None
    visual_quality_acceptable: Optional[bool] = None
    portrait_quality_report: Optional[dict[str, Any]] = None
    matte_quality_report: Optional[dict[str, Any]] = None
    quality_mode: Optional[str] = None
    diagnostic_available: Optional[bool] = None


class JobStatusResponse(BaseModel):
    """Metadata detailing the current status of a processing job."""

    job_id: str
    status: ApiJobStatus
    created_at: str
    updated_at: str
    expires_at: Optional[str] = None
    is_valid: Optional[bool] = None
    issue_codes: Optional[List[str]] = None
    output_filename: Optional[str] = None
    report_url: Optional[str] = None
    output_url: Optional[str] = None
    preview_url: Optional[str] = None
    preview_watermarked: bool = False
    entitlement: JobEntitlement = JobEntitlement.PREVIEW_ONLY
    rule_compliant: Optional[bool] = None
    visual_quality_acceptable: Optional[bool] = None
    portrait_quality_report: Optional[dict[str, Any]] = None
    matte_quality_report: Optional[dict[str, Any]] = None
    quality_mode: Optional[str] = None
    diagnostic_available: Optional[bool] = None


class RequirementSummary(BaseModel):
    """One requirement as the picker and the kit list need it.

    ``platform_support`` and ``submission_method`` are carried as their own
    string values and are never reduced to a boolean or a bucket. DEC-056: a
    ``can_prepare`` field is precisely the mechanism by which ``supported``,
    ``partially_supported`` and ``guidance_only`` become indistinguishable, and
    it would deliver the product's worst failure mode through the contract
    where no amount of care in the interface could recover the distinction.
    """

    requirement_id: str
    requirement_name: str
    requirement_type: str
    submission_method: str
    requirement_status: str
    platform_support: str
    applicability: Optional[str] = None
    content_instructions: Optional[str] = None
    rejection_conditions: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    #: The published output specification, as recorded. ``None`` for a
    #: photograph, whose specification lives in ``image_requirements`` and is
    #: forbidden from being duplicated here (DEC-047).
    file_spec: Optional[dict[str, Any]] = None


class ExamSummaryResponse(BaseModel):
    """One examination as it appears in the picker.

    Deliberately not the whole record: the picker renders 39 of these and the
    requirement detail is a second call away.
    """

    exam_id: str
    exam_name: str
    conducting_body: str
    examination_year: int
    application_cycle: str
    application_stage: Optional[str] = None
    category: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)
    status: str
    #: All five ``platform_support`` values, always present, zeros included.
    requirement_counts: dict[str, int] = Field(default_factory=dict)
    requirement_total: int = 0


class UnavailableExamResponse(BaseModel):
    """An examination the research covers that the catalogue does not encode.

    Shown in the picker rather than omitted, on the same reasoning that keeps a
    guidance-only row on screen: a candidate searching SSC CGL and finding
    nothing concludes the platform does not cover it, and an absence discovered
    at the portal is worse than one admitted here (DEC-056).
    """

    exam_name: str
    reason: str
    detail: str
    #: What the candidate loses by the absence. Ten of the eleven carry at
    #: least one deliverable the platform could otherwise prepare.
    non_photograph_deliverables: int = 0


class ExamListResponse(BaseModel):
    """Every examination the platform can serve, ordered by name."""

    exams: List[ExamSummaryResponse] = Field(default_factory=list)
    total: int = 0
    #: Examinations known to the research but not encoded. Never merged into
    #: `exams`: one list is selectable and the other is not, and a single list
    #: with a flag is how that distinction gets lost.
    unavailable: List[UnavailableExamResponse] = Field(default_factory=list)
    #: Records present in the catalogue directory that could not be served,
    #: by file name and reason. Reported rather than swallowed: an examination
    #: missing from the picker with no trace is indistinguishable from one
    #: that was never researched.
    unreadable: dict[str, str] = Field(default_factory=dict)


class ExamDetailResponse(BaseModel):
    """One examination with its full inventory and photograph specification."""

    exam_id: str
    exam_name: str
    conducting_body: str
    examination_year: int
    application_cycle: str
    application_stage: Optional[str] = None
    jurisdiction: Optional[str] = None
    category: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)
    status: str
    rule_id: str
    rule_version: str
    notes: Optional[str] = None
    #: ``None`` when the deliverable research has not been done for this
    #: examination -- never that the photograph is the only thing it asks for
    #: (DEC-047).
    requirements: Optional[List[RequirementSummary]] = None
    requirement_counts: dict[str, int] = Field(default_factory=dict)
    #: The photograph specification, carried verbatim from the record.
    image_requirements: dict[str, Any] = Field(default_factory=dict)
    #: Per-field provenance, so a caller can tell a published figure from a
    #: platform estimate without a second request (DEC-057).
    provenance: dict[str, Any] = Field(default_factory=dict)


class PreparationOutcome(str, Enum):
    """The three states a preparation attempt can land in (DEC-056).

    ``PREPARED_WITH_FINDINGS`` exists because DEC-041 makes production the rule
    and refusal the exception: a blank page, an unreachable published minimum,
    a ceiling the platform invented and a document that would not fit are all
    reported *about a file that exists*. A two-state contract files every one
    of them under success, which is where nobody reads them.
    """

    PREPARED = "prepared"
    PREPARED_WITH_FINDINGS = "prepared_with_findings"
    BLOCKED = "blocked"
    NOT_PRODUCED = "not_produced"


class RequirementNotServedResponse(BaseModel):
    """Why the platform will not act on a requirement.

    Returned with 409 rather than a generic error, and carrying the
    requirement's own vocabulary, so the caller can say what the candidate must
    do instead rather than reporting a failure.
    """

    detail: str
    exam_id: str
    requirement_id: str
    requirement_name: str
    requirement_type: str
    submission_method: str
    platform_support: str
    content_instructions: Optional[str] = None
    applicability: Optional[str] = None


class PrepareRequirementResponse(BaseModel):
    """One prepared deliverable, and everything true about it."""

    job_id: str
    kit_id: Optional[str] = None
    exam_id: str
    requirement_id: str
    requirement_type: str
    platform_support: str
    status: ApiJobStatus
    outcome: PreparationOutcome
    expires_at: Optional[str] = None

    output_url: Optional[str] = None
    output_filename: Optional[str] = None
    output_media_type: Optional[str] = None
    report_url: Optional[str] = None
    byte_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None

    # --- The purchase gate (DEC-063) --------------------------------------
    #
    # `output_url` names a route that answers 402 until the job is released.
    # The preview is what a candidate may actually see before paying, and
    # `preview_watermarked` is set from the artifact that was written rather
    # than from the intent to write one: it is `False` wherever no mark was
    # burned in, so a client that trusts it is never shown a clean file
    # believing it is protected.
    preview_url: Optional[str] = None
    preview_watermarked: bool = False
    entitlement: JobEntitlement = JobEntitlement.PREVIEW_ONLY

    #: Everything the pipeline reported rather than raised.
    findings: List[str] = Field(default_factory=list)
    is_blank: Optional[bool] = None
    #: ``True`` when the byte ceiling was the platform's fallback rather than a
    #: figure the examination published.
    ceiling_was_unpublished: Optional[bool] = None
    exceeds_ceiling: Optional[bool] = None

    # Photograph path only.
    is_valid: Optional[bool] = None
    issue_codes: List[str] = Field(default_factory=list)
    rule_compliant: Optional[bool] = None
    visual_quality_acceptable: Optional[bool] = None


class DocumentPageResponse(BaseModel):
    """One page a candidate can order, rotate, repeat or omit (DEC-053)."""

    source_index: int
    page_index: int
    #: ``photograph``, ``document_scan`` or ``document_text``. The origin
    #: decides what may be done to the page: a page whose text is real text is
    #: never re-rendered, however impossible the ceiling (DEC-052).
    origin: str
    rotation: int = 0


class DocumentPlanResponse(BaseModel):
    """Every page available across a set of uploads."""

    job_id: str
    kit_id: Optional[str] = None
    exam_id: str
    requirement_id: str
    expires_at: Optional[str] = None
    pages: List[DocumentPageResponse] = Field(default_factory=list)
    #: Uploads that could not be read, by index, with the reason. One damaged
    #: file among five does not cost the candidate the other four.
    unreadable: dict[str, str] = Field(default_factory=dict)


class DocumentAssembleRequest(BaseModel):
    """The candidate's arrangement.

    ``order`` omitted means "every page, as they arrived". A page omitted from
    a supplied order is left out, and a page repeated is duplicated -- both
    deliberate, and available here and nowhere else (DEC-053).
    """

    order: Optional[List[DocumentPageResponse]] = None


class KitPackageItem(BaseModel):
    requirement_id: Optional[str] = None
    requirement_type: Optional[str] = None
    platform_support: Optional[str] = None
    outcome: Optional[str] = None
    included: bool = False
    #: DEC-063: prepared, and held out of the archive for want of a payment.
    #: Distinct from `included: False` for a requirement that produced nothing.
    awaiting_release: bool = False
    filename: Optional[str] = None
    byte_size: Optional[int] = None
    findings: List[str] = Field(default_factory=list)


class KitPackageResponse(BaseModel):
    """The checklist for a kit, alongside the archive that carries it."""

    kit_id: str
    exam_id: Optional[str] = None
    exam_name: Optional[str] = None
    files_included: int = 0
    #: How many prepared files the download is refusing to hand over (DEC-063).
    awaiting_release: int = 0
    package_url: Optional[str] = None
    requirements: List[dict[str, Any]] = Field(default_factory=list)
    items: List[KitPackageItem] = Field(default_factory=list)


class RuleValidationErrorResponse(BaseModel):
    """Structured error details returned during rule validation."""

    severity: str
    error_code: str
    field_path: str
    message: str
    suggested_resolution: Optional[str] = None


class RuleValidationRequest(BaseModel):
    """Payload containing an ExamRule JSON object to validate."""

    rule: dict[str, Any]


class RuleValidationResponse(BaseModel):
    """API response body for rule validation request."""

    is_valid: bool
    error_count: int
    errors: List[RuleValidationErrorResponse]
