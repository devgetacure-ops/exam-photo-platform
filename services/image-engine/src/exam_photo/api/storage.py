"""Local artifact storage adapter with path traversal protection."""

import re
import shutil
import time
from pathlib import Path
from typing import Callable, Optional

JOB_ID_REGEX = re.compile(r"^job_[A-Za-z0-9_-]+$")

#: Where a job's files wait, out of every candidate route's reach, for the
#: operator's longer window (DEC-122).
HELD_DIRECTORY = "_held"

#: Given a held directory, the epoch second at which it must be erased.
HeldDeadline = Callable[[Path], float]


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

    def delete_file(self, job_id: str, filename: str) -> None:
        """Remove one file from a job's directory, if it is there."""
        file_path = self._validate_file_path(job_id, filename)
        if file_path.is_file():
            file_path.unlink()

    def delete_job_directory(self, job_id: str) -> None:
        """Completely remove the job's directory and all its files from disk."""
        job_dir = self._validate_job_id(job_id)
        if job_dir.is_dir():
            shutil.rmtree(job_dir)

    def _held_directory(self, job_id: str) -> Path:
        self._validate_job_id(job_id)
        return self.artifact_root / HELD_DIRECTORY / job_id

    def hold_job_directory(self, job_id: str) -> None:
        """Take a job's files out of the candidate's reach, keeping them (DEC-122).

        The directory moves under `_held/`, which no job route reads, so to
        every candidate-facing route the job is as gone as a deleted one.
        """
        job_dir = self._validate_job_id(job_id)
        if not job_dir.is_dir():
            return
        held = self._held_directory(job_id)
        if held.exists():
            shutil.rmtree(held)
        held.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(job_dir), str(held))
        except OSError:
            # A file that cannot be kept must still leave the candidate's reach.
            shutil.rmtree(job_dir, ignore_errors=True)

    def held_job_directory(self, job_id: str) -> Optional[Path]:
        """The held directory of a job, if the operator's window still has it."""
        try:
            held = self._held_directory(job_id)
        except ValueError:
            return None
        return held if held.is_dir() else None

    def held_file_path(self, job_id: str, filename: str) -> Optional[Path]:
        """A file inside a held job, or None; never a path outside it."""
        held = self.held_job_directory(job_id)
        if held is None:
            return None
        root = held.resolve()
        path = (root / filename).resolve()
        if root not in path.parents or not path.is_file():
            return None
        return path

    def sweep_held(self, deadline_for: HeldDeadline) -> int:
        """Erase every held job whose operator window has closed."""
        root = self.artifact_root / HELD_DIRECTORY
        if not root.is_dir():
            return 0
        removed = 0
        now = time.time()
        for held in root.iterdir():
            if held.is_dir() and now >= deadline_for(held):
                shutil.rmtree(held, ignore_errors=True)
                removed += 1
        return removed
