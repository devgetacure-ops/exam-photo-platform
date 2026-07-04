"""FastAPI application for the local compliance API."""

import json
import re

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from exam_photo.api.contracts import (
    ApiJobStatus,
    JobStatusResponse,
    ProcessImageResponse,
    RuleValidationErrorResponse,
    RuleValidationRequest,
    RuleValidationResponse,
)
from exam_photo.api.service import ApiProcessingService, UploadLimitExceededError
from exam_photo.api.settings import get_settings
from exam_photo.rule_validation import validate_exam_rule

JOB_ID_REGEX = re.compile(r"^job_[A-Za-z0-9_-]+$")

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


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return the status of the local processing API."""
    return {"status": "healthy"}


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
    return Response(content=output_bytes, media_type="image/jpeg")


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
