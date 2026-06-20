"""Local artifact storage adapter with path traversal protection."""

import re
import shutil
from pathlib import Path

JOB_ID_REGEX = re.compile(r"^job_[A-Za-z0-9_-]+$")


class LocalArtifactStore:
    """Manages reading, writing, and deletion of temporary job artifacts."""

    def __init__(self, artifact_root: Path):
        self.artifact_root = artifact_root.resolve()

    def _validate_job_id(self, job_id: str) -> Path:
        """Validate job ID format and resolve job directory with traversal check."""
        if not JOB_ID_REGEX.match(job_id):
            raise ValueError(f"Invalid job_id format: {job_id}")
        job_dir = (self.artifact_root / job_id).resolve()
        # Verify job_dir is strictly inside artifact_root
        if self.artifact_root not in job_dir.parents and job_dir != self.artifact_root:
            raise ValueError("Directory traversal detected in job_id")
        return job_dir

    def _validate_file_path(self, job_id: str, filename: str) -> Path:
        """Ensure file path resides within the designated job directory boundary."""
        job_dir = self._validate_job_id(job_id)
        file_path = (job_dir / filename).resolve()
        # Verify file_path is strictly inside job_dir
        if job_dir not in file_path.parents and file_path != job_dir:
            raise ValueError("Directory traversal detected in filename")
        return file_path

    def write_file(self, job_id: str, filename: str, content: bytes) -> Path:
        """Write content to a file inside the job directory."""
        file_path = self._validate_file_path(job_id, filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
        return file_path

    def read_file(self, job_id: str, filename: str) -> bytes:
        """Read content from a file inside the job directory."""
        file_path = self._validate_file_path(job_id, filename)
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: {filename} in job {job_id}")
        return file_path.read_bytes()

    def file_exists(self, job_id: str, filename: str) -> bool:
        """Check if a file exists inside the job directory."""
        try:
            file_path = self._validate_file_path(job_id, filename)
            return file_path.is_file()
        except ValueError:
            return False

    def get_file_path(self, job_id: str, filename: str) -> Path:
        """Get the absolute Path to a file inside the job directory."""
        return self._validate_file_path(job_id, filename)

    def delete_job_directory(self, job_id: str) -> None:
        """Completely remove the job's directory and all its files from disk."""
        job_dir = self._validate_job_id(job_id)
        if job_dir.is_dir():
            shutil.rmtree(job_dir)
