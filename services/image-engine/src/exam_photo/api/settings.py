"""API configuration settings module."""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ApiSettings(BaseModel):
    """Configuration settings for the local API service."""

    artifact_root: Path = Field(default_factory=lambda: Path(".tmp/artifacts"))
    max_upload_bytes: int = Field(default=5 * 1024 * 1024)  # 5 MB
    job_ttl_seconds: int = Field(default=3600)  # 1 hour

    # Where the encoded examination catalogue is read from (DEC-055).  Relative
    # paths resolve against the repository root, the same way the model paths
    # do.  The directory is still named `examples/rules` while holding the real
    # generated catalogue; renaming it touches the encoder, the gap register
    # and every documented path, so the name is carried rather than changed.
    catalogue_root: Optional[Path] = None

    # Model configuration overrides
    face_model_path: Optional[Path] = None
    segmenter_model_path: Optional[Path] = None
    face_expected_sha256: Optional[str] = None
    segmenter_expected_sha256: Optional[str] = None

    # Subject segmentation backend (DEC-031).  "auto" uses BiRefNet when its
    # vendored weights and the optional matting extra are both present, and
    # falls back to MediaPipe otherwise, so the served app gets the better
    # matte without a separate opt-in step and still starts on a machine that
    # has not run scripts/download_birefnet.py.
    matting_backend: str = "auto"

    # Pipeline output and local CORS toggles
    allow_invalid_output_save: bool = False
    local_cors_enabled: bool = False

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
    if "EXAM_PHOTO_CATALOGUE_ROOT" in os.environ:
        kwargs["catalogue_root"] = Path(os.environ["EXAM_PHOTO_CATALOGUE_ROOT"])

    # Load model configuration paths and hashes from environment
    if "EXAM_PHOTO_FACE_MODEL_PATH" in os.environ:
        kwargs["face_model_path"] = Path(os.environ["EXAM_PHOTO_FACE_MODEL_PATH"])
    if "EXAM_PHOTO_SEGMENTER_MODEL_PATH" in os.environ:
        kwargs["segmenter_model_path"] = Path(
            os.environ["EXAM_PHOTO_SEGMENTER_MODEL_PATH"]
        )
    if "EXAM_PHOTO_FACE_MODEL_SHA256" in os.environ:
        kwargs["face_expected_sha256"] = os.environ["EXAM_PHOTO_FACE_MODEL_SHA256"]
    if "EXAM_PHOTO_SEGMENTER_MODEL_SHA256" in os.environ:
        kwargs["segmenter_expected_sha256"] = os.environ[
            "EXAM_PHOTO_SEGMENTER_MODEL_SHA256"
        ]

    if "EXAM_PHOTO_MATTING_BACKEND" in os.environ:
        kwargs["matting_backend"] = os.environ["EXAM_PHOTO_MATTING_BACKEND"].lower()

    # Load boolean flags
    if "EXAM_PHOTO_ALLOW_INVALID_OUTPUT_SAVE" in os.environ:
        val = os.environ["EXAM_PHOTO_ALLOW_INVALID_OUTPUT_SAVE"].lower()
        kwargs["allow_invalid_output_save"] = val in ("1", "true", "yes")
    if "EXAM_PHOTO_LOCAL_CORS_ENABLED" in os.environ:
        val = os.environ["EXAM_PHOTO_LOCAL_CORS_ENABLED"].lower()
        kwargs["local_cors_enabled"] = val in ("1", "true", "yes")

    return ApiSettings(**kwargs)
