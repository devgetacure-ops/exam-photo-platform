"""API configuration settings module."""

import os
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class ApiSettings(BaseModel):
    """Configuration settings for the local API service."""

    artifact_root: Path = Field(default_factory=lambda: Path(".tmp/artifacts"))
    max_upload_bytes: int = Field(default=5 * 1024 * 1024)  # 5 MB
    job_ttl_seconds: int = Field(default=3600)  # 1 hour

    @field_validator("artifact_root")
    @classmethod
    def validate_artifact_root(cls, v: Path) -> Path:
        """Ensure artifact_root is not a filesystem root drive."""
        resolved = v.resolve()
        # A root drive/directory resolves to a path where it equals its own parent
        # or has an empty name (like WindowsPath('C:\\') or PosixPath('/'))
        if resolved == resolved.parent or not resolved.name:
            raise ValueError(
                "artifact_root cannot be a filesystem root drive/directory"
            )
        return resolved

    @field_validator("max_upload_bytes")
    @classmethod
    def validate_max_upload(cls, v: int) -> int:
        """Ensure max upload bytes is strictly positive."""
        if v <= 0:
            raise ValueError("max_upload_bytes must be greater than 0")
        return v

    @field_validator("job_ttl_seconds")
    @classmethod
    def validate_job_ttl(cls, v: int) -> int:
        """Ensure job TTL seconds is strictly positive."""
        if v <= 0:
            raise ValueError("job_ttl_seconds must be greater than 0")
        return v


def get_settings() -> ApiSettings:
    """Load settings from environment variables with defaults."""
    from typing import Any
    kwargs: dict[str, Any] = {}
    if "EXAM_PHOTO_ARTIFACT_ROOT" in os.environ:
        kwargs["artifact_root"] = Path(os.environ["EXAM_PHOTO_ARTIFACT_ROOT"])
    if "EXAM_PHOTO_MAX_UPLOAD_BYTES" in os.environ:
        kwargs["max_upload_bytes"] = int(os.environ["EXAM_PHOTO_MAX_UPLOAD_BYTES"])
    if "EXAM_PHOTO_JOB_TTL_SECONDS" in os.environ:
        kwargs["job_ttl_seconds"] = int(os.environ["EXAM_PHOTO_JOB_TTL_SECONDS"])

    return ApiSettings(**kwargs)
