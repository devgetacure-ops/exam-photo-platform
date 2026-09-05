"""FastAPI application for the local compliance API."""

import json
import re
from pathlib import Path
from typing import Any, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from exam_photo.api.contracts import (
    ApiJobStatus,
    DocumentAssembleRequest,
    DocumentPageResponse,
    DocumentPlanResponse,
    ExamDetailResponse,
    ExamListResponse,
    ExamSummaryResponse,
    JobStatusResponse,
    KitPackageItem,
    KitPackageResponse,
    PreparationOutcome,
    PrepareRequirementResponse,
    ProcessImageResponse,
    RequirementNotServedResponse,
    RequirementSummary,
    RuleValidationErrorResponse,
    RuleValidationRequest,
    RuleValidationResponse,
    UnavailableExamResponse,
)
from exam_photo.api.jobs import KIT_ID_REGEX
from exam_photo.api.service import (
    ApiProcessingService,
    RequirementNotFoundError,
    RequirementNotServedError,
    UploadLimitExceededError,
)
from exam_photo.api.settings import get_settings
from exam_photo.models.exam_rule import RequirementType
from exam_photo.orchestration.rule_catalogue import CatalogueEntry, support_counts
from exam_photo.pdf import PageOrigin, PageRef
from exam_photo.rule_validation import validate_exam_rule

JOB_ID_REGEX = re.compile(r"^job_[A-Za-z0-9_-]+$")

# An exam identifier is slugified by the encoder and the model pins the shape.
# Matched here too so a traversal attempt is rejected as a bad identifier
# before it is ever used to look anything up.
EXAM_ID_REGEX = re.compile(r"^[a-z0-9\-]+$")

# A requirement identifier is `^[a-z0-9_]+$` in the model. Same reasoning.
REQUIREMENT_ID_REGEX = re.compile(r"^[a-z0-9_]+$")

app = FastAPI(
    title="Indian Exam-Photo Compliance Local API",
    description="Local-only API service for validating and cropping exam photos.",
    version="1.0.0",
)

# Initialize service using global settings
settings = get_settings()
service = ApiProcessingService(settings)

if settings.local_cors_enabled:
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:3000",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.exception_handler(Exception)
async def catch_all_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Exception handler returning generalized error details to avoid leakages."""
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    if isinstance(exc, UploadLimitExceededError):
        return JSONResponse(
            status_code=413,
            content={"detail": str(exc)},
        )
    # Log internal errors privately (not exposed to user response)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


@app.get("/test", include_in_schema=False)
def test_bench() -> Response:
    """A one-page manual test bench for the engine.

    Served by the service itself rather than by the web app, for two reasons.
    It is same-origin, so it sidesteps the CORS toggle that otherwise makes
    every browser request fail as an ordinary network error. And it is a
    testing tool rather than the product: any exam crossed with any file,
    showing input beside output plus stage timings and the raw report, with
    none of the pricing or guidance the candidate-facing app wraps around the
    same call.
    """
    page = Path(__file__).with_name("testbench.html")
    return Response(content=page.read_text(encoding="utf-8"), media_type="text/html")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return the status of the local processing API."""
    return {"status": "healthy"}


def _summarise(entry: CatalogueEntry) -> ExamSummaryResponse:
    """One catalogue entry as the picker needs it."""
    rule = entry.rule
    counts = {support.value: count for support, count in support_counts(rule).items()}
    return ExamSummaryResponse(
        exam_id=entry.exam_id,
        exam_name=rule.exam.exam_name,
        conducting_body=rule.exam.conducting_body,
        examination_year=rule.exam.examination_year,
        application_cycle=rule.exam.application_cycle,
        application_stage=rule.exam.application_stage,
        category=rule.exam.category,
        aliases=list(rule.exam.aliases),
        status=rule.status.value,
        requirement_counts=counts,
        requirement_total=len(rule.requirements or []),
    )


@app.get("/v1/exams", response_model=ExamListResponse)
def list_exams() -> ExamListResponse:
    """List every examination the platform holds an encoded rule for.

    The catalogue is the product's entry point: a candidate selects an
    examination and everything downstream is configured by that record
    (AGENTS.md, "Exam First, Tool Second").
    """
    catalogue = service.catalogue
    exams = [_summarise(entry) for entry in catalogue.listed()]
    return ExamListResponse(
        exams=exams,
        total=len(exams),
        unreadable=dict(catalogue.unreadable),
        unavailable=[
            UnavailableExamResponse(
                exam_name=item.exam_name,
                reason=item.reason,
                detail=item.detail,
                non_photograph_deliverables=item.non_photograph_deliverables,
            )
            for item in catalogue.unavailable
        ],
    )


@app.get("/v1/exams/{exam_id}", response_model=ExamDetailResponse)
def get_exam(exam_id: str) -> ExamDetailResponse:
    """Return one examination's full inventory and photograph specification."""
    if not EXAM_ID_REGEX.match(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID format")

    entry = service.catalogue.get(exam_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Examination not found")

    rule = entry.rule
    requirements = None
    if rule.requirements is not None:
        requirements = [
            RequirementSummary(
                requirement_id=requirement.requirement_id,
                requirement_name=requirement.requirement_name,
                requirement_type=requirement.requirement_type.value,
                submission_method=requirement.submission_method.value,
                requirement_status=requirement.requirement_status.value,
                platform_support=requirement.platform_support.value,
                applicability=requirement.applicability,
                content_instructions=requirement.content_instructions,
                rejection_conditions=list(requirement.rejection_conditions),
                notes=requirement.notes,
                file_spec=(
                    requirement.file_spec.model_dump(exclude_none=True)
                    if requirement.file_spec is not None
                    else None
                ),
            )
            for requirement in rule.requirements
        ]

    return ExamDetailResponse(
        exam_id=entry.exam_id,
        exam_name=rule.exam.exam_name,
        conducting_body=rule.exam.conducting_body,
        examination_year=rule.exam.examination_year,
        application_cycle=rule.exam.application_cycle,
        application_stage=rule.exam.application_stage,
        jurisdiction=rule.exam.jurisdiction,
        category=rule.exam.category,
        aliases=list(rule.exam.aliases),
        status=rule.status.value,
        rule_id=rule.rule_id,
        rule_version=rule.rule_version,
        notes=rule.notes,
        requirements=requirements,
        requirement_counts={
            support.value: count for support, count in support_counts(rule).items()
        },
        image_requirements=rule.image_requirements.model_dump(exclude_none=True),
        provenance={
            path: entry_value.model_dump(exclude_none=True)
            for path, entry_value in rule.provenance.items()
        },
    )


@app.post("/v1/process", response_model=ProcessImageResponse)
async def process_image(
    file: UploadFile = File(...),  # noqa: B008
    rule: str = Form(...),  # noqa: B008
    allow_invalid_output: bool = Query(default=False),  # noqa: B008
    quality_mode: str = Query(default="balanced"),  # noqa: B008
    save_diagnostic_artifacts: bool = Query(default=False),  # noqa: B008
) -> ProcessImageResponse:
    """Synchronously run compliance processing pipeline and return status."""
    # 1. Enforce size limits before reading the whole file into memory
    max_bytes = service.settings.max_upload_bytes
    content = bytearray()
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Upload size exceeds maximum limit of {max_bytes} bytes",
            )
    image_bytes = bytes(content)

    # 2. Parse rule JSON
    try:
        rule_dict = json.loads(rule)
    except json.JSONDecodeError as err:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON format for rule",
        ) from err

    # 3. Process job synchronously
    job_id = service.generate_job_id()
    record = service.process_job_sync(
        job_id=job_id,
        image_bytes=image_bytes,
        rule_dict=rule_dict,
        allow_invalid_output=allow_invalid_output,
        quality_mode=quality_mode,
        save_diagnostic_artifacts=save_diagnostic_artifacts,
    )

    # 4. Expose API relative URL routes
    report_url = f"/v1/jobs/{job_id}/report"
    output_url = f"/v1/jobs/{job_id}/output" if record.output_filename else None

    return ProcessImageResponse(
        job_id=job_id,
        status=record.status,
        report_url=report_url,
        output_url=output_url,
        expires_at=record.expires_at,
        is_valid=record.is_valid,
        output_filename=record.output_filename,
        issue_codes=record.issue_codes,
        rule_compliant=record.rule_compliant,
        visual_quality_acceptable=record.visual_quality_acceptable,
        portrait_quality_report=record.portrait_quality_report,
        matte_quality_report=record.matte_quality_report,
        quality_mode=record.quality_mode,
        diagnostic_available=record.diagnostic_available,
    )


async def _read_upload(file: UploadFile) -> bytes:
    """Read one upload, enforcing the size cap as it streams."""
    max_bytes = service.settings.max_upload_bytes
    content = bytearray()
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Upload size exceeds maximum limit of {max_bytes} bytes",
            )
    return bytes(content)


def _resolve_or_404(exam_id: str, requirement_id: str) -> tuple[Any, Any]:
    """Find a requirement, mapping every miss onto the right status code."""
    if not EXAM_ID_REGEX.match(exam_id):
        raise HTTPException(status_code=400, detail="Invalid exam ID format")
    if not REQUIREMENT_ID_REGEX.match(requirement_id):
        raise HTTPException(status_code=400, detail="Invalid requirement ID format")
    try:
        return service.resolve_requirement(exam_id, requirement_id)
    except KeyError as err:
        raise HTTPException(status_code=404, detail="Examination not found") from err
    except RequirementNotFoundError as err:
        raise HTTPException(
            status_code=404,
            detail="This examination does not carry that requirement.",
        ) from err


def _gate_or_409(exam_id: str, requirement: Any) -> None:
    """Refuse to act on a requirement the platform does not prepare.

    The 409 body carries the requirement's own vocabulary rather than a generic
    message, so a caller can tell the candidate what to do instead. DEC-056:
    this is the second of two independent barriers, the first being the rule
    model's refusal to record an impossible support state at all.
    """
    try:
        service.require_served(requirement)
    except RequirementNotServedError as err:
        raise HTTPException(
            status_code=409,
            detail=RequirementNotServedResponse(
                detail=str(err),
                exam_id=exam_id,
                requirement_id=requirement.requirement_id,
                requirement_name=requirement.requirement_name,
                requirement_type=requirement.requirement_type.value,
                submission_method=requirement.submission_method.value,
                platform_support=requirement.platform_support.value,
                content_instructions=requirement.content_instructions,
                applicability=requirement.applicability,
            ).model_dump(),
        ) from err


def _validated_kit_id(kit_id: Optional[str]) -> Optional[str]:
    if kit_id is None or kit_id == "":
        return None
    if not KIT_ID_REGEX.match(kit_id):
        raise HTTPException(status_code=400, detail="Invalid kit ID format")
    return kit_id


def _preparation_response(
    record: Any, exam_id: str, requirement: Any
) -> PrepareRequirementResponse:
    job_id = record.job_id
    return PrepareRequirementResponse(
        job_id=job_id,
        kit_id=record.kit_id,
        exam_id=exam_id,
        requirement_id=requirement.requirement_id,
        requirement_type=requirement.requirement_type.value,
        platform_support=requirement.platform_support.value,
        status=record.status,
        outcome=PreparationOutcome(record.outcome or "not_produced"),
        expires_at=record.expires_at,
        output_url=(f"/v1/jobs/{job_id}/output" if record.output_filename else None),
        output_filename=record.output_filename,
        output_media_type=record.output_media_type,
        report_url=f"/v1/jobs/{job_id}/report",
        byte_size=record.output_byte_size,
        width=record.output_width,
        height=record.output_height,
        findings=list(record.findings),
        is_blank=record.is_blank,
        ceiling_was_unpublished=record.ceiling_was_unpublished,
        exceeds_ceiling=record.exceeds_ceiling,
        is_valid=record.is_valid,
        issue_codes=list(record.issue_codes),
        rule_compliant=record.rule_compliant,
        visual_quality_acceptable=record.visual_quality_acceptable,
    )


@app.post(
    "/v1/exams/{exam_id}/requirements/{requirement_id}/prepare",
    response_model=PrepareRequirementResponse,
)
async def prepare_requirement(
    exam_id: str,
    requirement_id: str,
    file: UploadFile = File(...),  # noqa: B008
    kit_id: Optional[str] = Form(default=None),  # noqa: B008
    allow_invalid_output: bool = Query(default=False),  # noqa: B008
    quality_mode: str = Query(default="balanced"),  # noqa: B008
) -> PrepareRequirementResponse:
    """Prepare one item of one examination.

    One endpoint for every requirement type, dispatching on the type itself
    (DEC-055). The alternative -- a photograph route beside a deliverable route
    -- would require the browser to know which engine serves which requirement,
    duplicating `_TREATMENT_BY_TYPE` with nothing keeping the copy honest, and
    would invert *Exam First, Tool Second*: a caller names an item of an
    examination, never a pipeline.
    """
    rule, requirement = _resolve_or_404(exam_id, requirement_id)
    _gate_or_409(exam_id, requirement)
    kit = _validated_kit_id(kit_id)

    upload = await _read_upload(file)
    job_id = service.generate_job_id()

    if requirement.requirement_type == RequirementType.PHOTOGRAPH:
        record = service.process_job_sync(
            job_id=job_id,
            image_bytes=upload,
            rule_dict=rule.model_dump(mode="json", exclude_none=True),
            allow_invalid_output=allow_invalid_output,
            quality_mode=quality_mode,
            kit_id=kit,
            exam_id=exam_id,
            requirement=requirement,
        )
    else:
        record = service.prepare_requirement_sync(
            job_id=job_id,
            upload=upload,
            filename=file.filename or "upload",
            rule=rule,
            requirement=requirement,
            exam_id=exam_id,
            kit_id=kit,
        )

    return _preparation_response(record, exam_id, requirement)


@app.post(
    "/v1/exams/{exam_id}/requirements/{requirement_id}/documents",
    response_model=DocumentPlanResponse,
)
async def plan_requirement_document(
    exam_id: str,
    requirement_id: str,
    files: List[UploadFile] = File(...),  # noqa: B008
    kit_id: Optional[str] = Form(default=None),  # noqa: B008
) -> DocumentPlanResponse:
    """Accept a set of uploads and return the pages they contain.

    The first half of the pair DEC-053 requires: a single call would offer no
    point at which the candidate arranges anything.
    """
    _rule, requirement = _resolve_or_404(exam_id, requirement_id)
    _gate_or_409(exam_id, requirement)
    kit = _validated_kit_id(kit_id)

    if not files:
        raise HTTPException(status_code=400, detail="No files were supplied")

    uploads: list[tuple[bytes, str]] = []
    for upload in files:
        uploads.append((await _read_upload(upload), upload.filename or "upload"))

    job_id = service.generate_job_id()
    record, plan = service.plan_document_job(
        job_id=job_id,
        uploads=uploads,
        rule=_rule,
        requirement=requirement,
        exam_id=exam_id,
        kit_id=kit,
    )

    return DocumentPlanResponse(
        job_id=record.job_id,
        kit_id=record.kit_id,
        exam_id=exam_id,
        requirement_id=requirement.requirement_id,
        expires_at=record.expires_at,
        pages=[
            DocumentPageResponse(
                source_index=page.source_index,
                page_index=page.page_index,
                origin=page.origin.value,
            )
            for page in plan.pages
        ],
        unreadable={str(k): v for k, v in plan.unreadable.items()},
    )


@app.post("/v1/documents/{job_id}/assemble", response_model=PrepareRequirementResponse)
def assemble_requirement_document(
    job_id: str, request: DocumentAssembleRequest
) -> PrepareRequirementResponse:
    """Assemble a planned document in the candidate's own arrangement."""
    if not JOB_ID_REGEX.match(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    record = service.registry.get_job(job_id)
    if not record or record.status == ApiJobStatus.DELETED:
        raise HTTPException(status_code=404, detail="Document job not found")
    if not record.document_sources:
        raise HTTPException(
            status_code=409, detail="This job does not hold a planned document."
        )
    if record.exam_id is None or record.requirement_id is None:
        raise HTTPException(
            status_code=409, detail="This job is not bound to a requirement."
        )

    _rule, requirement = _resolve_or_404(record.exam_id, record.requirement_id)
    _gate_or_409(record.exam_id, requirement)

    order = None
    if request.order is not None:
        order = [
            PageRef(
                source_index=page.source_index,
                page_index=page.page_index,
                # The plan carries the true origin; assembly re-reads it from
                # the plan, so whatever a caller claims here cannot promote a
                # text page into one that may be re-rendered (DEC-052).
                origin=PageOrigin.PHOTOGRAPH,
                rotation=page.rotation,
            )
            for page in request.order
        ]

    try:
        updated, _result = service.assemble_document_job(record, order, requirement)
    except ValueError as err:
        # "No readable pages" is the one hard error: an empty PDF is not a
        # deliverable.
        raise HTTPException(status_code=422, detail=str(err)) from err

    return _preparation_response(updated, record.exam_id, requirement)


@app.get("/v1/kits/{kit_id}/package", response_model=KitPackageResponse)
def get_kit_package_manifest(kit_id: str) -> KitPackageResponse:
    """The checklist for a kit, without downloading the archive."""
    if not KIT_ID_REGEX.match(kit_id):
        raise HTTPException(status_code=400, detail="Invalid kit ID format")
    try:
        _archive, checklist = service.build_kit_package(kit_id)
    except KeyError as err:
        raise HTTPException(status_code=404, detail="Kit not found") from err

    return KitPackageResponse(
        kit_id=kit_id,
        exam_id=checklist.get("exam_id"),
        exam_name=checklist.get("exam_name"),
        files_included=checklist.get("files_included", 0),
        package_url=f"/v1/kits/{kit_id}/package/download",
        requirements=checklist.get("requirements", []),
        items=[KitPackageItem(**item) for item in checklist.get("items", [])],
    )


@app.get("/v1/kits/{kit_id}/package/download")
def download_kit_package(kit_id: str) -> Response:
    """Download the kit as a ZIP with its checklist and validation report."""
    if not KIT_ID_REGEX.match(kit_id):
        raise HTTPException(status_code=400, detail="Invalid kit ID format")
    try:
        archive, _checklist = service.build_kit_package(kit_id)
    except KeyError as err:
        raise HTTPException(status_code=404, detail="Kit not found") from err

    return Response(
        content=archive,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{kit_id}.zip"',
        },
    )


@app.get("/v1/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> JobStatusResponse:
    """Retrieve metadata detailing the current status of a processing job."""
    if not JOB_ID_REGEX.match(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    record = service.registry.get_job(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")

    report_url = None
    output_url = None

    if record.status != ApiJobStatus.DELETED:
        report_url = f"/v1/jobs/{job_id}/report"
        if record.output_filename:
            output_url = f"/v1/jobs/{job_id}/output"

    return JobStatusResponse(
        job_id=record.job_id,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
        expires_at=record.expires_at,
        is_valid=record.is_valid,
        issue_codes=record.issue_codes,
        output_filename=record.output_filename,
        report_url=report_url,
        output_url=output_url,
        rule_compliant=record.rule_compliant,
        visual_quality_acceptable=record.visual_quality_acceptable,
        portrait_quality_report=record.portrait_quality_report,
        matte_quality_report=record.matte_quality_report,
        quality_mode=record.quality_mode,
        diagnostic_available=record.diagnostic_available,
    )


@app.get("/v1/jobs/{job_id}/report")
def get_job_report(job_id: str) -> Response:
    """Retrieve full pipeline report."""
    if not JOB_ID_REGEX.match(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    record = service.registry.get_job(job_id)
    if not record or record.status == ApiJobStatus.DELETED:
        raise HTTPException(status_code=404, detail="Job or report not found")

    if not service.store.file_exists(job_id, "report.json"):
        raise HTTPException(status_code=404, detail="Report artifact not found")

    report_data = service.store.read_file(job_id, "report.json")
    return Response(content=report_data, media_type="application/json")


@app.get("/v1/jobs/{job_id}/output")
def get_job_output(job_id: str) -> Response:
    """Stream raw JPEG output candidate if it exists and validation constraints are met."""
    if not JOB_ID_REGEX.match(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    record = service.registry.get_job(job_id)
    if not record or record.status == ApiJobStatus.DELETED:
        raise HTTPException(status_code=404, detail="Job or output not found")

    if not record.output_filename:
        raise HTTPException(status_code=404, detail="Output artifact not available")

    # Enforce validity: must be succeeded or failed but invalid-output-save was allowed
    # (which implies the output file actually exists in registry and store)
    if not service.store.file_exists(job_id, record.output_filename):
        raise HTTPException(
            status_code=404, detail="Output artifact file not found on disk"
        )

    output_bytes = service.store.read_file(job_id, record.output_filename)
    # A deliverable may legitimately be a PDF (DEC-052), so the media type is
    # read from the record rather than assumed to be JPEG as it could be when
    # a photograph was the only thing this service produced.
    return Response(
        content=output_bytes,
        media_type=record.output_media_type or "image/jpeg",
        headers={
            "Content-Disposition": (f'attachment; filename="{record.output_filename}"')
        },
    )


@app.delete("/v1/jobs/{job_id}")
def delete_job(job_id: str) -> dict[str, str]:
    """Completely remove all input, rule, report, output, and manifest artifacts."""
    if not JOB_ID_REGEX.match(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    record = service.registry.get_job(job_id)
    if not record or record.status == ApiJobStatus.DELETED:
        raise HTTPException(status_code=404, detail="Job not found or already deleted")

    # 1. Delete all artifacts on disk (including job.json manifest)
    service.store.delete_job_directory(job_id)

    # 2. Update registry to DELETED (retains status in-memory only)
    service.registry.delete_job(job_id)

    return {"detail": "Job artifacts deleted successfully"}


@app.post("/v1/cleanup-expired")
def cleanup_expired() -> dict[str, int]:
    """Trigger TTL cleanup of expired job folders on disk."""
    count = service.cleanup_expired_jobs()
    return {"cleaned_count": count}


@app.post("/v1/rules/validate", response_model=RuleValidationResponse)
def validate_rule(req: RuleValidationRequest) -> RuleValidationResponse:
    """Validate an exam rule against canonical schema and pydantic constraints."""
    errors = validate_exam_rule(req.rule)
    mapped_errors = [
        RuleValidationErrorResponse(
            severity=err.severity.value,
            error_code=err.error_code,
            field_path=err.field_path,
            message=err.message,
            suggested_resolution=err.suggested_resolution,
        )
        for err in errors
    ]
    is_valid = len(mapped_errors) == 0
    return RuleValidationResponse(
        is_valid=is_valid,
        error_count=len(mapped_errors),
        errors=mapped_errors,
    )
