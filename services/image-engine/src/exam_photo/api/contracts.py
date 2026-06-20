"""API response and request contract models."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ApiJobStatus(str, Enum):
    """Execution status of a processing job."""

    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    DELETED = "DELETED"


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
