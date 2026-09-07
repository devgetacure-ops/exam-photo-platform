"""FastAPI application for the local compliance API."""

import json
import re
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, List, Optional

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import JSONResponse, Response

from exam_photo.api.contracts import (
    ApiJobStatus,
    DocumentAssembleRequest,
    DocumentPageResponse,
    DocumentPlanResponse,
    EmailDeliveryRequest,
    EmailDeliveryResponse,
    EnhancementToggleRequest,
    ExamDetailResponse,
    ExamListResponse,
    ExamSummaryResponse,
    JobRetentionResponse,
    JobStatusResponse,
    KitOrderResponse,
    KitPackageItem,
    KitPackageResponse,
    KitQuoteResponse,
    OrderEvidenceResponse,
    PreparationOutcome,
    PrepareRequirementResponse,
    ProcessImageResponse,
    QuoteLineResponse,
    RequirementNotServedResponse,
    RequirementSummary,
    RuleValidationErrorResponse,
    RuleValidationRequest,
    RuleValidationResponse,
    UnavailableExamResponse,
)
from exam_photo.api.delivery import EmailRejectedError
from exam_photo.api.jobs import KIT_ID_REGEX, ProcessingJobRecord
from exam_photo.api.payments import (
    SIGNATURE_HEADER,
    WebhookRejectedError,
    verify_and_read,
)
from exam_photo.api.pricing import quote_for
from exam_photo.api.progress import json_safe
from exam_photo.api.protection import (
    AllowanceExceededError,
    ChallengeFailedError,
    verify_turnstile,
)
from exam_photo.api.razorpay_orders import OrderCreationError, order_notes
from exam_photo.api.service import (
    ApiProcessingService,
    RequirementNotFoundError,
    RequirementNotServedError,
    RetentionCeilingReachedError,
    ServiceBusyError,
    UploadLimitExceededError,
)
from exam_photo.api.settings import get_settings
from exam_photo.models.exam_rule import RequirementType
from exam_photo.orchestration.rule_catalogue import CatalogueEntry, support_counts
from exam_photo.pdf import PageOrigin, PageRef
from exam_photo.preview import PREVIEW_MEDIA_TYPE
from exam_photo.rule_validation import validate_exam_rule

JOB_ID_REGEX = re.compile(r"^job_[A-Za-z0-9_-]+$")

# An exam identifier is slugified by the encoder and the model pins the shape.
# Matched here too so a traversal attempt is rejected as a bad identifier
# before it is ever used to look anything up.
EXAM_ID_REGEX = re.compile(r"^[a-z0-9\-]+$")

# A requirement identifier is `^[a-z0-9_]+$` in the model. Same reasoning.
REQUIREMENT_ID_REGEX = re.compile(r"^[a-z0-9_]+$")

# Initialize service using global settings
settings = get_settings()
service = ApiProcessingService(settings)

#: Development origins, used when browser access is enabled and no explicit
#: origin list is given.
_LOCAL_ORIGINS = ["http://127.0.0.1:3000", "http://localhost:3000"]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Warm the model and start the artifact sweeper (DEC-064).

    Warmup runs on a background thread rather than blocking startup. A process
    that binds its port late is indistinguishable from one that crashed;
    binding immediately and answering `GET /ready` with `warming` is something
    an orchestrator can act on, and is what makes a rolling deploy possible.
    """
    service.start_background_workers()
    try:
        yield
    finally:
        service.stop_background_workers()


app = FastAPI(
    title="Indian Exam-Photo Compliance Local API",
    description="Local-only API service for validating and cropping exam photos.",
    version="1.0.0",
    lifespan=lifespan,
)

_allowed_origins = settings.allowed_origins or (
    _LOCAL_ORIGINS if settings.local_cors_enabled else []
)
if _allowed_origins:
    from fastapi.middleware.cors import CORSMiddleware

    # A deployed origin is configured, never hardcoded (DEC-064). Serving the
    # app and the engine from one origin behind a reverse proxy is better
    # still, and then this list stays empty.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def require_operator(
    x_operator_token: Optional[str] = Header(default=None),  # noqa: B008
) -> None:
    """Gate the operator surface on a shared secret (DEC-064).

    Guards `/v1/process`, `/v1/rules/validate`, `/v1/cleanup-expired` and the
    `/test` bench -- routes no candidate touches and where the damage is
    asymmetric: rule validation changes what the platform believes an
    examination requires, and `/v1/process` is an ungated pipeline exempt from
    the DEC-063 purchase gate.

    The candidate surface is deliberately not gated this way. A browser would
    have to carry the token and would hand it to anyone who opened the network
    tab, so it would protect nothing while looking like it did.

    With no token configured the surface stays open -- correct for local
    development -- and `GET /ready` reports `operator_surface:
    "unauthenticated"` so the state is visible where a deployment checks.
    """
    expected = service.settings.operator_token
    if not expected:
        return
    if x_operator_token is None or not secrets.compare_digest(
        x_operator_token, expected
    ):
        raise HTTPException(
            status_code=401,
            detail="This endpoint requires a valid X-Operator-Token header.",
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


@app.get(
    "/test",
    include_in_schema=False,
    dependencies=[Depends(require_operator)],  # noqa: B008
)
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
    """Liveness: the process is up and answering.

    Deliberately says nothing about whether the model is loaded. Readiness is
    `GET /ready`, and conflating the two is what routes the first candidate of
    every deploy into a cold worker (DEC-064).
    """
    return {"status": "healthy"}


@app.get("/ready")
def readiness_check(response: Response) -> dict[str, Any]:
    """Readiness: this process can serve a photograph now (DEC-064).

    503 while warming and 503 on a failed warmup, so a load balancer keeps
    traffic away until the first inference has been paid for. A failure names
    what is missing -- on a host without the BiRefNet weights that is
    DEC-060's loud deployment failure arriving where a deployment looks.
    """
    state = service.readiness()
    if state["status"] != "ready":
        response.status_code = 503
    return state


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


@app.post(
    "/v1/process",
    response_model=ProcessImageResponse,
    dependencies=[Depends(require_operator)],  # noqa: B008
)
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

    # 3. Process job synchronously, inside the same global concurrency limit
    # as the candidate path (DEC-064): the operator surface is authenticated,
    # but its CPU is the same CPU, and an unbounded console would starve the
    # candidates the box exists to serve.
    job_id = service.generate_job_id()
    try:
        with service.preparation_slot():
            record = service.process_job_sync(
                job_id=job_id,
                image_bytes=image_bytes,
                rule_dict=rule_dict,
                allow_invalid_output=allow_invalid_output,
                quality_mode=quality_mode,
                save_diagnostic_artifacts=save_diagnostic_artifacts,
            )
    except ServiceBusyError as err:
        raise _busy(err) from err

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


def _job_or_expired(job_id: str) -> Optional[ProcessingJobRecord]:
    """Fetch a job, erasing it first if its retention deadline has passed.

    Every job route reads through here, so retention is bounded by the
    deadline itself and not by when the sweeper next runs (DEC-066). An
    expired job comes back marked `DELETED`, which each route's existing
    guard already refuses -- so this adds no new status to the wire and the
    routes keep their own wording for what could not be found.
    """
    record = service.registry.get_job(job_id)
    if record is not None:
        service.expire_job_if_due(record)
    return record


def _validated_kit_id(kit_id: Optional[str]) -> Optional[str]:
    if kit_id is None or kit_id == "":
        return None
    if not KIT_ID_REGEX.match(kit_id):
        raise HTTPException(status_code=400, detail="Invalid kit ID format")
    return kit_id


def _busy(error: ServiceBusyError) -> HTTPException:
    """429 with a `Retry-After`, rather than a queue nobody survives.

    A request held behind a hundred others would be cut by nginx or Cloudflare
    long before it ran, so telling the caller to come back is the honest
    answer. The hint is one photograph's work, which is what a slot frees in.
    """
    return HTTPException(
        status_code=429,
        detail=f"{error} Please retry in a few seconds.",
        headers={"Retry-After": "15"},
    )


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
        # DEC-063. `preview_url` is served only where a mark was actually
        # burned in, so a client can never be shown a clean file while being
        # told it is watermarked.
        preview_url=(
            f"/v1/jobs/{job_id}/preview" if record.preview_watermarked else None
        ),
        preview_watermarked=record.preview_watermarked,
        entitlement=record.entitlement,
        enhancement_enabled=record.enhancement_enabled,
        enhancements_applied=list(record.enhancements_applied),
        enhancement_switchable=bool(record.alternate_output_filename),
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
    request: Request = None,  # type: ignore[assignment]  # noqa: B008
    cf_turnstile_response: Optional[str] = Form(default=None),  # noqa: B008
    enhancement_enabled: bool = Form(default=True),  # noqa: B008
    progress_token: Optional[str] = Form(default=None),  # noqa: B008
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

    # DEC-073, before the upload is read: a challenge that is going to fail
    # should not first cost us the bytes.
    try:
        verify_turnstile(
            cf_turnstile_response or "",
            service.settings.turnstile_secret,
            request.client.host if request and request.client else None,
        )
    except ChallengeFailedError as err:
        print(f"turnstile rejected a preparation: {err}")
        raise HTTPException(
            status_code=403,
            detail="Could not verify this request came from a browser.",
        ) from None

    if kit:
        try:
            service.usage.check_allowance(
                kit, service.settings.free_preparation_allowance
            )
        except AllowanceExceededError as err:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"This session has prepared {err.used} files without a "
                    "purchase. Buy the ones you need and you can carry on."
                ),
            ) from None

    upload = await _read_upload(file)
    job_id = service.generate_job_id()
    if kit:
        service.usage.record_preparation(kit)
    # DEC-075. Opened before the concurrency slot, so a candidate waiting
    # behind a full queue sees "queued" rather than nothing at all.
    if progress_token:
        service.progress.start(progress_token)

    # Bounded concurrency, not a per-IP quota (DEC-064). The slot is taken
    # after the support gate and the upload read, so a refused requirement or
    # an oversized file never occupies one.
    try:
        with service.preparation_slot():
            if requirement.requirement_type == RequirementType.PHOTOGRAPH:
                record = service.process_job_sync(
                    job_id=job_id,
                    image_bytes=upload,
                    rule_dict=rule.model_dump(mode="json", exclude_none=True),
                    allow_invalid_output=allow_invalid_output,
                    quality_mode=quality_mode,
                    # DEC-074. The photograph path only. Ink correction is not
                    # offered as a choice: it is what makes a signature legible
                    # (DEC-050), not a look applied to a face.
                    enhancement_enabled=enhancement_enabled,
                    progress_token=progress_token,
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
    except ServiceBusyError as err:
        if progress_token:
            service.progress.finish(progress_token, failed=True)
        raise _busy(err) from err
    except Exception:
        if progress_token:
            service.progress.finish(progress_token, failed=True)
        raise
    finally:
        # Closed on every path, so a poller is never left watching a bar that
        # will not move again.
        if progress_token:
            service.progress.finish(progress_token)

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

    # `_read_upload` bounds each file; nothing bounded the count, so one
    # request could hand the service an unlimited number of 5 MB uploads to
    # hold in memory and write to disk (DEC-064).
    if len(files) > service.settings.max_document_files:
        raise HTTPException(
            status_code=413,
            detail=(
                f"A document may carry at most "
                f"{service.settings.max_document_files} files; "
                f"{len(files)} were supplied."
            ),
        )

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

    record = _job_or_expired(job_id)
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
        awaiting_release=checklist.get("awaiting_release", 0),
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
        archive, checklist = service.build_kit_package(kit_id)
    except KeyError as err:
        raise HTTPException(status_code=404, detail="Kit not found") from err

    # DEC-063: the archive is the clean files. The builder already leaves an
    # unreleased one out of it, and the download is refused rather than served
    # short, because a package silently missing the photograph is worse than
    # one the candidate is told they have not paid for.
    awaiting = int(checklist.get("awaiting_release", 0))
    if awaiting:
        raise HTTPException(
            status_code=402,
            detail=(
                f"{awaiting} prepared file(s) in this kit have not been paid "
                "for. The checklist is available at "
                f"/v1/kits/{kit_id}/package."
            ),
        )

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

    record = _job_or_expired(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")

    report_url = None
    output_url = None
    preview_url = None

    if record.status != ApiJobStatus.DELETED:
        report_url = f"/v1/jobs/{job_id}/report"
        if record.output_filename:
            output_url = f"/v1/jobs/{job_id}/output"
        if record.preview_watermarked:
            preview_url = f"/v1/jobs/{job_id}/preview"

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
        preview_url=preview_url,
        preview_watermarked=record.preview_watermarked,
        entitlement=record.entitlement,
        extendable=service.job_is_extendable(record),
        enhancement_enabled=record.enhancement_enabled,
        enhancements_applied=list(record.enhancements_applied),
        enhancement_switchable=bool(record.alternate_output_filename),
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

    record = _job_or_expired(job_id)
    if not record or record.status == ApiJobStatus.DELETED:
        raise HTTPException(status_code=404, detail="Job or report not found")

    if not service.store.file_exists(job_id, "report.json"):
        raise HTTPException(status_code=404, detail="Report artifact not found")

    report_data = service.store.read_file(job_id, "report.json")
    return Response(content=report_data, media_type="application/json")


@app.get("/v1/jobs/{job_id}/preview")
def get_job_preview(job_id: str) -> Response:
    """Stream the watermarked, reduced-resolution preview (DEC-063).

    This is the only image of a prepared file the browser may have before it
    is paid for. The mark is burned into the pixels of a downscale, so there
    is no layer to switch off and no clean copy underneath it.
    """
    if not JOB_ID_REGEX.match(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    record = _job_or_expired(job_id)
    if not record or record.status == ApiJobStatus.DELETED:
        raise HTTPException(status_code=404, detail="Job or preview not found")

    # `preview_watermarked` is written from the artifact, so an unmarked file
    # can never be served from this route by mistake.
    if not record.preview_watermarked or not record.preview_filename:
        raise HTTPException(
            status_code=404,
            detail="No preview could be rendered for this file",
        )

    if not service.store.file_exists(job_id, record.preview_filename):
        raise HTTPException(status_code=404, detail="Preview artifact not on disk")

    return Response(
        content=service.store.read_file(job_id, record.preview_filename),
        media_type=PREVIEW_MEDIA_TYPE,
        headers={
            "Content-Disposition": 'inline; filename="preview.jpg"',
            # A preview is one candidate's face. Nothing between here and the
            # browser may keep a copy of it.
            "Cache-Control": "private, no-store",
        },
    )


@app.get("/v1/jobs/{job_id}/output")
def get_job_output(job_id: str) -> Response:
    """Stream the clean prepared file, once the job is released (DEC-063)."""
    if not JOB_ID_REGEX.match(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    record = _job_or_expired(job_id)
    if not record or record.status == ApiJobStatus.DELETED:
        raise HTTPException(status_code=404, detail="Job or output not found")

    if not record.output_filename:
        raise HTTPException(status_code=404, detail="Output artifact not available")

    # The purchase gate. 402 rather than 403 because the condition is
    # payment and is expected to clear, and the message names the preview so
    # a caller is told what it may have instead.
    if not service.output_is_released(record):
        raise HTTPException(
            status_code=402,
            detail=(
                "This file has not been paid for. A watermarked preview is "
                f"available at /v1/jobs/{job_id}/preview."
            ),
        )

    # Enforce validity: must be succeeded or failed but invalid-output-save was allowed
    # (which implies the output file actually exists in registry and store)
    if not service.store.file_exists(job_id, record.output_filename):
        raise HTTPException(
            status_code=404, detail="Output artifact file not found on disk"
        )

    output_bytes = service.store.read_file(job_id, record.output_filename)
    # DEC-072: recorded after the bytes were successfully read, so this counts
    # files that actually left rather than requests that arrived.
    service.record_download(record)
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


@app.post("/v1/jobs/{job_id}/extend", response_model=JobRetentionResponse)
def extend_job_retention(job_id: str) -> JobRetentionResponse:
    """Give a live job one more retention window (DEC-067).

    Unauthenticated on purpose, like the rest of the candidate surface: a
    browser cannot hold a secret, and the worst this route can do is keep
    one file for `job_max_lifetime_seconds`, which is exactly what every
    file used to get unconditionally. It cannot resurrect an expired job and
    it cannot release one -- payment is a separate gate (DEC-063).
    """
    if not JOB_ID_REGEX.match(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    try:
        record = service.extend_job(job_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=(
                "This file is no longer available. It may have reached its "
                "deletion time, after which nothing can be extended."
            ),
        ) from None
    except RetentionCeilingReachedError:
        raise HTTPException(
            status_code=409,
            detail=(
                "This file has already been kept for as long as the platform "
                "will keep it. Download it now, or prepare it again later."
            ),
        ) from None

    return JobRetentionResponse(
        job_id=record.job_id,
        expires_at=record.expires_at,
        extendable=service.job_is_extendable(record),
    )


@app.get("/v1/progress/{token}")
def get_progress(token: str) -> dict[str, object]:
    """How far a preparation has got (DEC-075).

    Polled alongside the preparation, which is still a blocking request. The
    client mints the token because the job id does not exist until the work
    finishes, so it cannot be what identifies work in flight.

    An unknown token is `404` rather than a zeroed state: "I have never heard
    of this" and "this has not started yet" are different answers, and a
    client that cannot tell them apart will wait forever on a typo.
    """
    state = service.progress.get(token)
    if state is None:
        raise HTTPException(status_code=404, detail="No progress for that token")
    return json_safe(state)


@app.get("/v1/kits/{kit_id}/quote", response_model=KitQuoteResponse)
def get_kit_quote(kit_id: str) -> KitQuoteResponse:
    """What this kit costs, itemised (DEC-070).

    Read-only and safe to call on every render: it creates no order and
    reserves nothing, so the interface can show a price without committing the
    candidate to anything.
    """
    if not KIT_ID_REGEX.match(kit_id):
        raise HTTPException(status_code=400, detail="Invalid kit ID format")

    quote = quote_for(service.registry.jobs_in_kit(kit_id))
    return KitQuoteResponse(
        kit_id=kit_id,
        amount_paise=quote.amount_paise,
        list_amount_paise=quote.list_amount_paise,
        currency=quote.currency,
        chargeable_count=quote.chargeable_count,
        included_free_count=quote.included_free_count,
        already_released_count=quote.already_released_count,
        is_payable=quote.is_payable,
        lines=[
            QuoteLineResponse(
                job_id=line.job_id,
                requirement_id=line.requirement_id,
                requirement_type=line.requirement_type,
                chargeable=line.chargeable,
                reason=line.reason,
            )
            for line in quote.lines
        ],
    )


@app.post("/v1/kits/{kit_id}/order", response_model=KitOrderResponse)
def create_kit_order(kit_id: str) -> KitOrderResponse:
    """Create a Razorpay order for this kit, at a price we computed (DEC-070).

    This is what makes DEC-069's webhook safe on live keys. The amount comes
    from the jobs on disk, never from the caller, so a browser cannot ask to
    be charged less; and the order carries the kit in its `notes`, which is
    the only link between paying and receiving.
    """
    if not KIT_ID_REGEX.match(kit_id):
        raise HTTPException(status_code=400, detail="Invalid kit ID format")

    records = service.registry.jobs_in_kit(kit_id)
    quote = quote_for(records)
    if not quote.is_payable:
        # Nothing to charge for: an empty kit, one already paid, or one that
        # holds only document work, which is free. Sending a zero-amount order
        # to a payment gateway would be asking it to take nothing.
        raise HTTPException(
            status_code=409,
            detail="There is nothing to pay for in this kit.",
        )

    try:
        order = service.order_gateway.create_order(
            amount_paise=quote.amount_paise,
            currency=quote.currency,
            notes=order_notes(kit_id),
            receipt=f"kit-{kit_id}",
        )
    except OrderCreationError as err:
        print(f"razorpay order creation failed for {kit_id}: {err}")
        raise HTTPException(
            status_code=503,
            detail="Payment could not be started. Please try again shortly.",
        ) from None

    # DEC-071: remember exactly what was priced, so the payment releases that
    # set and not whatever the kit holds when the webhook arrives. Every live
    # job is recorded, not only the charged ones -- document work is free
    # *with* a purchase, so it is delivered by the same payment.
    try:
        service.orders.create(
            order_id=order.order_id,
            kit_id=kit_id,
            job_ids=[line.job_id for line in quote.lines],
            amount_paise=order.amount_paise,
            currency=order.currency,
        )
    except (ValueError, OSError) as err:
        # The order exists at Razorpay but we could not record it. Refusing is
        # right: paying against an order we cannot resolve would release
        # nothing and take the money.
        print(f"could not record order {order.order_id} for {kit_id}: {err}")
        raise HTTPException(
            status_code=503,
            detail="Payment could not be started. Please try again shortly.",
        ) from None

    return KitOrderResponse(
        kit_id=kit_id,
        order_id=order.order_id,
        amount_paise=order.amount_paise,
        currency=order.currency,
        key_id=order.key_id,
    )


@app.post("/v1/kits/{kit_id}/email", response_model=EmailDeliveryResponse)
def email_kit(kit_id: str, request: EmailDeliveryRequest) -> EmailDeliveryResponse:
    """Email a kit's paid files, so they outlive the thirty-minute window.

    Only released files are sent. The address is used and not stored (DEC-072).
    """
    if not KIT_ID_REGEX.match(kit_id):
        raise HTTPException(status_code=400, detail="Invalid kit ID format")

    records = service.registry.jobs_in_kit(kit_id)
    if request.job_ids:
        wanted = set(request.job_ids)
        records = [record for record in records if record.job_id in wanted]

    try:
        outcome = service.email_jobs(records, request.address)
    except EmailRejectedError as err:
        print(f"email delivery failed for {kit_id}: {err}")
        raise HTTPException(status_code=422, detail=str(err)) from None

    return EmailDeliveryResponse(**outcome)


@app.get(
    "/v1/orders/{order_id}/evidence",
    response_model=OrderEvidenceResponse,
    dependencies=[Depends(require_operator)],
)
def get_order_evidence(order_id: str) -> OrderEvidenceResponse:
    """What is known about one order, for deciding a refund (DEC-072).

    Operator-gated: it names a payment and what became of the files, which is
    nobody's business but the operator's. It establishes our facts and not the
    candidate's honesty -- a file can be delivered and still not arrive.
    """
    order = service.orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    jobs = []
    for job_id in order.job_ids:
        record = service.registry.get_job(job_id)
        if record is None:
            continue
        jobs.append(
            {
                "job_id": record.job_id,
                "requirement_type": record.requirement_type,
                "entitlement": record.entitlement.value,
                "released_at": record.released_at,
                "download_count": record.download_count,
                "first_downloaded_at": record.first_downloaded_at,
                "expires_at": record.expires_at,
                "email_attempts": [
                    attempt.model_dump() for attempt in record.email_attempts
                ],
            }
        )

    return OrderEvidenceResponse(
        order_id=order.order_id,
        kit_id=order.kit_id,
        amount_paise=order.amount_paise,
        currency=order.currency,
        created_at=order.created_at,
        paid_at=order.paid_at,
        payment_reference=order.payment_reference,
        delivered_at=order.delivered_at,
        delivery_method=order.delivery_method,
        job_ids=order.job_ids,
        jobs=jobs,
    )


@app.get(
    "/v1/metrics/usage",
    dependencies=[Depends(require_operator)],
)
def get_usage_metrics() -> dict[str, object]:
    """Preparations and conversion, per kit (DEC-073).

    Operator-gated, and the point of it: the free-preparation allowance should
    be set from what candidates actually do, not from a guess. Reports a
    distribution rather than a mean, because the mean of a population holding
    one script and a thousand candidates describes neither.
    """
    return service.usage.summary()


@app.post("/v1/jobs/{job_id}/enhancement", response_model=JobStatusResponse)
def set_job_enhancement(job_id: str, request: EnhancementToggleRequest) -> Any:
    """Switch a prepared photograph's lighting variant, instantly (DEC-076).

    Both variants were made during the one preparation, so this costs a file
    swap and a re-rendered preview rather than another ten seconds of the
    pipeline. Available before payment, which is the point: the candidate
    decides against the real result, and what they buy is what they chose.
    """
    if not JOB_ID_REGEX.match(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    record = _job_or_expired(job_id)
    if not record or record.status == ApiJobStatus.DELETED:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        service.set_enhancement(record, request.enabled)
    except LookupError as err:
        raise HTTPException(status_code=409, detail=str(err)) from None

    return get_job_status(job_id)


@app.post("/v1/payments/razorpay/webhook")
async def razorpay_webhook(request: Request) -> JSONResponse:
    """Release the files a verified Razorpay payment paid for (DEC-069).

    This is the caller DEC-063 anticipated when it left `release_job` with
    nothing calling it. What makes it acceptable where a plain release route
    was not is that the shared-secret signature is checked over the **raw
    request body, before the payload is parsed at all** -- so an unsigned
    request never reaches any code that reads what it is asking for.

    Deliberately not behind the operator token. Razorpay cannot send one, and
    the signature is a stronger proof of origin than a bearer token would be.
    """
    body = await request.body()
    signature = request.headers.get(SIGNATURE_HEADER, "")

    try:
        instruction = verify_and_read(
            body, signature, service.settings.razorpay_webhook_secret
        )
    except WebhookRejectedError as err:
        # 400 with nothing that would help a forger narrow down which check
        # failed. The reason goes to the operator's log, not to the caller.
        print(f"razorpay webhook rejected: {err.reason}")
        raise HTTPException(status_code=400, detail="Webhook rejected") from None

    if instruction is None:
        # A real event this service does not act on. Acknowledged, because
        # Razorpay retries anything it is not told arrived.
        return JSONResponse({"status": "ignored"})

    if instruction.names_nothing:
        # Signed by Razorpay, so the money moved, but the order carried no
        # job or kit in its notes and nothing can be released. Acknowledged
        # rather than refused -- retrying will not add the notes -- and
        # logged loudly, because it means an order was created without them
        # and a candidate has paid for something they will not receive.
        print(
            "razorpay webhook named no job or kit: "
            f"payment={instruction.payment_id} order={instruction.order_id}"
        )
        return JSONResponse({"status": "no_targets"})

    outcome = service.apply_release_instruction(instruction)
    if outcome["unknown"]:
        print(
            f"razorpay webhook could not release {outcome['unknown']} "
            f"for payment={instruction.payment_id}"
        )
    return JSONResponse({"status": "released", **outcome})


@app.delete("/v1/jobs/{job_id}")
def delete_job(job_id: str) -> dict[str, str]:
    """Completely remove all input, rule, report, output, and manifest artifacts."""
    if not JOB_ID_REGEX.match(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    record = _job_or_expired(job_id)
    if not record or record.status == ApiJobStatus.DELETED:
        raise HTTPException(status_code=404, detail="Job not found or already deleted")

    # 1. Delete all artifacts on disk (including job.json manifest)
    service.store.delete_job_directory(job_id)

    # 2. Update registry to DELETED (retains status in-memory only)
    service.registry.delete_job(job_id)

    return {"detail": "Job artifacts deleted successfully"}


@app.post(
    "/v1/cleanup-expired",
    dependencies=[Depends(require_operator)],  # noqa: B008
)
def cleanup_expired() -> dict[str, int]:
    """Trigger TTL cleanup of expired job folders on disk."""
    count = service.cleanup_expired_jobs()
    return {"cleaned_count": count}


@app.post(
    "/v1/rules/validate",
    response_model=RuleValidationResponse,
    dependencies=[Depends(require_operator)],  # noqa: B008
)
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
