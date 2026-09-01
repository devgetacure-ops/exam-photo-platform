"""API Orchestration Service coordinating job creation, processing, and storage."""

import io
import json
import os
import secrets
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from exam_photo.api.contracts import ApiJobStatus
from exam_photo.api.jobs import JobRegistry, ProcessingJobRecord
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore
from exam_photo.models.exam_rule import (
    ExamRequirement,
    ExamRule,
    PlatformSupport,
)
from exam_photo.orchestration.deliverable_pipeline import (
    DeliverableResult,
    prepare_deliverable,
)
from exam_photo.orchestration.filename_generation import (
    FilenameGenerationConfig,
    generate_safe_filename,
)
from exam_photo.orchestration.rule_catalogue import Catalogue, load_catalogue

# Lazy imports for rule pipeline to avoid importing heavy libraries at startup
from exam_photo.orchestration.rule_pipeline import (
    RuleOrchestratedPipeline,
    RulePipelineConfig,
)
from exam_photo.pdf import (
    DocumentPlan,
    DocumentResult,
    PageRef,
    assemble_document,
    plan_document,
)


class UploadLimitExceededError(ValueError):
    """Exception raised when an upload exceeds the allowed byte size limit."""

    pass


class RequirementNotFoundError(LookupError):
    """The examination exists but does not carry the named requirement."""


class RequirementNotServedError(PermissionError):
    """The platform does not prepare this requirement, and says why.

    Raised for any requirement whose ``platform_support`` is not ``supported``
    or ``partially_supported``. The rule model already refuses to *record* an
    impossible support state; this is the independent second barrier that
    refuses to *act* on one (DEC-056). A candidate believing the platform
    completed their live capture is this product's worst failure mode, and
    leaving the check to the browser would put the whole boundary behind one
    layer of client code.
    """

    def __init__(self, requirement: "ExamRequirement") -> None:
        self.requirement = requirement
        self.platform_support = requirement.platform_support.value
        self.submission_method = requirement.submission_method.value
        super().__init__(
            f"The platform does not prepare '{requirement.requirement_name}'. "
            f"Its support state is '{requirement.platform_support.value}' and "
            f"it is provided by '{requirement.submission_method.value}'."
        )


#: The only two states in which the platform will act on a requirement.
#:
#: `partially_supported` is included deliberately: it produces a real file that
#: satisfies part of the specification -- TNPSC and Kerala PSC want a name and
#: date printed on the photograph, which the engine cannot render -- and the
#: shortfall travels with the response rather than being converted into a
#: refusal. Withholding the file would help nobody.
_SERVED_SUPPORT = frozenset(
    {PlatformSupport.SUPPORTED, PlatformSupport.PARTIALLY_SUPPORTED}
)


#: Extension to media type for the files this service serves.
#:
#: A deliverable may legitimately be a PDF (DEC-052), so the download route
#: cannot assume JPEG the way it could when a photograph was the only output.
_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".pdf": "application/pdf",
}


def _published_filename(requirement: ExamRequirement) -> Optional[str]:
    """The exact filename the body requires, where one is published."""
    spec = requirement.file_spec
    filename = spec.filename if spec is not None else None
    if filename is None:
        return None
    exact = filename.exact_filename
    return str(exact) if exact else None


def _media_type_for(filename: str) -> str:
    """The media type for a produced file, defaulting to an opaque one.

    Falling back to `application/octet-stream` rather than to JPEG: a wrong
    content type on a download is how a PDF arrives named `.pdf` and refuses
    to open, and guessing image is the guess most likely to be wrong now that
    documents are in scope.
    """
    return _MEDIA_TYPES.get(Path(filename).suffix.lower(), "application/octet-stream")


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

        # Read the examination catalogue once at startup.  It is 39 records of
        # roughly 10 KB, it changes only when the encoder is re-run, and every
        # picker request would otherwise re-read and re-validate the whole
        # directory.  `reload_catalogue` exists for the case where it does
        # change under a running service.
        self.catalogue = load_catalogue(self.catalogue_root)

    @property
    def catalogue_root(self) -> Path:
        """Where the encoded examination catalogue is read from.

        Relative settings resolve against the repository root, the same way
        the model asset paths do, so a service started from any working
        directory finds the same catalogue.
        """
        configured = self.settings.catalogue_root
        if configured is None:
            return self.repo_root / "examples" / "rules"
        if configured.is_absolute():
            return configured
        return self.repo_root / configured

    def reload_catalogue(self) -> Catalogue:
        """Re-read the catalogue from disk, e.g. after re-running the encoder."""
        self.catalogue = load_catalogue(self.catalogue_root)
        return self.catalogue

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

    def _resolve_birefnet_onnx(self) -> Optional[Tuple[Path, str]]:
        """Return (model_dir, sha256) if the ONNX BiRefNet backend is usable
        on this machine, else None."""
        try:
            from exam_photo.providers.segmenters.birefnet_onnx_segmenter import (
                load_manifest_defaults,
            )

            model_dir, weights_name, sha, _size = load_manifest_defaults(self.repo_root)
        except Exception:
            return None
        if not (model_dir / weights_name).exists():
            return None
        try:
            import onnxruntime  # noqa: F401
        except ImportError:
            return None
        return model_dir, sha

    def _resolve_birefnet_torch(self) -> Optional[Tuple[Path, str]]:
        """Return (model_dir, sha256) if the PyTorch BiRefNet backend is
        usable on this machine, else None."""
        try:
            from exam_photo.providers.segmenters.birefnet_segmenter import (
                load_manifest_defaults,
            )

            model_dir, weights_name, sha, _size = load_manifest_defaults(self.repo_root)
        except Exception:
            return None
        if not (model_dir / weights_name).exists():
            return None
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
        except ImportError:
            return None
        return model_dir, sha

    def _resolve_matting_backend(self) -> Tuple[str, Optional[Path], str]:
        """Resolve the subject segmentation backend for this service.

        Returns ``(backend, birefnet_model_dir, birefnet_sha256)``. ``"auto"``
        (the default) prefers the ONNX backend (faster-matting Step 1: same
        weights and maths as the PyTorch backend, roughly 2x faster on CPU,
        and needs only the lightweight ``matting-onnx`` extra rather than
        torch), then falls back to the PyTorch backend, then to MediaPipe --
        so a machine that has not run the model acquisition/export scripts
        still serves requests rather than failing every job.
        """
        requested = (self.settings.matting_backend or "auto").lower()
        if requested == "mediapipe":
            return "mediapipe", None, ""

        if requested == "birefnet_onnx":
            resolved = self._resolve_birefnet_onnx()
            if resolved is None:
                raise RuntimeError(
                    "matting_backend='birefnet_onnx' requested but missing "
                    "the exported weights (run scripts/export_birefnet_onnx.py) "
                    'or the matting-onnx extra (pip install -e ".[dev,matting-onnx]").'
                )
            return "birefnet_onnx", resolved[0], resolved[1]

        if requested == "birefnet":
            resolved = self._resolve_birefnet_torch()
            if resolved is None:
                raise RuntimeError(
                    "matting_backend='birefnet' requested but missing the "
                    "vendored weights (run scripts/download_birefnet.py) or "
                    'the matting extra (pip install -e ".[dev,matting]").'
                )
            return "birefnet", resolved[0], resolved[1]

        # "auto": prefer ONNX, then PyTorch, then MediaPipe.
        onnx_resolved = self._resolve_birefnet_onnx()
        if onnx_resolved is not None:
            return "birefnet_onnx", onnx_resolved[0], onnx_resolved[1]
        torch_resolved = self._resolve_birefnet_torch()
        if torch_resolved is not None:
            return "birefnet", torch_resolved[0], torch_resolved[1]
        return "mediapipe", None, ""

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
        quality_mode: str = "balanced",
        save_diagnostic_artifacts: bool = False,
        kit_id: Optional[str] = None,
        exam_id: Optional[str] = None,
        requirement: Optional[ExamRequirement] = None,
    ) -> ProcessingJobRecord:
        """Run the compliance processing pipeline synchronously and persist artifacts.

        The identity arguments are absent for `/v1/process`, which serves the
        rule-admin console and names no examination, and present when this is
        reached through the kit's preparation endpoint.
        """
        self.check_upload_limit(len(image_bytes))

        # 1. Create a job record and store input/rule files
        record = self.registry.create_job(job_id, self.settings.job_ttl_seconds)
        record.status = ApiJobStatus.PROCESSING
        record.kit_id = kit_id
        record.exam_id = exam_id
        if requirement is not None:
            record.requirement_id = requirement.requirement_id
            record.requirement_type = requirement.requirement_type.value
            record.platform_support = requirement.platform_support.value
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

            backend, birefnet_dir, birefnet_sha = self._resolve_matting_backend()
            pipeline = RuleOrchestratedPipeline(
                face_model_path=face_model,
                segmenter_model_path=segmenter_model,
                face_expected_sha256=face_sha,
                segmenter_expected_sha256=segmenter_sha,
                matting_backend=backend,
                birefnet_model_dir=birefnet_dir,
                birefnet_expected_sha256=birefnet_sha,
            )

            job_dir = self.store.get_file_path(job_id, ".")

            config = RulePipelineConfig(
                save_diagnostic_artifacts=save_diagnostic_artifacts,
                allow_invalid_output=allow_invalid_output,
                output_dir=job_dir,
                quality_mode=quality_mode,
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

            if save_diagnostic_artifacts:
                artifact_names.extend(
                    ["refined_alpha.png", "decontaminate_foreground.png"]
                )

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
            record.rule_compliant = result.rule_compliant
            record.visual_quality_acceptable = result.visual_quality_acceptable
            record.portrait_quality_report = result.portrait_quality_report
            record.matte_quality_report = result.matte_quality_report
            record.quality_mode = quality_mode
            record.diagnostic_available = save_diagnostic_artifacts
            record.output_media_type = (
                _media_type_for(record.output_filename)
                if record.output_filename
                else None
            )
            record.output_byte_size = (
                len(result.encoded_bytes) if result.encoded_bytes else None
            )
            # DEC-056's third state, on the photograph path too: a compliant
            # file with warnings against it is not the same outcome as a clean
            # one, and neither is the same as no file at all.
            if not result.is_valid:
                record.outcome = "not_produced" if not should_save_output else "blocked"
            elif record.issue_codes:
                record.outcome = "prepared_with_findings"
            else:
                record.outcome = "prepared"

        except Exception:
            # Pipeline failure fallback
            record.status = ApiJobStatus.FAILED
            record.is_valid = False
            record.outcome = "not_produced"
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

    # ------------------------------------------------------------------
    # Requirement resolution and the platform-support gate (DEC-056)
    # ------------------------------------------------------------------

    def resolve_requirement(
        self, exam_id: str, requirement_id: str
    ) -> Tuple[ExamRule, ExamRequirement]:
        """Find one requirement of one examination, or raise.

        Deliberately does *not* apply the support gate. Reading a requirement
        is how the kit renders a guidance-only row, which it must; acting on
        one is what `require_served` governs.
        """
        entry = self.catalogue.get(exam_id)
        if entry is None:
            raise KeyError(exam_id)
        for requirement in entry.rule.requirements or []:
            if requirement.requirement_id == requirement_id:
                return entry.rule, requirement
        raise RequirementNotFoundError(requirement_id)

    @staticmethod
    def require_served(requirement: ExamRequirement) -> None:
        """Refuse to act on a requirement the platform does not prepare."""
        if requirement.platform_support not in _SERVED_SUPPORT:
            raise RequirementNotServedError(requirement)

    def prepare_requirement_sync(
        self,
        job_id: str,
        upload: bytes,
        filename: str,
        rule: ExamRule,
        requirement: ExamRequirement,
        exam_id: str,
        kit_id: Optional[str] = None,
    ) -> ProcessingJobRecord:
        """Prepare one non-photograph deliverable and persist it as a job.

        The photograph path is `process_job_sync` and is reached through the
        same endpoint; the split is made by `requirement_type` at the edge so
        the caller names an item of an examination rather than a pipeline
        (DEC-055).
        """
        self.check_upload_limit(len(upload))

        record = self.registry.create_job(job_id, self.settings.job_ttl_seconds)
        record.status = ApiJobStatus.PROCESSING
        record.kit_id = kit_id
        record.exam_id = exam_id
        record.requirement_id = requirement.requirement_id
        record.requirement_type = requirement.requirement_type.value
        record.platform_support = requirement.platform_support.value
        self.registry.update_job(record)

        self.store.write_file(job_id, "input.bin", upload)
        artifact_names = ["input.bin"]

        try:
            result = prepare_deliverable(
                upload,
                filename,
                requirement.requirement_type,
                file_spec=requirement.file_spec,
            )
        except Exception:
            # DEC-041 permits a hard failure only where no truthful output is
            # possible -- an undecodable upload is exactly that case.
            record.status = ApiJobStatus.FAILED
            record.is_valid = False
            record.outcome = "not_produced"
            record.issue_codes = ["DELIVERABLE_PREPARATION_ERROR"]
            record.findings = [
                "The uploaded file could not be prepared. It may not be an "
                "image this platform can decode."
            ]
            record.artifact_names = artifact_names
            self.registry.update_job(record)
            return record

        self.store.write_file(job_id, result.filename, result.content)
        artifact_names.append(result.filename)

        report = {
            "exam_id": exam_id,
            "requirement_id": requirement.requirement_id,
            "requirement_name": requirement.requirement_name,
            "requirement_type": requirement.requirement_type.value,
            "platform_support": requirement.platform_support.value,
            "output_filename": result.filename,
            "byte_size": result.byte_size,
            "width": result.width,
            "height": result.height,
            "is_blank": result.is_blank,
            "ceiling_was_unpublished": result.ceiling_was_unpublished,
            "findings": list(result.findings),
            "file_spec": (
                requirement.file_spec.model_dump(exclude_none=True)
                if requirement.file_spec is not None
                else None
            ),
        }
        self.store.write_file(
            job_id, "report.json", json.dumps(report, indent=2).encode("utf-8")
        )
        artifact_names.append("report.json")

        record.status = ApiJobStatus.SUCCEEDED
        record.is_valid = True
        record.outcome = self._outcome_for(result)
        record.output_filename = result.filename
        record.output_media_type = _media_type_for(result.filename)
        record.output_byte_size = result.byte_size
        record.output_width = result.width
        record.output_height = result.height
        record.is_blank = result.is_blank
        record.ceiling_was_unpublished = result.ceiling_was_unpublished
        record.findings = list(result.findings)
        record.artifact_names = artifact_names
        self.registry.update_job(record)
        return record

    # ------------------------------------------------------------------
    # Multi-page documents (DEC-053)
    # ------------------------------------------------------------------

    def plan_document_job(
        self,
        job_id: str,
        uploads: list[Tuple[bytes, str]],
        rule: ExamRule,
        requirement: ExamRequirement,
        exam_id: str,
        kit_id: Optional[str] = None,
    ) -> Tuple[ProcessingJobRecord, DocumentPlan]:
        """Persist a set of uploads and return the pages they contain.

        Two calls rather than one, because a single call offers no point at
        which the candidate arranges anything -- and DEC-053 built stable page
        identities precisely so they can. The uploads therefore have to outlive
        this request, which is why they are written into the job directory
        before the plan is returned.
        """
        total = sum(len(data) for data, _ in uploads)
        self.check_upload_limit(total)

        record = self.registry.create_job(job_id, self.settings.job_ttl_seconds)
        record.status = ApiJobStatus.PROCESSING
        record.kit_id = kit_id
        record.exam_id = exam_id
        record.requirement_id = requirement.requirement_id
        record.requirement_type = requirement.requirement_type.value
        record.platform_support = requirement.platform_support.value

        stored: list[str] = []
        for index, (data, name) in enumerate(uploads):
            # The candidate's own filename is never used on disk: it is
            # attacker-controlled and would defeat the store's traversal guard
            # by arriving as a legitimate-looking relative path.
            stored_name = f"source_{index}{Path(name).suffix.lower()[:8]}"
            self.store.write_file(job_id, stored_name, data)
            stored.append(stored_name)

        record.document_sources = stored
        record.artifact_names = list(stored)

        plan = plan_document([(data, name) for data, name in uploads])
        self.store.write_file(
            job_id,
            "plan.json",
            json.dumps(
                {
                    "pages": [
                        {
                            "source_index": page.source_index,
                            "page_index": page.page_index,
                            "origin": page.origin.value,
                        }
                        for page in plan.pages
                    ],
                    "unreadable": {str(k): v for k, v in plan.unreadable.items()},
                },
                indent=2,
            ).encode("utf-8"),
        )
        record.artifact_names.append("plan.json")
        record.status = ApiJobStatus.SUCCEEDED
        record.findings = list(plan.unreadable.values())
        self.registry.update_job(record)
        return record, plan

    def assemble_document_job(
        self,
        record: ProcessingJobRecord,
        order: Optional[list[PageRef]],
        requirement: ExamRequirement,
    ) -> Tuple[ProcessingJobRecord, DocumentResult]:
        """Assemble a previously planned document in the candidate's order."""
        sources: list[Tuple[bytes, str]] = [
            (self.store.read_file(record.job_id, name), name)
            for name in record.document_sources
        ]

        spec = requirement.file_spec
        size = spec.file_size if spec is not None else None
        ceiling = size.maximum_bytes if size is not None else None

        result = assemble_document(sources, order=order, maximum_bytes=ceiling)

        filename = generate_safe_filename(
            _published_filename(requirement) or requirement.requirement_type.value,
            config=FilenameGenerationConfig(extension="pdf"),
        )
        self.store.write_file(record.job_id, filename, result.content)

        record.output_filename = filename
        record.output_media_type = "application/pdf"
        record.output_byte_size = result.byte_size
        record.exceeds_ceiling = result.exceeds_ceiling
        record.ceiling_was_unpublished = ceiling is None
        record.findings = list(result.findings)
        record.is_valid = True
        record.status = ApiJobStatus.SUCCEEDED
        record.outcome = (
            "prepared_with_findings"
            if result.findings or result.exceeds_ceiling
            else "prepared"
        )
        if filename not in record.artifact_names:
            record.artifact_names.append(filename)
        self.registry.update_job(record)
        return record, result

    @staticmethod
    def _outcome_for(result: DeliverableResult) -> str:
        """Which of the three outcome states a prepared file landed in.

        DEC-056: a file produced with something worth reading about it is its
        own state, not a success with a footnote. A two-state contract files
        every finding under success, where nobody reads it.
        """
        if result.findings or result.is_blank:
            return "prepared_with_findings"
        return "prepared"

    # ------------------------------------------------------------------
    # The package (DEC-055 step 4, DEC-056, DEC-057)
    # ------------------------------------------------------------------

    def build_kit_package(self, kit_id: str) -> Tuple[bytes, dict[str, Any]]:
        """Bundle a kit's prepared files with a checklist and a report.

        Returns the ZIP and the checklist, so a caller can render the checklist
        without unpacking the archive.
        """
        records = self.registry.jobs_in_kit(kit_id)
        if not records:
            raise KeyError(kit_id)

        exam_ids = {r.exam_id for r in records if r.exam_id}
        entry = None
        if len(exam_ids) == 1:
            entry = self.catalogue.get(next(iter(exam_ids)))

        items: list[dict[str, Any]] = []
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
            used: dict[str, int] = {}
            for record in records:
                item: dict[str, Any] = {
                    "requirement_id": record.requirement_id,
                    "requirement_type": record.requirement_type,
                    "platform_support": record.platform_support,
                    "outcome": record.outcome,
                    "findings": list(record.findings),
                    "byte_size": record.output_byte_size,
                    "included": False,
                }
                # DEC-056: nothing carrying a non-served support state may be
                # counted as an output.  Such a job should never exist -- the
                # gate refuses it at the edge -- so this is a second reading of
                # the same rule at the point where a file would be handed over.
                servable = record.platform_support in {
                    PlatformSupport.SUPPORTED.value,
                    PlatformSupport.PARTIALLY_SUPPORTED.value,
                    None,
                }
                if record.output_filename and servable:
                    try:
                        content = self.store.read_file(
                            record.job_id, record.output_filename
                        )
                    except (FileNotFoundError, ValueError):
                        item["findings"].append(
                            "The prepared file is no longer on disk; it may "
                            "have expired."
                        )
                    else:
                        name = record.output_filename
                        # Two requirements can publish the same exact filename.
                        # Silently overwriting one with the other inside the
                        # archive would hand the candidate a package missing a
                        # deliverable it claims to contain.
                        if name in used:
                            used[name] += 1
                            stem = Path(name)
                            name = f"{stem.stem}_{used[name]}{stem.suffix}"
                        else:
                            used[name] = 1
                        bundle.writestr(name, content)
                        item["included"] = True
                        item["filename"] = name
                items.append(item)

            checklist = self._build_checklist(kit_id, entry, items)
            bundle.writestr(
                "checklist.json", json.dumps(checklist, indent=2).encode("utf-8")
            )
            bundle.writestr(
                "validation-report.json",
                json.dumps(
                    self._build_validation_report(entry, items), indent=2
                ).encode("utf-8"),
            )

        return archive.getvalue(), checklist

    @staticmethod
    def _build_checklist(
        kit_id: str,
        entry: Optional[Any],
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """What the examination asks for, and what is in the package.

        Every requirement appears, including the ones the platform will never
        produce. An omitted requirement reads as "this examination does not ask
        for it", which for a live-capture item is false and is exactly the
        confusion that makes a candidate think a step was completed for them.
        """
        prepared = {item["requirement_id"] for item in items if item["included"]}
        requirements: list[dict[str, Any]] = []
        if entry is not None:
            for requirement in entry.rule.requirements or []:
                served = requirement.platform_support in _SERVED_SUPPORT
                requirements.append(
                    {
                        "requirement_id": requirement.requirement_id,
                        "requirement_name": requirement.requirement_name,
                        "requirement_type": requirement.requirement_type.value,
                        "requirement_status": requirement.requirement_status.value,
                        "submission_method": requirement.submission_method.value,
                        "platform_support": requirement.platform_support.value,
                        "prepared_by_platform": (
                            requirement.requirement_id in prepared
                        ),
                        "completed_by_candidate_elsewhere": not served,
                        "content_instructions": requirement.content_instructions,
                        "applicability": requirement.applicability,
                    }
                )

        return {
            "kit_id": kit_id,
            "exam_id": entry.exam_id if entry is not None else None,
            "exam_name": entry.rule.exam.exam_name if entry is not None else None,
            "files_included": sum(1 for item in items if item["included"]),
            "requirements": requirements,
            "items": items,
        }

    @staticmethod
    def _build_validation_report(
        entry: Optional[Any], items: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """The report somebody opens after a portal rejects a file.

        DEC-057: every interim value is named here explicitly. In the
        application the same fact is a quiet marker, because a candidate cannot
        act on it -- but this is read at the moment a file has been rejected,
        and "this ceiling was our estimate, not a published figure" is then the
        most useful sentence in the document.
        """
        estimates: list[dict[str, Any]] = []
        if entry is not None:
            for path, provenance in entry.rule.provenance.items():
                if provenance.type.value != "interim_default":
                    continue
                estimates.append(
                    {
                        "field": path,
                        "reasoning": provenance.reasoning,
                        "confidence": provenance.confidence,
                        "note": (
                            "This value is a platform estimate, not a figure "
                            "published by the examination body. If the portal "
                            "rejected this file, check the current "
                            "notification for the published specification."
                        ),
                    }
                )

        return {
            "exam_id": entry.exam_id if entry is not None else None,
            "exam_name": entry.rule.exam.exam_name if entry is not None else None,
            "rule_version": entry.rule.rule_version if entry is not None else None,
            "rule_status": entry.rule.status.value if entry is not None else None,
            "platform_estimates": estimates,
            "estimate_count": len(estimates),
            "findings": [
                {
                    "requirement_id": item["requirement_id"],
                    "outcome": item["outcome"],
                    "findings": item["findings"],
                }
                for item in items
                if item["findings"]
            ],
        }

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
