"""Job record models and registry."""

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from exam_photo.api.contracts import ApiJobStatus

JOB_ID_REGEX = re.compile(r"^job_[A-Za-z0-9_-]+$")


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
