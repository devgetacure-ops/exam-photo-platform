"""API Orchestration Service coordinating job creation, processing, and storage."""

import io
import json
import os
import secrets
import threading
import time
import zipfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from exam_photo.api.contracts import ApiJobStatus, JobEntitlement
from exam_photo.api.delivery import (
    Attachment,
    EmailRejectedError,
    EmailSender,
    check_attachment_budget,
    compose,
    mask_address,
    sender_for,
    validate_address,
)
from exam_photo.api.jobs import (
    EmailAttempt,
    JobRegistry,
    ProcessingJobRecord,
    parse_manifest_timestamp,
)
from exam_photo.api.orders import OrderRegistry
from exam_photo.api.payments import ReleaseInstruction
from exam_photo.api.progress import ProgressRegistry
from exam_photo.api.protection import UsageRegistry
from exam_photo.api.razorpay_orders import (
    SIMULATED_ORDER_PREFIX,
    OrderGateway,
    gateway_for,
)
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore
from exam_photo.models.exam_rule import (
    ExamRequirement,
    ExamRule,
    PlatformSupport,
)
from exam_photo.orchestration.deliverable_pipeline import (
    DeliverableResult,
    PasswordProtectedPdfError,
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
from exam_photo.preview import (
    PREVIEW_FILENAME,
    PreviewUnavailableError,
    render_watermarked_preview,
)


class UploadLimitExceededError(ValueError):
    """Exception raised when an upload exceeds the allowed byte size limit."""

    pass


class ServiceBusyError(RuntimeError):
    """Every preparation slot is occupied (DEC-064).

    Distinct from a failure: nothing is wrong with the request, and retrying
    it shortly will work. The API turns this into 429 with `Retry-After`.
    """


class RetentionCeilingReachedError(RuntimeError):
    """This job cannot be kept any longer (DEC-067).

    Distinct from "not found": the file is still there and still
    downloadable right now. What has run out is room to postpone its
    deletion, and the caller is told so rather than being given a silent
    no-op that looks like a successful extension.
    """


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


def _alternate_filename(filename: str) -> str:
    """The stored name of the other lighting variant (DEC-076).

    Never served to a candidate: the delivered file always carries the
    examination's own required name, and this is only how the two are told
    apart on disk while both exist.
    """
    stem, _, extension = filename.rpartition(".")
    if not stem:
        return f"{filename}__alt"
    return f"{stem}__alt.{extension}"


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
        #: Orders outlive the files they paid for (DEC-071).
        self.orders = OrderRegistry(settings.artifact_root)
        #: Per-kit counters, surviving retention (DEC-073).
        self.usage = UsageRegistry(settings.artifact_root)
        #: Ephemeral per-preparation progress (DEC-075).
        self.progress = ProgressRegistry(settings.artifact_root)
        #: Overwritten wholesale in tests, like `store` and `registry`, so no
        #: test ever reaches api.razorpay.com (DEC-070).
        self._order_gateway: Optional[OrderGateway] = None
        self._email_sender: Optional[EmailSender] = None
        self.repo_root = find_repo_root()

        # Load existing manifests on startup
        self.registry.scan_manifests()

        # The matting pipeline is expensive to build -- an onnxruntime session
        # over a 940 MB graph -- and nothing about it varies per request, so it
        # is built on first use and reused (DEC-062).
        self._pipeline: Optional[RuleOrchestratedPipeline] = None
        self._pipeline_lock = threading.Lock()

        # Boot warmup and the artifact sweeper (DEC-064).  Four states, and
        # the distinctions matter to a load balancer: "not_started" (the
        # lifespan hook has not run, so this process cannot yet claim
        # anything), "warming", "ready", "failed", and "skipped" for a host
        # that deliberately turned warmup off.  Conflating the last two with
        # the first would make `warmup_on_boot=false` a permanent 503 and the
        # flag unusable behind a load balancer.
        self._warmup_state = "not_started"
        self._warmup_error: Optional[str] = None
        self._warmup_started_at: Optional[float] = None
        self._warmup_finished_at: Optional[float] = None
        self._sweeper_thread: Optional[threading.Thread] = None
        self._sweeper_stop = threading.Event()

        # The only thing standing between a public port and 10 s of CPU per
        # request.  A bounded semaphore rather than a counter so that an
        # unbalanced release raises instead of quietly widening the limit.
        self._preparation_slots = threading.BoundedSemaphore(
            settings.max_concurrent_preparations
        )

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

    def _get_pipeline(self) -> RuleOrchestratedPipeline:
        """The pipeline, built once for the life of the service.

        It used to be constructed inside `process_job_sync`, so every request
        built a fresh one -- and with it a fresh onnxruntime `InferenceSession`
        over a 940 MB BiRefNet graph. The model was being loaded from disk for
        every photograph.

        Measured on one warm request before the change, the two matting stages
        cost 13.9 s and 14.1 s, while the same `segment_subject` call measured
        5.5 s standalone. The gap was session construction, paid twice per
        photograph and attributed to inference by every timing we had -- which
        is why the engine looked far slower in the service than on the bench.

        Every constructor argument derives from settings, which do not change
        while the process runs, so there is nothing per-request to vary. The
        segmenters carry their own `RLock`, so sharing one instance across the
        threadpool FastAPI runs sync endpoints on is what they were built for.
        """
        with self._pipeline_lock:
            if self._pipeline is None:
                face_model, face_sha = self._resolve_face_model()
                segmenter_model, segmenter_sha = self._resolve_segmenter_model()
                backend, birefnet_dir, birefnet_sha = self._resolve_matting_backend()
                self._pipeline = RuleOrchestratedPipeline(
                    face_model_path=face_model,
                    segmenter_model_path=segmenter_model,
                    face_expected_sha256=face_sha,
                    segmenter_expected_sha256=segmenter_sha,
                    matting_backend=backend,
                    birefnet_model_dir=birefnet_dir,
                    birefnet_expected_sha256=birefnet_sha,
                )
            return self._pipeline

    def _resolve_matting_backend(self) -> Tuple[str, Optional[Path], str]:
        """Resolve the subject segmentation backend for this service.

        Returns ``(backend, birefnet_model_dir, birefnet_sha256)``. ``"auto"``
        (the default) prefers the ONNX backend (faster-matting Step 1: same
        weights and maths as the PyTorch backend, roughly 2x faster on CPU,
        and needs only the lightweight ``matting-onnx`` extra rather than
        torch), then the PyTorch backend.

        **``"auto"`` never resolves to MediaPipe** (DEC-060). It used to, so
        that a machine without the model assets still served requests instead
        of failing every job. That reasoning is wrong for a paid product: the
        MediaPipe mask is 256px and on a real photograph it leaves visibly
        blocky edges with pieces missing from the ear and hair. Serving that
        silently means charging for output the platform would not stand
        behind, and the candidate cannot tell which backend produced their
        file. A job that fails loudly can be retried; a bad file that was paid
        for and submitted cannot.

        MediaPipe stays selectable explicitly, for diagnostics and for the
        tests that assert against its coarse mask.
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

        # "auto": prefer ONNX, then PyTorch. Never MediaPipe -- see above.
        onnx_resolved = self._resolve_birefnet_onnx()
        if onnx_resolved is not None:
            return "birefnet_onnx", onnx_resolved[0], onnx_resolved[1]
        torch_resolved = self._resolve_birefnet_torch()
        if torch_resolved is not None:
            return "birefnet", torch_resolved[0], torch_resolved[1]
        raise RuntimeError(
            "No BiRefNet matting backend is available, and the service will "
            "not silently fall back to MediaPipe for a paid output (DEC-060). "
            "Fix it with one of:\n"
            "  python scripts/download_birefnet.py --yes        "
            "# then the PyTorch backend works\n"
            "  python scripts/export_birefnet_onnx.py           "
            "# ~2x faster; needs the `matting` extra installed\n"
            '  pip install -e ".[dev,face,matting]"             '
            "# if the export fails on a missing onnx dependency\n"
            "To run the coarse backend deliberately, for diagnostics only, "
            "set EXAM_PHOTO_MATTING_BACKEND=mediapipe."
        )

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

    # ------------------------------------------------------------------
    # What protects the CPU (DEC-064)
    # ------------------------------------------------------------------

    @contextmanager
    def preparation_slot(self) -> Iterator[None]:
        """Hold one of the limited preparation slots, or refuse immediately.

        The pipeline is roughly 10 s of CPU per photograph, so an unbounded
        public endpoint is an invitation to exhaust the box. This caps how many
        run at once and refuses the rest with a `Retry-After`, which is the
        honest answer -- a request queued behind a hundred others would be cut
        by nginx or Cloudflare long before it ran anyway.

        There is deliberately **no per-IP limit**. Carrier-grade NAT on Indian
        mobile networks puts thousands of candidates behind a single address:
        a per-IP quota either punishes everyone sharing a carrier or is set so
        high it protects nothing. A global cap protects the resource that is
        actually scarce without ever penalising a candidate for their network.
        """
        if not self._preparation_slots.acquire(blocking=False):
            raise ServiceBusyError(
                "The service is preparing as many files as it can at once."
            )
        try:
            yield
        finally:
            self._preparation_slots.release()

    # ------------------------------------------------------------------
    # Boot warmup, readiness and the artifact sweeper (DEC-064)
    # ------------------------------------------------------------------

    def warmup(self) -> None:
        """Build the pipeline and run one real inference.

        Called from a background thread at boot. Records its own outcome so
        `GET /ready` can report it: a host without the BiRefNet weights fails
        here, loudly and at deployment time, which is where DEC-060 wants that
        failure rather than on a candidate's first request.
        """
        self._warmup_started_at = time.monotonic()
        try:
            self._get_pipeline().warmup()
        except Exception as error:  # noqa: BLE001 - reported, never raised
            self._warmup_error = f"{type(error).__name__}: {error}"
            self._warmup_state = "failed"
        else:
            self._warmup_error = None
            self._warmup_state = "ready"
        finally:
            self._warmup_finished_at = time.monotonic()

    def readiness(self) -> Dict[str, Any]:
        """Whether this process can serve a photograph, and since when.

        Deliberately distinct from `/health`. A process is *live* the moment
        it binds a port and *ready* only once the model has run once; a load
        balancer that cannot tell those apart routes the first candidate of
        every deploy into a 100-150 s wait that nginx or Cloudflare will cut
        before it finishes.
        """
        elapsed: Optional[float] = None
        if self._warmup_started_at is not None:
            end = self._warmup_finished_at or time.monotonic()
            elapsed = round(end - self._warmup_started_at, 1)

        # A host that turned warmup off is as ready as it is going to get;
        # only a process that has not run the hook, is still warming, or
        # failed, should be kept out of the rotation.
        ready = self._warmup_state in ("ready", "skipped")

        return {
            "status": "ready" if ready else self._warmup_state,
            "warmup": self._warmup_state,
            "warmup_seconds": elapsed,
            "error": self._warmup_error,
            "matting_backend": self.settings.matting_backend,
            "purchase_gate": (
                "enabled" if self.settings.purchase_gate_enabled else "disabled"
            ),
            # Surfaced because an unauthenticated operator surface is a
            # deployment mistake that is otherwise completely silent.
            "operator_surface": (
                "authenticated" if self.settings.operator_token else "unauthenticated"
            ),
            # DEC-069. With the gate on and no webhook secret, every prepared
            # file answers 402 and nothing can ever release one -- a deployment
            # that looks healthy and cannot take money. This is the one place
            # that state is visible.
            "payments": (
                "simulated"
                if self.settings.payment_simulator_enabled
                else "configured"
                if self.settings.razorpay_webhook_secret
                else "not_configured"
            ),
        }

    def start_background_workers(self) -> None:
        """Start the boot warmup and the expired-artifact sweeper."""
        if self._warmup_state == "not_started":
            if self.settings.warmup_on_boot:
                self._warmup_state = "warming"
                threading.Thread(
                    target=self.warmup, name="exam-photo-warmup", daemon=True
                ).start()
            else:
                self._warmup_state = "skipped"

        if self._sweeper_thread is None:
            self._sweeper_stop.clear()
            self._sweeper_thread = threading.Thread(
                target=self._sweep_forever, name="exam-photo-sweeper", daemon=True
            )
            self._sweeper_thread.start()

    def stop_background_workers(self) -> None:
        """Ask the sweeper to finish. Warmup is a daemon and is left to exit."""
        self._sweeper_stop.set()
        thread, self._sweeper_thread = self._sweeper_thread, None
        if thread is not None:
            thread.join(timeout=5.0)

    def _sweep_forever(self) -> None:
        """Delete expired artifacts on a timer, for the life of the process.

        `expires_at` was written onto every manifest and acted on by nothing:
        `POST /v1/cleanup-expired` existed and no caller invoked it, so a
        candidate's face photograph stayed on disk for the life of the host.
        A retention policy nothing enforces is a retention claim.

        A failed sweep must never stop the loop -- one unreadable directory
        would otherwise silently end retention for the whole process.
        """
        interval = self.settings.cleanup_interval_seconds
        while not self._sweeper_stop.wait(interval):
            try:
                self.cleanup_expired_jobs()
            except Exception:  # noqa: BLE001 - one bad sweep is not the last
                continue

    # ------------------------------------------------------------------
    # The purchase gate and its preview (DEC-063)
    # ------------------------------------------------------------------

    def write_preview(
        self, record: ProcessingJobRecord, output_bytes: bytes
    ) -> ProcessingJobRecord:
        """Render and store the watermarked preview of a finished file.

        Never fails the job it is previewing. A preparation that succeeded has
        produced the candidate's file, and losing the preview of it is a lesser
        outcome than losing the file; where no preview can be made the fields
        stay unset and the caller reports the absence honestly, which is what
        stops a client from showing the clean output believing it is protected.
        """
        try:
            preview = render_watermarked_preview(
                output_bytes, media_type=record.output_media_type
            )
        except PreviewUnavailableError:
            # The ordinary case is a PDF: rendering a page needs a rasteriser
            # this repository deliberately does not carry (DEC-063).
            record.preview_filename = None
            record.preview_watermarked = False
            record.preview_width = None
            record.preview_height = None
            return record

        try:
            self.store.write_file(record.job_id, PREVIEW_FILENAME, preview.content)
        except OSError:
            # A disk that cannot take the preview has still taken the file the
            # candidate paid to have made.  Losing the preview costs a purchase
            # gate on one job; letting this propagate would land the job in the
            # pipeline-failure handler and lose the file itself.
            record.preview_filename = None
            record.preview_watermarked = False
            record.preview_width = None
            record.preview_height = None
            return record

        if PREVIEW_FILENAME not in record.artifact_names:
            record.artifact_names.append(PREVIEW_FILENAME)
        record.preview_filename = PREVIEW_FILENAME
        record.preview_watermarked = True
        record.preview_width = preview.width
        record.preview_height = preview.height
        return record

    def output_is_released(self, record: ProcessingJobRecord) -> bool:
        """Whether this job's clean output may be served.

        With the gate switched off every job is released, which is the state
        engine quality work needs: judging a matte on a watermarked
        half-resolution copy is judging it on the wrong thing.
        """
        if not self.settings.purchase_gate_enabled:
            return True
        return record.entitlement == JobEntitlement.RELEASED

    def release_job(
        self, job_id: str, payment: Optional[ReleaseInstruction] = None
    ) -> ProcessingJobRecord:
        """Release one job's clean output, once it has been paid for.

        This is the seam a payment confirmation calls, and it is deliberately
        reachable only from inside the process. There is no HTTP route that
        releases a job: an unauthenticated one would not be a weaker gate than
        none but a worse one, because it reads as protection to anyone
        scanning the route list. Razorpay's verified webhook is what calls it
        (DEC-069) -- signature checked against the shared secret before the
        payload is even parsed.

        `payment` is the reconciliation trail: a release with no payment
        reference is what an audit needs to be able to notice.
        """
        record = self.registry.get_job(job_id)
        if record is None or record.status == ApiJobStatus.DELETED:
            raise KeyError(job_id)
        if self.expire_job_if_due(record):
            # DEC-066: the artifacts are gone. Marking an erased job released
            # would leave a manifest claiming an entitlement to nothing.
            raise KeyError(job_id)
        record.entitlement = JobEntitlement.RELEASED
        if payment is not None:
            record.payment_reference = payment.payment_id or payment.order_id
            record.payment_amount = payment.amount
            record.payment_currency = payment.currency
        record.released_at = datetime.now(timezone.utc).isoformat()
        self.registry.update_job(record)
        return record

    def apply_release_instruction(
        self, instruction: ReleaseInstruction
    ) -> Dict[str, Any]:
        """Release everything a verified webhook names (DEC-069).

        Idempotent by construction: releasing an already-released job sets the
        same entitlement again. That matters because Razorpay retries any
        webhook it was not told was received, so this method is guaranteed to
        be called more than once for some payments.

        A job the instruction names but that cannot be found -- expired,
        deleted, never existed -- is reported as unknown rather than raised
        on. One bad identifier in a bundle must not stop the rest of the
        candidate's files being released, and the whole point of a payment
        webhook is that the money has already moved.
        """
        released: list[str] = []
        unknown: list[str] = []

        # DEC-071. An order we created names the exact jobs it was priced
        # from, so it -- not the kit -- decides what this payment releases. A
        # file prepared after the order is simply not in it, which is what
        # makes the quote and the release the same set by construction rather
        # than by timing.
        order = self.orders.get(instruction.order_id or "")
        if order is not None:
            self.orders.mark_paid(order.order_id, instruction.payment_id)
            self.usage.record_purchase(order.kit_id)
            for job_id in order.job_ids:
                try:
                    self.release_job(job_id, payment=instruction)
                except KeyError:
                    unknown.append(job_id)
                else:
                    released.append(job_id)
            return {
                "released": list(dict.fromkeys(released)),
                "unknown": list(dict.fromkeys(unknown)),
                "order_id": order.order_id,
            }

        for job_id in instruction.job_ids:
            try:
                self.release_job(job_id, payment=instruction)
            except KeyError:
                unknown.append(job_id)
            else:
                released.append(job_id)

        for kit_id in instruction.kit_ids:
            records = self.registry.jobs_in_kit(kit_id)
            if not records:
                unknown.append(kit_id)
                continue
            for record in records:
                try:
                    self.release_job(record.job_id, payment=instruction)
                except KeyError:
                    unknown.append(record.job_id)
                else:
                    released.append(record.job_id)

        return {
            "released": list(dict.fromkeys(released)),
            "unknown": list(dict.fromkeys(unknown)),
        }

    def simulate_payment(self, order_id: str) -> Dict[str, Any]:
        """Settle a simulated order as a verified payment would (DEC-089).

        Only for a host running the simulator with no Razorpay credentials,
        and only for an order the simulator created. It builds the same
        instruction a verified `order.paid` webhook carries and releases
        through `apply_release_instruction`, so what a tester sees after
        paying is what a candidate will see.
        """
        settings = self.settings
        if (
            not settings.payment_simulator_enabled
            or settings.razorpay_key_id
            or settings.razorpay_key_secret
        ):
            raise PermissionError("the payment simulator is not enabled")
        if not order_id.startswith(SIMULATED_ORDER_PREFIX):
            raise KeyError(order_id)
        order = self.orders.get(order_id)
        if order is None:
            raise KeyError(order_id)
        instruction = ReleaseInstruction(
            event="order.paid",
            payment_id=f"pay_sim{secrets.token_hex(7)}",
            order_id=order.order_id,
            amount=order.amount_paise,
            currency=order.currency,
        )
        return self.apply_release_instruction(instruction)

    @property
    def order_gateway(self) -> OrderGateway:
        """The gateway this host's credentials entitle it to (DEC-070).

        Built on first use from the current settings, so a test that swaps
        `settings` gets a gateway matching them, and a host with no keys gets
        one that refuses rather than one that pretends.
        """
        if self._order_gateway is None:
            self._order_gateway = gateway_for(
                self.settings.razorpay_key_id,
                self.settings.razorpay_key_secret,
                simulator=self.settings.payment_simulator_enabled,
            )
        return self._order_gateway

    @order_gateway.setter
    def order_gateway(self, gateway: OrderGateway) -> None:
        self._order_gateway = gateway

    def expire_job_if_due(self, record: ProcessingJobRecord) -> bool:
        """Erase a job whose retention deadline has passed, on the way to it.

        The sweeper (DEC-064) runs on a timer, so between an artifact
        expiring and the next sweep there was a window -- up to
        `cleanup_interval_seconds`, five minutes by default -- in which an
        expired file was still served in full. A deletion promise measured
        in minutes cannot carry a five-minute hole of that kind, so expiry
        is enforced on the read path as well and the timer becomes the
        backstop for jobs nobody touches again (DEC-066).

        Marking the record `DELETED` rather than reporting expiry separately
        is deliberate: every route already refuses a deleted job, so this
        needs no new status on the wire and no change to the shared contract.
        """
        if record.status == ApiJobStatus.DELETED or not record.is_expired():
            return False
        try:
            self.store.delete_job_directory(record.job_id)
        except OSError:
            # The sweeper in this or another worker may have removed the
            # directory already (DEC-064). The record is still marked below:
            # the caller must be refused either way.
            pass
        self.registry.delete_job(record.job_id)
        return True

    def extend_job(self, job_id: str) -> ProcessingJobRecord:
        """Give a live job one more retention window, up to its ceiling.

        This exists because DEC-066's thirty minutes is short enough to catch
        a candidate who is still working, and the alternative -- holding
        every file for longer in case a few need it -- makes everyone pay for
        those few. An extension is asked for, by the one person whose file it
        is, and it is bounded twice: a new window is measured from now rather
        than added to what is left, and no extension may pass
        `job_max_lifetime_seconds` measured from creation, so repeating the
        request cannot walk a file forward indefinitely.

        **An expired job cannot be extended.** Its artifacts are gone by the
        time this is reached, so there is nothing to keep, and saying so as a
        404 is the truth. That is precisely why the interface must warn
        before the deadline rather than offer this after it (DEC-067).
        """
        record = self.registry.get_job(job_id)
        if record is None or record.status == ApiJobStatus.DELETED:
            raise KeyError(job_id)
        if self.expire_job_if_due(record):
            raise KeyError(job_id)

        ceiling = record.lifetime_ceiling(self.settings.job_max_lifetime_seconds)
        if ceiling is None:
            raise RetentionCeilingReachedError(job_id)

        now = datetime.now(timezone.utc)
        proposed = min(now + timedelta(seconds=self.settings.job_ttl_seconds), ceiling)
        current = parse_manifest_timestamp(record.expires_at)
        if current is not None and proposed <= current:
            # Already at the ceiling, or the request bought nothing. Refusing
            # is better than returning success and an unchanged deadline.
            raise RetentionCeilingReachedError(job_id)

        record.expires_at = proposed.isoformat()
        self.registry.update_job(record)
        return record

    def job_is_extendable(self, record: ProcessingJobRecord) -> bool:
        """Whether `extend_job` would currently buy this job any more time."""
        ceiling = record.lifetime_ceiling(self.settings.job_max_lifetime_seconds)
        if ceiling is None or record.is_expired():
            return False
        current = parse_manifest_timestamp(record.expires_at)
        proposed = min(
            datetime.now(timezone.utc)
            + timedelta(seconds=self.settings.job_ttl_seconds),
            ceiling,
        )
        return current is None or proposed > current

    @property
    def email_sender(self) -> EmailSender:
        """The sender this host's SMTP configuration entitles it to (DEC-072)."""
        if self._email_sender is None:
            self._email_sender = sender_for(
                self.settings.smtp_host,
                self.settings.smtp_port,
                self.settings.smtp_username,
                self.settings.smtp_password,
                self.settings.smtp_from_address,
                self.settings.smtp_use_tls,
            )
        return self._email_sender

    @email_sender.setter
    def email_sender(self, sender: EmailSender) -> None:
        self._email_sender = sender

    def set_enhancement(
        self, record: ProcessingJobRecord, enabled: bool
    ) -> ProcessingJobRecord:
        """Switch between the two lighting variants, instantly (DEC-076).

        Both were composed and compressed during the one preparation, so this
        is a swap of two small files and a re-rendered preview -- a few tens of
        milliseconds against the ten seconds a re-preparation would cost.

        **The contents are exchanged, not the names.** The delivered file has
        to keep the examination's own required filename (`generate_safe_
        filename`), and several portals reject an upload on its name alone, so
        pointing the record at `..__alt.jpg` would have produced a file that
        was correct in every respect except the one that gets it thrown out.

        Raises `LookupError` when there is nothing to switch to: the correction
        changed nothing, or the alternate would not fit the size ceiling. The
        interface should not offer the control then, and being told is better
        than a silent no-op.
        """
        if record.enhancement_enabled == enabled:
            return record
        alternate = record.alternate_output_filename
        served = record.output_filename
        if not alternate or not served:
            raise LookupError("this job has no alternate lighting variant")

        try:
            incoming = self.store.read_file(record.job_id, alternate)
            outgoing = self.store.read_file(record.job_id, served)
        except (FileNotFoundError, ValueError) as err:
            raise LookupError("the alternate variant is no longer on disk") from err

        # Written before the record changes, so a failure here leaves the job
        # exactly as it was rather than naming a state that is not on disk.
        self.store.write_file(record.job_id, served, incoming)
        self.store.write_file(record.job_id, alternate, outgoing)

        record.enhancement_enabled = enabled
        record.output_byte_size = len(incoming)
        self.write_preview(record, incoming)
        self.registry.update_job(record)
        return record

    def record_download(self, record: ProcessingJobRecord) -> None:
        """Note that the candidate actually took the file (DEC-072).

        Called from the download route, so this counts deliveries rather than
        intentions. `mark_delivered` on the order is what a refund claim is
        decided against, and it keeps only the first.
        """
        record.download_count += 1
        if record.first_downloaded_at is None:
            record.first_downloaded_at = datetime.now(timezone.utc).isoformat()
        self.registry.update_job(record)
        self.orders.mark_delivered(record.job_id, "download")

    def email_jobs(
        self, records: List[ProcessingJobRecord], address: str
    ) -> Dict[str, Any]:
        """Email the released files in `records` to `address` (DEC-072).

        Only released files are attached. Emailing a preview would put a
        watermarked half-resolution copy in a candidate's inbox looking like
        the thing they bought; emailing a clean file before payment would be
        the purchase gate with a hole in it.

        The address is validated, used, and **not stored**. What is recorded
        against each job is a masked form and whether the send succeeded.
        """
        address = validate_address(address)
        masked = mask_address(address)

        deliverable = [
            record
            for record in records
            if record.output_filename
            and self.output_is_released(record)
            and not record.is_expired()
            and record.status != ApiJobStatus.DELETED
        ]
        if not deliverable:
            raise EmailRejectedError("there is nothing released to send")

        attachments = []
        for record in deliverable:
            try:
                content = self.store.read_file(
                    record.job_id, str(record.output_filename)
                )
            except (FileNotFoundError, ValueError):
                continue
            attachments.append(
                Attachment(
                    filename=str(record.output_filename),
                    content=content,
                    media_type=record.output_media_type or "image/jpeg",
                )
            )
        if not attachments:
            raise EmailRejectedError("the prepared files are no longer on disk")
        check_attachment_budget(attachments)

        exam_names = list(dict.fromkeys(r.exam_id for r in deliverable if r.exam_id))
        subject, body = compose(
            exam_names,
            [item.filename for item in attachments],
            deliverable[0].expires_at,
        )

        sent_at = datetime.now(timezone.utc).isoformat()
        try:
            self.email_sender.send(address, subject, body, attachments)
        except EmailRejectedError as err:
            for record in deliverable:
                record.email_attempts.append(
                    EmailAttempt(
                        at=sent_at,
                        masked_address=masked,
                        succeeded=False,
                        error=str(err)[:200],
                    )
                )
                self.registry.update_job(record)
            raise

        for record in deliverable:
            record.email_attempts.append(
                EmailAttempt(at=sent_at, masked_address=masked, succeeded=True)
            )
            self.registry.update_job(record)
            self.orders.mark_delivered(record.job_id, "email")

        return {
            "sent": True,
            "masked_address": masked,
            "job_ids": [record.job_id for record in deliverable],
            "filenames": [item.filename for item in attachments],
        }

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
        enhancement_enabled: bool = True,
        progress_token: Optional[str] = None,
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
        # DEC-074. Written here, with the other inputs, rather than with the
        # outcomes below: the candidate's choice is a fact about the request
        # and must survive a pipeline failure. Recorded on the success path
        # only, a failed job would report the default and misrepresent what
        # they asked for.
        record.enhancement_enabled = enhancement_enabled
        if requirement is not None:
            record.requirement_id = requirement.requirement_id
            record.requirement_type = requirement.requirement_type.value
            record.platform_support = requirement.platform_support.value
        else:
            # `/v1/process` names no examination: it serves the local-only
            # rule-admin console and never reaches a candidate, so its output
            # is not behind the purchase gate (DEC-063).
            record.entitlement = JobEntitlement.RELEASED
        self.registry.update_job(record)

        self.store.write_file(job_id, "input.jpg", image_bytes)
        self.store.write_file(
            job_id,
            "rule.json",
            json.dumps(rule_dict, indent=2).encode("utf-8"),
        )

        artifact_names = ["input.jpg", "rule.json"]

        try:
            # 2. The pipeline, built once and reused (DEC-062).
            pipeline = self._get_pipeline()

            job_dir = self.store.get_file_path(job_id, ".")

            config = RulePipelineConfig(
                save_diagnostic_artifacts=save_diagnostic_artifacts,
                allow_invalid_output=allow_invalid_output,
                output_dir=job_dir,
                quality_mode=quality_mode,
                enhancement_enabled=enhancement_enabled,
                progress_callback=(
                    (lambda stage: self.progress.advance(progress_token, stage))
                    if progress_token
                    else None
                ),
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

            # DEC-076. The other lighting variant, so the candidate can switch
            # instantly instead of paying ten seconds to see the difference.
            if (
                should_save_output
                and result.output_filename
                and result.alternate_encoded_bytes
            ):
                alternate_name = _alternate_filename(result.output_filename)
                self.store.write_file(
                    job_id, alternate_name, result.alternate_encoded_bytes
                )
                artifact_names.append(alternate_name)
                record.alternate_output_filename = alternate_name

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
            # DEC-074: what the planner actually did, which is an outcome and
            # so belongs here. Empty means the photograph needed nothing.
            record.enhancements_applied = list(result.enhancements_applied)
            record.diagnostic_available = save_diagnostic_artifacts
            record.output_media_type = (
                _media_type_for(record.output_filename)
                if record.output_filename
                else None
            )
            record.output_byte_size = (
                len(result.encoded_bytes) if result.encoded_bytes else None
            )
            # The pipeline knows the finished pixel size; before this it was
            # reported only for the deliverable path, leaving a photograph's
            # dimensions null in a response that has fields for them.
            record.output_width = result.final_width
            record.output_height = result.final_height
            # DEC-056's third state, on the photograph path too: a compliant
            # file with warnings against it is not the same outcome as a clean
            # one, and neither is the same as no file at all.
            if not result.is_valid:
                record.outcome = "not_produced" if not should_save_output else "blocked"
            elif record.issue_codes:
                record.outcome = "prepared_with_findings"
            else:
                record.outcome = "prepared"

            # The watermarked preview (DEC-063). Built from the encoded bytes
            # that were written, so it is a preview of the delivered file and
            # not of an intermediate.
            if should_save_output and result.encoded_bytes:
                record.artifact_names = artifact_names
                self.write_preview(record, result.encoded_bytes)
                artifact_names = record.artifact_names

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
        except PasswordProtectedPdfError:
            # Its own code, so the candidate is told what to upload instead
            # rather than that the file is undecodable. No output is written,
            # so the quote classes the job `nothing_prepared` and never prices
            # it (DEC-052 amendment).
            record.status = ApiJobStatus.FAILED
            record.is_valid = False
            record.outcome = "not_produced"
            record.issue_codes = ["PDF_PASSWORD_PROTECTED"]
            record.findings = [
                "The PDF is password-protected, so it can't be opened. Upload a "
                "copy of the PDF without a password."
            ]
            record.artifact_names = artifact_names
            self.registry.update_job(record)
            return record
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
        # The watermarked preview (DEC-063). A signature or a declaration is an
        # image and gets one; a certificate assembled as a PDF does not, and
        # `preview_watermarked` stays False rather than claiming a mark that
        # was never applied.
        self.write_preview(record, result.content)
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
        # An assembled document is a PDF, so `write_preview` records that no
        # preview exists rather than inventing one (DEC-063). Called anyway so
        # the fields are set from the artifact and not left at their defaults.
        self.write_preview(record, result.content)
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
                # DEC-063: an unreleased file is described in the checklist
                # and left out of the archive.  Skipping it here rather than
                # only refusing at the route means a caller that reaches this
                # method directly still cannot obtain a file nobody paid for.
                released = self.output_is_released(record)
                item["awaiting_release"] = bool(record.output_filename) and not released
                if record.output_filename and servable and released:
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
            # DEC-063: how many prepared files the archive is holding back for
            # want of a payment.  The route refuses the download while this is
            # non-zero; the checklist itself stays readable, because what an
            # examination asks for is not something a candidate should have to
            # buy in order to see.
            "awaiting_release": sum(
                1 for item in items if item.get("awaiting_release")
            ),
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
        # DEC-075: progress files are genuinely ephemeral, so they ride the
        # existing sweeper rather than needing a retention decision of their
        # own the way `_orders/` and `_usage/` do.
        self.progress.sweep()

        records = self.registry.scan_manifests()
        deleted_count = 0

        for record in records:
            if record.status != ApiJobStatus.DELETED and record.is_expired():
                try:
                    self.store.delete_job_directory(record.job_id)
                except OSError:
                    # Another worker's sweeper may have removed this directory
                    # between the scan and now -- each uvicorn worker runs its
                    # own sweeper (DEC-064). One racing or locked directory
                    # must not abort the rest of the sweep, or a single stuck
                    # job would silently end retention for every other one.
                    continue
                self.registry.delete_job(record.job_id)
                deleted_count += 1

        return deleted_count
