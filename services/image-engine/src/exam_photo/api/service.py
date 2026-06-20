"""API Orchestration Service coordinating job creation, processing, and storage."""

import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

from exam_photo.api.contracts import ApiJobStatus
from exam_photo.api.jobs import JobRegistry, ProcessingJobRecord
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore

# Lazy imports for rule pipeline to avoid importing heavy libraries at startup
from exam_photo.orchestration.rule_pipeline import (
    RuleOrchestratedPipeline,
    RulePipelineConfig,
)


class UploadLimitExceededError(ValueError):
    """Exception raised when an upload exceeds the allowed byte size limit."""

    pass


def find_repo_root() -> Path:
    """Traverse upward to find the repository root containing AGENTS.md."""
    env_val = os.environ.get("EXAM_PHOTO_REPO_ROOT")
    if env_val:
        p = Path(env_val).resolve()
        if p.exists():
            return p

    curr = Path(__file__).resolve().parent
    for _ in range(7):
        if (curr / "AGENTS.md").exists() or (curr / "model-manifests").exists():
            return curr
        if curr.parent == curr:
            break
        curr = curr.parent
    return Path(".").resolve()


class ApiProcessingService:
    """Service layer executing rule validation pipeline and managing job state."""

    def __init__(self, settings: ApiSettings):
        self.settings = settings
        self.store = LocalArtifactStore(settings.artifact_root)
        self.registry = JobRegistry(settings.artifact_root)
        self.repo_root = find_repo_root()

        # Load existing manifests on startup
        self.registry.scan_manifests()

    def _resolve_face_model(self) -> Tuple[Path, str]:
        """Resolve face model path and expected sha256."""
        if self.settings.face_model_path:
            return (
                self.settings.face_model_path,
                self.settings.face_expected_sha256 or "",
            )

        face_model_path_str = os.environ.get("EXAM_PHOTO_FACE_MODEL_PATH")
        expected_face_sha = os.environ.get("EXAM_PHOTO_FACE_MODEL_SHA256", "")
        if not face_model_path_str:
            manifest_path = self.repo_root / "model-manifests" / "face-detector.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as mf:
                        manifest = json.load(mf)
                    face_model_path_str = manifest.get("local_model_path_default")
                    expected_face_sha = manifest.get("sha256", "")
                except Exception:
                    pass
            if not face_model_path_str:
                face_model_path_str = "model-assets/blaze_face_short_range.tflite"

        face_model_path = Path(face_model_path_str)
        if not face_model_path.is_absolute():
            face_model_path = self.repo_root / face_model_path
        return face_model_path, expected_face_sha

    def _resolve_segmenter_model(self) -> Tuple[Path, str]:
        """Resolve segmenter model path and expected sha256."""
        if self.settings.segmenter_model_path:
            return (
                self.settings.segmenter_model_path,
                self.settings.segmenter_expected_sha256 or "",
            )

        segmenter_model_path_str = os.environ.get("EXAM_PHOTO_SEGMENTER_MODEL_PATH")
        expected_seg_sha = os.environ.get("EXAM_PHOTO_SEGMENTER_MODEL_SHA256", "")
        if not segmenter_model_path_str:
            manifest_path = (
                self.repo_root / "model-manifests" / "subject-segmenter.json"
            )
            if manifest_path.exists():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as mf:
                        manifest = json.load(mf)
                    variant_name = manifest.get(
                        "selected_variant", "selfie_bin_general"
                    )
                    variants = manifest.get("variants", {})
                    variant = variants.get(variant_name)
                    if variant is not None:
                        filename = variant.get("filename")
                        if filename:
                            segmenter_model_path_str = "model-assets/" + filename
                        expected_seg_sha = variant.get("sha256", "")
                except Exception:
                    pass
            if not segmenter_model_path_str:
                segmenter_model_path_str = (
                    "model-assets/selfie_multiclass_256x256.tflite"
                )

        segmenter_model_path = Path(segmenter_model_path_str)
        if not segmenter_model_path.is_absolute():
            segmenter_model_path = self.repo_root / segmenter_model_path
        return segmenter_model_path, expected_seg_sha

    def generate_job_id(self) -> str:
        """Generate a random urlsafe token for a job ID."""
        return f"job_{secrets.token_urlsafe(16)}"

    def check_upload_limit(self, size_bytes: int) -> None:
        """Raise an error if the uploaded content size exceeds setting limits."""
        if size_bytes > self.settings.max_upload_bytes:
            raise UploadLimitExceededError(
                f"File size of {size_bytes} bytes exceeds the limit "
                f"of {self.settings.max_upload_bytes} bytes."
            )

    def process_job_sync(
        self,
        job_id: str,
        image_bytes: bytes,
        rule_dict: Dict[str, Any],
        allow_invalid_output: bool = False,
    ) -> ProcessingJobRecord:
        """Run the compliance processing pipeline synchronously and persist artifacts."""
        self.check_upload_limit(len(image_bytes))

        # 1. Create a job record and store input/rule files
        record = self.registry.create_job(job_id, self.settings.job_ttl_seconds)
        record.status = ApiJobStatus.PROCESSING
        self.registry.update_job(record)

        self.store.write_file(job_id, "input.jpg", image_bytes)
        self.store.write_file(
            job_id,
            "rule.json",
            json.dumps(rule_dict, indent=2).encode("utf-8"),
        )

        artifact_names = ["input.jpg", "rule.json"]

        try:
            # 2. Instantiate pipeline using resolved models
            face_model, face_sha = self._resolve_face_model()
            segmenter_model, segmenter_sha = self._resolve_segmenter_model()

            pipeline = RuleOrchestratedPipeline(
                face_model_path=face_model,
                segmenter_model_path=segmenter_model,
                face_expected_sha256=face_sha,
                segmenter_expected_sha256=segmenter_sha,
            )

            job_dir = self.store.get_file_path(job_id, ".")

            config = RulePipelineConfig(
                save_diagnostic_artifacts=True,
                allow_invalid_output=allow_invalid_output,
                output_dir=job_dir,
            )

            # 3. Execute pipeline
            result = pipeline.process_rule(image_bytes, rule_dict, config)

            # 4. Save report.json (encoded_bytes is excluded automatically)
            report_bytes = result.model_dump_json(indent=2).encode("utf-8")
            self.store.write_file(job_id, "report.json", report_bytes)
            artifact_names.append("report.json")

            # 5. Save output if valid or explicitly requested
            should_save_output = result.is_valid or allow_invalid_output
            if should_save_output and result.output_filename and result.encoded_bytes:
                self.store.write_file(
                    job_id,
                    result.output_filename,
                    result.encoded_bytes,
                )
                artifact_names.append(result.output_filename)

            # Update job record with pipeline outcomes
            record.status = (
                ApiJobStatus.SUCCEEDED if result.is_valid else ApiJobStatus.FAILED
            )
            record.is_valid = result.is_valid
            record.output_filename = (
                result.output_filename if should_save_output else None
            )
            record.issue_codes = [c.value for c in result.issue_codes]
            record.artifact_names = artifact_names

        except Exception:
            # Pipeline failure fallback
            record.status = ApiJobStatus.FAILED
            record.is_valid = False
            record.issue_codes = ["PIPELINE_ERROR"]
            record.artifact_names = artifact_names

            # Save minimal failure report
            error_report = {
                "is_valid": False,
                "issue_codes": ["PIPELINE_ERROR"],
                "message": "Processing failed internally.",
                "error_code": "PIPELINE_ERROR",
            }
            self.store.write_file(
                job_id,
                "report.json",
                json.dumps(error_report, indent=2).encode("utf-8"),
            )
            artifact_names.append("report.json")
            record.artifact_names = artifact_names

        self.registry.update_job(record)
        return record

    def cleanup_expired_jobs(self) -> int:
        """Scan all manifests on disk and clean up expired job artifacts."""
        records = self.registry.scan_manifests()
        now_str = datetime.now(timezone.utc).isoformat()
        deleted_count = 0

        for record in records:
            if record.status != ApiJobStatus.DELETED and record.expires_at < now_str:
                self.store.delete_job_directory(record.job_id)
                self.registry.delete_job(record.job_id)
                deleted_count += 1

        return deleted_count
