"""Job record models and registry."""

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from exam_photo.api.contracts import ApiJobStatus

JOB_ID_REGEX = re.compile(r"^job_[A-Za-z0-9_-]+$")

#: A kit identifier is minted by the browser and arrives from an untrusted
#: caller.  It is only ever a grouping key -- never a path segment -- but it
#: does appear in a URL, so its shape is pinned here and checked at the edge.
KIT_ID_REGEX = re.compile(r"^kit_[A-Za-z0-9_-]{1,64}$")


class ProcessingJobRecord(BaseModel):
    """Schema representing a job's manifest."""

    job_id: str
    status: ApiJobStatus
    created_at: str
    updated_at: str
    expires_at: str
    is_valid: Optional[bool] = None
    output_filename: Optional[str] = None
    issue_codes: List[str] = Field(default_factory=list)
    artifact_names: List[str] = Field(default_factory=list)
    rule_compliant: Optional[bool] = None
    visual_quality_acceptable: Optional[bool] = None
    portrait_quality_report: Optional[dict[str, Any]] = None
    matte_quality_report: Optional[dict[str, Any]] = None
    quality_mode: Optional[str] = None
    diagnostic_available: Optional[bool] = None

    # --- Kit and requirement identity (DEC-055, DEC-058) -------------------
    #
    # `kit_id` is a grouping key written into the manifest that already
    # exists, not a record of its own: gathering a kit is a scan of manifests
    # the registry already performs at startup.  All four are optional because
    # `/v1/process` still serves a caller that holds a rule and names no
    # examination.
    kit_id: Optional[str] = None
    exam_id: Optional[str] = None
    requirement_id: Optional[str] = None
    requirement_type: Optional[str] = None
    #: Carried verbatim from the rule record so the package can honour DEC-056
    #: without re-reading the catalogue, and never reduced to a boolean.
    platform_support: Optional[str] = None

    # --- Deliverable outcome ----------------------------------------------
    #
    # DEC-041 makes production the rule and refusal the exception, so these
    # record what is *true about* a file that was produced rather than whether
    # one was.  DEC-056 turns them into the third UI state.
    outcome: Optional[str] = None
    findings: List[str] = Field(default_factory=list)
    is_blank: Optional[bool] = None
    ceiling_was_unpublished: Optional[bool] = None
    exceeds_ceiling: Optional[bool] = None
    output_byte_size: Optional[int] = None
    output_width: Optional[int] = None
    output_height: Optional[int] = None
    #: Set so the download route can serve a PDF as a PDF.  The photograph
    #: path is always JPEG; a deliverable may be either.
    output_media_type: Optional[str] = None
    #: Uploaded sources for a multi-page document, in the order they arrived
    #: (DEC-053).  Held so `assemble` can re-read what `plan` accepted.
    document_sources: List[str] = Field(default_factory=list)


class JobRegistry:
    """Manages job records by storing them in memory and persisting job.json manifests."""

    def __init__(self, artifact_root: Path):
        self.artifact_root = artifact_root
        self._cache: Dict[str, ProcessingJobRecord] = {}

    def _get_manifest_path(self, job_id: str) -> Path:
        return self.artifact_root / job_id / "job.json"

    def create_job(self, job_id: str, ttl_seconds: int) -> ProcessingJobRecord:
        """Create a new job record, cache it, and save the manifest to disk."""
        if not JOB_ID_REGEX.match(job_id):
            raise ValueError(f"Invalid job_id format: {job_id}")

        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=ttl_seconds)

        record = ProcessingJobRecord(
            job_id=job_id,
            status=ApiJobStatus.RECEIVED,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            expires_at=expires.isoformat(),
        )
        self._cache[job_id] = record
        self._save_to_disk(record)
        return record

    def get_job(self, job_id: str) -> Optional[ProcessingJobRecord]:
        """Retrieve a job record by job_id from cache or by reading its manifest from disk."""
        if not JOB_ID_REGEX.match(job_id):
            return None

        # Check cache
        if job_id in self._cache:
            return self._cache[job_id]

        # Try to load from disk
        path = self._get_manifest_path(job_id)
        if path.is_file():
            try:
                record = ProcessingJobRecord.model_validate_json(
                    path.read_text(encoding="utf-8")
                )
                self._cache[job_id] = record
                return record
            except Exception:
                # Return None if the manifest on disk is corrupted
                pass
        return None

    def update_job(self, record: ProcessingJobRecord) -> None:
        """Update job record in cache and persist changes to its manifest file."""
        if not JOB_ID_REGEX.match(record.job_id):
            raise ValueError(f"Invalid job_id format in record: {record.job_id}")
        record.updated_at = datetime.now(timezone.utc).isoformat()
        self._cache[record.job_id] = record
        self._save_to_disk(record)

    def delete_job(self, job_id: str) -> None:
        """Mark the job as DELETED in memory only (does not write to disk)."""
        if not JOB_ID_REGEX.match(job_id):
            raise ValueError(f"Invalid job_id format: {job_id}")
        record = self.get_job(job_id)
        if record:
            record.status = ApiJobStatus.DELETED
            record.updated_at = datetime.now(timezone.utc).isoformat()
            self._cache[job_id] = record

    def jobs_in_kit(self, kit_id: str) -> List[ProcessingJobRecord]:
        """Every live job belonging to one kit, oldest first.

        Reads from disk before filtering, so a kit assembled by an earlier
        process -- or before a restart -- is still gatherable. Deleted jobs are
        excluded: a candidate who removed a deliverable did so deliberately and
        it must not reappear in their package.
        """
        if not KIT_ID_REGEX.match(kit_id):
            return []
        self.scan_manifests()
        matching = [
            record
            for record in self._cache.values()
            if record.kit_id == kit_id and record.status != ApiJobStatus.DELETED
        ]
        return sorted(matching, key=lambda record: record.created_at)

    def _save_to_disk(self, record: ProcessingJobRecord) -> None:
        path = self._get_manifest_path(record.job_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(record.model_dump_json(indent=2), encoding="utf-8")

    def scan_manifests(self) -> List[ProcessingJobRecord]:
        """Scan all job directories on disk and load any valid job.json manifests."""
        records: List[ProcessingJobRecord] = []
        if not self.artifact_root.is_dir():
            return records

        for job_dir in self.artifact_root.iterdir():
            if job_dir.is_dir() and JOB_ID_REGEX.match(job_dir.name):
                manifest_path = job_dir / "job.json"
                if manifest_path.is_file():
                    try:
                        record = ProcessingJobRecord.model_validate_json(
                            manifest_path.read_text(encoding="utf-8")
                        )
                        self._cache[record.job_id] = record
                        records.append(record)
                    except Exception:
                        pass
        return records
